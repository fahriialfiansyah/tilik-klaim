"""Cloned documentation: one narrative reused across different patients.

**This injector needs two bundles from the same provider and different participants**, because
that is what cloning is. An injector that copied a note within one patient's own record would
produce a case the clone detector is not looking for — and would have hidden the very scoping
defect this project found the hard way.

Difficulty controls how much the copy is altered: an obvious clone is verbatim, a subtle one
changes a few words so exact-match fails and only n-gram similarity survives.
"""
from __future__ import annotations

from random import Random

from tilik_domain.canonical import CanonicalBundle, ResourceRef, ResourceType
from tilik_domain.reasons import ReasonCode, RiskMode

from tilik_data.injectors.labels import Difficulty, InjectionLabel
from tilik_data.vocab import similarity, text_hash

MINIMUM_RETAINED_SIMILARITY = 0.75
"""How similar an altered copy must remain for the injection to be labelled at all.

An injection whose label claims "the clone rule should fire" is a lie if the alteration left the
notes too different to recognise. Rather than emit an undetectable case and call it a miss, the
injector refuses: a short note that cannot absorb the alteration produces no injection.

Set above any reasonable detector reporting threshold so the guarantee holds without the
generator tuning itself to a specific detector.
"""

SUBTLE_SUBSTITUTIONS = (
    ("membaik", "menunjukkan perbaikan"),
    ("stabil", "relatif stabil"),
    ("kontrol ulang", "kontrol kembali"),
    ("lanjutkan terapi", "terapi diteruskan"),
)


def inject(
    source: CanonicalBundle,
    target: CanonicalBundle,
    rng: Random,
    difficulty: Difficulty,
    injection_id: str,
    seed: int,
) -> tuple[tuple[CanonicalBundle, ...], InjectionLabel] | None:
    """Copy `source`'s note into `target`, which belongs to a different participant."""
    if not source.documents or not target.documents:
        return None
    if source.claim.provider_id != target.claim.provider_id:
        return None
    if source.claim.participant_id == target.claim.participant_id:
        return None

    original = source.documents[0]
    if original.text is None:
        return None

    text = original.text
    if difficulty is not Difficulty.OBVIOUS:
        # Alter a little, so an exact-hash match no longer catches it. One substitution, not
        # several: short notes lose too much overlap when heavily reworded, and an unrecognisable
        # copy is not a clone.
        for find, replace in rng.sample(SUBTLE_SUBSTITUTIONS, k=1):
            text = text.replace(find, replace)
        if similarity(text, original.text) < MINIMUM_RETAINED_SIMILARITY:
            return None

    existing = target.documents[0]
    cloned = existing.model_copy(update={"text": text, "text_hash": text_hash(text)})
    mutated = target.model_copy(update={"documents": (cloned, *target.documents[1:])})

    label = InjectionLabel(
        injection_id=injection_id,
        mode=RiskMode.CLONED_DOCUMENTATION,
        difficulty=difficulty,
        source_bundle_id=source.bundle_id,
        target_bundle_ids=(mutated.bundle_id,),
        expected_reason_codes=(ReasonCode.NEAR_DUPLICATE_DOCUMENTATION,),
        expected_evidence_refs=(
            ResourceRef(resource_type=ResourceType.DOCUMENT, resource_id=cloned.document_id),
            ResourceRef(resource_type=ResourceType.DOCUMENT, resource_id=original.document_id),
        ),
        violated_invariants=(
            "Catatan dan urutan layanan bervariasi antar kunjungan.",
        ),
        seed=seed,
    )
    return (mutated,), label
