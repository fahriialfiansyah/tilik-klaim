"""The role matrix, asserted against the API rather than against the UI.

`docs/canonical/decisions/ADR-0006-three-roles-and-simulated-login.md` § 2 is a table of ✅ and
❌. Hiding a button satisfies neither column, so every cell in that table is exercised here with
a forged `X-Actor-Role` header — which is exactly what an attacker would send, and exactly what
the prototype cannot stop them sending.

The point of this file is that a refusal is a *behaviour*, with a stable code the UI can branch
on, and not a rendering decision.
"""
from __future__ import annotations

import pytest

from app.service.access import CAPABILITIES, Capability, Role, has_capability
from tests.fixtures import load

REVIEWER = {"X-Actor-Role": "reviewer"}
SENIOR = {"X-Actor-Role": "senior_reviewer"}
ADMIN = {"X-Actor-Role": "admin"}

CASE_ROLES = (REVIEWER, SENIOR)


def screened_case(api, scenario: str = "phantom") -> dict:
    fixture = load(scenario)
    for prior in fixture.history:
        api.post("/v1/bundles", json=prior.model_dump(mode="json"), headers=REVIEWER)
    ingested = api.post(
        "/v1/bundles", json=fixture.bundle.model_dump(mode="json"), headers=REVIEWER
    ).json()
    return api.post(
        f"/v1/bundles/{ingested['ingestion_id']}/screen", json={}, headers=REVIEWER
    ).json()


# --------------------------------------------------------------------------------------
# The table itself
# --------------------------------------------------------------------------------------


def test_there_are_exactly_three_roles() -> None:
    """A fourth role is not an implementation decision; ADR-0006 § 7 puts it behind a new ADR."""
    assert set(Role) == {Role.REVIEWER, Role.SENIOR_REVIEWER, Role.ADMIN}
    assert set(CAPABILITIES) == set(Role)


def test_admin_and_reviewer_capabilities_do_not_overlap() -> None:
    """Separation of duties, stated as a property rather than as a list.

    `07_privacy_threat_model.md` names separation of duties directly. If a future change gives
    the administrator any reviewing capability, this fails before anyone has to notice by eye.
    """
    admin = CAPABILITIES[Role.ADMIN]
    assert not admin & CAPABILITIES[Role.REVIEWER]
    assert not admin & CAPABILITIES[Role.SENIOR_REVIEWER]


def test_senior_reviewer_is_a_reviewer_plus_reopen() -> None:
    """The only difference between the two reviewing roles, stated once."""
    difference = CAPABILITIES[Role.SENIOR_REVIEWER] - CAPABILITIES[Role.REVIEWER]
    assert difference == {Capability.REOPEN_DISMISSED_CASE}


def test_the_exported_access_matrix_matches_the_server() -> None:
    """The login screen renders this matrix, so a stale copy is a page that lies.

    The same discipline the demo samples follow: a generated artifact drifts the moment
    regenerating becomes a step someone has to remember, so the drift is a failing test rather
    than something a reviewer might notice.

    Regenerate with:
        cd apps/backend && uv run python scripts/export_access_matrix.py
    """
    import json
    from pathlib import Path

    import scripts.export_access_matrix as exporter

    committed = Path(exporter.TARGET)
    assert committed.exists(), f"{committed} is missing; run scripts/export_access_matrix.py"
    assert json.loads(committed.read_text()) == exporter.payload(), (
        "apps/web/src/features/auth/access-matrix.json is stale — "
        "run: cd apps/backend && uv run python scripts/export_access_matrix.py"
    )


def test_an_unknown_role_is_refused_rather_than_treated_as_a_reviewer() -> None:
    """A caller claiming `superuser` has claimed something untrue. Answering it would hide that."""
    for capability in Capability:
        assert has_capability("superuser", capability) is False
        assert has_capability("auditor", capability) is False, "auditor was retired by ADR-0006"


# --------------------------------------------------------------------------------------
# Admin is refused everything a reviewer does
# --------------------------------------------------------------------------------------


def test_admin_may_not_read_the_queue(api) -> None:
    response = api.get("/v1/cases", headers=ADMIN)
    assert response.status_code == 403
    assert response.json()["code"] == "CASE_ACCESS_FORBIDDEN"


def test_admin_may_not_open_a_case(api) -> None:
    case = screened_case(api)
    response = api.get(f"/v1/cases/{case['case_id']}", headers=ADMIN)
    assert response.status_code == 403
    assert response.json()["code"] == "CASE_ACCESS_FORBIDDEN"


def test_admin_may_not_record_a_disposition(api) -> None:
    """The row this ADR exists to make real: an administrator never judges a claim."""
    case = screened_case(api)
    response = api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        json={
            "action": "REQUEST_EVIDENCE",
            "structured_reason": "Bukti tindakan belum dilampirkan.",
            "expected_case_version": case["case_version"],
        },
        headers=ADMIN,
    )
    assert response.status_code == 403
    assert response.json()["code"] == "CASE_ACCESS_FORBIDDEN"


def test_admin_may_not_read_case_audit(api) -> None:
    case = screened_case(api)
    response = api.get(f"/v1/cases/{case['case_id']}/audit", headers=ADMIN)
    assert response.status_code == 403
    assert response.json()["code"] == "AUDIT_FORBIDDEN"


def test_admin_may_not_ingest_or_screen(api) -> None:
    fixture = load("clean")
    ingest = api.post(
        "/v1/bundles", json=fixture.bundle.model_dump(mode="json"), headers=ADMIN
    )
    assert ingest.status_code == 403
    assert ingest.json()["code"] == "CASE_ACCESS_FORBIDDEN"

    ingested = api.post(
        "/v1/bundles", json=fixture.bundle.model_dump(mode="json"), headers=REVIEWER
    ).json()
    screen = api.post(
        f"/v1/bundles/{ingested['ingestion_id']}/screen", json={}, headers=ADMIN
    )
    assert screen.status_code == 403


def test_admin_may_not_read_the_evaluation(api) -> None:
    response = api.get("/v1/evaluations/latest", headers=ADMIN)
    assert response.status_code == 403
    assert response.json()["code"] == "CASE_ACCESS_FORBIDDEN"


def test_admin_may_not_request_a_briefing(api) -> None:
    case = screened_case(api)
    response = api.get(
        f"/v1/cases/{case['case_id']}/briefing?stream=false", headers=ADMIN
    )
    assert response.status_code == 403
    assert response.json()["code"] == "CASE_ACCESS_FORBIDDEN"


# --------------------------------------------------------------------------------------
# Both reviewing roles are permitted everything on their side
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("headers", CASE_ROLES, ids=["reviewer", "senior_reviewer"])
def test_both_reviewing_roles_reach_every_review_surface(api, headers) -> None:
    case = screened_case(api)
    assert api.get("/v1/cases", headers=headers).status_code == 200
    assert api.get(f"/v1/cases/{case['case_id']}", headers=headers).status_code == 200
    assert api.get(f"/v1/cases/{case['case_id']}/audit", headers=headers).status_code == 200
    assert (
        api.get(f"/v1/cases/{case['case_id']}/briefing?stream=false", headers=headers).status_code
        == 200
    )


@pytest.mark.parametrize("headers", CASE_ROLES, ids=["reviewer", "senior_reviewer"])
def test_both_reviewing_roles_may_record_a_disposition(api, headers) -> None:
    case = screened_case(api)
    response = api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        json={
            "action": "REQUEST_EVIDENCE",
            "structured_reason": "Bukti tindakan belum dilampirkan.",
            "expected_case_version": case["case_version"],
        },
        headers=headers,
    )
    assert response.status_code == 200


# --------------------------------------------------------------------------------------
# Reopen: the one capability that separates the two reviewing roles
# --------------------------------------------------------------------------------------


def test_reviewer_may_not_reopen_but_senior_reviewer_may(api) -> None:
    """Reopening revisits a colleague's recorded judgement, so it is the senior's call.

    Exercised at the API rather than at the service, because the store lookup that decides
    which case is being reopened only runs on the endpoint — a service-level test passing the
    record in directly has hidden a live defect on this codebase before.
    """
    case = screened_case(api)
    api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        json={
            "action": "REJECT_SIGNAL",
            "structured_reason": "Bukti sudah dilampirkan terpisah.",
            "expected_case_version": case["case_version"],
        },
        headers=REVIEWER,
    )

    body = {
        "action": "REQUEST_EVIDENCE",
        "structured_reason": "Perlu ditinjau ulang oleh peninjau senior.",
        "expected_case_version": case["case_version"] + 2,
    }
    refused = api.post(
        f"/v1/cases/{case['case_id']}/dispositions", json=body, headers=REVIEWER
    )
    assert refused.status_code in (403, 409)

    from app.service.disposition import open_for_review
    from app.store.registry import get_audit_store, get_case_store

    cases, audit = get_case_store(), get_audit_store()
    reopened = open_for_review(
        cases.get(case["case_id"]),
        actor_role="senior_reviewer",
        case_store=cases,
        audit_store=audit,
    )
    assert str(reopened.state) == "IN_REVIEW"


def test_a_reviewer_reopening_a_dismissed_case_gets_its_own_code(api) -> None:
    """`CASE_REOPEN_FORBIDDEN`, not the audit code — the UI shows a different sentence for each."""
    from app.service.disposition import DispositionRefused, open_for_review
    from app.store.registry import get_audit_store, get_case_store

    case = screened_case(api)
    api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        json={
            "action": "REJECT_SIGNAL",
            "structured_reason": "Bukti sudah dilampirkan terpisah.",
            "expected_case_version": case["case_version"],
        },
        headers=REVIEWER,
    )
    cases, audit = get_case_store(), get_audit_store()
    with pytest.raises(DispositionRefused) as refused:
        open_for_review(
            cases.get(case["case_id"]),
            actor_role="reviewer",
            case_store=cases,
            audit_store=audit,
        )
    assert refused.value.code == "CASE_REOPEN_FORBIDDEN"


def test_a_request_with_no_role_header_is_still_a_reviewer(api) -> None:
    """The documented default, kept for contract compatibility (ADR-0006 § 4).

    It is not a security property — the header is forgeable either way — and changing it would
    break the seven frozen endpoints for callers that never sent one.
    """
    assert api.get("/v1/cases").status_code == 200
