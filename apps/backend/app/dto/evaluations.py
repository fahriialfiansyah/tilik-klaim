"""`GET /v1/evaluations/{run_id}`."""
from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.dto.common import Dto, VersionStamp
from tilik_domain.reasons import RiskMode


class BaselineMetrics(Dto):
    """One row of the baseline comparison table."""

    baseline: str = Field(description="B0_RANDOM | B1_RULES_ONLY | B2_STATISTICAL_ONLY | HYBRID")
    macro_f1: float
    pr_auc: float
    precision_at_k: float
    recall_at_k: float
    false_positives_per_100_clean: float


class ModeMetrics(Dto):
    mode: RiskMode
    precision: float
    recall: float
    f1: float
    support: int = Field(ge=0)


class RunManifest(Dto):
    """What makes a run reproducible.

    Every field here is needed to rebuild the result from a clean environment and compare
    hashes. A metric without its manifest cannot be defended when a judge asks how it was
    produced.
    """

    dataset_hash: str
    generator_version: str
    split_manifest_hash: str
    feature_version: str
    ruleset_version: str
    model_version: str
    threshold_logic: str
    code_commit: str
    environment_hash: str
    artifact_hashes: dict[str, str]


class LimitationsCard(Dto):
    """What the numbers show, and what they do not.

    Copy-ready by design so it can go into the deck verbatim. It is the first thing dropped
    under deadline pressure and the last thing that should be.
    """

    demonstrates: tuple[str, ...]
    does_not_demonstrate: tuple[str, ...]
    mandatory_statement: str = Field(
        default=(
            "This dataset is synthetic and does not represent JKN prevalence or real "
            "provider behavior."
        )
    )


class EvaluationResponse(Dto):
    """Read-only. The page renders artifacts; it never computes a metric itself."""

    run_id: str
    completed_at: datetime
    data_class: str = Field(default="synthetic", description="Rendered prominently by the UI.")
    baselines: tuple[BaselineMetrics, ...]
    per_mode: tuple[ModeMetrics, ...]
    latency_p50_ms: int = Field(ge=0)
    latency_p95_ms: int = Field(ge=0)
    manifest: RunManifest
    limitations: LimitationsCard
    versions: VersionStamp
