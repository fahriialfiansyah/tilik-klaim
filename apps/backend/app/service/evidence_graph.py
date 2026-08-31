"""Derive the canonical evidence graph over a validated bundle.

The graph is what makes "what supports this billed line?" answerable. Each edge records the
rule that produced it and the version of that rule, so a reviewer can follow any signal back
to the resources it came from — and so the same bundle screens identically twice.

Two properties matter more than completeness:

*Gaps are recorded, never raised.* An incomplete bundle is a normal input, not an error. A
missing link resolves to a gap the reviewer can see and act on. Treating incompleteness as
failure would quietly turn "we have no record of this" into "this did not happen", which
`docs/canonical/01_product_decision.md` forbids.

*Inference is labelled.* Structural edges are read straight out of the bundle and carry no
confidence. The two cross-claim edges are computed, so they always carry one. `EvidenceEdge`
enforces that split at construction time.

Contract: `docs/canonical/03_architecture.md` § Canonical evidence edges.
"""
from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

import networkx as nx
from pydantic import BaseModel, ConfigDict
from tilik_domain.canonical import (
    CanonicalBundle,
    ClaimLine,
    DocumentRef,
    EventStatus,
    ResourceRef,
    ResourceType,
)
from tilik_domain.edges import EdgeType, EvidenceEdge

if TYPE_CHECKING:
    from collections.abc import Iterable

# --------------------------------------------------------------------------------------
# Tunables. Each is a candidate-generation floor for drawing an edge — never a risk
# threshold. Bands and their calibration belong to the rule engine, which is the only place
# `docs/canonical/05_model_card.md` allows a threshold to influence a decision.
# --------------------------------------------------------------------------------------

SIMILARITY_CANDIDATE_FLOOR = 0.5
"""Below this, two notes are not similar enough to be worth a reviewer's attention."""

DUPLICATE_CANDIDATE_FLOOR = 0.5
"""Below this, two claims overlap too little to be offered as a duplicate candidate."""

SHINGLE_SIZE = 5
"""Character n-gram width for note similarity, per the model card's transparent baseline."""

FOLLOW_UP_DOCUMENT_KINDS: frozenset[str] = frozenset({"follow-up", "follow-up-note"})
"""Document kinds that document a legitimate return visit.

A follow-up is the ordinary reason two claims sit close together in one episode. Grouping
them anyway would manufacture a split-episode signal out of good clinical practice.
"""

EVIDENCE_BEARING_STATUSES: frozenset[EventStatus] = frozenset({EventStatus.COMPLETED})
"""Only a completed event evidences that a billed service happened.

`entered-in-error` deserves care: it is a retraction, so it counts as absent evidence rather
than as contradiction. The gap says which it was, and the rule engine states that reason.
"""


class GapReason(StrEnum):
    """Why a link the bundle implies could not be drawn."""

    DANGLING_REFERENCE = "DANGLING_REFERENCE"
    """A reference names a resource the bundle does not contain."""

    LINE_WITHOUT_SUPPORT = "LINE_WITHOUT_SUPPORT"
    """A billed line asserts no supporting evidence at all."""

    UNCOMPLETED_EVIDENCE = "UNCOMPLETED_EVIDENCE"
    """The supporting resource exists but its status does not evidence delivery."""


class EvidenceGap(BaseModel):
    """One link the bundle implies but the graph could not resolve.

    A gap is an observation about the record, never a finding about conduct.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    reason: GapReason
    edge_type: EdgeType
    source: ResourceRef
    target: ResourceRef | None = None
    detail: str = ""


class EvidenceGraph(BaseModel):
    """Derived edges and recorded gaps for one bundle, plus its history."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    bundle_id: str
    edges: tuple[EvidenceEdge, ...]
    gaps: tuple[EvidenceGap, ...]

    def edges_of(self, edge_type: EdgeType) -> tuple[EvidenceEdge, ...]:
        return tuple(edge for edge in self.edges if edge.edge_type is edge_type)

    def supported_line_ids(self) -> frozenset[str]:
        """Lines with at least one resolvable, evidence-bearing support."""
        return frozenset(
            edge.source.resource_id for edge in self.edges_of(EdgeType.SUPPORTED_BY)
        )

    def unsupported_line_ids(self) -> frozenset[str]:
        """Lines of *this* claim with no support. The phantom-billing observable."""
        billed = frozenset(
            edge.target.resource_id for edge in self.edges_of(EdgeType.CONTAINS)
        )
        return billed - self.supported_line_ids()

    def as_networkx(self) -> nx.MultiDiGraph:
        """The working graph, rebuilt on demand so the model itself stays immutable."""
        graph = nx.MultiDiGraph()
        for edge in self.edges:
            graph.add_edge(
                edge.source.key(),
                edge.target.key(),
                key=str(edge.edge_type),
                derivation_rule=edge.derivation_rule,
                ruleset_version=edge.ruleset_version,
                confidence=edge.confidence,
            )
        return graph


def build_evidence_graph(
    bundle: CanonicalBundle,
    history: Iterable[CanonicalBundle] = (),
    peer_documents: Iterable[DocumentRef] = (),
) -> EvidenceGraph:
    """Derive every canonical edge over `bundle`.

    `history` carries prior claims for the same participant at the same provider, which is what
    repeat billing and unbundling compare against. `peer_documents` carries notes from *other*
    participants at the same provider, because cloned documentation is a per-provider pattern —
    without them the clone detector cannot see anything. Only documents cross that wider
    boundary; whole bundles never do.

    Output ordering is stable regardless of how the input resources were ordered, so two runs
    of the same bundle diff to nothing.
    """
    prior = tuple(history)
    peers = tuple(peer_documents)
    edges: list[EvidenceEdge] = []
    gaps: list[EvidenceGap] = []

    _derive_structural(bundle, edges, gaps)
    for past in prior:
        _derive_structural(past, edges, gaps)

    _derive_episode_grouping(bundle, prior, edges)
    _derive_possible_duplicates(bundle, prior, edges)
    _derive_similar_documents(bundle, prior, peers, edges)

    return EvidenceGraph(
        bundle_id=bundle.bundle_id,
        edges=tuple(sorted(set(edges), key=_edge_sort_key)),
        gaps=tuple(sorted(set(gaps), key=_gap_sort_key)),
    )


# --------------------------------------------------------------------------------------
# Structural edges — read out of one bundle, never inferred
# --------------------------------------------------------------------------------------


def _derive_structural(
    bundle: CanonicalBundle,
    edges: list[EvidenceEdge],
    gaps: list[EvidenceGap],
) -> None:
    index = bundle.resource_index()
    claim_ref = _ref(ResourceType.CLAIM, bundle.claim.claim_id)

    edges.append(
        _stated(
            EdgeType.FOR_ENCOUNTER,
            claim_ref,
            _ref(ResourceType.ENCOUNTER, bundle.claim.encounter_id),
            "claim-for-encounter/v1",
        )
    )

    for line in bundle.lines:
        line_ref = _ref(ResourceType.CLAIM_LINE, line.line_id)
        edges.append(_stated(EdgeType.CONTAINS, claim_ref, line_ref, "claim-contains-line/v1"))
        _derive_line_billing(line, line_ref, index, edges, gaps)
        _derive_line_support(line, line_ref, index, edges, gaps)

    _derive_encounter_events(bundle, edges)
    _derive_document_edges(bundle, edges)


def _derive_line_billing(
    line: ClaimLine,
    line_ref: ResourceRef,
    index: dict[tuple[str, str], object],
    edges: list[EvidenceEdge],
    gaps: list[EvidenceGap],
) -> None:
    if line.charge_item_ref is None:
        return
    if line.charge_item_ref.key() not in index:
        gaps.append(
            EvidenceGap(
                reason=GapReason.DANGLING_REFERENCE,
                edge_type=EdgeType.BILLED_FROM,
                source=line_ref,
                target=line.charge_item_ref,
                detail="charge item is referenced but absent from the bundle",
            )
        )
        return
    edges.append(
        _stated(EdgeType.BILLED_FROM, line_ref, line.charge_item_ref, "line-billed-from/v1")
    )


def _derive_line_support(
    line: ClaimLine,
    line_ref: ResourceRef,
    index: dict[tuple[str, str], object],
    edges: list[EvidenceEdge],
    gaps: list[EvidenceGap],
) -> None:
    """Link a billed line to the clinical events that evidence it.

    A line with no support is the phantom-billing observable. It is recorded as a gap and
    nothing more — the rule engine decides what, if anything, it means.
    """
    if not line.supporting_refs:
        gaps.append(
            EvidenceGap(
                reason=GapReason.LINE_WITHOUT_SUPPORT,
                edge_type=EdgeType.SUPPORTED_BY,
                source=line_ref,
                detail="billed line asserts no supporting clinical evidence",
            )
        )
        return

    for ref in line.supporting_refs:
        resource = index.get(ref.key())
        if resource is None:
            gaps.append(
                EvidenceGap(
                    reason=GapReason.DANGLING_REFERENCE,
                    edge_type=EdgeType.SUPPORTED_BY,
                    source=line_ref,
                    target=ref,
                    detail="supporting resource is referenced but absent from the bundle",
                )
            )
            continue

        status = getattr(resource, "status", None)
        if isinstance(status, EventStatus) and status not in EVIDENCE_BEARING_STATUSES:
            gaps.append(
                EvidenceGap(
                    reason=GapReason.UNCOMPLETED_EVIDENCE,
                    edge_type=EdgeType.SUPPORTED_BY,
                    source=line_ref,
                    target=ref,
                    detail=f"supporting resource has status {status}",
                )
            )
            continue

        edges.append(_stated(EdgeType.SUPPORTED_BY, line_ref, ref, "line-supported-by/v1"))


def _derive_encounter_events(bundle: CanonicalBundle, edges: list[EvidenceEdge]) -> None:
    groups: tuple[tuple[ResourceType, tuple, str], ...] = (
        (ResourceType.CONDITION, bundle.conditions, "condition_id"),
        (ResourceType.PROCEDURE, bundle.procedures, "procedure_id"),
        (ResourceType.MEDICATION, bundle.medications, "medication_id"),
        (ResourceType.DOCUMENT, bundle.documents, "document_id"),
        (ResourceType.DIAGNOSTIC, bundle.diagnostics, "diagnostic_id"),
    )
    known_encounters = {encounter.encounter_id for encounter in bundle.encounters}
    for resource_type, items, id_field in groups:
        for item in items:
            if item.encounter_id not in known_encounters:
                continue  # the encounter itself is missing; that gap is the bundle's, not ours
            edges.append(
                _stated(
                    EdgeType.HAS_CLINICAL_EVENT,
                    _ref(ResourceType.ENCOUNTER, item.encounter_id),
                    _ref(resource_type, getattr(item, id_field)),
                    "encounter-has-event/v1",
                )
            )


def _derive_document_edges(bundle: CanonicalBundle, edges: list[EvidenceEdge]) -> None:
    known_encounters = {encounter.encounter_id for encounter in bundle.encounters}
    for document in bundle.documents:
        document_ref = _ref(ResourceType.DOCUMENT, document.document_id)
        if document.author_id is not None:
            edges.append(
                _stated(
                    EdgeType.AUTHORED_BY,
                    document_ref,
                    _ref(ResourceType.PRACTITIONER, document.author_id),
                    "document-authored-by/v1",
                )
            )
        if document.encounter_id in known_encounters:
            edges.append(
                _stated(
                    EdgeType.PART_OF_ENCOUNTER,
                    document_ref,
                    _ref(ResourceType.ENCOUNTER, document.encounter_id),
                    "document-part-of-encounter/v1",
                )
            )


# --------------------------------------------------------------------------------------
# Episode grouping and the two inferred cross-claim edges
# --------------------------------------------------------------------------------------


def _derive_episode_grouping(
    bundle: CanonicalBundle,
    history: tuple[CanonicalBundle, ...],
    edges: list[EvidenceEdge],
) -> None:
    """Group claims that share an episode, unless a follow-up documents the return visit."""
    episode_id = bundle.claim.episode_id
    if episode_id is None:
        return

    episode_ref = _ref(ResourceType.EPISODE, episode_id)
    edges.append(
        _stated(
            EdgeType.PART_OF_EPISODE,
            _ref(ResourceType.CLAIM, bundle.claim.claim_id),
            episode_ref,
            "claim-part-of-episode/v1",
        )
    )

    if _documents_a_follow_up(bundle):
        return

    for past in history:
        if past.claim.episode_id != episode_id:
            continue
        edges.append(
            _stated(
                EdgeType.PART_OF_EPISODE,
                _ref(ResourceType.CLAIM, past.claim.claim_id),
                episode_ref,
                "claim-part-of-episode/v1",
            )
        )


def _documents_a_follow_up(bundle: CanonicalBundle) -> bool:
    return any(
        document.kind.lower() in FOLLOW_UP_DOCUMENT_KINDS for document in bundle.documents
    )


def _derive_possible_duplicates(
    bundle: CanonicalBundle,
    history: tuple[CanonicalBundle, ...],
    edges: list[EvidenceEdge],
) -> None:
    """Offer prior claims that bill overlapping codes for the same participant and provider.

    This proposes a pair for a human to compare. It is not a duplicate finding: two claims can
    legitimately repeat a code, and the rule engine weighs the timing and amounts.
    """
    claim = bundle.claim
    codes = _billed_codes(bundle)
    if not codes:
        return

    source = _ref(ResourceType.CLAIM, claim.claim_id)
    for past in history:
        if past.claim.participant_id != claim.participant_id:
            continue
        if past.claim.provider_id != claim.provider_id:
            continue
        past_codes = _billed_codes(past)
        overlap = _jaccard(codes, past_codes)
        if not codes & past_codes or overlap < DUPLICATE_CANDIDATE_FLOOR:
            continue
        edges.append(
            _inferred(
                EdgeType.POSSIBLE_DUPLICATE_OF,
                source,
                _ref(ResourceType.CLAIM, past.claim.claim_id),
                "claim-code-overlap/v1",
                overlap,
            )
        )


def _derive_similar_documents(
    bundle: CanonicalBundle,
    history: tuple[CanonicalBundle, ...],
    peer_documents: tuple[DocumentRef, ...],
    edges: list[EvidenceEdge],
) -> None:
    """Link notes that read alike, so a reviewer can judge templating against copying.

    Candidates come from two places: this participant's own prior claims, and other
    participants' notes at the same provider. The second source is the one that matters —
    copying a narrative between patients is the pattern, and comparing a patient only against
    themselves would never reveal it.
    """
    own_ids = {document.document_id for document in bundle.documents}
    candidates: list[DocumentRef] = [
        candidate for past in history for candidate in past.documents
    ]
    candidates.extend(
        candidate for candidate in peer_documents if candidate.document_id not in own_ids
    )

    seen: set[tuple[str, str]] = set()
    for document in bundle.documents:
        source = _ref(ResourceType.DOCUMENT, document.document_id)
        for candidate in candidates:
            pair = (document.document_id, candidate.document_id)
            if pair in seen or candidate.document_id == document.document_id:
                continue
            seen.add(pair)
            score = _document_similarity(document, candidate)
            if score < SIMILARITY_CANDIDATE_FLOOR:
                continue
            edges.append(
                _inferred(
                    EdgeType.SIMILAR_TO,
                    source,
                    _ref(ResourceType.DOCUMENT, candidate.document_id),
                    f"document-char-{SHINGLE_SIZE}gram-jaccard/v1",
                    score,
                )
            )


def _document_similarity(left: DocumentRef, right: DocumentRef) -> float:
    """Character n-gram Jaccard, falling back to hash equality when text is withheld.

    Text is optional by design — `docs/canonical/07_privacy_threat_model.md` allows a bundle to
    carry only the hash. Identical hashes then mean identical text, which is certainty, not a
    guess; anything less is unknowable without the text and scores zero.
    """
    if left.text is None or right.text is None:
        return 1.0 if left.text_hash == right.text_hash else 0.0
    return _jaccard(_shingles(left.text), _shingles(right.text))


def _shingles(text: str) -> frozenset[str]:
    normalised = " ".join(text.lower().split())
    if len(normalised) < SHINGLE_SIZE:
        return frozenset({normalised}) if normalised else frozenset()
    return frozenset(
        normalised[i : i + SHINGLE_SIZE]
        for i in range(len(normalised) - SHINGLE_SIZE + 1)
    )


def _jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    union = left | right
    if not union:
        return 0.0
    return len(left & right) / len(union)


def _billed_codes(bundle: CanonicalBundle) -> frozenset[str]:
    return frozenset(f"{line.code_system}|{line.code}" for line in bundle.lines)


# --------------------------------------------------------------------------------------
# Construction helpers
# --------------------------------------------------------------------------------------


def _ref(resource_type: ResourceType, resource_id: str) -> ResourceRef:
    return ResourceRef(resource_type=resource_type, resource_id=resource_id)


def _stated(
    edge_type: EdgeType,
    source: ResourceRef,
    target: ResourceRef,
    derivation_rule: str,
) -> EvidenceEdge:
    return EvidenceEdge(
        edge_type=edge_type, source=source, target=target, derivation_rule=derivation_rule
    )


def _inferred(
    edge_type: EdgeType,
    source: ResourceRef,
    target: ResourceRef,
    derivation_rule: str,
    confidence: float,
) -> EvidenceEdge:
    return EvidenceEdge(
        edge_type=edge_type,
        source=source,
        target=target,
        derivation_rule=derivation_rule,
        confidence=round(confidence, 6),
    )


def _edge_sort_key(edge: EvidenceEdge) -> tuple[str, str, str, str, str]:
    return (
        str(edge.edge_type),
        str(edge.source.resource_type),
        edge.source.resource_id,
        str(edge.target.resource_type),
        edge.target.resource_id,
    )


def _gap_sort_key(gap: EvidenceGap) -> tuple[str, str, str, str]:
    target = gap.target
    return (
        str(gap.reason),
        str(gap.edge_type),
        gap.source.resource_id,
        target.resource_id if target is not None else "",
    )
