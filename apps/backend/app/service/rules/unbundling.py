"""Unbundling: one episode's services split across several nearby claims.

The signal is *fragmentation*, which is the opposite of the repeat rule's overlap: the same
episode, close in time, but billing different codes. Because splitting is also what legitimate
staged care looks like, the rule leans on the evidence graph's episode grouping — which already
declines to merge claims when a follow-up document explains the return visit.
"""
from __future__ import annotations

from datetime import timedelta

from tilik_domain.canonical import CanonicalBundle, ResourceRef, ResourceType
from tilik_domain.edges import EdgeType
from tilik_domain.reasons import ReasonCode, RiskMode

from app.service.rules.registry import CounterEvidence, ReasonHit, RuleContext, make_hit

ADJACENCY_WINDOW = timedelta(days=3)
"""How close two claims must sit before splitting is worth a reviewer's time.

Beyond this, an episode spanning several claims is ordinary continuing care.
"""

MINIMUM_FRAGMENTS = 2
"""One claim cannot be a split. The pattern needs at least a pair."""


class UnbundlingRule:
    """Sibling claims in one episode that bill disjoint services close together."""

    rule_id = "unbundling/v1"
    mode = RiskMode.UNBUNDLING_FRAGMENTATION

    def evaluate(self, context: RuleContext) -> tuple[ReasonHit, ...]:
        bundle = context.bundle
        episode_id = bundle.claim.episode_id
        if episode_id is None:
            return ()

        grouped = {
            edge.source.resource_id
            for edge in context.graph.edges_of(EdgeType.PART_OF_EPISODE)
            if edge.target.resource_id == episode_id
        }
        siblings = tuple(
            past
            for past in context.history
            if past.claim.claim_id in grouped
            and past.claim.claim_id != bundle.claim.claim_id
        )
        if len(siblings) + 1 < MINIMUM_FRAGMENTS:
            return ()

        adjacent = tuple(
            past
            for past in siblings
            if abs(bundle.claim.submitted_at - past.claim.submitted_at) <= ADJACENCY_WINDOW
        )
        if not adjacent:
            return ()

        # Overlapping codes are the repeat rule's business. Fragmentation means the split
        # halves bill *different* things, so a full overlap is not this pattern.
        distinct = tuple(past for past in adjacent if not _codes(bundle) & _codes(past))
        if not distinct:
            return ()

        return (self._hit(bundle, distinct, episode_id),)

    def _hit(
        self,
        bundle: CanonicalBundle,
        siblings: tuple[CanonicalBundle, ...],
        episode_id: str,
    ) -> ReasonHit:
        evidence = [
            _claim_ref(bundle.claim.claim_id),
            ResourceRef(
                resource_type=ResourceType.ENCOUNTER,
                resource_id=bundle.claim.encounter_id,
            ),
        ]
        evidence.extend(_claim_ref(past.claim.claim_id) for past in siblings)

        spans = [
            abs(bundle.claim.submitted_at - past.claim.submitted_at) for past in siblings
        ]
        split_total = sum(past.claim.total_amount for past in siblings)

        return make_hit(
            ReasonCode.EPISODE_SPLIT_ACROSS_CLAIMS,
            rule_id=self.rule_id,
            evidence=tuple(evidence),
            counter_evidence=_staged_care_notes(siblings, episode_id),
            component_scores=(
                ("fragment_count", float(len(siblings) + 1)),
                ("max_hours_apart", round(max(spans).total_seconds() / 3600, 3)),
                ("sibling_total_amount", float(split_total)),
            ),
        )


def _staged_care_notes(
    siblings: tuple[CanonicalBundle, ...], episode_id: str
) -> tuple[CounterEvidence, ...]:
    """Staged care is the honest alternative reading, and it must appear on the same screen."""
    notes = [
        CounterEvidence(
            note_id=(
                "Layanan bertahap yang direncanakan juga tampak seperti ini: satu episode, "
                "beberapa klaim berdekatan, dengan tindakan yang berbeda-beda."
            ),
            refs=tuple(_claim_ref(past.claim.claim_id) for past in siblings),
        ),
        CounterEvidence(
            note_id=(
                f"Klaim-klaim ini memang dikelompokkan pada episode {episode_id}, "
                "sehingga keterkaitannya sudah tercatat dan bukan temuan tersembunyi."
            ),
        ),
    ]
    return tuple(notes)


def _codes(bundle: CanonicalBundle) -> frozenset[str]:
    return frozenset(f"{line.code_system}|{line.code}" for line in bundle.lines)


def _claim_ref(claim_id: str) -> ResourceRef:
    return ResourceRef(resource_type=ResourceType.CLAIM, resource_id=claim_id)
