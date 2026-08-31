"""Build the full corpus: generate clean records, verify them, then inject.

The order is a safety property, not a convenience. **The clean state is verified before anything
is injected**, because an injection into an already-inconsistent record produces a case whose
label is a lie — the detector might fire on the pre-existing defect and be scored as a hit. If
the base corpus does not hold, generation aborts rather than producing labelled noise.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from random import Random

from tilik_domain.canonical import CanonicalBundle
from tilik_domain.reasons import RiskMode

from tilik_data.amounts import ROUNDING_TOLERANCE
from tilik_data.generator import generate_corpus
from tilik_data.injectors import clone, phantom, repeat, unbundling
from tilik_data.injectors.labels import Difficulty, InjectionLabel, LabelSet


class BaseCorpusInconsistent(RuntimeError):
    """The clean corpus failed its own invariants. Injecting into it would produce bad labels."""


@dataclass(frozen=True)
class InjectionPlan:
    """How many of each mode, at which difficulties, and how much overlap is allowed."""

    per_mode: int
    multi_label_ratio: float
    difficulty_mix: dict[str, float]

    def difficulties(self, rng: Random, count: int) -> tuple[Difficulty, ...]:
        """Draw difficulties in the documented proportions, deterministically."""
        levels = [Difficulty(name) for name in self.difficulty_mix]
        weights = [self.difficulty_mix[str(level)] for level in levels]
        return tuple(rng.choices(levels, weights=weights, k=count))


@dataclass(frozen=True)
class Corpus:
    """The generated corpus and its ground truth."""

    bundles: tuple[CanonicalBundle, ...]
    labels: LabelSet
    clean_bundle_ids: frozenset[str]

    def injected_bundle_ids(self) -> frozenset[str]:
        return self.labels.bundle_ids()


def verify_clean(bundles: tuple[CanonicalBundle, ...]) -> None:
    """Assert the normal patterns hold before a single injection is made.

    Checks exactly the invariants the injectors will later break, so a break can only be
    attributable to an injection.
    """
    problems: list[str] = []
    for bundle in bundles:
        if bundle.unresolved_refs():
            problems.append(f"{bundle.bundle_id}: dangling references")

        line_sum = sum((line.line_amount for line in bundle.lines), Decimal("0"))
        if abs(bundle.claim.total_amount - line_sum) > ROUNDING_TOLERANCE:
            problems.append(f"{bundle.bundle_id}: total does not reconcile with lines")

        if any(not line.supporting_refs for line in bundle.lines):
            problems.append(f"{bundle.bundle_id}: billed line without supporting evidence")

        encounters = {encounter.encounter_id: encounter for encounter in bundle.encounters}
        for procedure in bundle.procedures:
            encounter = encounters.get(procedure.encounter_id)
            if encounter is None:
                problems.append(f"{bundle.bundle_id}: procedure outside any encounter")
            elif procedure.performed_at < encounter.start_at:
                problems.append(f"{bundle.bundle_id}: procedure precedes its encounter")

        ids = [line.line_id for line in bundle.lines]
        if len(ids) != len(set(ids)):
            problems.append(f"{bundle.bundle_id}: duplicate line ids")

    if problems:
        raise BaseCorpusInconsistent(
            f"{len(problems)} problem(s) in the clean corpus; refusing to inject. "
            f"First few: {problems[:5]}"
        )


def build_corpus(
    seed: int,
    *,
    claims: int,
    participants: int,
    providers: int,
    plan: InjectionPlan,
) -> Corpus:
    """Generate, verify, then inject. Deterministic for a given seed."""
    clean = generate_corpus(
        seed, claims, participant_count=participants, provider_count=providers
    )
    verify_clean(clean)

    rng = Random(seed ^ 0x5EED)
    by_id = {bundle.bundle_id: bundle for bundle in clean}
    labels: list[InjectionLabel] = []
    touched: set[str] = set()

    order = list(clean)
    rng.shuffle(order)
    cursor = 0

    def take() -> CanonicalBundle | None:
        """Pick the next bundle to inject into.

        Usually a fresh one, so most cases carry exactly one cause. But at the configured
        `multi_label_ratio` an already-injected bundle is deliberately reused, producing a case
        with more than one problem. That overlap is not an accident to be avoided: real claims
        carry several issues at once, and an evaluation where every case has exactly one cause
        would be measuring an easier problem than the real one. The proportion is capped by
        configuration and reported in the data card rather than left implicit.
        """
        nonlocal cursor
        if touched and rng.random() < plan.multi_label_ratio:
            reused = sorted(touched)[rng.randrange(len(touched))]
            existing = by_id.get(reused)
            if existing is not None:
                return existing
        while cursor < len(order):
            candidate = order[cursor]
            cursor += 1
            if candidate.bundle_id not in touched:
                return candidate
        return None

    for mode in RiskMode:
        difficulties = plan.difficulties(rng, plan.per_mode)
        made = 0
        while made < plan.per_mode:
            bundle = take()
            if bundle is None:
                break  # corpus exhausted; report what was achieved rather than looping
            outcome = _apply(mode, bundle, order, rng, difficulties[made], seed, len(labels))
            if outcome is None:
                continue
            produced, label = outcome
            for mutated in produced:
                by_id[mutated.bundle_id] = mutated
                touched.add(mutated.bundle_id)
            labels.append(label)
            made += 1

    labelled = _mark_multi_label(tuple(labels))
    return Corpus(
        bundles=tuple(by_id[key] for key in sorted(by_id)),
        labels=LabelSet(labels=labelled, seed=seed),
        clean_bundle_ids=frozenset(
            bundle.bundle_id for bundle in clean if bundle.bundle_id not in touched
        ),
    )


def _apply(
    mode: RiskMode,
    bundle: CanonicalBundle,
    pool: list[CanonicalBundle],
    rng: Random,
    difficulty: Difficulty,
    seed: int,
    ordinal: int,
) -> tuple[tuple[CanonicalBundle, ...], InjectionLabel] | None:
    injection_id = f"INJ-{ordinal:05d}"
    if mode is RiskMode.PHANTOM_OR_NO_PROCEDURE_EVIDENCE:
        return phantom.inject(bundle, rng, difficulty, injection_id, seed)
    if mode is RiskMode.REPEAT_BILLING:
        return repeat.inject(bundle, rng, difficulty, injection_id, seed)
    if mode is RiskMode.UNBUNDLING_FRAGMENTATION:
        return unbundling.inject(bundle, rng, difficulty, injection_id, seed)

    # Cloning needs a second bundle: same provider, different participant.
    partner = next(
        (
            other
            for other in pool
            if other.bundle_id != bundle.bundle_id
            and other.claim.provider_id == bundle.claim.provider_id
            and other.claim.participant_id != bundle.claim.participant_id
            and other.documents
        ),
        None,
    )
    if partner is None:
        return None
    return clone.inject(partner, bundle, rng, difficulty, injection_id, seed)


def _mark_multi_label(labels: tuple[InjectionLabel, ...]) -> tuple[InjectionLabel, ...]:
    """Flag every label whose bundles are touched by more than one injection.

    Overlap is allowed and disclosed rather than prevented: real cases carry more than one
    problem, and an evaluation that assumes exactly one cause per case would be measuring an
    easier problem than the real one.
    """
    occupancy: dict[str, int] = {}
    for label in labels:
        for bundle_id in label.target_bundle_ids:
            occupancy[bundle_id] = occupancy.get(bundle_id, 0) + 1

    return tuple(
        label.model_copy(
            update={
                "is_multi_label": any(
                    occupancy[bundle_id] > 1 for bundle_id in label.target_bundle_ids
                )
            }
        )
        for label in labels
    )
