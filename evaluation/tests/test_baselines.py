"""What each baseline flags, how it ranks, and what it is honest about not knowing."""
from __future__ import annotations

import pytest
from runner.baselines import BaselineId, predictions_for, screen_all
from tilik_domain.reasons import PriorityBand
from tilik_model.dataset import TEST, build_contexts

SEED = 20260902


@pytest.fixture(scope="module")
def outcomes(artifacts, model):
    bundles = artifacts.partition(TEST)
    return screen_all(bundles, build_contexts(artifacts.bundles), model)


def test_every_bundle_is_screened_exactly_once(outcomes, artifacts) -> None:
    assert len(outcomes) == len(artifacts.partition(TEST))
    assert len({outcome.bundle_id for outcome in outcomes}) == len(outcomes)


def test_screening_records_a_latency_for_every_bundle(outcomes) -> None:
    assert all(outcome.latency_ms > 0 for outcome in outcomes)


def test_every_baseline_predicts_for_every_bundle(outcomes) -> None:
    for baseline in BaselineId:
        predictions = predictions_for(baseline, outcomes, seed=SEED)
        assert {p.bundle_id for p in predictions} == {o.bundle_id for o in outcomes}


def test_only_the_attributing_baselines_claim_a_mode(outcomes) -> None:
    """B0 and B2 produce a score, not a reason. Saying otherwise would be reading the answer."""
    for baseline in (BaselineId.B0_RANDOM, BaselineId.B2_STATISTICAL_ONLY):
        for prediction in predictions_for(baseline, outcomes, seed=SEED):
            assert not prediction.attributes_modes
            assert not prediction.modes
    for baseline in (BaselineId.B1_RULES_ONLY, BaselineId.HYBRID):
        assert all(p.attributes_modes for p in predictions_for(baseline, outcomes, seed=SEED))


def test_the_random_baseline_spends_the_same_review_budget_as_the_rules_baseline(
    outcomes,
) -> None:
    """Matched workload is what makes the comparison about *which* cases, not how many."""
    rules = predictions_for(BaselineId.B1_RULES_ONLY, outcomes, seed=SEED)
    random_ = predictions_for(BaselineId.B0_RANDOM, outcomes, seed=SEED)
    assert sum(p.flagged for p in random_) == sum(p.flagged for p in rules)


def test_the_random_baseline_is_reproducible_and_order_independent(outcomes) -> None:
    first = predictions_for(BaselineId.B0_RANDOM, outcomes, seed=SEED)
    shuffled = predictions_for(BaselineId.B0_RANDOM, tuple(reversed(outcomes)), seed=SEED)
    assert {p.bundle_id: p.score for p in first} == {p.bundle_id: p.score for p in shuffled}
    assert {p.bundle_id for p in first if p.flagged} == {
        p.bundle_id for p in shuffled if p.flagged
    }


def test_a_different_seed_produces_a_different_random_ordering(outcomes) -> None:
    """Otherwise the "random" baseline is a constant and proves nothing."""
    first = {p.bundle_id: p.score for p in predictions_for(BaselineId.B0_RANDOM, outcomes, seed=1)}
    second = {p.bundle_id: p.score for p in predictions_for(BaselineId.B0_RANDOM, outcomes, seed=2)}
    assert first != second


def test_the_hybrid_never_ranks_across_a_band_boundary(outcomes) -> None:
    """The band is a claim shown on screen; a tiebreak must not quietly contradict it."""
    from runner.baselines import BAND_RANK

    for prediction, outcome in zip(
        predictions_for(BaselineId.HYBRID, outcomes, seed=SEED), outcomes, strict=True
    ):
        assert int(prediction.score) == BAND_RANK[outcome.hybrid_band]


def test_the_rules_baseline_flags_exactly_what_the_engine_banded(outcomes) -> None:
    for prediction, outcome in zip(
        predictions_for(BaselineId.B1_RULES_ONLY, outcomes, seed=SEED), outcomes, strict=True
    ):
        assert prediction.flagged == (outcome.rules_band is not PriorityBand.NO_OBSERVED_RISK)


def test_the_rules_engine_actually_fires_on_this_corpus(outcomes) -> None:
    """If nothing fires the whole evaluation is measuring an empty comparison."""
    assert sum(1 for outcome in outcomes if outcome.flagged_by_rules) > 0
    assert {mode for outcome in outcomes for mode in outcome.reason_modes}


def test_displayed_evidence_resolves_to_real_resources(outcomes) -> None:
    """Explanation integrity: a reason pointing at nothing is worse than no reason.

    "Real" means anything the reviewer can open — the bundle, its history, and the peer notes a
    clone reason cites. Checking only the bundle reported 39 of 140 references as broken on this
    corpus, all of them clone reasons pointing at another participant's note, which is exactly
    where a clone reason is supposed to point.
    """
    total = sum(outcome.evidence_refs_total for outcome in outcomes)
    resolved = sum(outcome.evidence_refs_resolved for outcome in outcomes)
    assert total > 0, "no reason carried any evidence reference at all"
    assert resolved == total, f"{total - resolved} displayed references do not resolve"
