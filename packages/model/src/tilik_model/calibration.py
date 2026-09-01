"""Turn a continuous score into a band, and report when the population underneath has moved.

**Fitted on validation data only.** Training scores come from rows the model already fitted on,
so a cut point placed against them sits in the wrong part of the distribution. Test scores are
what the final metric is computed from, so a cut point placed against those is a threshold
tuned on the exam. `fit` therefore takes the partition's *name* and refuses anything but
validation — the control is checkable rather than a convention someone has to remember.

**A statistical score can never reach `DETERMINISTIC_CONFLICT`.** That band means a versioned
invariant was violated outright, which is something the rules layer observes and a forest
cannot. The highest band available here is `HIGH_PRIORITY_SIGNAL`, and `ranking.py` caps text
similarity lower still.

Drift is **reported, not acted on**. When the score distribution moves, the honest response is
to say so and let a person decide whether the thresholds still mean what they meant — silently
re-fitting would make an old case and a new case incomparable without anyone noticing.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from pydantic import BaseModel, ConfigDict
from tilik_domain.reasons import PriorityBand

from tilik_model.version import CALIBRATION_VERSION

CALIBRATION_PARTITION = "validation"
"""The only partition thresholds may be fitted on."""

NEEDS_CONTEXT_QUANTILE = 0.90
"""Above the 90th percentile of validation scores, a case is worth a reviewer's context.

Provisional, and deliberately conservative: a review budget is finite, and a threshold that
raises a tenth of the queue is already a large ask. Sprint 06 measures whether it earns itself.
"""

HIGH_PRIORITY_QUANTILE = 0.98
"""Above the 98th percentile, a case goes near the front of the queue — still only a queue."""

DRIFT_QUANTILES: tuple[float, ...] = (0.10, 0.25, 0.50, 0.75, 0.90, 0.99)
"""Where the two distributions are compared. Reported individually, never averaged away."""

DRIFT_TOLERANCE = 0.10
"""How far a quantile may move before the shift is worth a human's attention."""


class CalibrationRefused(RuntimeError):
    """Thresholds were about to be fitted on something they may not be fitted on."""


class DriftReport(BaseModel):
    """How far a new population's scores sit from the one the thresholds were set against."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    max_quantile_shift: float
    shifted: bool
    per_quantile: tuple[tuple[float, float], ...]
    sample_size: int

    def summary(self) -> str:
        verdict = (
            "distribusi skor bergeser — ambang batas perlu ditinjau ulang"
            if self.shifted
            else "distribusi skor stabil"
        )
        return (
            f"{verdict} (pergeseran kuantil terbesar {self.max_quantile_shift:.3f}, "
            f"toleransi {DRIFT_TOLERANCE:.2f}, n={self.sample_size})"
        )


class BandCalibration(BaseModel):
    """Two cut points, and everything needed to say where they came from."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    needs_context_at: float
    high_priority_at: float

    fitted_on: str
    sample_size: int
    quantiles: tuple[float, float] = (NEEDS_CONTEXT_QUANTILE, HIGH_PRIORITY_QUANTILE)
    reference_quantiles: tuple[tuple[float, float], ...] = ()
    """The fitted distribution's shape, kept so drift can be measured against it later."""

    version: str = CALIBRATION_VERSION

    @classmethod
    def fit(cls, scores: Sequence[float], *, partition: str) -> BandCalibration:
        """Place cut points at the declared quantiles of the **validation** score distribution."""
        if partition != CALIBRATION_PARTITION:
            raise CalibrationRefused(
                f"thresholds may only be fitted on the {CALIBRATION_PARTITION!r} partition, "
                f"not {partition!r}. Fitting on training rows places a cut point against data "
                "the model memorised; fitting on test rows tunes the threshold on the exam."
            )
        if not scores:
            raise CalibrationRefused(
                "no scores to calibrate on — an empty distribution would put every cut point "
                "at zero and band the whole queue at the top."
            )

        values = np.asarray(scores, dtype=float)
        return cls(
            needs_context_at=float(np.quantile(values, NEEDS_CONTEXT_QUANTILE)),
            high_priority_at=float(np.quantile(values, HIGH_PRIORITY_QUANTILE)),
            fitted_on=partition,
            sample_size=len(scores),
            reference_quantiles=tuple(
                (quantile, float(np.quantile(values, quantile))) for quantile in DRIFT_QUANTILES
            ),
        )

    def band_for(self, score: float) -> PriorityBand:
        """Which band this score argues for, on its own.

        The boundary belongs to the **higher** band: a score exactly at a cut point is in it.
        """
        if score >= self.high_priority_at:
            return PriorityBand.HIGH_PRIORITY_SIGNAL
        if score >= self.needs_context_at:
            return PriorityBand.NEEDS_CONTEXT
        return PriorityBand.NO_OBSERVED_RISK

    def drift_against(self, scores: Sequence[float]) -> DriftReport:
        """Compare a new population to the one these thresholds were set against."""
        if not scores or not self.reference_quantiles:
            return DriftReport(
                max_quantile_shift=0.0, shifted=False, per_quantile=(), sample_size=len(scores)
            )

        values = np.asarray(scores, dtype=float)
        shifts = tuple(
            (quantile, abs(float(np.quantile(values, quantile)) - reference))
            for quantile, reference in self.reference_quantiles
        )
        worst = max(shift for _, shift in shifts)
        return DriftReport(
            max_quantile_shift=worst,
            shifted=worst > DRIFT_TOLERANCE,
            per_quantile=shifts,
            sample_size=len(scores),
        )
