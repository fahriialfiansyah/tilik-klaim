"""The aggregation and its three caps.

The formula is fixed by `docs/canonical/05_model_card.md` § Risk aggregation:

    priority = max(deterministic_reason_priority, calibrated_similarity, calibrated_anomaly)

and three caps apply to it. Each cap stops a specific harm, so each is tested for the harm and
not only for the arithmetic:

* text similarity alone must never reach a high band — shared templates are ordinary practice;
* missing evidence plus an incomplete bundle must lower certainty toward *request evidence* —
  an incomplete record is not evidence a service was not delivered;
* an exact duplicate fingerprint is high priority and **still human-reviewed**.
"""
from __future__ import annotations

import pytest
from tilik_domain.reasons import DispositionAction, PriorityBand
from tilik_model.calibration import CALIBRATION_PARTITION, BandCalibration
from tilik_model.ranking import (
    Cap,
    Certainty,
    RankedPriority,
    RankingModel,
    ReasonSummary,
    combine,
)

SCORES = tuple(index / 100.0 for index in range(101))
NOTHING = ReasonSummary()
DETERMINISTIC = ReasonSummary(has_any_reason=True, has_deterministic_reason=True)
SIMILARITY_ONLY = ReasonSummary(has_any_reason=True, is_similarity_only=True)
DUPLICATE = ReasonSummary(
    has_any_reason=True, has_deterministic_reason=True, has_exact_duplicate_fingerprint=True
)


@pytest.fixture(scope="module")
def calibration() -> BandCalibration:
    return BandCalibration.fit(SCORES, partition=CALIBRATION_PARTITION)


def _combine(reasons, similarity, anomaly, calibration, certainty=Certainty.FULL):
    return combine(
        bundle_id="BND-TEST",
        reasons=reasons,
        similarity_score=similarity,
        anomaly_score=anomaly,
        similarity_calibration=calibration,
        anomaly_calibration=calibration,
        certainty=certainty,
    )


def test_the_aggregate_is_the_maximum_of_the_three_components(calibration) -> None:
    """A deterministic conflict outranks any statistical score, and a quiet rule does not."""
    conflict = _combine(DETERMINISTIC, 0.0, 0.0, calibration)
    assert conflict.band is PriorityBand.DETERMINISTIC_CONFLICT

    raised = _combine(NOTHING, 0.0, 1.0, calibration)
    assert raised.band is PriorityBand.HIGH_PRIORITY_SIGNAL

    quiet = _combine(NOTHING, 0.0, 0.0, calibration)
    assert quiet.band is PriorityBand.NO_OBSERVED_RISK


def test_text_similarity_alone_can_never_reach_a_high_band(calibration) -> None:
    """Cap one. A perfect similarity score with nothing else argues for a look, not the front."""
    for score in (0.9, 0.99, 1.0, 5.0):
        result = _combine(SIMILARITY_ONLY, score, 0.0, calibration)
        assert result.band is PriorityBand.NEEDS_CONTEXT, score
        assert result.similarity_band is PriorityBand.NEEDS_CONTEXT
        assert Cap.SIMILARITY_ONLY_CEILING in result.caps_applied


def test_the_similarity_component_is_capped_even_beside_other_signals(calibration) -> None:
    """The ceiling is on the component, so no combination lets text alone lift the band."""
    result = _combine(DETERMINISTIC, 1.0, 0.0, calibration)
    assert result.similarity_band is PriorityBand.NEEDS_CONTEXT
    assert result.band is PriorityBand.DETERMINISTIC_CONFLICT  # from the rule, not the text


def test_an_incomplete_bundle_lowers_the_band_and_asks_for_evidence(calibration) -> None:
    """Cap two. An incomplete record is not evidence a service was not delivered."""
    result = _combine(
        DETERMINISTIC, 0.0, 0.0, calibration, certainty=Certainty.REDUCED_INCOMPLETE_BUNDLE
    )
    assert result.band is PriorityBand.HIGH_PRIORITY_SIGNAL  # stepped down from conflict
    assert result.suggested_action is DispositionAction.REQUEST_EVIDENCE
    assert Cap.INCOMPLETE_BUNDLE_STEP_DOWN in result.caps_applied


def test_an_incomplete_bundle_never_routes_toward_confirming_an_anomaly(calibration) -> None:
    """The whole point of the cap: reduced certainty must not push toward a finding."""
    for reasons in (NOTHING, DETERMINISTIC, SIMILARITY_ONLY, DUPLICATE):
        result = _combine(
            reasons, 1.0, 1.0, calibration, certainty=Certainty.REDUCED_INCOMPLETE_BUNDLE
        )
        assert result.suggested_action is DispositionAction.REQUEST_EVIDENCE


def test_a_step_down_never_hides_a_raised_case(calibration) -> None:
    """Lowering certainty moves a case down the queue; it must never remove it from the queue."""
    result = _combine(
        SIMILARITY_ONLY, 1.0, 0.0, calibration, certainty=Certainty.REDUCED_INCOMPLETE_BUNDLE
    )
    assert result.band is PriorityBand.NEEDS_CONTEXT
    assert result.band is not PriorityBand.NO_OBSERVED_RISK


def test_an_exact_duplicate_is_high_priority_and_still_human_reviewed(calibration) -> None:
    """Cap three. The floor raises the case; nothing about it decides anything."""
    result = _combine(DUPLICATE, 0.0, 0.0, calibration)
    assert result.band in (PriorityBand.HIGH_PRIORITY_SIGNAL, PriorityBand.DETERMINISTIC_CONFLICT)
    assert Cap.DUPLICATE_FINGERPRINT_FLOOR in result.caps_applied or result.band is (
        PriorityBand.DETERMINISTIC_CONFLICT
    )
    assert result.suggested_action is not DispositionAction.CONFIRM_ANOMALY


def test_a_duplicate_with_no_rule_reason_still_reaches_high(calibration) -> None:
    only_duplicate = ReasonSummary(has_any_reason=True, has_exact_duplicate_fingerprint=True)
    result = _combine(only_duplicate, 0.0, 0.0, calibration)
    assert result.band is PriorityBand.HIGH_PRIORITY_SIGNAL
    assert Cap.DUPLICATE_FINGERPRINT_FLOOR in result.caps_applied


def test_the_model_never_suggests_a_finding_or_an_action_on_the_claim(calibration) -> None:
    """Nothing this package produces may propose confirming, rejecting, or escalating."""
    forbidden = {
        DispositionAction.CONFIRM_ANOMALY,
        DispositionAction.ESCALATE,
        DispositionAction.REJECT_SIGNAL,
    }
    for reasons in (NOTHING, DETERMINISTIC, SIMILARITY_ONLY, DUPLICATE):
        for certainty in Certainty:
            for similarity in (0.0, 1.0):
                for anomaly in (0.0, 1.0):
                    result = _combine(reasons, similarity, anomaly, calibration, certainty)
                    assert result.suggested_action not in forbidden


def test_every_component_score_and_version_is_stored(calibration) -> None:
    """The model card requires all component scores and versions, not just the aggregate."""
    result = _combine(DETERMINISTIC, 0.42, 0.73, calibration)
    names = {component.name for component in result.components}
    assert {"deterministic_reason_priority", "text_similarity", "peer_anomaly"} <= names
    for component in result.components:
        assert component.version, component.name
    assert result.identity.model_version


def test_a_band_raised_only_by_a_model_score_is_flagged_as_unexplained(calibration) -> None:
    """A case with no rule reason has nothing to show a reviewer, and must say so."""
    model_only = _combine(NOTHING, 0.0, 1.0, calibration)
    assert not model_only.explained_by_reasons

    explained = _combine(DETERMINISTIC, 0.0, 0.0, calibration)
    assert explained.explained_by_reasons


def test_the_result_is_serialisable_and_frozen(calibration) -> None:
    result = _combine(DETERMINISTIC, 0.1, 0.2, calibration)
    from pydantic import ValidationError

    assert RankedPriority.model_validate_json(result.model_dump_json()) == result
    with pytest.raises(ValidationError):
        result.band = PriorityBand.NO_OBSERVED_RISK  # type: ignore[misc]


def test_a_trained_model_ranks_a_real_bundle(bundles) -> None:
    """The end-to-end path: train on one partition, calibrate on another, rank a claim."""
    half = len(bundles) // 2
    model = RankingModel.train(
        training_bundles=bundles[:half],
        validation_bundles=bundles[half:],
        dataset_digest="test-digest",
    )
    result = model.rank(bundles[0], reasons=DETERMINISTIC, certainty=Certainty.FULL)
    assert result.bundle_id == bundles[0].bundle_id
    assert result.identity.dataset_digest == "test-digest"
    assert result.band is PriorityBand.DETERMINISTIC_CONFLICT
