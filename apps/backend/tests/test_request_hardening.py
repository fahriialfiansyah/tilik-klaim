"""Bounded input, and the response headers a browser needs to treat this as a JSON API.

Found by probing: a 20 MB `note` passed schema validation (it was refused only because the case
was in the wrong state), and would have been written to the append-only audit log on a valid
transition — where nothing may delete it. No route limited its body except ingestion.
"""
from __future__ import annotations

import json

import pytest
from tilik_domain.canonical import ResourceType

from app.config import get_settings
from app.dto.dispositions import NOTE_MAX_CHARS, REASON_MAX_CHARS
from tests.fixtures import load

REVIEWER = {"X-Actor-Role": "reviewer"}
JSON_HEADERS = {**REVIEWER, "Content-Type": "application/json"}
REASON = "Catatan tindakan belum terkirim"


def screened_case(api) -> dict:
    fixture = load("phantom")
    for prior in fixture.history:
        api.post("/v1/bundles", json=prior.model_dump(mode="json"))
    ingested = api.post("/v1/bundles", json=fixture.bundle.model_dump(mode="json")).json()
    return api.post(f"/v1/bundles/{ingested['ingestion_id']}/screen", json={}).json()


def disposition(case: dict, **overrides) -> dict:
    return {
        "action": "REQUEST_EVIDENCE",
        "structured_reason": REASON,
        "expected_case_version": case["case_version"],
        **overrides,
    }


def post_disposition(api, case: dict, payload: dict):
    return api.post(f"/v1/cases/{case['case_id']}/dispositions", json=payload, headers=REVIEWER)


def audit_count(api, case: dict) -> int:
    return len(api.get(f"/v1/cases/{case['case_id']}/audit", headers=REVIEWER).json()["events"])


# --------------------------------------------------------------------------------------
# Field limits
# --------------------------------------------------------------------------------------


def test_a_note_at_the_limit_is_accepted(api) -> None:
    case = screened_case(api)
    response = post_disposition(api, case, disposition(case, note="A" * NOTE_MAX_CHARS))
    assert response.status_code == 200, response.text


def test_a_note_over_the_limit_is_refused_and_writes_nothing(api) -> None:
    case = screened_case(api)
    events_before = audit_count(api, case)

    response = post_disposition(api, case, disposition(case, note="A" * (NOTE_MAX_CHARS + 1)))

    assert response.status_code == 422
    assert audit_count(api, case) == events_before
    shown = api.get(f"/v1/cases/{case['case_id']}", headers=REVIEWER).json()
    assert shown["state"] == "SCREENED"


def test_an_overlong_reason_is_refused(api) -> None:
    case = screened_case(api)
    response = post_disposition(
        api, case, disposition(case, structured_reason="x" * (REASON_MAX_CHARS + 1))
    )
    assert response.status_code == 422


def test_more_requested_resources_than_there_are_types_is_refused(api) -> None:
    case = screened_case(api)
    too_many = ["Procedure"] * (len(ResourceType) + 1)
    response = post_disposition(api, case, disposition(case, requested_evidence=too_many))
    assert response.status_code == 422


# --------------------------------------------------------------------------------------
# Body size
# --------------------------------------------------------------------------------------


def oversized_disposition(case: dict) -> bytes:
    pad = "A" * (get_settings().max_request_bytes + 1)
    return json.dumps(disposition(case, note=pad)).encode()


def test_an_oversized_body_is_refused_with_its_own_stable_code(api) -> None:
    case = screened_case(api)

    response = api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        content=oversized_disposition(case),
        headers=JSON_HEADERS,
    )

    assert response.status_code == 413
    assert response.json()["code"] == "REQUEST_TOO_LARGE"


def test_an_oversized_body_with_no_declared_length_is_refused_too(api) -> None:
    """Chunked uploads declare no length, so counting the header alone would not stop them."""
    case = screened_case(api)
    payload = oversized_disposition(case)

    def chunks():
        for start in range(0, len(payload), 16 * 1024):
            yield payload[start : start + 16 * 1024]

    response = api.post(
        f"/v1/cases/{case['case_id']}/dispositions", content=chunks(), headers=JSON_HEADERS
    )

    assert response.status_code == 413, response.text
    assert response.json()["code"] == "REQUEST_TOO_LARGE"


def test_a_small_chunked_body_still_works(api) -> None:
    case = screened_case(api)
    payload = json.dumps(disposition(case)).encode()

    response = api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        content=(payload[i : i + 8] for i in range(0, len(payload), 8)),
        headers=JSON_HEADERS,
    )

    assert response.status_code == 200, response.text


def test_ingestion_keeps_its_own_limit_and_its_own_code(api) -> None:
    """A body over the general limit but under the bundle limit is ingestion's to judge."""
    padded = json.dumps({"pad": "A" * (get_settings().max_request_bytes + 1)})

    response = api.post("/v1/bundles", content=padded, headers=JSON_HEADERS)

    assert response.json()["code"] != "REQUEST_TOO_LARGE"
    assert response.status_code == 422


def test_reads_are_never_limited(api) -> None:
    assert api.get("/v1/cases", headers=REVIEWER).status_code == 200


# --------------------------------------------------------------------------------------
# Response headers
# --------------------------------------------------------------------------------------


def test_api_responses_carry_the_baseline_security_headers(api) -> None:
    headers = api.get("/v1/cases", headers=REVIEWER).headers

    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "no-referrer"
    assert "default-src 'none'" in headers["content-security-policy"]
    assert headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    ("path", "role", "status"),
    [("/v1/cases", "admin", 403), ("/v1/cases/case_missing", "reviewer", 404)],
)
def test_refusals_carry_the_headers_too(api, path: str, role: str, status: int) -> None:
    response = api.get(path, headers={"X-Actor-Role": role})

    assert response.status_code == status
    assert response.headers["x-content-type-options"] == "nosniff"


def test_a_body_limit_refusal_carries_the_headers_too(api) -> None:
    case = screened_case(api)
    response = api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        content=oversized_disposition(case),
        headers=JSON_HEADERS,
    )

    assert response.status_code == 413
    assert response.headers["x-content-type-options"] == "nosniff"


def test_the_health_probe_is_not_marked_uncacheable_like_case_data(api) -> None:
    response = api.get("/healthz")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert "cache-control" not in response.headers


def test_the_documentation_page_is_not_blanked_by_the_api_policy(api) -> None:
    response = api.get("/docs")

    assert response.status_code == 200
    assert "content-security-policy" not in response.headers
    assert response.headers["x-content-type-options"] == "nosniff"
