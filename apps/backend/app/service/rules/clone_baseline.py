"""Cloned documentation: notes that read as copies of an earlier visit.

This is the transparent baseline the model card asks for — character n-gram similarity above a
validated threshold — and nothing more. It reads the `SIMILAR_TO` edges the evidence graph
already derived rather than recomputing similarity, so the score a reviewer sees on screen is
the same number that drew the edge.

The reason it emits is the only non-deterministic one in the catalog, and that has a
consequence enforced in `screening.py`: **text similarity alone can never reach the top band.**
Templated documentation is normal clinical practice, and a template is not a claim about
conduct.
"""
from __future__ import annotations

from tilik_domain.canonical import ResourceRef, ResourceType
from tilik_domain.edges import EdgeType
from tilik_domain.reasons import ReasonCode, RiskMode

from app.service.evidence_graph import SIMILARITY_CANDIDATE_FLOOR
from app.service.rules.registry import CounterEvidence, ReasonHit, RuleContext, make_hit

REPORTING_THRESHOLD = 0.7
"""Similarity at or above this is worth showing a reviewer.

Deliberately higher than the graph's candidate floor: the graph draws an edge so the pair can
be inspected, while this decides whether to raise a reason at all. The value is provisional and
is calibrated on validation data in Sprint 06 — it is not a "this much similarity means
cloning" threshold, and the band caps mean it can never by itself drive the top band.
"""


class CloneBaselineRule:
    """Near-duplicate clinical notes, scored by character n-gram overlap."""

    rule_id = "clone-baseline/v1"
    mode = RiskMode.CLONED_DOCUMENTATION

    def evaluate(self, context: RuleContext) -> tuple[ReasonHit, ...]:
        documents = {doc.document_id for doc in context.bundle.documents}
        hits: list[ReasonHit] = []

        for edge in context.graph.edges_of(EdgeType.SIMILAR_TO):
            if edge.source.resource_id not in documents:
                continue  # a history-to-history pair; not this claim's business
            score = edge.confidence
            if score is None or score < REPORTING_THRESHOLD:
                continue
            hits.append(self._hit(context, edge.source, edge.target, score))

        return tuple(hits)

    def _hit(
        self,
        context: RuleContext,
        source: ResourceRef,
        target: ResourceRef,
        score: float,
    ) -> ReasonHit:
        encounter_ref = ResourceRef(
            resource_type=ResourceType.ENCOUNTER,
            resource_id=context.bundle.claim.encounter_id,
        )
        return make_hit(
            ReasonCode.NEAR_DUPLICATE_DOCUMENTATION,
            rule_id=self.rule_id,
            evidence=(source, target, encounter_ref),
            counter_evidence=(
                CounterEvidence(
                    note_id=(
                        "Formulir dan templat catatan yang dipakai bersama menghasilkan "
                        "kemiripan tinggi tanpa ada yang disalin."
                    ),
                    refs=(target,),
                ),
                CounterEvidence(
                    note_id=(
                        "Keluhan yang berulang pada pasien yang sama wajar menghasilkan "
                        "catatan yang hampir sama."
                    ),
                ),
            ),
            component_scores=(
                ("text_similarity", score),
                ("candidate_floor", SIMILARITY_CANDIDATE_FLOOR),
                ("reporting_threshold", REPORTING_THRESHOLD),
            ),
        )
