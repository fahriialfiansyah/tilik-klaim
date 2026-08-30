"""Phantom billing: a billed line with no completed clinical event behind it.

This rule is the one most likely to cause harm if written carelessly, so it is deliberately
narrow. It reports what was *searched* and what was *missing* — never what someone did.

An incomplete record is not evidence a service was not delivered. That principle is enforced
twice: here, by attaching the incompleteness as counter-evidence on the reason itself, and
again in `screening.py`, which lowers the band and routes such a case to "request evidence"
instead of letting it climb toward "confirm anomaly".
"""
from __future__ import annotations

from tilik_domain.canonical import ClaimLine, ResourceRef, ResourceType
from tilik_domain.reasons import ReasonCode, RiskMode

from app.service.evidence_graph import GapReason
from app.service.rules.registry import CounterEvidence, ReasonHit, RuleContext, make_hit

MEDICATION_CODE_SYSTEMS: frozenset[str] = frozenset({"KFA", "ATC"})
"""Code systems that identify a dispensed medicine rather than a procedure.

A medicine line and a procedure line fail for different reasons and need different evidence
requests, so they carry different reason codes.
"""


class PhantomRule:
    """Billed lines with absent or retracted supporting evidence."""

    rule_id = "phantom/v1"
    mode = RiskMode.PHANTOM_OR_NO_PROCEDURE_EVIDENCE

    def evaluate(self, context: RuleContext) -> tuple[ReasonHit, ...]:
        graph, bundle = context.graph, context.bundle
        lines_by_id = {line.line_id: line for line in bundle.lines}
        hits: list[ReasonHit] = []

        retracted = {
            gap.source.resource_id: gap
            for gap in graph.gaps
            if gap.reason is GapReason.UNCOMPLETED_EVIDENCE
        }

        for line_id in sorted(graph.unsupported_line_ids()):
            line = lines_by_id.get(line_id)
            if line is None:
                continue  # a history line; this rule screens the claim under review

            gap = retracted.get(line_id)
            if gap is not None:
                hits.append(self._entered_in_error_hit(line, gap.target))
                continue
            hits.append(self._missing_evidence_hit(line, context))

        return tuple(hits)

    def _missing_evidence_hit(self, line: ClaimLine, context: RuleContext) -> ReasonHit:
        """Report an unevidenced line, naming where the evidence was looked for."""
        is_medication = line.code_system.upper() in MEDICATION_CODE_SYSTEMS
        code = (
            ReasonCode.LINE_WITHOUT_MEDICATION_DISPENSE
            if is_medication
            else ReasonCode.LINE_WITHOUT_COMPLETED_PROCEDURE
        )
        encounter_ref = ResourceRef(
            resource_type=ResourceType.ENCOUNTER,
            resource_id=context.bundle.claim.encounter_id,
        )
        return make_hit(
            code,
            rule_id=self.rule_id,
            evidence=(_line_ref(line), encounter_ref),
            counter_evidence=_incompleteness_notes(context),
            component_scores=(("supporting_refs_found", 0.0),),
        )

    def _entered_in_error_hit(
        self, line: ClaimLine, target: ResourceRef | None
    ) -> ReasonHit:
        """A retracted record is absent evidence, and the reason says exactly that."""
        evidence = [_line_ref(line)]
        if target is not None:
            evidence.append(target)
        return make_hit(
            ReasonCode.SUPPORTING_EVIDENCE_ENTERED_IN_ERROR,
            rule_id=self.rule_id,
            evidence=tuple(evidence),
            counter_evidence=(
                CounterEvidence(
                    note_id=(
                        "Penandaan keliru-input bisa berarti koreksi administratif, "
                        "bukan layanan yang tidak diberikan."
                    ),
                    refs=(target,) if target is not None else (),
                ),
            ),
            component_scores=(("supporting_refs_found", 0.0),),
        )


def _line_ref(line: ClaimLine) -> ResourceRef:
    return ResourceRef(resource_type=ResourceType.CLAIM_LINE, resource_id=line.line_id)


def _incompleteness_notes(context: RuleContext) -> tuple[CounterEvidence, ...]:
    """Every argument against a missing-evidence reason, attached to the reason itself.

    The first note is unconditional, and deliberately so. This is the most accusatory reason
    the engine can emit, and the bundle only ever shows what was *sent* — evidence may exist
    on paper, in another system, or simply not yet synced. Shipping this reason without that
    caveat would let "we have no record" read on screen as "it did not happen", which
    `docs/canonical/07_privacy_threat_model.md` forbids outright.

    The later notes are conditional: they fire only when this particular bundle is also
    incomplete, so "we searched and found nothing" stays visibly different from "we could not
    search properly".
    """
    notes: list[CounterEvidence] = [
        CounterEvidence(
            note_id=(
                "Bundel ini hanya memuat bukti yang ikut terkirim. Tidak ditemukannya "
                "catatan di sini bukan bukti bahwa layanan tidak diberikan — catatan "
                "bisa berada di berkas fisik atau sistem lain."
            ),
            refs=(
                ResourceRef(
                    resource_type=ResourceType.ENCOUNTER,
                    resource_id=context.bundle.claim.encounter_id,
                ),
            ),
        )
    ]

    dangling = tuple(
        gap.target
        for gap in context.graph.gaps
        if gap.reason is GapReason.DANGLING_REFERENCE and gap.target is not None
    )
    if dangling:
        notes.append(
            CounterEvidence(
                note_id=(
                    "Bundel ini memuat rujukan yang tidak dapat diselesaikan, "
                    "sehingga bukti pendukung mungkin ada tetapi tidak ikut terkirim."
                ),
                refs=dangling,
            )
        )
    if not context.bundle.encounters:
        notes.append(
            CounterEvidence(
                note_id=(
                    "Bundel tidak memuat data kunjungan, sehingga bukti klinis "
                    "tidak dapat ditelusuri sama sekali."
                )
            )
        )
    return tuple(notes)
