"""Assemble every reported value once, so tables, charts, and JSON cannot disagree.

`metrics.json` is the single source of values. The CSV tables and the SVG charts are both
rendered *from this dictionary*, never from a second computation — which is what makes "chart
values match the JSON" a property rather than a hope.

**Nothing here carries a run id or a timestamp.** `metrics.json` is hashed and compared between
runs, so anything that legitimately differs between two runs of the same commit belongs in the
manifest instead. A run id inside a hashed artifact would make the hash comparison always fail
and the check would quietly be abandoned.
"""
from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from typing import Any

from runner.baselines import BaselineId, ScreeningOutcome, predictions_for
from runner.charts import format_value
from runner.metrics import (
    REVIEW_BUDGET_FRACTION,
    GroundTruth,
    ModeScore,
    Prediction,
    bootstrap_interval,
    budget_for,
    false_positives_per_100_clean,
    macro_f1,
    per_mode_scores,
    precision_at_k,
    precision_recall_auc,
    recall_at_k,
)

CASE_REPORT_SAMPLE = 25
"""Minimum false positives and false negatives written out for manual review."""

COMPLETE_EVIDENCE = "complete_evidence"
INCOMPLETE_EVIDENCE = "incomplete_evidence"
SINGLE_LABEL = "single_label"
MULTI_LABEL = "multi_label"


def build_metrics(
    outcomes: Sequence[ScreeningOutcome],
    truth: Sequence[GroundTruth],
    *,
    seed: int,
) -> dict[str, Any]:
    """Every deterministic value the run reports, in one dictionary."""
    budget = budget_for(len(truth))
    predictions = {
        baseline: predictions_for(baseline, outcomes, seed=seed) for baseline in BaselineId
    }

    return {
        "dataset": {
            "bundles_evaluated": len(truth),
            "injected": sum(1 for item in truth if item.is_injected),
            "clean": sum(1 for item in truth if not item.is_injected),
            "review_budget": budget,
            "review_budget_fraction": REVIEW_BUDGET_FRACTION,
        },
        "baselines": [
            _baseline_row(baseline, predictions[baseline], truth, budget, seed)
            for baseline in BaselineId
        ],
        "per_mode": {
            baseline.value: [
                _mode_row(score) for score in per_mode_scores(predictions[baseline], truth).values()
            ]
            for baseline in BaselineId
        },
        "breakdowns": _breakdowns(outcomes, truth, predictions),
        "evidence_reference_validity": _evidence_validity(outcomes),
        "hybrid_explanation": _hybrid_explanation(outcomes),
    }


def _baseline_row(
    baseline: BaselineId,
    predictions: Sequence[Prediction],
    truth: Sequence[GroundTruth],
    budget: int,
    seed: int,
) -> dict[str, Any]:
    scores = per_mode_scores(predictions, truth)
    return {
        "baseline": baseline.value,
        "attributes_modes": bool(predictions and predictions[0].attributes_modes),
        "flagged": sum(1 for prediction in predictions if prediction.flagged),
        "macro_f1": macro_f1(scores),
        "macro_f1_ci": _interval(
            predictions, truth, lambda p, t: macro_f1(per_mode_scores(p, t)), seed
        ),
        "pr_auc": precision_recall_auc(predictions, truth),
        "precision_at_k": precision_at_k(predictions, truth, budget),
        "precision_at_k_ci": _interval(
            predictions, truth, lambda p, t: precision_at_k(p, t, budget_for(len(t))), seed
        ),
        "recall_at_k": recall_at_k(predictions, truth, budget),
        "false_positives_per_100_clean": false_positives_per_100_clean(predictions, truth),
    }


def _interval(predictions, truth, estimate, seed) -> list[float] | None:
    interval = bootstrap_interval(predictions, truth, estimate, seed=seed)
    return [interval[0], interval[1]] if interval else None


def _mode_row(score: ModeScore) -> dict[str, Any]:
    return {
        "mode": score.mode.value,
        "precision": score.precision,
        "recall": score.recall,
        "f1": score.f1,
        "support": score.support,
        "predicted": score.predicted,
        "status": score.status.value,
    }


def _breakdowns(
    outcomes: Sequence[ScreeningOutcome],
    truth: Sequence[GroundTruth],
    predictions: dict[BaselineId, Sequence[Prediction]],
) -> dict[str, list[dict[str, Any]]]:
    """Detection recall inside each slice the evaluation plan requires.

    Reported per baseline and per slice, never averaged into one number: catching every obvious
    case while missing every subtle one is a different result from uniform performance, and only
    a breakdown can tell them apart.
    """
    by_id = {outcome.bundle_id: outcome for outcome in outcomes}
    slices: dict[str, dict[str, list[GroundTruth]]] = {
        "by_mode": {},
        "by_difficulty": {},
        "by_provider": {},
        "by_evidence_completeness": {},
        "by_label_cardinality": {},
    }
    for item in truth:
        if not item.is_injected:
            continue
        outcome = by_id.get(item.bundle_id)
        for mode in item.modes:
            slices["by_mode"].setdefault(mode.value, []).append(item)
        slices["by_difficulty"].setdefault(item.difficulty or "unknown", []).append(item)
        if outcome is not None:
            slices["by_provider"].setdefault(outcome.provider_id, []).append(item)
            completeness = (
                INCOMPLETE_EVIDENCE if outcome.unsupported_line_count else COMPLETE_EVIDENCE
            )
            slices["by_evidence_completeness"].setdefault(completeness, []).append(item)
        slices["by_label_cardinality"].setdefault(
            MULTI_LABEL if item.is_multi_label else SINGLE_LABEL, []
        ).append(item)

    return {
        dimension: [
            _slice_row(dimension, name, members, predictions)
            for name, members in sorted(groups.items())
        ]
        for dimension, groups in slices.items()
    }


def _slice_row(
    dimension: str,
    name: str,
    members: Sequence[GroundTruth],
    predictions: dict[BaselineId, Sequence[Prediction]],
) -> dict[str, Any]:
    member_ids = {item.bundle_id for item in members}
    row: dict[str, Any] = {"dimension": dimension, "slice": name, "injected": len(members)}
    for baseline, items in predictions.items():
        caught = sum(
            1 for prediction in items if prediction.flagged and prediction.bundle_id in member_ids
        )
        row[f"recall_{baseline.value}"] = caught / len(members) if members else None
    return row


def _evidence_validity(outcomes: Sequence[ScreeningOutcome]) -> dict[str, Any]:
    total = sum(outcome.evidence_refs_total for outcome in outcomes)
    resolved = sum(outcome.evidence_refs_resolved for outcome in outcomes)
    return {
        "references_displayed": total,
        "references_resolved": resolved,
        "validity": resolved / total if total else None,
    }


def _hybrid_explanation(outcomes: Sequence[ScreeningOutcome]) -> dict[str, Any]:
    """How many hybrid flags have no rule reason a reviewer could read."""
    flagged = [outcome for outcome in outcomes if outcome.flagged_by_hybrid]
    unexplained = [outcome for outcome in flagged if not outcome.reason_modes]
    return {
        "flagged": len(flagged),
        "unexplained_by_reasons": len(unexplained),
        "unexplained_share": len(unexplained) / len(flagged) if flagged else None,
    }


def latency_report(outcomes: Sequence[ScreeningOutcome]) -> dict[str, Any]:
    """Measured, and kept out of the hashed artifact set — see `manifest.py`."""
    from runner.metrics import percentile

    samples = [outcome.latency_ms for outcome in outcomes]
    return {
        "p50_ms": percentile(samples, 0.50),
        "p95_ms": percentile(samples, 0.95),
        "samples": len(samples),
        "note": (
            "Measures this machine screening one bundle with its history in memory. It is not a "
            "production latency figure and carries no claim about load at scale."
        ),
    }


def case_reports(
    outcomes: Sequence[ScreeningOutcome],
    truth: Sequence[GroundTruth],
    *,
    sample: int = CASE_REPORT_SAMPLE,
) -> dict[str, Any]:
    """False positives and false negatives written out for a human to read.

    Selected deterministically by identifier so two runs review the same cases; the evaluation
    plan asks for at least 25 of each, and the failure-mode write-up on top of them is a human
    task this file only supplies the material for.
    """
    by_id = {item.bundle_id: item for item in truth}
    false_positives, false_negatives = [], []
    for outcome in sorted(outcomes, key=lambda item: item.bundle_id):
        actual = by_id.get(outcome.bundle_id)
        if actual is None:
            continue
        if outcome.flagged_by_hybrid and not actual.is_injected:
            false_positives.append(_case_row(outcome, actual))
        elif not outcome.flagged_by_hybrid and actual.is_injected:
            false_negatives.append(_case_row(outcome, actual))

    return {
        "requested_sample": sample,
        "false_positives_total": len(false_positives),
        "false_negatives_total": len(false_negatives),
        "false_positives": false_positives[:sample],
        "false_negatives": false_negatives[:sample],
        "failure_mode_writeup": (
            "Owed: a human reads these cases and writes the top failure modes. This artifact "
            "supplies the material and makes no claim about what they show."
        ),
    }


def _case_row(outcome: ScreeningOutcome, actual: GroundTruth) -> dict[str, Any]:
    return {
        "bundle_id": outcome.bundle_id,
        "injected_modes": sorted(mode.value for mode in actual.modes),
        "difficulty": actual.difficulty,
        "is_multi_label": actual.is_multi_label,
        "reason_codes": sorted(code.value for code in outcome.reason_codes),
        "rules_band": outcome.rules_band.value,
        "hybrid_band": outcome.hybrid_band.value,
        "certainty": outcome.certainty.value,
        "similarity_score": outcome.similarity_score,
        "anomaly_score": outcome.anomaly_score,
        "billed_lines": outcome.billed_line_count,
        "unsupported_lines": outcome.unsupported_line_count,
    }


# --------------------------------------------------------------------------------------
# Tables and charts — rendered from `metrics`, never recomputed
# --------------------------------------------------------------------------------------


def baselines_csv(metrics: dict[str, Any]) -> str:
    columns = (
        "baseline",
        "attributes_modes",
        "flagged",
        "macro_f1",
        "pr_auc",
        "precision_at_k",
        "recall_at_k",
        "false_positives_per_100_clean",
    )
    return _csv(columns, metrics["baselines"])


def per_mode_csv(metrics: dict[str, Any]) -> str:
    rows = [
        {"baseline": baseline, **row}
        for baseline, entries in metrics["per_mode"].items()
        for row in entries
    ]
    return _csv(
        ("baseline", "mode", "precision", "recall", "f1", "support", "predicted", "status"), rows
    )


def breakdowns_csv(metrics: dict[str, Any]) -> str:
    rows = [row for entries in metrics["breakdowns"].values() for row in entries]
    columns = ("dimension", "slice", "injected", *(
        f"recall_{baseline.value}" for baseline in BaselineId
    ))
    return _csv(columns, rows)


def _csv(columns: tuple[str, ...], rows: Sequence[dict[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer, fieldnames=columns, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()
    for row in rows:
        writer.writerow({column: _cell(row.get(column)) for column in columns})
    return buffer.getvalue()


def _cell(value: Any) -> str:
    """One rendering of a value, shared with the charts so a table cannot disagree with a bar."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return format_value(value)
    return str(value)
