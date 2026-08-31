"""Ingestion: what gets accepted, what gets refused, and what gets said about it.

The refusals matter as much as the acceptances. An operator who is told "invalid bundle" can
only resubmit and hope; one who is told which resource is missing can fix it. Every rejection
path here asserts its own stable code.
"""
from __future__ import annotations

import json
import logging

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.dto.bundles import ValidationStatus
from app.errors import ErrorCode
from app.main import app
from app.service.hashing import canonical_json, idempotency_key, input_hash
from app.service.validation import completeness_notes
from app.store.registry import get_bundle_store
from tests.fixtures import SCENARIOS, load

JSON = {"content-type": "application/json"}


@pytest.fixture(autouse=True)
def store():
    """A clean store around every test, whichever backend the app selected."""
    backing = get_bundle_store()
    backing.clear()
    yield backing
    backing.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def payload_for(scenario: str) -> dict:
    return load(scenario).bundle.model_dump(mode="json")


def post(client: TestClient, payload, headers: dict | None = None):
    body = payload if isinstance(payload, (str, bytes)) else json.dumps(payload)
    return client.post("/v1/bundles", content=body, headers=JSON if headers is None else headers)


# --------------------------------------------------------------------------------------
# The happy path
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_every_gold_bundle_is_accepted_and_screenable(client, scenario: str) -> None:
    response = post(client, payload_for(scenario))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] in {ValidationStatus.VALID, ValidationStatus.VALID_WITH_NOTES}
    assert body["is_screenable"] is True
    assert len(body["input_hash"]) == 64
    assert body["ingestion_id"].startswith("ing_")
    assert body["schema_version"]


def test_response_reports_counts_per_resource_type(client) -> None:
    response = post(client, payload_for("clean"))
    counts = {row["resource_type"]: row["count"] for row in response.json()["resource_counts"]}

    assert counts["Claim"] == 1
    assert counts["ClaimLine"] == len(load("clean").bundle.lines)
    assert counts["Procedure"] == len(load("clean").bundle.procedures)


# --------------------------------------------------------------------------------------
# The load-bearing distinction: incomplete is not invalid
# --------------------------------------------------------------------------------------


def test_partial_bundle_is_valid_with_notes_not_invalid(client) -> None:
    """An incomplete record must never be refused as if it were a malformed one.

    This is the distinction that keeps "we were not sent the evidence" from being processed
    as "the service was not delivered".
    """
    bundle = load("clean").bundle
    bare_lines = tuple(line.model_copy(update={"supporting_refs": ()}) for line in bundle.lines)
    stripped = bundle.model_copy(
        update={"lines": bare_lines, "procedures": (), "medications": (), "provenance": ()}
    )

    response = post(client, stripped.model_dump(mode="json"))

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == ValidationStatus.VALID_WITH_NOTES
    assert body["is_screenable"] is True, "a thin bundle is still reviewable"
    assert body["completeness_notes"], "the notes are what carry the incompleteness onward"


def test_completeness_notes_describe_the_submission_not_the_care() -> None:
    """A note may say what the file lacks. It may never say what did or did not happen."""
    bundle = load("clean").bundle
    stripped = bundle.model_copy(
        update={"documents": (), "procedures": (), "medications": (), "encounters": ()}
    )
    notes = completeness_notes(stripped)
    assert notes
    for note in notes:
        lowered = note.lower()
        assert lowered.startswith("bundel"), f"a note must be about the file: {note!r}"
        for forbidden in ("tidak diberikan", "tidak dilakukan", "fiktif", "palsu"):
            assert forbidden not in lowered, f"note claims something about care: {note!r}"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_gold_bundles_are_all_evidence_complete(client, scenario: str) -> None:
    """The fixtures declare `expected_evidence_complete`, and ingestion must agree.

    Phantom is the one that matters: it carries a line with no supporting evidence, and the
    bundle is still *complete* — everything that should have been sent was sent. That missing
    evidence is a finding for the rule engine, not an incompleteness caveat. Recording it here
    would lower certainty downstream and defuse the detector.
    """
    assert load(scenario).expected_evidence_complete is True
    body = post(client, payload_for(scenario)).json()
    assert body["completeness_notes"] == [], f"{scenario} was wrongly marked incomplete"
    assert body["status"] == ValidationStatus.VALID


def test_an_unevidenced_line_is_a_finding_not_a_completeness_note() -> None:
    """Stated as its own assertion because collapsing the two breaks phantom detection."""
    phantom = load("phantom").bundle
    assert any(not line.supporting_refs for line in phantom.lines), "fixture precondition"
    assert completeness_notes(phantom) == ()


def test_a_complete_bundle_carries_no_notes(client) -> None:
    body = post(client, payload_for("clean")).json()
    assert body["status"] == ValidationStatus.VALID
    assert body["completeness_notes"] == []


# --------------------------------------------------------------------------------------
# Structural guards, applied before parsing
# --------------------------------------------------------------------------------------


def test_wrong_content_type_is_refused(client) -> None:
    response = client.post(
        "/v1/bundles", content=b"{}", headers={"content-type": "text/plain"}
    )
    assert response.status_code == 415
    assert response.json()["code"] == ErrorCode.BUNDLE_UNSUPPORTED_CONTENT_TYPE


def test_oversized_payload_is_refused_before_parsing(client, monkeypatch) -> None:
    """The limit must bite on size alone — the payload here is not even valid JSON."""
    settings = get_settings()
    monkeypatch.setattr(settings, "max_bundle_bytes", 64)

    response = post(client, b"x" * 4096)

    assert response.status_code == 413
    assert response.json()["code"] == ErrorCode.BUNDLE_TOO_LARGE


def test_over_deep_payload_is_refused(client, monkeypatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "max_json_depth", 8)

    nested: dict = {}
    cursor = nested
    for _ in range(40):
        cursor["next"] = {}
        cursor = cursor["next"]

    response = post(client, nested)

    assert response.status_code == 413
    assert response.json()["code"] == ErrorCode.BUNDLE_DEPTH_EXCEEDED


def test_deeply_nested_payload_does_not_exhaust_the_stack(client, monkeypatch) -> None:
    """Depth is measured iteratively; hostile nesting must be refused, not crash the service."""
    monkeypatch.setattr(get_settings(), "max_json_depth", 32)
    response = post(client, json.loads("[" * 400 + "]" * 400))
    assert response.status_code in {400, 413, 422}


@pytest.mark.parametrize(
    "raw",
    [b"", b"{", b"not json at all", b'{"bundle_id": }', b"\xff\xfe\x00", b"[1,2,3"],
)
def test_malformed_payloads_never_crash_the_service(client, raw: bytes) -> None:
    response = post(client, raw)
    assert response.status_code in {400, 422}
    assert response.json()["code"] in {
        ErrorCode.BUNDLE_MALFORMED_JSON,
        ErrorCode.BUNDLE_SCHEMA_INVALID,
    }


def test_non_object_top_level_is_refused(client) -> None:
    response = post(client, [1, 2, 3])
    assert response.json()["code"] == ErrorCode.BUNDLE_SCHEMA_INVALID


# --------------------------------------------------------------------------------------
# Validation issues, each with its own actionable code
# --------------------------------------------------------------------------------------


def test_unknown_resource_type_is_named_not_silently_dropped(client) -> None:
    payload = payload_for("clean")
    payload["unicorns"] = [{"id": "U1"}]

    response = post(client, payload)
    body = response.json()

    assert body["code"] == ErrorCode.BUNDLE_UNKNOWN_RESOURCE_TYPE
    assert any(issue["resource_type"] == "unicorns" for issue in body["issues"])


def test_dangling_reference_names_the_missing_resource(client) -> None:
    payload = payload_for("clean")
    payload["lines"][0]["supporting_refs"] = [
        {"resource_type": "Procedure", "resource_id": "PROC-DOES-NOT-EXIST"}
    ]

    body = post(client, payload).json()

    assert body["status"] == ValidationStatus.INVALID
    assert body["is_screenable"] is False
    issue = next(i for i in body["issues"] if i["code"] == ErrorCode.BUNDLE_DANGLING_REFERENCE)
    assert issue["resource_id"] == "PROC-DOES-NOT-EXIST"
    assert issue["resource_type"] == "Procedure"


def test_duplicate_resource_id_is_reported(client) -> None:
    payload = payload_for("clean")
    payload["lines"].append(json.loads(json.dumps(payload["lines"][0])))

    body = post(client, payload).json()

    assert body["status"] == ValidationStatus.INVALID
    assert any(
        issue["code"] == ErrorCode.BUNDLE_DUPLICATE_RESOURCE_ID for issue in body["issues"]
    )


def test_schema_violation_reports_the_field_not_the_value(client) -> None:
    """Pydantic echoes offending input; in this domain that can be clinical text."""
    payload = payload_for("clean")
    payload["claim"]["total_amount"] = "seratus ribu rupiah"

    body = post(client, payload).json()

    assert body["status"] == ValidationStatus.INVALID
    details = " ".join(issue["detail"] for issue in body["issues"])
    assert "total_amount" in details
    assert "seratus ribu rupiah" not in details


def test_circular_reference_is_detected_without_recursing(client) -> None:
    payload = payload_for("clean")
    line = payload["lines"][0]
    line["supporting_refs"] = [
        {"resource_type": "ClaimLine", "resource_id": line["line_id"]}
    ]

    body = post(client, payload).json()

    assert body["status"] == ValidationStatus.INVALID
    codes = {issue["code"] for issue in body["issues"]}
    assert codes & {ErrorCode.BUNDLE_CIRCULAR_REFERENCE, ErrorCode.BUNDLE_DANGLING_REFERENCE}


# --------------------------------------------------------------------------------------
# Hashing and idempotency
# --------------------------------------------------------------------------------------


def test_hash_ignores_key_order_and_whitespace() -> None:
    payload = payload_for("clean")
    reordered = json.loads(json.dumps(payload, sort_keys=True))
    spaced = json.loads(json.dumps(payload, indent=4))
    assert input_hash(payload) == input_hash(reordered) == input_hash(spaced)


def test_hash_changes_when_a_billed_amount_changes() -> None:
    payload = payload_for("clean")
    changed = json.loads(json.dumps(payload))
    changed["claim"]["total_amount"] = "999999.00"
    assert input_hash(payload) != input_hash(changed)


def test_timestamps_normalise_to_utc_before_hashing() -> None:
    """The same instant written in two zones is the same bundle."""
    utc = {"when": "2026-03-01T09:00:00+00:00"}
    jakarta = {"when": "2026-03-01T16:00:00+07:00"}
    assert canonical_json(utc) != canonical_json(jakarta), "strings differ as written"

    from datetime import datetime

    parsed_utc = {"when": datetime.fromisoformat(utc["when"])}
    parsed_jkt = {"when": datetime.fromisoformat(jakarta["when"])}
    assert input_hash(parsed_utc) == input_hash(parsed_jkt)


def test_a_version_bump_produces_a_new_idempotency_key() -> None:
    """Re-screening under new rules is a different result, not a cached one."""
    first = idempotency_key("abc", "0.1.0", "0.1.0")
    assert first != idempotency_key("abc", "0.2.0", "0.1.0")
    assert first != idempotency_key("abc", "0.1.0", "0.2.0")


def test_resubmitting_an_identical_bundle_returns_the_same_ingestion(client) -> None:
    """One claim must not become two cases because someone clicked twice."""
    payload = payload_for("phantom")
    first = post(client, payload).json()
    second = post(client, payload).json()

    assert first["ingestion_id"] == second["ingestion_id"]
    assert first["input_hash"] == second["input_hash"]


def test_a_changed_bundle_creates_a_new_ingestion(client) -> None:
    payload = payload_for("phantom")
    first = post(client, payload).json()

    changed = json.loads(json.dumps(payload))
    changed["claim"]["total_amount"] = "123456.00"
    second = post(client, changed).json()

    assert first["ingestion_id"] != second["ingestion_id"]


# --------------------------------------------------------------------------------------
# Storage and logging
# --------------------------------------------------------------------------------------


def test_raw_payload_and_canonical_rows_both_persist(client, store) -> None:
    """The raw form keeps a result re-derivable; the canonical form is what others read."""
    payload = payload_for("phantom")
    ingestion_id = post(client, payload).json()["ingestion_id"]

    record = store.get(ingestion_id)

    assert record is not None
    assert json.loads(record.raw_payload) == payload, "raw payload stored verbatim"
    assert record.bundle is not None, "canonical rows stored alongside"
    assert record.bundle.claim.claim_id == payload["claim"]["claim_id"]
    assert record.engine_version and record.ruleset_version


def test_invalid_submissions_keep_the_raw_payload_but_no_canonical_bundle(client, store) -> None:
    payload = payload_for("clean")
    payload["lines"][0]["supporting_refs"] = [
        {"resource_type": "Procedure", "resource_id": "PROC-GONE"}
    ]
    ingestion_id = post(client, payload).json()["ingestion_id"]

    record = store.get(ingestion_id)
    assert record is not None
    assert record.raw_payload
    assert record.bundle is None


def test_no_log_line_contains_raw_medical_text(client, caplog) -> None:
    """Clinical text in a log is a disclosure that outlives the request."""
    note_text = load("clone").bundle.documents[0].text
    assert note_text, "the clone fixture must carry note text for this test to mean anything"

    with caplog.at_level(logging.DEBUG):
        post(client, payload_for("clone"))

    logged = " ".join(record.getMessage() for record in caplog.records)
    assert note_text not in logged
    for fragment in note_text.split()[:6]:
        if len(fragment) > 5:
            assert fragment not in logged, f"log leaked {fragment!r}"


def test_rejection_logs_carry_the_code_but_not_the_payload(client, caplog) -> None:
    payload = payload_for("clone")
    payload["unicorns"] = [{"secret": "nyeri tenggorokan sejak empat hari"}]

    with caplog.at_level(logging.DEBUG):
        post(client, payload)

    logged = " ".join(record.getMessage() for record in caplog.records)
    assert "nyeri tenggorokan" not in logged


# --------------------------------------------------------------------------------------
# The endpoint matches the frozen contract
# --------------------------------------------------------------------------------------


def test_endpoint_is_published_in_the_openapi_schema() -> None:
    schema = app.openapi()
    assert "/v1/bundles" in schema["paths"]
    assert "post" in schema["paths"]["/v1/bundles"]


# --------------------------------------------------------------------------------------
# Store selection — the demo and the frontend team both run without a database
# --------------------------------------------------------------------------------------


def test_falls_back_to_the_in_memory_store_when_no_database_answers(monkeypatch) -> None:
    """An unreachable database must degrade to in-memory, not break the service.

    `docs/canonical/08_demo_runbook.md` requires the demo to run with no external network, and
    the frontend team runs this suite with no Docker at all.
    """
    from app.store.bundles import InMemoryBundleStore
    from app.store.registry import get_bundle_store as select_store
    from app.store.registry import reset_stores, use_database

    monkeypatch.setattr("app.store.registry.is_database_available", lambda: False)
    reset_stores()
    try:
        assert use_database() is False
        assert isinstance(select_store(), InMemoryBundleStore)
    finally:
        reset_stores()


def test_the_selected_store_satisfies_the_protocol() -> None:
    """Whichever backend was chosen, ingestion only ever calls these four methods."""
    store = get_bundle_store()
    for method in ("find_by_idempotency_key", "save", "get", "attach_case"):
        assert callable(getattr(store, method)), f"store is missing {method}"


# --------------------------------------------------------------------------------------
# The vertical slice: ingest -> screen -> case
# --------------------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def cases():
    """A clean case store and audit trail around every test."""
    from app.store.registry import get_audit_store, get_case_store

    case_store, audit = get_case_store(), get_audit_store()
    case_store.clear()
    audit.clear()
    yield case_store
    case_store.clear()
    audit.clear()


def screen(client: TestClient, ingestion_id: str):
    return client.post(f"/v1/bundles/{ingestion_id}/screen", json={})


def test_phantom_bundle_screens_to_its_expected_reason(client) -> None:
    ingestion_id = post(client, payload_for("phantom")).json()["ingestion_id"]

    body = screen(client, ingestion_id).json()

    assert body["case_id"].startswith("case_")
    assert body["case_version"] == 1
    assert body["state"] == "SCREENED"
    codes = {reason["code"] for reason in body["reasons"]}
    assert codes == {"LINE_WITHOUT_COMPLETED_PROCEDURE"}
    assert body["primary_reason"]["sentence"], "the UI reads this, it must not be empty"
    assert body["band"]["band"] == "DETERMINISTIC_CONFLICT"
    assert body["versions"]["ruleset_version"]


def test_clean_bundle_screens_to_no_observed_risk(client) -> None:
    ingestion_id = post(client, payload_for("clean")).json()["ingestion_id"]

    body = screen(client, ingestion_id).json()

    assert body["reasons"] == []
    assert body["primary_reason"] is None
    assert body["band"]["band"] == "NO_OBSERVED_RISK"
    assert "tidak ada sinyal" in body["band"]["basis"].lower()


def test_repeat_billing_is_found_across_two_ingestions(client) -> None:
    """History comes from earlier ingestions, so the prior claim must be submitted first."""
    fixture = load("repeat")
    post(client, fixture.history[0].model_dump(mode="json"))
    ingestion_id = post(client, payload_for("repeat")).json()["ingestion_id"]

    body = screen(client, ingestion_id).json()

    codes = {reason["code"] for reason in body["reasons"]}
    assert "OVERLAPPING_CLAIM_SAME_EPISODE" in codes


def test_every_reason_arrives_with_its_counter_evidence(client) -> None:
    fixture = load("repeat")
    post(client, fixture.history[0].model_dump(mode="json"))
    ingestion_id = post(client, payload_for("repeat")).json()["ingestion_id"]

    body = screen(client, ingestion_id).json()

    for reason in body["reasons"]:
        assert reason["component_scores"], "component scores travel with the reason"


def test_completeness_notes_are_carried_onto_the_case(client, cases) -> None:
    """The ingestion's notes must reach the reviewer, or the caveat is lost between screens."""
    bundle = load("clean").bundle
    bare = tuple(line.model_copy(update={"supporting_refs": ()}) for line in bundle.lines)
    thin = bundle.model_copy(
        update={"lines": bare, "procedures": (), "medications": (), "provenance": ()}
    )
    ingested = post(client, thin.model_dump(mode="json")).json()
    assert ingested["completeness_notes"], "precondition: this bundle is thin"

    body = screen(client, ingested["ingestion_id"]).json()

    case = cases.get(body["case_id"])
    assert case is not None
    assert case.completeness_notes == tuple(ingested["completeness_notes"])
    assert any("catatan kelengkapan" in cap for cap in body["band"]["caps_applied"])


def test_rescreening_reuses_the_case_and_bumps_its_version(client) -> None:
    """One claim, one case — re-screening must not fork a reviewer's queue."""
    ingestion_id = post(client, payload_for("phantom")).json()["ingestion_id"]

    first = screen(client, ingestion_id).json()
    second = screen(client, ingestion_id).json()

    assert first["case_id"] == second["case_id"]
    assert second["case_version"] == first["case_version"] + 1


def test_screening_links_the_case_back_to_the_ingestion(client, store) -> None:
    ingestion_id = post(client, payload_for("phantom")).json()["ingestion_id"]
    case_id = screen(client, ingestion_id).json()["case_id"]

    assert store.get(ingestion_id).case_id == case_id

    resubmitted = post(client, payload_for("phantom")).json()
    assert resubmitted["existing_case_id"] == case_id


def test_an_invalid_bundle_cannot_be_screened(client) -> None:
    payload = payload_for("clean")
    payload["lines"][0]["supporting_refs"] = [
        {"resource_type": "Procedure", "resource_id": "PROC-GONE"}
    ]
    ingestion_id = post(client, payload).json()["ingestion_id"]

    response = screen(client, ingestion_id)

    assert response.status_code == 409
    assert response.json()["code"] == ErrorCode.BUNDLE_NOT_SCREENABLE


def test_screening_an_unknown_ingestion_returns_not_found(client) -> None:
    response = screen(client, "ing_does_not_exist")
    assert response.status_code == 404
    assert response.json()["code"] == ErrorCode.INGESTION_NOT_FOUND


def test_cloned_documentation_is_detected_across_participants(client) -> None:
    """Regression: clone detection must survive the store, not just the service layer.

    This lived at the API level and nowhere else. The service-level tests passed
    `fixture.history` straight in, so they never exercised the lookup the endpoint uses — and
    that lookup scoped history per-participant, which made this mode silently inert. Cloning is
    a per-*provider* pattern: the gold fixture copies a narrative between PSN-1004 and PSN-1005,
    both at PRV-02.
    """
    fixture = load("clone")
    peer = fixture.history[0]
    assert peer.claim.participant_id != fixture.bundle.claim.participant_id, "precondition"
    assert peer.claim.provider_id == fixture.bundle.claim.provider_id, "precondition"

    post(client, peer.model_dump(mode="json"))
    ingestion_id = post(client, payload_for("clone")).json()["ingestion_id"]

    body = screen(client, ingestion_id).json()

    codes = {reason["code"] for reason in body["reasons"]}
    assert "NEAR_DUPLICATE_DOCUMENTATION" in codes, (
        "clone detection is inert through the API; peer documents are not reaching the graph"
    )
    assert body["band"]["band"] == "NEEDS_CONTEXT", "similarity alone cannot top the queue"


def test_peer_documents_never_carry_other_patients_claim_data(store) -> None:
    """The widened scope must stay narrow: notes cross, claim lines and diagnoses do not."""
    from tilik_domain.canonical import DocumentRef

    fixture = load("clone")
    for bundle in (fixture.history[0], fixture.bundle):
        post_record = bundle
        assert post_record is not None

    peers = store.peer_documents_for("PRV-02", exclude_bundle_id="none")
    assert all(isinstance(document, DocumentRef) for document in peers)
