"""Band thresholds: where they may be fitted, and exactly what happens at each boundary.

Two properties here are safety properties rather than tuning choices.

Thresholds are fitted on **validation data only**. Fitting them on training data would set cut
points against the same rows the model already memorised; fitting them on test data would set
them against the rows the final metric is computed on, which makes that metric meaningless.
`fit` refuses both by name rather than trusting the caller to pass the right list.

A statistical score can never reach `DETERMINISTIC_CONFLICT`. That band means a versioned
invariant was violated outright — something a rule observed, not something a forest inferred.
"""
from __future__ import annotations

import pytest
from tilik_domain.reasons import PriorityBand
from tilik_model.calibration import (
    CALIBRATION_PARTITION,
    HIGH_PRIORITY_QUANTILE,
    NEEDS_CONTEXT_QUANTILE,
    BandCalibration,
    CalibrationRefused,
)

SCORES = tuple(index / 100.0 for index in range(101))


@pytest.fixture(scope="module")
def calibration() -> BandCalibration:
    return BandCalibration.fit(SCORES, partition=CALIBRATION_PARTITION)


def test_fitting_on_training_data_is_refused() -> None:
    with pytest.raises(CalibrationRefused, match="validation"):
        BandCalibration.fit(SCORES, partition="train")


def test_fitting_on_test_data_is_refused() -> None:
    """The test partition sets the final number; a threshold fitted on it measures itself."""
    with pytest.raises(CalibrationRefused, match="validation"):
        BandCalibration.fit(SCORES, partition="test")


def test_fitting_on_nothing_is_refused() -> None:
    """Empty input would silently produce a zero threshold, banding every case at the top."""
    with pytest.raises(CalibrationRefused, match="no scores"):
        BandCalibration.fit((), partition=CALIBRATION_PARTITION)


def test_thresholds_sit_at_the_declared_quantiles(calibration) -> None:
    assert calibration.needs_context_at == pytest.approx(NEEDS_CONTEXT_QUANTILE, abs=0.02)
    assert calibration.high_priority_at == pytest.approx(HIGH_PRIORITY_QUANTILE, abs=0.02)
    assert calibration.needs_context_at < calibration.high_priority_at


def test_the_boundary_belongs_to_the_higher_band(calibration) -> None:
    """`>=` is the convention, stated once and asserted rather than left to a reader."""
    edge = calibration.high_priority_at
    assert calibration.band_for(edge) is PriorityBand.HIGH_PRIORITY_SIGNAL
    assert calibration.band_for(_just_below(edge)) is PriorityBand.NEEDS_CONTEXT

    lower = calibration.needs_context_at
    assert calibration.band_for(lower) is PriorityBand.NEEDS_CONTEXT
    assert calibration.band_for(_just_below(lower)) is PriorityBand.NO_OBSERVED_RISK


def test_a_statistical_score_can_never_claim_a_deterministic_conflict(calibration) -> None:
    """That band means a rule saw an invariant broken. A forest cannot see one."""
    for score in (0.0, 0.5, 0.99, 1.0, 5.0, 1e9):
        assert calibration.band_for(score) is not PriorityBand.DETERMINISTIC_CONFLICT


def test_banding_is_monotonic(calibration) -> None:
    """A higher score may never produce a lower band."""
    order = [
        PriorityBand.NO_OBSERVED_RISK,
        PriorityBand.NEEDS_CONTEXT,
        PriorityBand.HIGH_PRIORITY_SIGNAL,
    ]
    seen = [order.index(calibration.band_for(score)) for score in SCORES]
    assert seen == sorted(seen)


def test_calibration_records_where_it_came_from(calibration) -> None:
    """A threshold with no provenance cannot be defended or reproduced."""
    assert calibration.fitted_on == CALIBRATION_PARTITION
    assert calibration.sample_size == len(SCORES)
    assert calibration.version


def test_drift_against_the_same_distribution_is_quiet(calibration) -> None:
    report = calibration.drift_against(SCORES)
    assert not report.shifted
    assert report.max_quantile_shift == pytest.approx(0.0, abs=1e-9)


def test_drift_against_a_shifted_distribution_is_reported_not_acted_on(calibration) -> None:
    """Distribution shift is monitored and reported. Nothing here changes a band because of it."""
    report = calibration.drift_against(tuple(score + 0.5 for score in SCORES))
    assert report.shifted
    assert report.max_quantile_shift > 0.0
    assert "geser" in report.summary().lower() or "shift" in report.summary().lower()

    # The bands themselves are untouched: reporting drift is not the same as reacting to it.
    assert calibration.band_for(calibration.high_priority_at) is PriorityBand.HIGH_PRIORITY_SIGNAL


def _just_below(value: float) -> float:
    import math

    return math.nextafter(value, float("-inf"))
