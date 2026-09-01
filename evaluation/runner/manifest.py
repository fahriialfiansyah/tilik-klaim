"""The run manifest: everything needed to rebuild a number and check it came out the same.

`docs/canonical/05_model_card.md` § Model/version artifacts lists what a run must record, and
§ 20's constraint is that every metric quoted in the proposal is a generated artifact. A metric
without this manifest cannot be defended when a judge asks how it was produced.

**Latency is deliberately excluded from the hashed set.** p50 and p95 are measurements of the
machine, not of the method, and they differ between two runs of identical code. Hashing them
would make "a clean re-run reproduces identical hashes" permanently false and the check would be
switched off — so the deterministic artifacts are hashed, the measured ones are written beside
them, and the manifest names which is which rather than leaving a reader to guess.
"""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict
from tilik_domain.versioning import ENGINE_VERSION, RULESET_VERSION, SCHEMA_VERSION
from tilik_model.calibration import HIGH_PRIORITY_QUANTILE, NEEDS_CONTEXT_QUANTILE
from tilik_model.version import FEATURE_VERSION, MODEL_VERSION

RUNNER_VERSION = "0.1.0"

DETERMINISTIC_ARTIFACTS: tuple[str, ...] = (
    "metrics.json",
    "tables/baselines.csv",
    "tables/per_mode.csv",
    "tables/breakdowns.csv",
    "charts/false_positives_per_100.svg",
    "charts/precision_at_budget.svg",
    "charts/per_mode_f1.svg",
    "case_reports.json",
    "LIMITATIONS.md",
    "limitations.json",
)
"""Hashed, and compared across runs. Two clean runs of one commit must agree on all of these."""

MEASURED_ARTIFACTS: tuple[str, ...] = ("latency.json",)
"""Written but not hashed: they measure the machine, so they legitimately differ between runs."""

WORKING_TREE_DIRTY = "-dirty"
UNKNOWN_COMMIT = "unknown"


class RunManifest(BaseModel):
    """What produced one run, in enough detail to reproduce it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str
    generated_at: str

    dataset_hash: str
    generator_version: str
    split_manifest_hash: str

    schema_version: str = SCHEMA_VERSION
    ruleset_version: str = RULESET_VERSION
    engine_version: str = ENGINE_VERSION
    feature_version: str = FEATURE_VERSION
    model_version: str = MODEL_VERSION
    runner_version: str = RUNNER_VERSION

    threshold_logic: str
    code_commit: str
    environment_hash: str
    environment: dict[str, str]

    artifact_hashes: dict[str, str]
    deterministic_artifacts: tuple[str, ...] = DETERMINISTIC_ARTIFACTS
    excluded_from_hash: tuple[str, ...] = MEASURED_ARTIFACTS
    excluded_from_hash_reason: str = (
        "Latency measures the machine, not the method, and differs between two runs of "
        "identical code. It is written beside the hashed artifacts, never inside them."
    )


def threshold_logic() -> str:
    """One sentence a reader can check against the code, not a pointer to it."""
    return (
        "Band cut points are quantiles of the validation score distribution: "
        f"needs-context at q={NEEDS_CONTEXT_QUANTILE}, "
        f"high-priority at q={HIGH_PRIORITY_QUANTILE}. "
        "A score exactly at a cut point falls in the higher band. Text similarity is capped at "
        "needs-context; an exact duplicate fingerprint floors at high-priority; an incomplete "
        "bundle steps the aggregate down last, never below needs-context."
    )


def code_commit(repo_root: Path) -> str:
    """The commit the artifacts were built from, marked dirty when the tree has changes.

    An unmarked commit on a dirty tree is worse than no commit at all: it names a state that
    does not describe the code that ran.
    """
    try:
        revision = subprocess.run(
            ("git", "rev-parse", "HEAD"),
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
        status = subprocess.run(
            ("git", "status", "--porcelain"),
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return UNKNOWN_COMMIT
    return f"{revision}{WORKING_TREE_DIRTY}" if status else revision


def environment() -> dict[str, str]:
    """The parts of the environment that could change a number."""
    versions: dict[str, str] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(terse=True),
    }
    for package in ("numpy", "sklearn", "pydantic"):
        try:
            versions[package] = __import__(package).__version__
        except (ImportError, AttributeError):  # pragma: no cover - a stripped environment
            versions[package] = UNKNOWN_COMMIT
    return versions


def environment_hash(values: dict[str, str]) -> str:
    return _digest(json.dumps(values, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def hash_artifacts(directory: Path, names: tuple[str, ...] = DETERMINISTIC_ARTIFACTS) -> dict:
    """SHA-256 of each deterministic artifact, keyed by its path within the run directory."""
    hashes: dict[str, str] = {}
    for name in names:
        path = directory / name
        if path.exists():
            hashes[name] = _digest(path.read_bytes())
    return hashes


def stamped(**values: object) -> RunManifest:
    """Build a manifest with its generation timestamp.

    The timestamp describes the *run*, never an input — nothing hashed depends on it, which is
    what keeps two clean runs comparable.
    """
    stamp = datetime.now(UTC).isoformat()
    return RunManifest(generated_at=stamp, **values)  # type: ignore[arg-type]


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
