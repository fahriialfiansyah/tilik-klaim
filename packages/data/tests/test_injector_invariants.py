"""Each injector must make the rule it targets actually fire.

This is the assertion the whole corpus rests on. A label claiming "this bundle contains repeat
billing" is worth nothing unless the repeat rule actually fires on it — otherwise every recall
number measures the injector's imagination rather than the detector's ability.

**These tests import the rule engine from `apps/backend`.** That is a test-only dependency and
deliberately one-directional: `tilik_data` never imports the engine at runtime, because the
generator must not be able to see what the detector looks for. Importing it here, in a test, is
the only way to prove the two agree.
"""
from __future__ import annotations

import sys
from pathlib import Path
from random import Random

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND = REPO_ROOT / "apps" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.service.screening import screen_bundle  # noqa: E402
from tilik_domain.reasons import RiskMode  # noqa: E402

from tilik_data.corpus import InjectionPlan, build_corpus  # noqa: E402
from tilik_data.generator import generate_corpus  # noqa: E402
from tilik_data.injectors import clone, phantom, repeat, unbundling  # noqa: E402
from tilik_data.injectors.labels import Difficulty  # noqa: E402

SEED = 20260902
PLAN = InjectionPlan(
    per_mode=12,
    multi_label_ratio=0.05,
    difficulty_mix={"obvious": 0.3, "moderate": 0.5, "subtle": 0.2},
)


@pytest.fixture(scope="module")
def clean():
    return generate_corpus(SEED, 120, participant_count=40, provider_count=4)


def screen(bundle, history=(), peers=()):
    return screen_bundle(bundle, history, peers)


def codes(result) -> set[str]:
    return {str(hit.code) for hit in result.reasons}


# --------------------------------------------------------------------------------------
# The clean corpus must stay quiet — otherwise every "hit" below is meaningless
# --------------------------------------------------------------------------------------


def test_clean_bundles_raise_no_reasons(clean) -> None:
    """A clean corpus that already fires would make every precision number a fiction."""
    noisy = [bundle.bundle_id for bundle in clean if screen(bundle).reasons]
    assert not noisy, f"{len(noisy)} clean bundles fired without any injection: {noisy[:5]}"


# --------------------------------------------------------------------------------------
# One invariant test per injector
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_phantom_injector_makes_the_phantom_rule_fire(clean, difficulty) -> None:
    rng = Random(1)
    fired = 0
    attempted = 0
    for bundle in clean[:40]:
        outcome = phantom.inject(bundle, rng, difficulty, "INJ-T", SEED)
        if outcome is None:
            continue
        attempted += 1
        (mutated,), label = outcome
        result = screen(mutated)
        if set(str(code) for code in label.expected_reason_codes) & codes(result):
            fired += 1

    assert attempted, "no candidate bundles; the fixture cannot prove anything"
    assert fired == attempted, f"{attempted - fired}/{attempted} phantom injections did not fire"


@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_repeat_injector_makes_the_repeat_rule_fire(clean, difficulty) -> None:
    rng = Random(2)
    fired = attempted = 0
    for bundle in clean[:40]:
        outcome = repeat.inject(bundle, rng, difficulty, "INJ-T", SEED)
        if outcome is None:
            continue
        attempted += 1
        (original, duplicate), label = outcome
        result = screen(duplicate, history=(original,))
        if set(str(code) for code in label.expected_reason_codes) & codes(result):
            fired += 1

    assert attempted
    assert fired == attempted, f"{attempted - fired}/{attempted} repeat injections did not fire"


@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_unbundling_injector_makes_the_unbundling_rule_fire(clean, difficulty) -> None:
    rng = Random(3)
    fired = attempted = 0
    for bundle in clean[:60]:
        outcome = unbundling.inject(bundle, rng, difficulty, "INJ-T", SEED)
        if outcome is None:
            continue
        attempted += 1
        (first, second), label = outcome
        result = screen(second, history=(first,))
        if set(str(code) for code in label.expected_reason_codes) & codes(result):
            fired += 1

    assert attempted
    assert fired == attempted, f"{attempted - fired}/{attempted} unbundling injections missed"


@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_clone_injector_makes_the_clone_rule_fire(clean, difficulty) -> None:
    """Cloning is cross-participant, so the copy is compared against peer documents."""
    rng = Random(4)
    fired = attempted = 0
    by_provider: dict[str, list] = {}
    for bundle in clean:
        if bundle.documents:
            by_provider.setdefault(bundle.claim.provider_id, []).append(bundle)

    for bundles in by_provider.values():
        for source, target in zip(bundles, bundles[1:], strict=False):
            if source.claim.participant_id == target.claim.participant_id:
                continue
            outcome = clone.inject(source, target, rng, difficulty, "INJ-T", SEED)
            if outcome is None:
                continue
            attempted += 1
            (mutated,), label = outcome
            result = screen(mutated, peers=source.documents)
            if set(str(code) for code in label.expected_reason_codes) & codes(result):
                fired += 1

    assert attempted, "no cross-participant pairs at one provider; fixture too small"
    assert fired == attempted, f"{attempted - fired}/{attempted} clone injections did not fire"


# --------------------------------------------------------------------------------------
# Label quality
# --------------------------------------------------------------------------------------


def test_every_label_carries_expected_evidence_and_difficulty() -> None:
    corpus = build_corpus(SEED, claims=200, participants=60, providers=4, plan=PLAN)
    assert corpus.labels.labels
    for label in corpus.labels.labels:
        assert label.expected_reason_codes, f"{label.injection_id} expects no reason"
        assert label.expected_evidence_refs, f"{label.injection_id} names no evidence"
        assert label.violated_invariants, f"{label.injection_id} names no broken invariant"
        assert label.difficulty in set(Difficulty)
        assert label.injector_version and label.seed == SEED


def test_labels_are_excluded_from_features_by_construction() -> None:
    """The flag is asserted, not assumed — a leak should be a failed test, not an oversight."""
    corpus = build_corpus(SEED, claims=200, participants=60, providers=4, plan=PLAN)
    assert all(label.excluded_from_features for label in corpus.labels.labels)


def test_all_four_modes_are_represented() -> None:
    corpus = build_corpus(SEED, claims=400, participants=100, providers=6, plan=PLAN)
    counts = corpus.labels.counts_by_mode()
    for mode in RiskMode:
        assert counts.get(str(mode), 0) > 0, f"no injections for {mode}"


def test_multi_label_proportion_stays_within_its_cap() -> None:
    """Overlap is allowed and disclosed, never unbounded."""
    corpus = build_corpus(SEED, claims=400, participants=100, providers=6, plan=PLAN)
    assert corpus.labels.multi_label_ratio() <= PLAN.multi_label_ratio * 2


def test_no_label_uses_accusatory_naming() -> None:
    """Naming discipline: injection ground truth, never a claim about conduct."""
    corpus = build_corpus(SEED, claims=200, participants=60, providers=4, plan=PLAN)
    serialised = corpus.labels.model_dump_json().lower()
    for forbidden in ("fraud", "curang", "guilty", "is_fraud", "fraudulent"):
        assert forbidden not in serialised, f"label vocabulary contains {forbidden!r}"
