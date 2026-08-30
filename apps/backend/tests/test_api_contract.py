"""The frozen API contract.

Sprint 04's frontend builds against the committed fixtures here. A change that breaks these
tests breaks that parallelism, so treat a failure as a contract renegotiation rather than a
test to update.
"""
from __future__ import annotations

import json
import pathlib

import pytest
from fastapi.testclient import TestClient

from app.dto.bundles import IngestBundleResponse, ScreenResponse
from app.dto.cases import CaseDetailResponse, CaseQueueResponse, CaseSummary, QueueMetrics
from app.dto.dispositions import (
    AuditEvent,
    AuditResponse,
    DispositionRequest,
    DispositionResponse,
)
from app.dto.evaluations import EvaluationResponse
from app.errors import STATUS_FOR_CODE, ErrorCode, ErrorResponse
from app.main import app
from tilik_domain.reasons import REASON_CATALOG, DispositionAction

FIXTURE_DIR = pathlib.Path(__file__).parent / "fixtures" / "api"

FIXTURE_MODELS = {
    "post_bundles": IngestBundleResponse,
    "post_bundles_invalid": IngestBundleResponse,
    "post_screen": ScreenResponse,
    "get_cases": CaseQueueResponse,
    "get_case_detail": CaseDetailResponse,
    "get_case_detail_clone": CaseDetailResponse,
    "post_disposition": DispositionResponse,
    "post_disposition_conflict": ErrorResponse,
    "get_audit": AuditResponse,
    "get_evaluation": EvaluationResponse,
}

EXPECTED_PATHS = {
    "/v1/bundles",
    "/v1/bundles/{ingestion_id}/screen",
    "/v1/cases",
    "/v1/cases/{case_id}",
    "/v1/cases/{case_id}/dispositions",
    "/v1/cases/{case_id}/audit",
    "/v1/evaluations/{run_id}",
}

client = TestClient(app)


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / f"{name}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", sorted(FIXTURE_MODELS))
def test_fixture_validates_against_its_model(name: str) -> None:
    """Every committed example is a legal response. This is what the frontend relies on."""
    FIXTURE_MODELS[name].model_validate(_load(name))


def test_all_seven_endpoints_are_published() -> None:
    schema = app.openapi()
    assert EXPECTED_PATHS <= set(schema["paths"]), (
        f"missing from OpenAPI: {EXPECTED_PATHS - set(schema['paths'])}"
    )


def test_every_error_code_maps_to_an_http_status() -> None:
    """A code with no status would surface as a 500 and tell the operator nothing."""
    assert set(ErrorCode) == set(STATUS_FOR_CODE)


def test_queue_response_carries_no_medical_text() -> None:
    """`GET /v1/cases` returns pseudonymous fields only.

    Narrative text belongs in the detail response, and then only the fragment a reason
    depends on. A list endpoint that leaks clinical notes would spread them across every
    screen that renders a queue.
    """
    queue = CaseQueueResponse.model_validate(_load("get_cases"))
    forbidden = ("pasien datang", "keluhan", "auskultasi", "diagnosis", "anamnesis")
    payload = queue.model_dump_json().lower()
    for term in forbidden:
        assert term not in payload, f"queue response leaks medical text: {term!r}"


def test_queue_rows_lead_with_the_reason_sentence() -> None:
    """Reason before score — asserted on field order, which clients render in sequence."""
    CaseQueueResponse.model_validate(_load("get_cases"))  # fixture must stay parseable
    field_order = list(CaseSummary.model_fields)
    assert field_order[0] == "reason_sentence"
    assert field_order.index("reason_sentence") < field_order.index("band")
    assert field_order.index("reason_sentence") < field_order.index("total_amount")


def test_queue_exposes_exactly_five_operational_metrics() -> None:
    """Five metrics, all operational. Anything else is excluded by the dashboard principles."""
    CaseQueueResponse.model_validate(_load("get_cases"))  # fixture must stay parseable
    metric_fields = set(QueueMetrics.model_fields)
    assert metric_fields == {
        "awaiting_review",
        "deterministic_conflicts",
        "evidence_requested",
        "median_time_in_queue_hours",
        "versions",
    }
    forbidden = ("fraud", "saved", "recovered", "ranking", "league", "projection")
    for name in metric_fields:
        assert not any(term in name for term in forbidden), f"forbidden metric: {name}"


def test_reason_sentences_come_from_the_catalog() -> None:
    """Queue and detail must never disagree about why a case was raised."""
    catalogued = {definition.sentence_id for definition in REASON_CATALOG.values()}
    detail = CaseDetailResponse.model_validate(_load("get_case_detail"))
    assert detail.primary_reason is not None
    assert detail.primary_reason.sentence in catalogued

    queue = CaseQueueResponse.model_validate(_load("get_cases"))
    for row in queue.items:
        assert row.reason_sentence in catalogued


def test_clone_reason_is_capped_and_carries_the_template_caveat() -> None:
    """Text similarity alone can never reach the top band, and the reviewer is told why."""
    detail = CaseDetailResponse.model_validate(_load("get_case_detail_clone"))
    assert detail.band.band != "DETERMINISTIC_CONFLICT"
    assert detail.band.caps_applied, "a capped band must say which cap applied"
    assert detail.comparisons
    assert detail.comparisons[0].template_caveat, "clone comparison must carry the caveat"


def test_disposition_requires_a_non_blank_reason() -> None:
    """Enforced in the type, not only in the UI — a client can bypass the UI."""
    with pytest.raises(ValueError):
        DispositionRequest(
            action=DispositionAction.CONFIRM_ANOMALY,
            structured_reason="   ",
            expected_case_version=1,
        )


def test_disposition_requires_an_expected_case_version() -> None:
    """The optimistic lock is mandatory, so a stale write cannot silently overwrite."""
    with pytest.raises(ValueError):
        DispositionRequest(
            action=DispositionAction.REJECT_SIGNAL,
            structured_reason="Tindak lanjut yang sah.",
        )  # type: ignore[call-arg]


def test_version_conflict_fixture_uses_the_stable_code() -> None:
    error = ErrorResponse.model_validate(_load("post_disposition_conflict"))
    assert error.code is ErrorCode.CASE_VERSION_CONFLICT
    assert error.http_status == 409


def test_audit_supports_supersede_without_overwrite() -> None:
    """Corrections append. The field must exist even before the first correction is written."""
    audit = AuditResponse.model_validate(_load("get_audit"))
    assert "supersedes_event_id" in AuditEvent.model_fields
    assert [e.occurred_at for e in audit.events] == sorted(e.occurred_at for e in audit.events)


def test_evaluation_response_is_labelled_synthetic_and_carries_limitations() -> None:
    evaluation = EvaluationResponse.model_validate(_load("get_evaluation"))
    assert evaluation.data_class == "synthetic"
    assert evaluation.limitations.does_not_demonstrate
    assert "synthetic" in evaluation.limitations.mandatory_statement.lower()
    assert {m.baseline for m in evaluation.baselines} >= {"B1_RULES_ONLY", "HYBRID"}


def test_unimplemented_endpoints_answer_501_naming_their_task() -> None:
    """The contract is live; the behaviour is not. A caller gets an unambiguous answer."""
    response = client.get("/v1/cases")
    assert response.status_code == 501
    assert "sprint" in response.json()["detail"].lower()
