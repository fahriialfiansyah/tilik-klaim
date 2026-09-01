"""Every metric, checked against inputs small enough to verify by hand.

A metric implementation that is only ever run on 1,120 bundles is a metric nobody has checked.
These cases are four and five rows long on purpose: the expected value is written out in the
test, and a reader can confirm it without running anything.

The undefined cases matter as much as the arithmetic. A precision with no positive prediction
and a recall with no positive example are **undefined**, not zero, and reporting them as zero
would understate a baseline that simply never fired.
"""
from __future__ import annotations

import pytest
from runner.metrics import (
    REVIEW_BUDGET_FRACTION,
    GroundTruth,
    MetricStatus,
    Prediction,
    bootstrap_interval,
    false_positives_per_100_clean,
    macro_f1,
    per_mode_scores,
    percentile,
    precision_at_k,
    precision_recall_auc,
    ranked_at_budget,
    recall_at_k,
)
from tilik_domain.reasons import RiskMode

PHANTOM = RiskMode.PHANTOM_OR_NO_PROCEDURE_EVIDENCE
REPEAT = RiskMode.REPEAT_BILLING


def _truth(bundle_id: str, *modes: RiskMode) -> GroundTruth:
    return GroundTruth(bundle_id=bundle_id, modes=frozenset(modes))


def _prediction(bundle_id: str, flagged: bool, *modes: RiskMode, score: float = 0.0):
    return Prediction(
        bundle_id=bundle_id,
        flagged=flagged,
        modes=frozenset(modes),
        score=score,
        attributes_modes=True,
    )


def test_per_mode_scores_on_a_hand_checked_case() -> None:
    """Two true phantoms, one caught, one false alarm → precision 1/2, recall 1/2, F1 1/2."""
    truth = [_truth("A", PHANTOM), _truth("B", PHANTOM), _truth("C"), _truth("D")]
    predictions = [
        _prediction("A", True, PHANTOM),
        _prediction("B", False),
        _prediction("C", True, PHANTOM),
        _prediction("D", False),
    ]
    scores = per_mode_scores(predictions, truth)
    phantom = scores[PHANTOM]
    assert phantom.support == 2
    assert phantom.precision == pytest.approx(0.5)
    assert phantom.recall == pytest.approx(0.5)
    assert phantom.f1 == pytest.approx(0.5)
    assert phantom.status is MetricStatus.MEASURED


def test_a_mode_absent_from_the_test_set_is_reported_absent_not_zero() -> None:
    """A class with no examples has no recall. Zero would read as "we missed them all"."""
    truth = [_truth("A", PHANTOM), _truth("B")]
    predictions = [_prediction("A", True, PHANTOM), _prediction("B", False)]
    repeat = per_mode_scores(predictions, truth)[REPEAT]
    assert repeat.support == 0
    assert repeat.recall is None
    assert repeat.status is MetricStatus.ABSENT_FROM_TEST_SET


def test_a_mode_never_predicted_has_undefined_precision() -> None:
    """Nothing was flagged, so nothing flagged was wrong. That is not precision 0."""
    truth = [_truth("A", PHANTOM), _truth("B")]
    predictions = [_prediction("A", False), _prediction("B", False)]
    phantom = per_mode_scores(predictions, truth)[PHANTOM]
    assert phantom.precision is None
    assert phantom.recall == pytest.approx(0.0)
    assert phantom.status is MetricStatus.NO_POSITIVE_PREDICTION


def test_a_baseline_that_does_not_attribute_predicts_every_mode_when_it_flags() -> None:
    """That is what "no attribution" costs: precision drops, and it should."""
    truth = [_truth("A", PHANTOM), _truth("B", REPEAT), _truth("C")]
    blind = [
        Prediction(
            bundle_id=bundle_id,
            flagged=True,
            modes=frozenset(),
            score=1.0,
            attributes_modes=False,
        )
        for bundle_id in ("A", "B", "C")
    ]
    scores = per_mode_scores(blind, truth)
    # All three flagged, only one is truly phantom.
    assert scores[PHANTOM].precision == pytest.approx(1 / 3)
    assert scores[PHANTOM].recall == pytest.approx(1.0)


def test_macro_f1_averages_only_the_modes_it_could_measure() -> None:
    truth = [_truth("A", PHANTOM), _truth("B")]
    predictions = [_prediction("A", True, PHANTOM), _prediction("B", False)]
    scores = per_mode_scores(predictions, truth)
    assert macro_f1(scores) == pytest.approx(1.0)


def test_macro_f1_is_none_when_nothing_could_be_measured() -> None:
    truth = [_truth("A"), _truth("B")]
    predictions = [_prediction("A", False), _prediction("B", False)]
    assert macro_f1(per_mode_scores(predictions, truth)) is None


def test_false_positives_per_100_clean_claims() -> None:
    """Four clean claims, one flagged → 25 per 100."""
    truth = [_truth("A", PHANTOM), _truth("B"), _truth("C"), _truth("D"), _truth("E")]
    predictions = [
        _prediction("A", True, PHANTOM),
        _prediction("B", True, PHANTOM),
        _prediction("C", False),
        _prediction("D", False),
        _prediction("E", False),
    ]
    assert false_positives_per_100_clean(predictions, truth) == pytest.approx(25.0)


def test_false_positives_per_100_is_undefined_with_no_clean_claims() -> None:
    truth = [_truth("A", PHANTOM)]
    assert false_positives_per_100_clean([_prediction("A", True, PHANTOM)], truth) is None


def test_precision_and_recall_at_a_fixed_budget() -> None:
    """Budget of two: the two highest scores are reviewed, one of them is injected."""
    truth = [_truth("A", PHANTOM), _truth("B"), _truth("C", REPEAT), _truth("D")]
    predictions = [
        _prediction("A", True, PHANTOM, score=0.9),
        _prediction("B", True, PHANTOM, score=0.8),
        _prediction("C", False, score=0.2),
        _prediction("D", False, score=0.1),
    ]
    assert precision_at_k(predictions, truth, budget=2) == pytest.approx(0.5)
    assert recall_at_k(predictions, truth, budget=2) == pytest.approx(0.5)


def test_ties_are_broken_deterministically_by_identifier() -> None:
    """Equal scores must not make a run depend on dictionary order."""
    predictions = [
        _prediction("B", True, score=0.5),
        _prediction("A", True, score=0.5),
        _prediction("C", True, score=0.5),
    ]
    assert [p.bundle_id for p in ranked_at_budget(predictions, budget=3)] == ["A", "B", "C"]
    assert [p.bundle_id for p in ranked_at_budget(list(reversed(predictions)), budget=3)] == [
        "A",
        "B",
        "C",
    ]


def test_precision_recall_auc_is_one_for_a_perfect_ranking() -> None:
    truth = [_truth("A", PHANTOM), _truth("B", PHANTOM), _truth("C"), _truth("D")]
    perfect = [
        _prediction("A", True, PHANTOM, score=1.0),
        _prediction("B", True, PHANTOM, score=0.9),
        _prediction("C", False, score=0.2),
        _prediction("D", False, score=0.1),
    ]
    assert precision_recall_auc(perfect, truth) == pytest.approx(1.0)


def test_precision_recall_auc_of_a_useless_ranking_sits_near_the_base_rate() -> None:
    """Half the corpus injected and no signal → AUC around 0.5, not around 1."""
    truth = [_truth(f"B{i:02d}", PHANTOM) if i % 2 else _truth(f"B{i:02d}") for i in range(20)]
    flat = [_prediction(t.bundle_id, True, score=0.5) for t in truth]
    assert precision_recall_auc(flat, truth) == pytest.approx(0.5, abs=0.1)


def test_precision_recall_auc_is_undefined_with_no_positive_example() -> None:
    truth = [_truth("A"), _truth("B")]
    assert precision_recall_auc([_prediction("A", False), _prediction("B", False)], truth) is None


def test_percentiles_on_a_known_series() -> None:
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    assert percentile(values, 0.5) == pytest.approx(30.0)
    assert percentile(values, 0.95) == pytest.approx(48.0)
    assert percentile([], 0.5) is None


def test_the_review_budget_is_a_named_fraction_not_a_literal() -> None:
    assert 0.0 < REVIEW_BUDGET_FRACTION < 1.0


def test_bootstrap_interval_brackets_the_point_estimate() -> None:
    """A confidence interval that excludes its own estimate is a bug, not a wide interval."""
    truth = [_truth(f"B{i:02d}", PHANTOM) if i % 3 else _truth(f"B{i:02d}") for i in range(60)]
    predictions = [
        _prediction(t.bundle_id, bool(t.modes), *t.modes, score=1.0 if t.modes else 0.0)
        for t in truth
    ]
    point = macro_f1(per_mode_scores(predictions, truth))
    low, high = bootstrap_interval(
        predictions, truth, lambda p, t: macro_f1(per_mode_scores(p, t)), seed=7
    )
    assert low <= point <= high


def test_bootstrap_interval_is_reproducible() -> None:
    truth = [_truth(f"B{i:02d}", PHANTOM) if i % 3 else _truth(f"B{i:02d}") for i in range(40)]
    predictions = [
        _prediction(t.bundle_id, bool(t.modes), *t.modes, score=0.7) for t in truth
    ]

    def estimate(p, t):
        return macro_f1(per_mode_scores(p, t))
    assert bootstrap_interval(predictions, truth, estimate, seed=3) == bootstrap_interval(
        predictions, truth, estimate, seed=3
    )
