"""Unbundling: one episode's services split across temporally adjacent claims.

The split halves must bill *different* codes — that is what separates fragmentation from repeat
billing, where the halves overlap. Both claims keep the same episode id, so the relationship is
recorded rather than hidden; the pattern is the split itself, not concealment.

Staged care produces the same shape, which is why the engine returns that reading as
counter-evidence instead of resolving it. The injector cannot make the case unambiguous, and
should not try.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from random import Random

from tilik_domain.canonical import CanonicalBundle, ResourceRef, ResourceType
from tilik_domain.reasons import ReasonCode, RiskMode

from tilik_data.injectors.labels import Difficulty, InjectionLabel

DAY_GAP = {Difficulty.OBVIOUS: 1, Difficulty.MODERATE: 2, Difficulty.SUBTLE: 3}
MINIMUM_LINES_TO_SPLIT = 2


def inject(
    bundle: CanonicalBundle, rng: Random, difficulty: Difficulty, injection_id: str, seed: int
) -> tuple[tuple[CanonicalBundle, ...], InjectionLabel] | None:
    """Split one claim's lines into two adjacent claims sharing an episode."""
    if len(bundle.lines) < MINIMUM_LINES_TO_SPLIT:
        return None

    pivot = rng.randint(1, len(bundle.lines) - 1)
    first_lines, second_lines = bundle.lines[:pivot], bundle.lines[pivot:]

    # Fragmentation means the halves bill different things. If a code appears on both sides the
    # case is a repeat, not a split, and the label would be wrong.
    first_codes = {f"{line.code_system}|{line.code}" for line in first_lines}
    second_codes = {f"{line.code_system}|{line.code}" for line in second_lines}
    if first_codes & second_codes:
        return None

    gap = timedelta(days=DAY_GAP[difficulty])
    suffix = f"U{rng.randrange(1000):03d}"

    first = bundle.model_copy(
        update={
            "lines": first_lines,
            "claim": bundle.claim.model_copy(
                update={"total_amount": _total(first_lines)}
            ),
        }
    )
    second_claim_id = f"{bundle.claim.claim_id}-{suffix}"
    second = bundle.model_copy(
        update={
            "bundle_id": f"{bundle.bundle_id}-{suffix}",
            "lines": tuple(
                line.model_copy(
                    update={
                        "line_id": f"{line.line_id}-{suffix}",
                        "claim_id": second_claim_id,
                    }
                )
                for line in second_lines
            ),
            "claim": bundle.claim.model_copy(
                update={
                    "claim_id": second_claim_id,
                    "submitted_at": bundle.claim.submitted_at + gap,
                    "total_amount": _total(second_lines),
                }
            ),
        }
    )

    label = InjectionLabel(
        injection_id=injection_id,
        mode=RiskMode.UNBUNDLING_FRAGMENTATION,
        difficulty=difficulty,
        source_bundle_id=bundle.bundle_id,
        target_bundle_ids=(first.bundle_id, second.bundle_id),
        expected_reason_codes=(ReasonCode.EPISODE_SPLIT_ACROSS_CLAIMS,),
        expected_evidence_refs=(
            ResourceRef(resource_type=ResourceType.CLAIM, resource_id=bundle.claim.claim_id),
            ResourceRef(resource_type=ResourceType.CLAIM, resource_id=second_claim_id),
        ),
        violated_invariants=(
            "Satu episode ditagihkan dalam satu klaim kecuali ada tindak lanjut terdokumentasi.",
        ),
        seed=seed,
    )
    return (first, second), label


def _total(lines: tuple) -> Decimal:
    return sum((line.line_amount for line in lines), Decimal("0"))
