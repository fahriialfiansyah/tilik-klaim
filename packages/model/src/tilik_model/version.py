"""Version identity carried by every score this package produces.

`docs/canonical/05_model_card.md` § Model/version artifacts requires that a result can be traced
to the feature version, the threshold logic, and the hyperparameters that produced it. A score
without that identity is a number nobody can re-derive, so the identity travels *with* every
component score rather than being recorded once per run.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

FEATURE_VERSION = "0.1.0"
"""Bumped whenever a feature's definition changes, so old scores stay interpretable."""

SIMILARITY_VERSION = "0.1.0"
ANOMALY_VERSION = "0.1.0"
CALIBRATION_VERSION = "0.1.0"
MODEL_VERSION = "0.1.0"
"""The package as a whole. Bumped when any component version moves."""


class ModelIdentity(BaseModel):
    """Stamped onto every ranked priority, beside the engine identity from the rules layer."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    model_version: str = MODEL_VERSION
    feature_version: str = FEATURE_VERSION
    similarity_version: str = SIMILARITY_VERSION
    anomaly_version: str = ANOMALY_VERSION
    calibration_version: str = CALIBRATION_VERSION

    dataset_digest: str = "unset"
    """Digest of the corpus the model was fitted on. `unset` means nobody recorded it."""

    def as_label(self) -> str:
        """Compact form for a version badge or an artifact header."""
        return (
            f"model {self.model_version} · features {self.feature_version} "
            f"· similarity {self.similarity_version} · anomaly {self.anomaly_version} "
            f"· calibration {self.calibration_version} · data {self.dataset_digest[:12]}"
        )
