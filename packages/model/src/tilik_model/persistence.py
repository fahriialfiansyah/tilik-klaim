"""Save a fitted model and load it back so it predicts exactly what it predicted before.

Reproducibility is the whole claim this package makes. "Predictions are reproducible from a
saved model" is Sprint 05's done-when assertion, and a round trip that returns *approximately*
the same numbers would not satisfy it — a queue that reorders itself between two loads of one
artifact is not reviewable.

The saved file carries the versions it was fitted under, and loading refuses a mismatch. A model
reloaded against a changed feature schema would keep scoring happily while every column meant
something else, which is the kind of failure that produces confident, wrong numbers.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib

from tilik_model.anomaly import PeerAnomaly
from tilik_model.calibration import BandCalibration
from tilik_model.features import FeatureExtractor, PeerProfile
from tilik_model.ranking import RankingModel
from tilik_model.similarity import NoteSimilarity
from tilik_model.version import FEATURE_VERSION, MODEL_VERSION, ModelIdentity

ARTIFACT_FORMAT = 1
"""Bumped when the payload's shape changes, independently of what it was fitted on."""


class IncompatibleArtifact(RuntimeError):
    """The saved model was fitted under versions this code no longer agrees with."""


@dataclass(frozen=True)
class _Payload:
    """Exactly what goes on disk. Kept flat so a reader can see everything that was kept."""

    artifact_format: int
    model_version: str
    feature_version: str
    peers: PeerProfile
    similarity: NoteSimilarity
    anomaly: PeerAnomaly
    similarity_calibration: BandCalibration
    anomaly_calibration: BandCalibration
    identity: ModelIdentity


def save_model(model: RankingModel, path: Path) -> None:
    """Write the fitted model, with the versions it was fitted under."""
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        _Payload(
            artifact_format=ARTIFACT_FORMAT,
            model_version=MODEL_VERSION,
            feature_version=FEATURE_VERSION,
            peers=model.extractor.peers,
            similarity=model.similarity,
            anomaly=model.anomaly,
            similarity_calibration=model.similarity_calibration,
            anomaly_calibration=model.anomaly_calibration,
            identity=model.identity,
        ),
        path,
    )


def load_model(path: Path) -> RankingModel:
    """Read a saved model back, refusing anything fitted under a version that has moved."""
    payload = joblib.load(path)
    if not isinstance(payload, _Payload):
        raise IncompatibleArtifact(f"{path} does not contain a TilikKlaim ranking model")
    _assert_compatible(payload)

    return RankingModel(
        extractor=FeatureExtractor(payload.peers),
        similarity=payload.similarity,
        anomaly=payload.anomaly,
        similarity_calibration=payload.similarity_calibration,
        anomaly_calibration=payload.anomaly_calibration,
        identity=payload.identity,
    )


def _assert_compatible(payload: _Payload) -> None:
    mismatches = [
        f"{name} was {found!r}, this code is {expected!r}"
        for name, found, expected in (
            ("artifact_format", payload.artifact_format, ARTIFACT_FORMAT),
            ("feature_version", payload.feature_version, FEATURE_VERSION),
            ("model_version", payload.model_version, MODEL_VERSION),
        )
        if found != expected
    ]
    if mismatches:
        raise IncompatibleArtifact(
            "refusing to load a model fitted under different versions — every column could "
            f"mean something else: {'; '.join(mismatches)}"
        )
