"""Extract the six feature families from a bundle, its history, and its facility peers.

**Nothing here reads an identifier.** Identifiers are used only for equality — does this
reference resolve, does this provenance entry belong to that record, is this the same facility —
never as a value. `tests/test_features.py` proves it by re-identifying an entire corpus and
asserting the feature table does not move, which is the only form of the leakage probe strong
enough to cover the injector suffix, the ordinal, and anything else an id might carry.

Peer statistics are **fitted**, and must be fitted on training bundles only. A profile built
over the whole corpus would let a test claim influence the peer median it is later compared
against — small, but it is exactly the kind of leak that makes a metric unreproducible.
"""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from decimal import Decimal

from tilik_domain.canonical import CanonicalBundle, DocumentRef, EventStatus
from tilik_domain.versioning import SCHEMA_VERSION

from tilik_model.feature_schema import (
    FEATURE_NAMES,
    FEATURE_SCHEMA,
    FeatureFamily,
    FeatureRow,
    FeatureSpec,
    spec_for,
)
from tilik_model.measures import (
    SECONDS_PER_DAY,
    clinical_event_statuses,
    line_fingerprints,
    max_jaccard,
    median,
    nearest_sequence_distance,
    robust_scale,
    service_sequence,
    visit_window,
    windows_overlap,
)

__all__ = [
    "FEATURE_NAMES",
    "FEATURE_SCHEMA",
    "FeatureExtractor",
    "FeatureFamily",
    "FeatureRow",
    "FeatureSpec",
    "PeerProfile",
    "spec_for",
]

ZERO, ONE = Decimal(0), Decimal(1)
"""Named so the reconciliation arithmetic reads as arithmetic, not as literals."""

ARITHMETIC_TOLERANCE = Decimal("0.01")
"""Matches the corpus rounding tolerance; a smaller gap is rounding, not an error."""

@dataclass(frozen=True)
class _PeerStats:
    """Robust location and scale for one facility, plus the codes it has billed."""

    line_count_median: float
    line_count_scale: float
    total_amount_median: float
    total_amount_scale: float
    codes: frozenset[str]


class PeerProfile:
    """What each facility's ordinary claim looks like, fitted from a set of bundles.

    Medians and median absolute deviations rather than means and standard deviations: a peer
    group of eight synthetic facilities has no protection against one extreme claim dragging a
    mean, and a deviation feature built on a dragged mean would report the *rest* of the group
    as unusual.
    """

    def __init__(self, by_provider: dict[str, _PeerStats]) -> None:
        self._by_provider = by_provider

    @classmethod
    def fit(cls, bundles: Iterable[CanonicalBundle]) -> PeerProfile:
        grouped: dict[str, list[CanonicalBundle]] = {}
        for bundle in bundles:
            grouped.setdefault(bundle.claim.provider_id, []).append(bundle)

        return cls(
            {
                provider: _PeerStats(
                    line_count_median=median([float(len(b.lines)) for b in members]),
                    line_count_scale=robust_scale([float(len(b.lines)) for b in members]),
                    total_amount_median=median([float(b.claim.total_amount) for b in members]),
                    total_amount_scale=robust_scale(
                        [float(b.claim.total_amount) for b in members]
                    ),
                    codes=frozenset(line.code for b in members for line in b.lines),
                )
                for provider, members in grouped.items()
            }
        )

    def providers(self) -> frozenset[str]:
        return frozenset(self._by_provider)

    def stats_for(self, provider_id: str) -> _PeerStats | None:
        """`None` is the cold start: this facility was not in the fitting set."""
        return self._by_provider.get(provider_id)


class FeatureExtractor:
    """Turn one bundle into one schema-conformant row."""

    def __init__(self, peers: PeerProfile) -> None:
        self.peers = peers

    def extract(
        self,
        bundle: CanonicalBundle,
        history: Sequence[CanonicalBundle] = (),
        peer_documents: Sequence[DocumentRef] = (),
    ) -> FeatureRow:
        """Compute every declared column.

        `history` is prior claims for the same participant at the same facility; `peer_documents`
        are notes from *other* participants at that facility. The split matters: repeat billing
        and unbundling are per-participant patterns, while cloning crosses participants.
        """
        computed: dict[str, float] = {}
        imputed: list[str] = []

        def record(name: str, value: float | None) -> None:
            """`None` means the measurement could not be made, so the declared stand-in is used."""
            if value is None:
                computed[name] = spec_for(name).imputation
                imputed.append(name)
            else:
                computed[name] = float(value)

        self._completeness(bundle, record)
        self._episode(bundle, history, record)
        self._similarity(bundle, history, peer_documents, record)
        self._peer_context(bundle, record)
        self._provenance(bundle, record)
        self._amounts(bundle, record)

        return FeatureRow(
            bundle_id=bundle.bundle_id,
            values=tuple(computed[name] for name in FEATURE_NAMES),
            imputed=tuple(name for name in FEATURE_NAMES if name in set(imputed)),
        )

    def extract_all(
        self, bundles: Sequence[CanonicalBundle], contexts: dict[str, tuple] | None = None
    ) -> tuple[FeatureRow, ...]:
        """Rows for a whole partition, in the order given."""
        contexts = contexts or {}
        return tuple(
            self.extract(bundle, *contexts.get(bundle.bundle_id, ((), ())))
            for bundle in bundles
        )

    # -- family 1: evidence completeness -------------------------------------------------
    def _completeness(self, bundle: CanonicalBundle, record) -> None:
        index = bundle.resource_index()
        resolvable = [
            any(ref.key() in index for ref in line.supporting_refs) for line in bundle.lines
        ]
        record(
            "unsupported_line_ratio",
            None if not resolvable else 1.0 - sum(resolvable) / len(resolvable),
        )
        record("dangling_reference_count", float(len(bundle.unresolved_refs())))

        events = clinical_event_statuses(bundle)
        record(
            "retracted_evidence_count",
            float(sum(1 for status in events if status is EventStatus.ENTERED_IN_ERROR)),
        )
        record(
            "noncompleted_evidence_ratio",
            None
            if not events
            else sum(1 for status in events if status is not EventStatus.COMPLETED) / len(events),
        )

    # -- family 2: episode integrity -----------------------------------------------------
    def _episode(
        self, bundle: CanonicalBundle, history: Sequence[CanonicalBundle], record
    ) -> None:
        if not history:
            for name in ("overlapping_history_claim_count", "days_to_nearest_related_claim",
                         "repeated_line_fingerprint_ratio", "exact_claim_fingerprint_match"):
                record(name, None)
            return

        window = visit_window(bundle)
        record(
            "overlapping_history_claim_count",
            float(sum(1 for past in history if windows_overlap(window, visit_window(past)))),
        )
        record(
            "days_to_nearest_related_claim",
            min(
                abs((bundle.claim.submitted_at - past.claim.submitted_at).total_seconds())
                / SECONDS_PER_DAY
                for past in history
            ),
        )

        mine = line_fingerprints(bundle)
        theirs = {fingerprint for past in history for fingerprint in line_fingerprints(past)}
        record(
            "repeated_line_fingerprint_ratio",
            None if not mine else sum(1 for f in mine if f in theirs) / len(mine),
        )
        record(
            "exact_claim_fingerprint_match",
            float(
                bool(mine)
                and any(sorted(line_fingerprints(past)) == sorted(mine) for past in history)
            ),
        )

    # -- family 3: similarity (structural; note text is scored by similarity.py) ----------
    def _similarity(
        self,
        bundle: CanonicalBundle,
        history: Sequence[CanonicalBundle],
        peer_documents: Sequence[DocumentRef],
        record,
    ) -> None:
        record(
            "max_history_procedure_jaccard",
            max_jaccard(
                {procedure.code for procedure in bundle.procedures},
                ({procedure.code for procedure in past.procedures} for past in history),
            ),
        )
        record(
            "max_history_condition_jaccard",
            max_jaccard(
                {condition.code for condition in bundle.conditions},
                ({condition.code for condition in past.conditions} for past in history),
            ),
        )

        record(
            "service_sequence_distance",
            nearest_sequence_distance(
                service_sequence(bundle), [service_sequence(past) for past in history]
            ),
        )

        digests = {document.text_hash for document in bundle.documents}
        peer_digests = {document.text_hash for document in peer_documents}
        record(
            "duplicate_note_digest_count",
            None if not digests or not peer_digests else float(len(digests & peer_digests)),
        )

    # -- family 4: peer context ----------------------------------------------------------
    def _peer_context(self, bundle: CanonicalBundle, record) -> None:
        stats = self.peers.stats_for(bundle.claim.provider_id)
        if stats is None:
            # Cold start. An unseen facility is not evidence of anything; say so explicitly.
            for name in ("line_count_peer_deviation", "total_amount_peer_deviation",
                         "unseen_service_code_ratio"):
                record(name, None)
            return

        record(
            "line_count_peer_deviation",
            abs(len(bundle.lines) - stats.line_count_median) / stats.line_count_scale,
        )
        record(
            "total_amount_peer_deviation",
            abs(float(bundle.claim.total_amount) - stats.total_amount_median)
            / stats.total_amount_scale,
        )
        codes = [line.code for line in bundle.lines]
        record(
            "unseen_service_code_ratio",
            None if not codes else sum(1 for code in codes if code not in stats.codes) / len(codes),
        )

    # -- family 5: provenance ------------------------------------------------------------
    def _provenance(self, bundle: CanonicalBundle, record) -> None:
        covered = {entry.resource_id for entry in bundle.provenance}
        resources = [resource_id for _, resource_id in bundle.resource_index()]
        record(
            "missing_provenance_ratio",
            None
            if not resources
            else sum(1 for resource_id in resources if resource_id not in covered)
            / len(resources),
        )
        record(
            "missing_authorship_ratio",
            None
            if not bundle.documents
            else sum(1 for document in bundle.documents if not document.author_id)
            / len(bundle.documents),
        )
        record(
            "provenance_version_mismatch_count",
            float(
                sum(1 for entry in bundle.provenance if entry.schema_version != SCHEMA_VERSION)
            ),
        )

    # -- family 6: amount and quantity ---------------------------------------------------
    def _amounts(self, bundle: CanonicalBundle, record) -> None:
        total = bundle.claim.total_amount
        line_sum = sum((line.line_amount for line in bundle.lines), ZERO)
        denominator = max(abs(total), ONE)
        record("reconciliation_delta_ratio", float(abs(total - line_sum) / denominator))
        record(
            "line_arithmetic_error_count",
            float(
                sum(
                    1
                    for line in bundle.lines
                    if abs(line.quantity * line.unit_price - line.line_amount)
                    > ARITHMETIC_TOLERANCE
                )
            ),
        )
        record(
            "max_line_amount_share",
            None
            if not bundle.lines or total == 0
            else float(max(line.line_amount for line in bundle.lines) / total),
        )
