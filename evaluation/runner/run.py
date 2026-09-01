"""One command that rebuilds every metric, table, and chart the proposal will cite.

    uv run python -m runner.run --build ../packages/data/build --out artifacts/run-01

The order is a protocol, not a convenience, and it follows
`docs/canonical/06_evaluation_plan.md` § Experimental protocol exactly:

1. **Load the frozen artifacts.** The loader refuses a corpus, split, and labels that do not
   join, so the Sprint 01 defect cannot silently produce a metric.
2. **Run the gates** — leakage probe, injector-trace check, demo-fixture exclusion. Before any
   metric. A number computed on a leaking corpus is a number someone might believe.
3. **Fit on train, calibrate on validation.** Never on test. The training set additionally drops
   any participant appearing downstream, and the count is reported.
4. **Evaluate once, on the frozen test partition.**
5. **Write the artifacts and hash them**, so a clean re-run can be compared.

The test partition is read exactly once, at step 4. There is no tuning loop in this file, and
adding one would invalidate every number it produces.
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from tilik_model.dataset import (
    TEST,
    VALIDATION,
    BuildArtifacts,
    build_contexts,
    load_build,
    uncontaminated_training_bundles,
)
from tilik_model.ranking import RankingModel

from runner import charts, limitations, manifest
from runner.baselines import BaselineId, screen_all
from runner.ground_truth import load_ground_truth
from runner.metrics import MetricStatus
from runner.preflight import PreflightReport, run_preflight
from runner.report import (
    baselines_csv,
    breakdowns_csv,
    build_metrics,
    case_reports,
    latency_report,
    per_mode_csv,
)

DEFAULT_SEED = 20260902
DEFAULT_MAX_SECONDS = 900
"""Wall-clock bound for the whole run. Exceeding it halts and reports progress, never hangs."""


class EvaluationTimedOut(RuntimeError):
    """The run exceeded its wall-clock bound. Reported with how far it got."""


@dataclass(frozen=True)
class RunOutcome:
    """Everything one run produced, before any of it is written."""

    metrics: dict
    latency: dict
    cases: dict
    limitations_card: str
    limitations_payload: dict
    preflight: PreflightReport
    dropped_training_bundles: int
    dataset_hash: str
    split_manifest_hash: str
    generator_version: str


def evaluate(
    artifacts: BuildArtifacts,
    build_dir: Path,
    *,
    seed: int = DEFAULT_SEED,
    max_seconds: int = DEFAULT_MAX_SECONDS,
) -> RunOutcome:
    """Run the whole protocol and return every value, without writing anything."""
    started = time.monotonic()
    preflight = run_preflight(artifacts)

    training, dropped = uncontaminated_training_bundles(artifacts)
    model = RankingModel.train(
        training_bundles=training,
        validation_bundles=artifacts.partition(VALIDATION),
        dataset_digest=artifacts.dataset_digest(),
    )

    test_bundles = artifacts.partition(TEST)
    contexts = build_contexts(artifacts.bundles)
    outcomes = screen_all(test_bundles, contexts, model)
    _check_deadline(started, max_seconds, len(outcomes), len(test_bundles))

    truth = load_ground_truth(build_dir, test_bundles)
    metrics = build_metrics(outcomes, truth, seed=seed)
    _check_deadline(started, max_seconds, len(outcomes), len(test_bundles))

    caveats = limitations.caveats_for(
        undefined_metrics=_undefined_metrics(metrics),
        absent_modes=_absent_modes(metrics),
        dropped_training_bundles=len(dropped),
        unexplained_flag_share=metrics["hybrid_explanation"]["unexplained_share"],
        test_bundles=metrics["dataset"]["bundles_evaluated"],
        clean_bundles=metrics["dataset"]["clean"],
    )
    return RunOutcome(
        metrics=metrics,
        latency=latency_report(outcomes),
        cases=case_reports(outcomes, truth),
        limitations_card=limitations.render(caveats),
        limitations_payload=limitations.as_payload(caveats),
        preflight=preflight,
        dropped_training_bundles=len(dropped),
        dataset_hash=artifacts.dataset_digest(),
        split_manifest_hash=manifest.environment_hash(
            {"split": (build_dir / "split.json").read_text(encoding="utf-8")}
        ),
        generator_version=str(artifacts.manifest.get("generator_version", "unknown")),
    )


def write_artifacts(outcome: RunOutcome, out_dir: Path, *, run_id: str, repo_root: Path) -> Path:
    """Write every artifact, then the manifest that hashes them."""
    (out_dir / "tables").mkdir(parents=True, exist_ok=True)
    (out_dir / "charts").mkdir(parents=True, exist_ok=True)

    _write(out_dir / "metrics.json", _json(outcome.metrics))
    _write(out_dir / "latency.json", _json(outcome.latency))
    _write(out_dir / "case_reports.json", _json(outcome.cases))
    _write(out_dir / "LIMITATIONS.md", outcome.limitations_card)
    _write(out_dir / "limitations.json", _json(outcome.limitations_payload))
    _write(out_dir / "tables/baselines.csv", baselines_csv(outcome.metrics))
    _write(out_dir / "tables/per_mode.csv", per_mode_csv(outcome.metrics))
    _write(out_dir / "tables/breakdowns.csv", breakdowns_csv(outcome.metrics))
    for name, svg in render_charts(outcome.metrics).items():
        _write(out_dir / "charts" / name, svg)

    run_manifest = manifest.stamped(
        run_id=run_id,
        dataset_hash=outcome.dataset_hash,
        generator_version=outcome.generator_version,
        split_manifest_hash=outcome.split_manifest_hash,
        threshold_logic=manifest.threshold_logic(),
        code_commit=manifest.code_commit(repo_root),
        environment=manifest.environment(),
        environment_hash=manifest.environment_hash(manifest.environment()),
        artifact_hashes=manifest.hash_artifacts(out_dir),
    )
    _write(out_dir / "manifest.json", run_manifest.model_dump_json(indent=2) + "\n")
    return out_dir


def render_charts(metrics: dict) -> dict[str, str]:
    """Charts built from `metrics`, so a bar cannot disagree with the table beside it."""
    budget = metrics["dataset"]["review_budget"]
    return {
        "false_positives_per_100.svg": charts.bar_chart(
            "False positives per 100 clean claims",
            "Lower is less review work spent on claims with nothing wrong",
            [
                (row["baseline"], row["false_positives_per_100_clean"])
                for row in metrics["baselines"]
            ],
        ),
        "precision_at_budget.svg": charts.bar_chart(
            f"Precision at a review budget of {budget} cases",
            "Share of the reviewed cases that carried an injected pattern",
            [(row["baseline"], row["precision_at_k"]) for row in metrics["baselines"]],
        ),
        "per_mode_f1.svg": charts.bar_chart(
            "Hybrid F1 per risk mode",
            "A mode with no example in the test partition is shown as not measured",
            [
                (row["mode"], row["f1"])
                for row in metrics["per_mode"][BaselineId.HYBRID.value]
            ],
        ),
    }


def _undefined_metrics(metrics: dict) -> tuple[str, ...]:
    undefined = [
        f"{row['baseline']} {name}"
        for row in metrics["baselines"]
        for name in ("macro_f1", "pr_auc", "precision_at_k", "false_positives_per_100_clean")
        if row[name] is None
    ]
    return tuple(undefined)


def _absent_modes(metrics: dict) -> tuple[str, ...]:
    return tuple(
        row["mode"]
        for row in metrics["per_mode"][BaselineId.HYBRID.value]
        if row["status"] == MetricStatus.ABSENT_FROM_TEST_SET.value
    )


def _check_deadline(started: float, max_seconds: int, done: int, total: int) -> None:
    elapsed = time.monotonic() - started
    if elapsed > max_seconds:
        raise EvaluationTimedOut(
            f"evaluation exceeded its {max_seconds}s bound after {elapsed:.0f}s "
            f"({done} of {total} bundles screened). No partial metric is written."
        )


def _json(payload: dict) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def default_run_id() -> str:
    return datetime.now(UTC).strftime("run-%Y%m%dT%H%M%SZ")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build", type=Path, default=Path("../packages/data/build"))
    parser.add_argument("--out", type=Path, default=None, help="defaults to artifacts/<run_id>")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--max-seconds", type=int, default=DEFAULT_MAX_SECONDS)
    args = parser.parse_args()

    run_id = args.run_id or default_run_id()
    out_dir = args.out or Path("artifacts") / run_id

    artifacts = load_build(args.build)
    outcome = evaluate(artifacts, args.build, seed=args.seed, max_seconds=args.max_seconds)
    write_artifacts(outcome, out_dir, run_id=run_id, repo_root=Path(__file__).resolve().parents[2])

    print(f"preflight  {outcome.preflight.summary()}")
    for row in outcome.metrics["baselines"]:
        print(
            f"{row['baseline']:22} macro-F1 {_show(row['macro_f1'])}  "
            f"PR-AUC {_show(row['pr_auc'])}  P@K {_show(row['precision_at_k'])}  "
            f"FP/100 {_show(row['false_positives_per_100_clean'])}"
        )
    validity = outcome.metrics["evidence_reference_validity"]
    resolved = validity["references_resolved"]
    displayed = validity["references_displayed"]
    print(f"evidence   {resolved}/{displayed} displayed references resolve")
    print(
        f"latency    p50 {outcome.latency['p50_ms']:.2f} ms "
        f"· p95 {outcome.latency['p95_ms']:.2f} ms"
    )
    print(f"artifacts  {out_dir.resolve()}")
    return 0


def _show(value: float | None) -> str:
    return "  n/a " if value is None else f"{value:6.4f}"


if __name__ == "__main__":
    raise SystemExit(main())
