"""A saved model must reload and reproduce identical predictions.

"Identical", not "close". Sprint 05's done-when assertion is that predictions are reproducible
from a saved model, and a band that flips between two loads of one artifact would make an
audited case unauditable.
"""
from __future__ import annotations

import dataclasses

import pytest
from tilik_model.dataset import build_contexts
from tilik_model.persistence import IncompatibleArtifact, load_model, save_model
from tilik_model.ranking import Certainty, RankingModel, ReasonSummary

REASONS = ReasonSummary(has_any_reason=True, has_deterministic_reason=False)


@pytest.fixture(scope="module")
def trained(bundles) -> RankingModel:
    half = len(bundles) // 2
    return RankingModel.train(
        training_bundles=bundles[:half],
        validation_bundles=bundles[half:],
        dataset_digest="serialisation-test",
    )


def test_a_reloaded_model_reproduces_identical_predictions(trained, bundles, tmp_path) -> None:
    path = tmp_path / "ranking.joblib"
    save_model(trained, path)
    reloaded = load_model(path)

    contexts = build_contexts(bundles)
    for bundle in bundles[:60]:
        context = contexts[bundle.bundle_id]
        before = trained.rank(
            bundle, reasons=REASONS, certainty=Certainty.FULL, context=context
        )
        after = reloaded.rank(
            bundle, reasons=REASONS, certainty=Certainty.FULL, context=context
        )
        assert after == before, bundle.bundle_id


def test_the_reloaded_model_keeps_its_thresholds_and_identity(trained, tmp_path) -> None:
    path = tmp_path / "ranking.joblib"
    save_model(trained, path)
    reloaded = load_model(path)

    assert reloaded.similarity_calibration == trained.similarity_calibration
    assert reloaded.anomaly_calibration == trained.anomaly_calibration
    assert reloaded.identity == trained.identity
    assert reloaded.identity.dataset_digest == "serialisation-test"


def test_a_model_fitted_under_a_different_feature_version_is_refused(
    trained, tmp_path
) -> None:
    """Every column could mean something else. Loading it anyway would score confident noise."""
    import joblib

    path = tmp_path / "ranking.joblib"
    save_model(trained, path)
    payload = joblib.load(path)
    joblib.dump(dataclasses.replace(payload, feature_version="0.0.1-old"), path)

    with pytest.raises(IncompatibleArtifact, match="feature_version"):
        load_model(path)


def test_a_file_that_is_not_a_model_is_refused(tmp_path) -> None:
    import joblib

    path = tmp_path / "not-a-model.joblib"
    joblib.dump({"anything": "else"}, path)
    with pytest.raises(IncompatibleArtifact, match="does not contain"):
        load_model(path)
