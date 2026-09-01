"""Isolation Forest over the feature table — the unsupervised half of the baseline.

`docs/canonical/05_model_card.md` offers Isolation Forest or LOF on robust peer features.
Isolation Forest is chosen because it scores a *new* claim without keeping the training set
around, which matters for a service that screens one bundle at a time.

**The score is unsupervised and label-free on purpose.** It is fitted on training bundles with
no reference to the injection labels, so it cannot learn the generator's answer key even if the
corpus leaked one. What it can do is notice that a claim is unlike its population — which is a
reason to look, and never more than that.

Features are scaled with a median/IQR scaler rather than a mean/standard-deviation one: the
peer group is small and synthetic, and a single extreme claim would drag a mean far enough to
make the rest of the population look unusual.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import RobustScaler

from tilik_model.feature_schema import FEATURE_NAMES, FeatureRow
from tilik_model.version import ANOMALY_VERSION

N_ESTIMATORS = 200
"""Trees in the forest. Enough for a stable score at this corpus size, cheap enough to refit."""

RANDOM_STATE = 20260902
"""Pinned to the corpus seed, so two fits of the same data produce the same forest."""

MAX_SAMPLES = 256
"""The Isolation Forest default; named here so it is a recorded hyperparameter, not a default."""


class AnomalyScore(BaseModel):
    """How unusual one claim looks against the population the forest was fitted on."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    value: float = 0.0
    """Position in the fitted population, 0 (ordinary) to 1 (most unusual seen while fitting)."""
    raw: float = 0.0
    """The forest's own score before it was placed against that population."""

    version: str = ANOMALY_VERSION


class PeerAnomaly:
    """A fitted scaler-plus-forest, and the training score distribution it is read against."""

    def __init__(
        self, pipeline: Pipeline | None, training_scores: tuple[float, ...] = ()
    ) -> None:
        self._pipeline = pipeline
        self._training_scores = training_scores

    @property
    def is_fitted(self) -> bool:
        return self._pipeline is not None

    @property
    def hyperparameters(self) -> dict[str, object]:
        """Recorded on every artifact — a score nobody can re-derive is not evidence."""
        return {
            "n_estimators": N_ESTIMATORS,
            "max_samples": MAX_SAMPLES,
            "random_state": RANDOM_STATE,
            "scaler": "RobustScaler",
            "features": len(FEATURE_NAMES),
            "fitted_on": len(self._training_scores),
        }

    @classmethod
    def fit(cls, rows: Sequence[FeatureRow]) -> PeerAnomaly:
        """Fit on training rows only. An empty partition yields an inert model, not an error."""
        if not rows:
            return cls(None)

        matrix = _matrix(rows)
        pipeline = Pipeline(
            (
                ("scale", RobustScaler()),
                (
                    "forest",
                    IsolationForest(
                        n_estimators=N_ESTIMATORS,
                        max_samples=min(MAX_SAMPLES, len(rows)),
                        random_state=RANDOM_STATE,
                        contamination="auto",
                    ),
                ),
            )
        )
        pipeline.fit(matrix)
        raw = _raw_scores(pipeline, matrix)
        return cls(pipeline, tuple(sorted(float(value) for value in raw)))

    def score(self, row: FeatureRow) -> AnomalyScore:
        """Score one row against the fitted population."""
        _check_width(row)
        if not self.is_fitted:
            return AnomalyScore()

        assert self._pipeline is not None  # narrowed by is_fitted
        raw = float(_raw_scores(self._pipeline, _matrix((row,)))[0])
        return AnomalyScore(value=self._position_of(raw), raw=raw)

    def _position_of(self, raw: float) -> float:
        """Where this score falls in the training distribution, as a share below it.

        A monotone re-expression of the forest's own number, so ranking is unchanged. Band cut
        points are **not** set here — `calibration.py` sets them, on validation data only.
        """
        if not self._training_scores:
            return 0.0
        below = int(np.searchsorted(self._training_scores, raw, side="right"))
        return float(min(below / len(self._training_scores), 1.0))


def _matrix(rows: Sequence[FeatureRow]) -> np.ndarray:
    return np.asarray([row.values for row in rows], dtype=float)


def _raw_scores(pipeline: Pipeline, matrix: np.ndarray) -> np.ndarray:
    """Higher means more unusual. `score_samples` runs the other way, so it is negated."""
    return -pipeline.score_samples(matrix)


def _check_width(row: FeatureRow) -> None:
    if len(row.values) != len(FEATURE_NAMES):
        raise ValueError(
            f"row {row.bundle_id!r} carries {len(row.values)} feature values, "
            f"but the schema declares {len(FEATURE_NAMES)}"
        )
