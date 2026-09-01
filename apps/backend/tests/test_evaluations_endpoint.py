"""`GET /v1/evaluations/{run_id}` — reading artifacts, and refusing to invent them.

The endpoint's whole job is to serve what the offline runner wrote. So the tests build a run
directory by hand, exactly as the runner lays one out, and assert on what comes back — including
the cases where a value is undefined, which must be **absent** rather than rendered as zero.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.service.evaluation_artifacts import LATEST

client = TestClient(app)

MANIFEST = {
    "run_id": "run-20260901T000000Z",
    "generated_at": "2026-09-01T00:00:00+00:00",
    "dataset_hash": "1ff95898c696",
    "generator_version": "0.1.0",
    "split_manifest_hash": "aa11",
    "schema_version": "0.1.0",
    "ruleset_version": "0.1.0",
    "engine_version": "0.1.0",
    "feature_version": "0.1.0",
    "model_version": "0.1.0",
    "threshold_logic": "quantiles of the validation distribution",
    "code_commit": "abc123",
    "environment_hash": "bb22",
    "artifact_hashes": {"metrics.json": "cc33"},
}

METRICS = {
    "dataset": {"bundles_evaluated": 228, "injected": 60, "clean": 168, "review_budget": 23},
    "baselines": [
        {
            "baseline": "B1_RULES_ONLY",
            "macro_f1": 0.6510,
            "pr_auc": 0.7122,
            "precision_at_k": 0.9565,
            "recall_at_k": 0.3667,
            "false_positives_per_100_clean": 51.875,
        },
        {
            "baseline": "HYBRID",
            "macro_f1": 0.6510,
            "pr_auc": 0.8440,
            "precision_at_k": 1.0,
            "recall_at_k": 0.3833,
            "false_positives_per_100_clean": 52.5,
        },
        {
            "baseline": "B0_RANDOM",
            "macro_f1": None,
            "pr_auc": 0.2681,
            "precision_at_k": 0.087,
            "recall_at_k": 0.05,
            "false_positives_per_100_clean": 63.75,
        },
    ],
    "per_mode": {
        "HYBRID": [
            {
                "mode": "PHANTOM_OR_NO_PROCEDURE_EVIDENCE",
                "precision": 0.8,
                "recall": 0.75,
                "f1": 0.774,
                "support": 12,
                "status": "measured",
            },
            {
                "mode": "CLONED_DOCUMENTATION",
                "precision": None,
                "recall": None,
                "f1": None,
                "support": 0,
                "status": "absent_from_test_set",
            },
        ]
    },
}

LIMITATIONS = {
    "mandatory_statement": (
        "This dataset is synthetic and does not represent JKN prevalence or real provider "
        "behavior."
    ),
    "demonstrates": ["Detectors recover known injected patterns"],
    "does_not_demonstrate": ["Real-world JKN fraud accuracy or prevalence"],
    "run_caveats": ["Measured on 228 held-out bundles, of which 168 carry no injection."],
    "impact_model": "No cost saving is claimed.",
}


def _write_run(root, run_id: str, *, complete: bool = True) -> None:
    directory = root / run_id
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "metrics.json").write_text(json.dumps(METRICS), encoding="utf-8")
    (directory / "limitations.json").write_text(json.dumps(LIMITATIONS), encoding="utf-8")
    (directory / "latency.json").write_text(
        json.dumps({"p50_ms": 1.97, "p95_ms": 2.55}), encoding="utf-8"
    )
    if complete:
        (directory / "manifest.json").write_text(
            json.dumps({**MANIFEST, "run_id": run_id}), encoding="utf-8"
        )


@pytest.fixture
def artifacts_root(tmp_path, monkeypatch):
    """Point the API at a throwaway artifacts directory for the duration of one test."""
    get_settings.cache_clear()
    monkeypatch.setenv("EVALUATION_ARTIFACTS_DIR", str(tmp_path))
    yield tmp_path
    get_settings.cache_clear()


def test_a_completed_run_is_served_from_its_artifacts(artifacts_root) -> None:
    _write_run(artifacts_root, "run-20260901T000000Z")
    response = client.get("/v1/evaluations/run-20260901T000000Z")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "run-20260901T000000Z"
    assert payload["data_class"] == "synthetic"
    assert payload["latency_p50_ms"] == 2
    assert payload["manifest"]["code_commit"] == "abc123"


def test_a_baseline_with_an_undefined_metric_is_omitted_not_zeroed(artifacts_root) -> None:
    """A zero would claim we measured it and found nothing. We did not measure it."""
    _write_run(artifacts_root, "run-1")
    payload = client.get("/v1/evaluations/run-1").json()

    reported = {row["baseline"] for row in payload["baselines"]}
    assert reported == {"B1_RULES_ONLY", "HYBRID"}
    assert "B0_RANDOM" not in reported
    assert all(row["macro_f1"] != 0.0 for row in payload["baselines"])


def test_a_mode_absent_from_the_test_set_is_omitted_not_zeroed(artifacts_root) -> None:
    _write_run(artifacts_root, "run-1")
    payload = client.get("/v1/evaluations/run-1").json()

    modes = {row["mode"] for row in payload["per_mode"]}
    assert modes == {"PHANTOM_OR_NO_PROCEDURE_EVIDENCE"}
    assert "CLONED_DOCUMENTATION" not in modes


def test_the_limitations_card_carries_the_canonical_rows_and_this_run_s_caveats(
    artifacts_root,
) -> None:
    """The caveats are the only part that changes with the result; dropping them guts the card."""
    _write_run(artifacts_root, "run-1")
    card = client.get("/v1/evaluations/run-1").json()["limitations"]

    assert "synthetic" in card["mandatory_statement"].lower()
    assert "Real-world JKN fraud accuracy or prevalence" in card["does_not_demonstrate"]
    assert any("228 held-out bundles" in line for line in card["does_not_demonstrate"])


def test_latest_resolves_to_the_most_recent_complete_run(artifacts_root) -> None:
    _write_run(artifacts_root, "run-20260901T000000Z")
    _write_run(artifacts_root, "run-20260902T000000Z")
    payload = client.get(f"/v1/evaluations/{LATEST}").json()
    assert payload["run_id"] == "run-20260902T000000Z"


def test_latest_skips_a_partially_written_run(artifacts_root) -> None:
    """A half-written directory is not a result, and must not be served as the newest one."""
    _write_run(artifacts_root, "run-20260901T000000Z")
    _write_run(artifacts_root, "run-20260903T000000Z", complete=False)
    payload = client.get(f"/v1/evaluations/{LATEST}").json()
    assert payload["run_id"] == "run-20260901T000000Z"


def test_no_run_at_all_is_a_404_naming_the_state(artifacts_root) -> None:
    response = client.get(f"/v1/evaluations/{LATEST}")
    assert response.status_code == 404
    assert response.json()["code"] == "EVALUATION_RUN_NOT_FOUND"
    assert "no completed evaluation run" in response.json()["detail"]


def test_a_run_id_containing_a_path_separator_is_refused(artifacts_root) -> None:
    """A run id names a directory. Treating it as a path would read files outside the root."""
    (artifacts_root.parent / "secret.json").write_text("{}", encoding="utf-8")
    for hostile in ("..%2Fsecret", "%2Fetc%2Fpasswd", "..", "."):
        assert client.get(f"/v1/evaluations/{hostile}").status_code == 404


def test_an_unreadable_run_is_reported_as_missing_not_as_a_broken_service(
    artifacts_root,
) -> None:
    """A hand-edited artifact should send the operator to re-run, not to the API logs."""
    _write_run(artifacts_root, "run-1")
    (artifacts_root / "run-1" / "metrics.json").write_text("{not json", encoding="utf-8")
    response = client.get("/v1/evaluations/run-1")
    assert response.status_code == 404
    assert "re-run the offline evaluation" in response.json()["detail"]


def test_the_endpoint_computes_nothing_itself(artifacts_root) -> None:
    """Served values must be exactly what the artifact holds, to four decimals and beyond."""
    _write_run(artifacts_root, "run-1")
    payload = client.get("/v1/evaluations/run-1").json()
    hybrid = next(row for row in payload["baselines"] if row["baseline"] == "HYBRID")
    assert hybrid["pr_auc"] == 0.8440
    assert hybrid["false_positives_per_100_clean"] == 52.5
