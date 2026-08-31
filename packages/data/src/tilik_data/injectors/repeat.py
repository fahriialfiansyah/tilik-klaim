"""Repeat billing: a second claim covering services the first already billed.

Two shapes, and the injector produces both because the engine reports them differently.

An **obvious** repeat is a verbatim resubmission: same encounter, same lines, same total. Its
claim fingerprint matches the original exactly, so the expected reason is
`DUPLICATE_CLAIM_FINGERPRINT`.

A **moderate or subtle** repeat bills the same services again at a *different encounter*. The
fingerprint no longer matches, so the case falls to the weaker
`OVERLAPPING_CLAIM_SAME_EPISODE` — which is the honest outcome, because a second visit billing
the same service is exactly what legitimate repeat care looks like until a human weighs the
timing and the differing fields.

Getting this wrong is how a label lies. An earlier version copied the encounter for every
difficulty and then claimed the overlap reason, so the invariant test failed against the engine
— correctly, because the engine was right and the label was not.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from random import Random

from tilik_domain.canonical import CanonicalBundle, ResourceRef, ResourceType
from tilik_domain.reasons import ReasonCode, RiskMode

from tilik_data.injectors.labels import Difficulty, InjectionLabel


def _total(lines: tuple) -> Decimal:
    return sum((line.line_amount for line in lines), Decimal("0"))


DAY_SHIFT = {Difficulty.OBVIOUS: 0, Difficulty.MODERATE: 1, Difficulty.SUBTLE: 3}


def inject(
    bundle: CanonicalBundle, rng: Random, difficulty: Difficulty, injection_id: str, seed: int
) -> tuple[tuple[CanonicalBundle, ...], InjectionLabel] | None:
    """Produce a second claim overlapping the first. Both bundles are returned."""
    if not bundle.lines:
        return None

    suffix = f"R{rng.randrange(1000):03d}"
    shift = timedelta(days=DAY_SHIFT[difficulty])
    verbatim = difficulty is Difficulty.OBVIOUS

    # A subtle repeat drops a line, so the overlap is partial rather than total.
    kept = bundle.lines[:-1] if difficulty is Difficulty.SUBTLE and len(bundle.lines) > 1 else bundle.lines
    new_claim_id = f"{bundle.claim.claim_id}-{suffix}"

    lines = tuple(
        line.model_copy(
            update={
                "line_id": f"{line.line_id}-{suffix}",
                "claim_id": new_claim_id,
                "service_at": line.service_at + shift,
                # References point back at the original bundle's evidence, which is precisely
                # the overlap a reviewer needs to see.
            }
        )
        for line in kept
    )

    claim_updates = {
        "claim_id": new_claim_id,
        "submitted_at": bundle.claim.submitted_at + shift,
        "total_amount": _total(lines),
    }
    bundle_updates = {
        "bundle_id": f"{bundle.bundle_id}-{suffix}",
        "lines": lines,
    }

    if not verbatim:
        # A second visit: new encounter, so the fingerprint no longer matches and the case
        # resolves to the weaker overlap reason rather than an exact duplicate.
        new_encounter_id = f"{bundle.claim.encounter_id}-{suffix}"
        claim_updates["encounter_id"] = new_encounter_id
        bundle_updates["encounters"] = tuple(
            encounter.model_copy(
                update={
                    "encounter_id": new_encounter_id,
                    "start_at": encounter.start_at + shift,
                    "end_at": (encounter.end_at + shift) if encounter.end_at else None,
                }
            )
            for encounter in bundle.encounters
        )

    bundle_updates["claim"] = bundle.claim.model_copy(update=claim_updates)
    duplicate = bundle.model_copy(update=bundle_updates)

    expected = (
        ReasonCode.DUPLICATE_CLAIM_FINGERPRINT
        if verbatim
        else ReasonCode.OVERLAPPING_CLAIM_SAME_EPISODE
    )

    label = InjectionLabel(
        injection_id=injection_id,
        mode=RiskMode.REPEAT_BILLING,
        difficulty=difficulty,
        source_bundle_id=bundle.bundle_id,
        target_bundle_ids=(bundle.bundle_id, duplicate.bundle_id),
        expected_reason_codes=(expected,),
        expected_evidence_refs=(
            ResourceRef(resource_type=ResourceType.CLAIM, resource_id=bundle.claim.claim_id),
            ResourceRef(resource_type=ResourceType.CLAIM, resource_id=new_claim_id),
        ),
        violated_invariants=(
            "Satu layanan pada satu episode ditagihkan tepat satu kali.",
        ),
        seed=seed,
    )
    return (bundle, duplicate), label
