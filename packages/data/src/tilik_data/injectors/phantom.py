"""Phantom billing: a billed line whose supporting evidence is absent or retracted.

Two shapes, and the difference matters downstream. Removing the evidence outright leaves the
line unsupported. Marking it `entered-in-error` leaves a record that *exists* but no longer
evidences delivery — a retraction, which the engine must report differently because an
administrative correction is a plausible innocent explanation.

The line and its charge item stay untouched, so the claim total still reconciles. The injection
must break exactly one invariant; a second, accidental break would let a detector score a hit
for the wrong reason.
"""
from __future__ import annotations

from random import Random

from tilik_domain.canonical import CanonicalBundle, EventStatus, ResourceRef, ResourceType
from tilik_domain.reasons import ReasonCode, RiskMode

from tilik_data.injectors.labels import Difficulty, InjectionLabel


def inject(
    bundle: CanonicalBundle, rng: Random, difficulty: Difficulty, injection_id: str, seed: int
) -> tuple[tuple[CanonicalBundle, ...], InjectionLabel] | None:
    """Strip or retract the evidence behind one billed line.

    Returns `None` when the bundle offers nothing to work with — a single-line bundle whose one
    line is a medication, for instance. Skipping is correct; forcing an injection into an
    unsuitable record would produce a case the label misdescribes.
    """
    candidates = [
        (position, line)
        for position, line in enumerate(bundle.lines)
        if line.supporting_refs
    ]
    if not candidates:
        return None

    position, line = candidates[rng.randrange(len(candidates))]
    target_ref = line.supporting_refs[0]

    # Obvious: the evidence is simply gone. Subtle: it is still there but retracted, which reads
    # as a record-keeping issue until someone checks the status.
    retract = difficulty is not Difficulty.OBVIOUS and target_ref.resource_type is ResourceType.PROCEDURE

    if retract:
        procedures = tuple(
            procedure.model_copy(update={"status": EventStatus.ENTERED_IN_ERROR})
            if procedure.procedure_id == target_ref.resource_id
            else procedure
            for procedure in bundle.procedures
        )
        mutated = bundle.model_copy(update={"procedures": procedures})
        code = ReasonCode.SUPPORTING_EVIDENCE_ENTERED_IN_ERROR
        invariant = "Setiap baris tagihan punya satu peristiwa klinis berstatus selesai."
    else:
        stripped = line.model_copy(update={"supporting_refs": ()})
        lines = tuple(
            stripped if index == position else other
            for index, other in enumerate(bundle.lines)
        )
        procedures = tuple(
            procedure
            for procedure in bundle.procedures
            if procedure.procedure_id != target_ref.resource_id
        )
        medications = tuple(
            medication
            for medication in bundle.medications
            if medication.medication_id != target_ref.resource_id
        )
        mutated = bundle.model_copy(
            update={"lines": lines, "procedures": procedures, "medications": medications}
        )
        code = (
            ReasonCode.LINE_WITHOUT_MEDICATION_DISPENSE
            if target_ref.resource_type is ResourceType.MEDICATION
            else ReasonCode.LINE_WITHOUT_COMPLETED_PROCEDURE
        )
        invariant = "Setiap baris tagihan punya satu peristiwa klinis pendukung."

    label = InjectionLabel(
        injection_id=injection_id,
        mode=RiskMode.PHANTOM_OR_NO_PROCEDURE_EVIDENCE,
        difficulty=difficulty,
        source_bundle_id=bundle.bundle_id,
        target_bundle_ids=(mutated.bundle_id,),
        expected_reason_codes=(code,),
        expected_evidence_refs=(
            ResourceRef(resource_type=ResourceType.CLAIM_LINE, resource_id=line.line_id),
        ),
        violated_invariants=(invariant,),
        seed=seed,
    )
    return (mutated,), label
