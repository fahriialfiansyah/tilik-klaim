"""Repeat billing: the same service billed more than once.

Two reasons live here, and the difference between them matters to a reviewer. An identical
claim fingerprint is an outright conflict. An overlap within one episode is weaker — a
legitimate repeat visit produces exactly that shape — so the rule surfaces the timing and the
differing fields and lets a person judge.

Neither reason says a claim should be rejected. `docs/canonical/05_model_card.md` is explicit
that an exact duplicate is high priority *and still human-reviewed*.
"""
from __future__ import annotations

import hashlib
from datetime import timedelta
from decimal import Decimal

from tilik_domain.canonical import CanonicalBundle, ResourceRef, ResourceType
from tilik_domain.edges import EdgeType
from tilik_domain.reasons import ReasonCode, RiskMode

from app.service.rules.registry import CounterEvidence, ReasonHit, RuleContext, make_hit

FOLLOW_UP_GRACE = timedelta(days=1)
"""Claims separated by more than this are far enough apart that a repeat visit is ordinary.

Inside the window, the same service billed twice is worth a look. Outside it, the passage of
time is itself the counter-argument, and the reason carries that.
"""


ROUNDING_TOLERANCE = Decimal("0.01")
"""Amounts within this are the same amount.

Claim totals are rounded at several points upstream. Comparing them exactly would let a one-cent
difference tell a reviewer the two claims bill different sums, which is noise presented as fact.
"""


class RepeatBillingRule:
    """Identical fingerprints, and overlapping lines inside one episode."""

    rule_id = "repeat/v1"
    mode = RiskMode.REPEAT_BILLING

    def evaluate(self, context: RuleContext) -> tuple[ReasonHit, ...]:
        bundle = context.bundle
        candidates = tuple(
            edge.target.resource_id
            for edge in context.graph.edges_of(EdgeType.POSSIBLE_DUPLICATE_OF)
        )
        if not candidates:
            return ()

        by_claim_id = {past.claim.claim_id: past for past in context.history}
        hits: list[ReasonHit] = []

        for claim_id in sorted(candidates):
            past = by_claim_id.get(claim_id)
            if past is None:
                continue
            hits.append(self._compare(bundle, past))

        return tuple(hits)

    def _compare(self, bundle: CanonicalBundle, past: CanonicalBundle) -> ReasonHit:
        current_ref = _claim_ref(bundle.claim.claim_id)
        past_ref = _claim_ref(past.claim.claim_id)
        overlap = _shared_codes(bundle, past)
        gap = abs(bundle.claim.submitted_at - past.claim.submitted_at)

        if _fingerprint(bundle) == _fingerprint(past):
            return make_hit(
                ReasonCode.DUPLICATE_CLAIM_FINGERPRINT,
                rule_id=self.rule_id,
                evidence=(current_ref, past_ref),
                counter_evidence=(
                    CounterEvidence(
                        note_id=(
                            "Sidik identik juga muncul saat klaim dikirim ulang "
                            "setelah koreksi administratif."
                        ),
                        refs=(past_ref,),
                    ),
                ),
                component_scores=(
                    ("fingerprint_match", 1.0),
                    ("shared_code_count", float(len(overlap))),
                    ("hours_apart", round(gap.total_seconds() / 3600, 3)),
                ),
            )

        return make_hit(
            ReasonCode.OVERLAPPING_CLAIM_SAME_EPISODE,
            rule_id=self.rule_id,
            evidence=(current_ref, past_ref, *_overlapping_line_refs(bundle, overlap)),
            counter_evidence=_overlap_counter_evidence(bundle, past, gap),
            component_scores=(
                ("fingerprint_match", 0.0),
                ("shared_code_count", float(len(overlap))),
                ("hours_apart", round(gap.total_seconds() / 3600, 3)),
            ),
        )


def _overlap_counter_evidence(
    bundle: CanonicalBundle, past: CanonicalBundle, gap: timedelta
) -> tuple[CounterEvidence, ...]:
    notes: list[CounterEvidence] = []
    if gap > FOLLOW_UP_GRACE:
        notes.append(
            CounterEvidence(
                note_id=(
                    f"Kedua klaim terpisah {gap.days} hari, jarak yang lazim "
                    "untuk kunjungan ulang yang sah."
                ),
                refs=(_claim_ref(past.claim.claim_id),),
            )
        )
    differing = _differing_fields(bundle, past)
    if differing:
        notes.append(
            CounterEvidence(
                note_id=(
                    "Bidang berikut berbeda antara kedua klaim, sehingga keduanya "
                    f"mungkin memang layanan terpisah: {', '.join(differing)}."
                ),
                refs=(_claim_ref(past.claim.claim_id),),
            )
        )
    return tuple(notes)


def _differing_fields(bundle: CanonicalBundle, past: CanonicalBundle) -> tuple[str, ...]:
    """Name what is *not* the same, so a reviewer can see the case against the signal."""
    checks = (
        ("kunjungan", bundle.claim.encounter_id != past.claim.encounter_id),
        (
            "total tagihan",
            abs(bundle.claim.total_amount - past.claim.total_amount) > ROUNDING_TOLERANCE,
        ),
        ("jumlah baris", len(bundle.lines) != len(past.lines)),
        ("jenis perawatan", bundle.claim.care_type != past.claim.care_type),
    )
    return tuple(label for label, differs in checks if differs)


def _fingerprint(bundle: CanonicalBundle) -> str:
    """A stable digest of what was billed, independent of claim ids and submission time.

    The encounter is part of the digest, and that inclusion is the whole distinction between
    this rule's two reasons. The same service billed twice for the *same visit* is a duplicate
    submission. The same service billed again at a *different visit* is ordinary repeat care
    until something else argues otherwise — so it falls through to the weaker overlap reason,
    where the reviewer sees the timing and the differing fields and decides.

    Matching fingerprints are a conflict worth surfacing. They are never proof of intent.
    """
    parts = [
        bundle.claim.participant_id,
        bundle.claim.provider_id,
        bundle.claim.encounter_id,
        str(bundle.claim.total_amount.quantize(ROUNDING_TOLERANCE)),
    ]
    parts.extend(
        sorted(
            f"{line.code_system}|{line.code}|{line.quantity}"
            f"|{line.line_amount.quantize(ROUNDING_TOLERANCE)}"
            for line in bundle.lines
        )
    )
    return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()


def _shared_codes(bundle: CanonicalBundle, past: CanonicalBundle) -> frozenset[str]:
    return _codes(bundle) & _codes(past)


def _codes(bundle: CanonicalBundle) -> frozenset[str]:
    return frozenset(f"{line.code_system}|{line.code}" for line in bundle.lines)


def _overlapping_line_refs(
    bundle: CanonicalBundle, overlap: frozenset[str]
) -> tuple[ResourceRef, ...]:
    return tuple(
        ResourceRef(resource_type=ResourceType.CLAIM_LINE, resource_id=line.line_id)
        for line in bundle.lines
        if f"{line.code_system}|{line.code}" in overlap
    )


def _claim_ref(claim_id: str) -> ResourceRef:
    return ResourceRef(resource_type=ResourceType.CLAIM, resource_id=claim_id)
