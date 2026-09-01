"""Read what the offline evaluation runner wrote. This module computes no metric.

`docs/canonical/06_evaluation_plan.md` requires that every metric quoted in the proposal comes
from a generated artifact. Recomputing anything here would create a second source of the same
number, and the two would eventually disagree — so this is a reader, and only a reader.

**Undefined values are dropped, never rendered as zero.** `EvaluationResponse` is a frozen wire
model whose metric fields are plain floats, so a value the runner reported as `null` — a mode
with no example in the test partition, a baseline that never flagged — cannot be represented.
Those rows are omitted rather than zero-filled, and the page shows the four known baselines and
four known modes from its own enums, marking anything missing as not measured. A zero would say
"we measured this and it was nothing", which is a different and false claim.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tilik_domain.reasons import RiskMode
from tilik_domain.versioning import EngineIdentity

from app.dto.common import VersionStamp
from app.dto.evaluations import (
    BaselineMetrics,
    EvaluationResponse,
    LimitationsCard,
    ModeMetrics,
    RunManifest,
)

LATEST = "latest"
"""Reserved run id resolving to the most recent run. A path value, not a new endpoint."""

HEADLINE_BASELINE = "HYBRID"
"""Whose per-mode numbers the response carries. The full table stays in `metrics.json`."""

REQUIRED_FILES: tuple[str, ...] = ("metrics.json", "manifest.json", "limitations.json")
"""A run directory missing any of these is a partial write, not a run."""

RUN_ID_PATTERN = "run-"


class EvaluationRunNotFound(LookupError):
    """No completed run under that id. The page shows the command to produce one."""


def artifacts_root(configured: str) -> Path:
    """Resolve the configured directory, relative to the repository root when it is relative."""
    path = Path(configured)
    return path if path.is_absolute() else _repository_root() / path


def resolve_run(root: Path, run_id: str) -> Path:
    """The directory for one run. `latest` picks the most recent complete one."""
    if run_id == LATEST:
        return _latest_run(root)

    if "/" in run_id or "\\" in run_id or run_id in ("", ".", ".."):
        # A run id is a directory name, never a path. Rejecting separators here keeps a
        # crafted id from reading a file outside the artifacts root.
        raise EvaluationRunNotFound(f"{run_id!r} is not a valid run id")

    directory = root / run_id
    if not _is_complete(directory):
        raise EvaluationRunNotFound(f"no completed evaluation run at {run_id!r}")
    return directory


def read_run(directory: Path) -> EvaluationResponse:
    """Map one run's artifacts onto the frozen response model."""
    metrics = _load(directory / "metrics.json")
    manifest = _load(directory / "manifest.json")
    limitations = _load(directory / "limitations.json")
    latency = _load(directory / "latency.json") if (directory / "latency.json").exists() else {}

    return EvaluationResponse(
        run_id=str(manifest["run_id"]),
        completed_at=manifest["generated_at"],
        baselines=tuple(_baselines(metrics)),
        per_mode=tuple(_per_mode(metrics)),
        latency_p50_ms=_milliseconds(latency.get("p50_ms")),
        latency_p95_ms=_milliseconds(latency.get("p95_ms")),
        manifest=_manifest(manifest),
        limitations=_limitations(limitations),
        versions=VersionStamp(
            **EngineIdentity(
                schema_version=str(manifest.get("schema_version", "unset")),
                ruleset_version=str(manifest.get("ruleset_version", "unset")),
                engine_version=str(manifest.get("engine_version", "unset")),
                dataset_version=str(manifest.get("dataset_hash", "unset")),
            ).model_dump()
        ),
    )


def _baselines(metrics: dict[str, Any]) -> list[BaselineMetrics]:
    fields = (
        "macro_f1",
        "pr_auc",
        "precision_at_k",
        "recall_at_k",
        "false_positives_per_100_clean",
    )
    rows = []
    for row in metrics.get("baselines", ()):
        values = {name: row.get(name) for name in fields}
        if any(value is None for value in values.values()):
            continue  # not measured — the page says so rather than showing a zero
        rows.append(BaselineMetrics(baseline=str(row["baseline"]), **values))
    return rows


def _per_mode(metrics: dict[str, Any]) -> list[ModeMetrics]:
    rows = []
    for row in metrics.get("per_mode", {}).get(HEADLINE_BASELINE, ()):
        if any(row.get(name) is None for name in ("precision", "recall", "f1")):
            continue
        rows.append(
            ModeMetrics(
                mode=RiskMode(row["mode"]),
                precision=row["precision"],
                recall=row["recall"],
                f1=row["f1"],
                support=int(row["support"]),
            )
        )
    return rows


def _manifest(manifest: dict[str, Any]) -> RunManifest:
    return RunManifest(
        dataset_hash=str(manifest.get("dataset_hash", "unset")),
        generator_version=str(manifest.get("generator_version", "unset")),
        split_manifest_hash=str(manifest.get("split_manifest_hash", "unset")),
        feature_version=str(manifest.get("feature_version", "unset")),
        ruleset_version=str(manifest.get("ruleset_version", "unset")),
        model_version=str(manifest.get("model_version", "unset")),
        threshold_logic=str(manifest.get("threshold_logic", "unset")),
        code_commit=str(manifest.get("code_commit", "unknown")),
        environment_hash=str(manifest.get("environment_hash", "unset")),
        artifact_hashes=dict(manifest.get("artifact_hashes", {})),
    )


def _limitations(limitations: dict[str, Any]) -> LimitationsCard:
    """Canonical rows first, then this run's own caveats.

    Both are statements of what the numbers do not support, and a limitations card in a deck is
    read as one list. Keeping the run's caveats out because the wire model has no separate field
    would drop the only part of the card that changes with the result.
    """
    return LimitationsCard(
        demonstrates=tuple(limitations.get("demonstrates", ())),
        does_not_demonstrate=(
            *limitations.get("does_not_demonstrate", ()),
            *limitations.get("run_caveats", ()),
        ),
    )


def _latest_run(root: Path) -> Path:
    candidates = sorted(
        (child for child in root.glob(f"{RUN_ID_PATTERN}*") if _is_complete(child)),
        key=lambda child: child.name,
    )
    if not candidates:
        raise EvaluationRunNotFound("no completed evaluation run has been written yet")
    return candidates[-1]


def _is_complete(directory: Path) -> bool:
    """A run is readable only when every required artifact landed."""
    return directory.is_dir() and all((directory / name).exists() for name in REQUIRED_FILES)


def _milliseconds(value: float | None) -> int:
    """Latency is optional: it is measured, so it is not part of the hashed artifact set."""
    return max(0, round(value)) if value is not None else 0


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _repository_root() -> Path:
    """`apps/backend/app/service/…` → the repository root."""
    return Path(__file__).resolve().parents[4]
