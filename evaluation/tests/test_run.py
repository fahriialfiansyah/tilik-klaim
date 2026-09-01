"""The whole runner, end to end: gates, artifacts, hashes, and what must never be in them."""
from __future__ import annotations

import json
import re

import pytest
from runner.baselines import BaselineId
from runner.charts import UNDEFINED_LABEL
from runner.manifest import DETERMINISTIC_ARTIFACTS, MEASURED_ARTIFACTS
from runner.preflight import PreflightFailed, run_preflight
from runner.run import evaluate, render_charts, write_artifacts
from tilik_data.split import GOLD_BUNDLE_IDS
from tilik_model.dataset import TEST

SEED = 20260902


@pytest.fixture(scope="module")
def outcome(artifacts, build_dir):
    return evaluate(artifacts, build_dir, seed=SEED)


@pytest.fixture(scope="module")
def written(outcome, tmp_path_factory):
    out = tmp_path_factory.mktemp("run")
    return write_artifacts(outcome, out, run_id="run-test", repo_root=out)


def test_preflight_passes_on_a_regenerated_corpus(artifacts) -> None:
    report = run_preflight(artifacts)
    assert "no leak detected" in report.leakage_summary


def test_preflight_refuses_a_corpus_that_still_carries_an_injector_suffix(artifacts) -> None:
    """The gate that would have caught the Sprint 01 defect before any metric existed."""
    leaky = artifacts.bundles[0].model_copy(update={"bundle_id": "BND-00042-R173"})
    broken = type(artifacts)(
        bundles=(leaky, *artifacts.bundles[1:]),
        partitions=artifacts.partitions,
        excluded_demo=artifacts.excluded_demo,
        labelled_bundle_ids=artifacts.labelled_bundle_ids,
        manifest=artifacts.manifest,
    )
    with pytest.raises(PreflightFailed, match="injector suffix"):
        run_preflight(broken)


def test_preflight_refuses_a_demo_fixture_in_a_partition(artifacts) -> None:
    """The five curated cases are the ones most likely to have been looked at while tuning."""
    intruded = dict(artifacts.partitions)
    intruded[TEST] = intruded[TEST] | {next(iter(GOLD_BUNDLE_IDS))}
    broken = type(artifacts)(
        bundles=artifacts.bundles,
        partitions=intruded,
        excluded_demo=artifacts.excluded_demo,
        labelled_bundle_ids=artifacts.labelled_bundle_ids,
        manifest=artifacts.manifest,
    )
    with pytest.raises(PreflightFailed, match="demo fixture"):
        run_preflight(broken)


def test_all_four_baselines_are_reported(outcome) -> None:
    reported = {row["baseline"] for row in outcome.metrics["baselines"]}
    assert reported == {baseline.value for baseline in BaselineId}


def test_every_mode_appears_with_a_status(outcome) -> None:
    """A mode with no example is reported absent, never silently skipped."""
    for baseline in BaselineId:
        rows = outcome.metrics["per_mode"][baseline.value]
        assert len(rows) == 4
        assert all(row["status"] for row in rows)


def test_the_required_breakdowns_are_all_present(outcome) -> None:
    assert set(outcome.metrics["breakdowns"]) == {
        "by_mode",
        "by_difficulty",
        "by_provider",
        "by_evidence_completeness",
        "by_label_cardinality",
    }


def test_false_positives_per_100_is_reported_for_every_baseline(outcome) -> None:
    for row in outcome.metrics["baselines"]:
        assert "false_positives_per_100_clean" in row


def test_latency_is_measured_and_kept_out_of_the_hashed_set(outcome) -> None:
    assert outcome.latency["p50_ms"] > 0
    assert "latency.json" in MEASURED_ARTIFACTS
    assert "latency.json" not in DETERMINISTIC_ARTIFACTS


def test_metrics_json_carries_no_run_id_or_timestamp(outcome) -> None:
    """Anything that differs between two runs of one commit belongs in the manifest."""
    serialised = json.dumps(outcome.metrics)
    assert "run_id" not in serialised
    assert "generated_at" not in serialised


def test_every_artifact_is_written(written) -> None:
    for name in (*DETERMINISTIC_ARTIFACTS, *MEASURED_ARTIFACTS, "manifest.json"):
        assert (written / name).exists(), name


def test_the_manifest_records_everything_needed_to_reproduce(written) -> None:
    payload = json.loads((written / "manifest.json").read_text(encoding="utf-8"))
    for field in (
        "dataset_hash",
        "generator_version",
        "split_manifest_hash",
        "feature_version",
        "ruleset_version",
        "model_version",
        "threshold_logic",
        "code_commit",
        "environment_hash",
        "artifact_hashes",
    ):
        assert payload[field], field
    assert set(payload["artifact_hashes"]) == set(DETERMINISTIC_ARTIFACTS)


def test_a_clean_rerun_reproduces_identical_artifact_hashes(
    artifacts, build_dir, tmp_path_factory
) -> None:
    """The reproducibility claim, checked rather than asserted in prose."""
    first = write_artifacts(
        evaluate(artifacts, build_dir, seed=SEED),
        tmp_path_factory.mktemp("a"),
        run_id="run-a",
        repo_root=build_dir,
    )
    second = write_artifacts(
        evaluate(artifacts, build_dir, seed=SEED),
        tmp_path_factory.mktemp("b"),
        run_id="run-b",
        repo_root=build_dir,
    )
    left = json.loads((first / "manifest.json").read_text())["artifact_hashes"]
    right = json.loads((second / "manifest.json").read_text())["artifact_hashes"]
    assert left == right


def test_chart_values_match_metrics_json(outcome) -> None:
    """The acceptance criterion, checked by reading the numbers back out of the SVG."""
    known = _every_number(outcome.metrics)
    for name, svg in render_charts(outcome.metrics).items():
        for rendered in re.findall(r">(\d+\.\d{4})<", svg):
            assert rendered in known, f"{name} renders {rendered}, which is not in metrics.json"


def test_a_chart_shows_an_undefined_value_as_unmeasured_not_as_zero(outcome) -> None:
    svg = render_charts(
        {
            **outcome.metrics,
            "baselines": [{"baseline": "B0_RANDOM", "precision_at_k": None,
                           "false_positives_per_100_clean": None}],
        }
    )["precision_at_budget.svg"]
    assert UNDEFINED_LABEL in svg
    assert ">0.0000<" not in svg


def test_the_limitations_card_is_present_and_copy_ready(written) -> None:
    card = (written / "LIMITATIONS.md").read_text(encoding="utf-8")
    assert "synthetic and does not represent JKN prevalence" in card
    assert "## What these results do not demonstrate" in card
    assert "Caveats specific to this run" in card


def test_the_card_never_states_fraud_as_a_finding(written) -> None:
    """A bare word search would flag the disclaimer that rules the word out.

    The canonical evaluation plan's own row — "Real-world JKN fraud accuracy or prevalence" —
    appears verbatim under *what these results do not demonstrate*, which is the opposite of a
    finding. So the check is on finding-shaped phrasing, and on the word appearing nowhere else.
    """
    card = (written / "LIMITATIONS.md").read_text(encoding="utf-8")
    lines_with_the_word = [
        line for line in card.splitlines() if re.search(r"\bfraud\b", line, flags=re.IGNORECASE)
    ]
    assert lines_with_the_word == ["- Real-world JKN fraud accuracy or prevalence"]
    for finding in ("is fraud", "fraud detected", "indicates fraud", "terbukti", "penipuan"):
        assert finding.lower() not in card.lower()


def test_case_reports_supply_material_for_manual_review(written) -> None:
    payload = json.loads((written / "case_reports.json").read_text(encoding="utf-8"))
    assert payload["requested_sample"] == 25
    assert "failure_mode_writeup" in payload
    for case in (*payload["false_positives"], *payload["false_negatives"]):
        assert case["bundle_id"]
        assert "reason_codes" in case


def test_no_demo_fixture_appears_in_any_artifact(written) -> None:
    """Provably absent, checked against the files rather than trusted."""
    for name in DETERMINISTIC_ARTIFACTS:
        content = (written / name).read_text(encoding="utf-8")
        for gold in GOLD_BUNDLE_IDS:
            assert gold not in content, f"{gold} appears in {name}"


def test_tables_and_charts_agree_on_the_same_values(outcome, written) -> None:
    table = (written / "tables/baselines.csv").read_text(encoding="utf-8")
    for row in outcome.metrics["baselines"]:
        value = row["false_positives_per_100_clean"]
        if value is not None:
            assert f"{value:.4f}" in table


def _every_number(payload) -> set[str]:
    """Every numeric value in the metrics, at the precision the charts render."""
    found: set[str] = set()

    def walk(node) -> None:
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            found.add(f"{float(node):.4f}")

    walk(payload)
    return found
