"""The seven primary metrics from `docs/canonical/06_evaluation_plan.md` § Primary metrics.

Three conventions run through this module, and each exists because the obvious alternative
would misreport a result.

**Undefined is not zero.** Precision with no positive prediction, recall with no positive
example, and false-positives-per-100 with no clean claim are all undefined. Returning `0.0`
would make a baseline that never fired look like one that fired and was always wrong, which is
the opposite of what happened. Every such value is `None` and carries a `MetricStatus` naming
why.

**A baseline that cannot attribute a mode predicts every mode when it flags.** B0 and B2 produce
a score, not a reason: they can say "look at this claim" but not "because the procedure record
is missing". Scoring them as if a flag were a correct attribution would be circular — it would
read the answer off the ground truth. So a flag counts as a prediction for all four modes, and
per-mode precision falls accordingly. That is what the absence of attribution costs, measured
rather than argued.

**Ties are broken by identifier, ascending.** Equal scores are common — a band-based ranking
produces at most four distinct values — and without a stated tie-break the review order would
depend on dictionary ordering and a re-run would not reproduce.
"""
from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from random import Random

from tilik_domain.reasons import RiskMode

REVIEW_BUDGET_FRACTION = 0.10
"""Share of the test set a reviewer is assumed able to work through.

A tenth is already a large ask of a real reviewer, and prioritisation only means anything
against a budget smaller than the queue. Named here so the number in the proposal has a source.
"""

BOOTSTRAP_RESAMPLES = 1000
BOOTSTRAP_INTERVAL = 0.95


class MetricStatus(StrEnum):
    """Why a metric is missing, when it is."""

    MEASURED = "measured"
    ABSENT_FROM_TEST_SET = "absent_from_test_set"
    """No example of this class reached the test partition, so recall has no denominator."""
    NO_POSITIVE_PREDICTION = "no_positive_prediction"
    """Nothing was flagged for this class, so precision has no denominator."""


@dataclass(frozen=True)
class GroundTruth:
    """What the generator actually injected into one bundle. Empty `modes` means clean."""

    bundle_id: str
    modes: frozenset[RiskMode]
    difficulty: str | None = None
    is_multi_label: bool = False

    @property
    def is_injected(self) -> bool:
        return bool(self.modes)


@dataclass(frozen=True)
class Prediction:
    """What one baseline said about one bundle."""

    bundle_id: str
    flagged: bool
    """Whether this baseline raised the case at all."""
    modes: frozenset[RiskMode]
    """Modes it attributed. Empty when `attributes_modes` is false."""
    score: float
    """Continuous ranking score. Higher means reviewed sooner."""
    attributes_modes: bool
    """False for a score-only baseline, which can raise a case but not say why."""

    def predicts(self, mode: RiskMode) -> bool:
        if not self.flagged:
            return False
        return mode in self.modes if self.attributes_modes else True


@dataclass(frozen=True)
class ModeScore:
    """Precision, recall, and F1 for one risk mode — any of them possibly undefined."""

    mode: RiskMode
    precision: float | None
    recall: float | None
    f1: float | None
    support: int
    predicted: int
    status: MetricStatus


def per_mode_scores(
    predictions: Sequence[Prediction], truth: Sequence[GroundTruth]
) -> dict[RiskMode, ModeScore]:
    """Precision, recall, and F1 for each of the four modes."""
    by_id = {item.bundle_id: item for item in truth}
    return {
        mode: _score_one_mode(mode, predictions, by_id) for mode in RiskMode
    }


def _score_one_mode(
    mode: RiskMode, predictions: Sequence[Prediction], truth: dict[str, GroundTruth]
) -> ModeScore:
    true_positive = false_positive = false_negative = 0
    support = sum(1 for item in truth.values() if mode in item.modes)

    for prediction in predictions:
        actual = truth.get(prediction.bundle_id)
        if actual is None:
            continue
        predicted = prediction.predicts(mode)
        is_true = mode in actual.modes
        if predicted and is_true:
            true_positive += 1
        elif predicted:
            false_positive += 1
        elif is_true:
            false_negative += 1

    predicted_total = true_positive + false_positive
    if support == 0:
        status = MetricStatus.ABSENT_FROM_TEST_SET
    elif predicted_total == 0:
        status = MetricStatus.NO_POSITIVE_PREDICTION
    else:
        status = MetricStatus.MEASURED

    precision = true_positive / predicted_total if predicted_total else None
    recall = true_positive / support if support else None
    return ModeScore(
        mode=mode,
        precision=precision,
        recall=recall,
        f1=_harmonic_mean(precision, recall),
        support=support,
        predicted=predicted_total,
        status=status,
    )


def macro_f1(scores: dict[RiskMode, ModeScore]) -> float | None:
    """Mean F1 across the modes that could be measured. `None` when none could."""
    measurable = [score.f1 for score in scores.values() if score.f1 is not None]
    return sum(measurable) / len(measurable) if measurable else None


def false_positives_per_100_clean(
    predictions: Sequence[Prediction], truth: Sequence[GroundTruth]
) -> float | None:
    """Workload a reviewer absorbs for nothing, per hundred clean claims."""
    by_id = {item.bundle_id: item for item in truth}
    clean = [item for item in by_id.values() if not item.is_injected]
    if not clean:
        return None
    clean_ids = {item.bundle_id for item in clean}
    flagged_clean = sum(
        1 for prediction in predictions if prediction.flagged and prediction.bundle_id in clean_ids
    )
    return 100.0 * flagged_clean / len(clean)


def ranked_at_budget(
    predictions: Sequence[Prediction], budget: int
) -> tuple[Prediction, ...]:
    """The cases a reviewer would actually open, highest score first, ties by identifier."""
    ordered = sorted(predictions, key=lambda item: (-item.score, item.bundle_id))
    return tuple(ordered[: max(budget, 0)])


def budget_for(population: int, fraction: float = REVIEW_BUDGET_FRACTION) -> int:
    """At least one case, so a tiny partition still produces a defined metric."""
    return max(1, round(population * fraction))


def precision_at_k(
    predictions: Sequence[Prediction], truth: Sequence[GroundTruth], budget: int
) -> float | None:
    reviewed = ranked_at_budget(predictions, budget)
    if not reviewed:
        return None
    by_id = {item.bundle_id: item for item in truth}
    hits = sum(
        1
        for prediction in reviewed
        if (actual := by_id.get(prediction.bundle_id)) is not None and actual.is_injected
    )
    return hits / len(reviewed)


def recall_at_k(
    predictions: Sequence[Prediction], truth: Sequence[GroundTruth], budget: int
) -> float | None:
    injected = [item for item in truth if item.is_injected]
    if not injected:
        return None
    reviewed = {prediction.bundle_id for prediction in ranked_at_budget(predictions, budget)}
    return sum(1 for item in injected if item.bundle_id in reviewed) / len(injected)


def precision_recall_auc(
    predictions: Sequence[Prediction], truth: Sequence[GroundTruth]
) -> float | None:
    """Area under the precision–recall curve, by the trapezoid rule over every cut point.

    Precision–recall rather than ROC: the canonical evaluation plan makes PR the headline
    because the positive class is rare, and ROC flatters a ranker under that imbalance.
    """
    by_id = {item.bundle_id: item for item in truth}
    ordered = sorted(predictions, key=lambda item: (-item.score, item.bundle_id))
    labels = [
        bool(actual.is_injected)
        for prediction in ordered
        if (actual := by_id.get(prediction.bundle_id)) is not None
    ]
    positives = sum(labels)
    if not positives:
        return None

    area = 0.0
    true_positive = 0
    previous_recall = 0.0
    for index, is_positive in enumerate(labels, start=1):
        true_positive += 1 if is_positive else 0
        if not is_positive:
            continue
        precision = true_positive / index
        recall = true_positive / positives
        area += precision * (recall - previous_recall)
        previous_recall = recall
    return area


def percentile(values: Sequence[float], quantile: float) -> float | None:
    """Linear-interpolated percentile. `None` for an empty series rather than a crash."""
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = quantile * (len(ordered) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def bootstrap_interval(
    predictions: Sequence[Prediction],
    truth: Sequence[GroundTruth],
    estimate: Callable[[Sequence[Prediction], Sequence[GroundTruth]], float | None],
    *,
    seed: int,
    resamples: int = BOOTSTRAP_RESAMPLES,
    interval: float = BOOTSTRAP_INTERVAL,
) -> tuple[float, float] | None:
    """Percentile bootstrap over bundles, resampled together with their ground truth.

    Predictions and truth are resampled as **pairs**. Resampling them independently would
    scramble the correspondence and produce an interval for a quantity nobody computed.

    Each drawn pair is **relabelled with a fresh identifier**. Resampling with replacement draws
    the same bundle more than once, and the metric functions key ground truth by identifier — so
    without relabelling the duplicates collapse in the denominator while still counting in the
    numerator, and recall climbs above one.
    """
    by_id = {item.bundle_id: item for item in predictions}
    paired = [(by_id[item.bundle_id], item) for item in truth if item.bundle_id in by_id]
    if not paired:
        return None

    rng = Random(seed)
    estimates: list[float] = []
    for _ in range(resamples):
        drawn = [paired[rng.randrange(len(paired))] for _ in range(len(paired))]
        sample = [
            (
                replace(prediction, bundle_id=f"R{index:06d}"),
                replace(actual, bundle_id=f"R{index:06d}"),
            )
            for index, (prediction, actual) in enumerate(drawn)
        ]
        value = estimate([pair[0] for pair in sample], [pair[1] for pair in sample])
        if value is not None:
            estimates.append(value)
    if not estimates:
        return None

    estimates.sort()
    tail = (1.0 - interval) / 2.0
    low = percentile(estimates, tail)
    high = percentile(estimates, 1.0 - tail)
    return (low, high) if low is not None and high is not None else None


def _harmonic_mean(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None:
        return None
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)
