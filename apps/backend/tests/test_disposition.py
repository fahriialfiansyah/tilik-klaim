"""Human dispositions and the audit trail.

These tests defend accountability, not correctness. A wrong band costs a reviewer time; a
decision recorded without a reason, silently overwritten, or quietly edited afterwards costs
someone the ability to answer for what was done.
"""
from __future__ import annotations

import pytest
from tilik_domain.reasons import CaseState, DispositionAction
from tilik_domain.versioning import EngineIdentity

from app.store.audit import AuditEventRecord, AuditWriteRefused
from app.store.registry import get_audit_store, get_case_store, use_database
from tests.fixtures import load

REVIEWER = {"X-Actor-Role": "reviewer"}
SENIOR = {"X-Actor-Role": "senior_reviewer"}


def screened_case(api, scenario: str = "phantom") -> dict:
    fixture = load(scenario)
    for prior in fixture.history:
        api.post("/v1/bundles", json=prior.model_dump(mode="json"))
    ingested = api.post("/v1/bundles", json=fixture.bundle.model_dump(mode="json")).json()
    return api.post(f"/v1/bundles/{ingested['ingestion_id']}/screen", json={}).json()


def disposition(action: str, version: int, reason: str = "Bukti sudah dilampirkan terpisah."):
    return {
        "action": action,
        "structured_reason": reason,
        "expected_case_version": version,
    }


# --------------------------------------------------------------------------------------
# The four actions
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("action", "expected_state"),
    [
        ("REJECT_SIGNAL", "DISMISSED"),
        ("REQUEST_EVIDENCE", "EVIDENCE_REQUESTED"),
        ("CONFIRM_ANOMALY", "CONFIRMED_ANOMALY"),
        ("ESCALATE", "ESCALATED"),
    ],
)
def test_each_action_moves_the_case_to_its_state(api, action: str, expected_state: str) -> None:
    case = screened_case(api)
    response = api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        json=disposition(action, case["case_version"]),
        headers=REVIEWER,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["new_state"] == expected_state
    assert body["new_case_version"] > case["case_version"]


def test_request_evidence_records_which_resources_were_asked_for(api) -> None:
    case = screened_case(api)
    payload = disposition("REQUEST_EVIDENCE", case["case_version"])
    payload["requested_evidence"] = ["Procedure", "Document"]

    api.post(f"/v1/cases/{case['case_id']}/dispositions", json=payload, headers=REVIEWER)

    events = api.get(f"/v1/cases/{case['case_id']}/audit", headers=REVIEWER).json()["events"]
    requested = [e for e in events if e["action"] == "REQUEST_EVIDENCE"]
    assert requested
    assert {ref["resource_type"] for ref in requested[0]["evidence"]} == {
        "Procedure",
        "Document",
    }


# --------------------------------------------------------------------------------------
# A reason is required, at the storage layer
# --------------------------------------------------------------------------------------


def test_a_disposition_without_a_reason_is_rejected(api) -> None:
    case = screened_case(api)
    response = api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        json={
            "action": "CONFIRM_ANOMALY",
            "structured_reason": "",
            "expected_case_version": case["case_version"],
        },
        headers=REVIEWER,
    )
    assert response.status_code == 422


def test_whitespace_is_not_a_reason(api) -> None:
    case = screened_case(api)
    response = api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        json=disposition("CONFIRM_ANOMALY", case["case_version"], reason="   "),
        headers=REVIEWER,
    )
    assert response.status_code == 422


def test_the_storage_layer_refuses_a_reasonless_disposition_even_bypassing_the_dto() -> None:
    """The UI and the DTO can both be bypassed by an internal caller. This cannot."""
    with pytest.raises(AuditWriteRefused, match="requires a structured reason"):
        AuditEventRecord(
            event_id="evt_x",
            case_id="case_x",
            event_kind="DISPOSITION",
            actor_role="reviewer",
            action=DispositionAction.CONFIRM_ANOMALY,
            structured_reason="  ",
            identity=EngineIdentity(),
            occurred_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        )


@pytest.mark.skipif(not use_database(), reason="needs Postgres for the check constraint")
def test_the_database_also_refuses_a_reasonless_disposition() -> None:
    """Three layers, because only the last one catches everything."""
    from datetime import UTC, datetime

    from sqlalchemy.exc import IntegrityError

    from app.store.engine import session_scope
    from app.store.tables import audit_events

    with pytest.raises(IntegrityError), session_scope() as session:
        session.execute(
            audit_events.insert().values(
                event_id="evt_no_reason",
                case_id="case_x",
                event_kind="DISPOSITION",
                actor_role="reviewer",
                action="CONFIRM_ANOMALY",
                structured_reason=None,
                evidence=[],
                schema_version="0.1.0",
                ruleset_version="0.1.0",
                engine_version="0.1.0",
                dataset_version="unset",
                occurred_at=datetime.now(UTC),
            )
        )


# --------------------------------------------------------------------------------------
# Optimistic locking
# --------------------------------------------------------------------------------------


def test_a_stale_version_is_rejected_and_writes_nothing(api) -> None:
    """Overwriting a colleague's recorded judgement unknowingly is the failure this prevents."""
    case = screened_case(api)
    case_id = case["case_id"]

    first = api.post(
        f"/v1/cases/{case_id}/dispositions",
        json=disposition("REQUEST_EVIDENCE", case["case_version"]),
        headers=REVIEWER,
    ).json()

    before = len(api.get(f"/v1/cases/{case_id}/audit", headers=REVIEWER).json()["events"])

    second = api.post(
        f"/v1/cases/{case_id}/dispositions",
        json=disposition("CONFIRM_ANOMALY", case["case_version"]),
        headers=REVIEWER,
    )

    assert second.status_code == 409
    assert second.json()["code"] == "CASE_VERSION_CONFLICT"

    after = len(api.get(f"/v1/cases/{case_id}/audit", headers=REVIEWER).json()["events"])
    assert after == before, "a refused disposition must write no event"

    state = api.get(f"/v1/cases/{case_id}").json()
    assert state["case_version"] == first["new_case_version"], "first decision preserved"


def test_the_conflict_message_names_what_changed(api) -> None:
    """A bare 409 tells a reviewer nothing about whether to change their mind."""
    case = screened_case(api)
    api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        json=disposition("REQUEST_EVIDENCE", case["case_version"]),
        headers=REVIEWER,
    )
    conflict = api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        json=disposition("CONFIRM_ANOMALY", case["case_version"]),
        headers=REVIEWER,
    ).json()

    detail = conflict["detail"]
    assert "EVIDENCE_REQUESTED" in detail, "the message must say what the case became"
    assert "not recorded" in detail.lower()


def test_concurrent_dispositions_keep_the_first(api) -> None:
    case = screened_case(api)
    version = case["case_version"]
    results = [
        api.post(
            f"/v1/cases/{case['case_id']}/dispositions",
            json=disposition(action, version),
            headers=REVIEWER,
        )
        for action in ("REJECT_SIGNAL", "CONFIRM_ANOMALY")
    ]
    assert [r.status_code for r in results] == [200, 409]


# --------------------------------------------------------------------------------------
# Append-only history
# --------------------------------------------------------------------------------------


def test_screening_and_disposition_both_appear_in_the_history(api) -> None:
    case = screened_case(api)
    api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        json=disposition("ESCALATE", case["case_version"]),
        headers=REVIEWER,
    )
    kinds = [
        e["event_kind"]
        for e in api.get(f"/v1/cases/{case['case_id']}/audit", headers=REVIEWER).json()["events"]
    ]
    assert "SCREENED" in kinds, "a reviewer must see when the case was raised"
    assert "DISPOSITION" in kinds


def test_a_correction_appends_and_links_instead_of_overwriting(api) -> None:
    """History is added to. The original decision, and whoever made it, stays visible."""
    case = screened_case(api)
    case_id = case["case_id"]
    audit = get_audit_store()
    cases = get_case_store()

    first = api.post(
        f"/v1/cases/{case_id}/dispositions",
        json=disposition("REJECT_SIGNAL", case["case_version"]),
        headers=REVIEWER,
    ).json()

    from app.service.disposition import apply_disposition, open_for_review

    reopened = open_for_review(
        cases.get(case_id), actor_role="senior_reviewer", case_store=cases, audit_store=audit
    )
    outcome = apply_disposition(
        reopened,
        action=DispositionAction.CONFIRM_ANOMALY,
        structured_reason="Peninjauan ulang menemukan ketidaksesuaian.",
        expected_case_version=reopened.case_version,
        actor_role="senior_reviewer",
        supersedes_event_id=first["event_id"],
        case_store=cases,
        audit_store=audit,
    )

    events = api.get(f"/v1/cases/{case_id}/audit", headers=SENIOR).json()["events"]
    ids = [e["event_id"] for e in events]
    assert first["event_id"] in ids, "the superseded decision must remain visible"
    assert outcome.event.event_id in ids
    superseding = next(e for e in events if e["event_id"] == outcome.event.event_id)
    assert superseding["supersedes_event_id"] == first["event_id"]


@pytest.mark.skipif(not use_database(), reason="needs Postgres for the append-only trigger")
def test_update_and_delete_against_the_audit_table_fail() -> None:
    """A convention is not a control. The database refuses both outright."""
    from datetime import UTC, datetime

    from sqlalchemy import text

    from app.store.engine import session_scope
    from app.store.tables import audit_events

    with session_scope() as session:
        session.execute(
            audit_events.insert().values(
                event_id="evt_immutable",
                case_id="case_x",
                event_kind="SCREENED",
                actor_role="system",
                evidence=[],
                schema_version="0.1.0",
                ruleset_version="0.1.0",
                engine_version="0.1.0",
                dataset_version="unset",
                occurred_at=datetime.now(UTC),
            )
        )

    for statement in (
        "update audit_events set note = 'tampered' where event_id = 'evt_immutable'",
        "delete from audit_events where event_id = 'evt_immutable'",
    ):
        with pytest.raises(Exception, match="append-only"), session_scope() as session:
            session.execute(text(statement))


def test_audit_read_is_restricted(api) -> None:
    """The trail names people and their decisions, so reading it is an access decision."""
    case = screened_case(api)
    forbidden = api.get(
        f"/v1/cases/{case['case_id']}/audit", headers={"X-Actor-Role": "analyst"}
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "AUDIT_FORBIDDEN"
    assert api.get(f"/v1/cases/{case['case_id']}/audit", headers=REVIEWER).status_code == 200


def test_every_audit_event_carries_its_engine_versions(api) -> None:
    """An event that cannot be tied to the rules that produced it is not auditable."""
    case = screened_case(api)
    api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        json=disposition("ESCALATE", case["case_version"]),
        headers=REVIEWER,
    )
    for event in api.get(f"/v1/cases/{case['case_id']}/audit", headers=REVIEWER).json()["events"]:
        assert event["versions"]["ruleset_version"]
        assert event["versions"]["engine_version"]
        assert event["actor_role"]


# --------------------------------------------------------------------------------------
# The state machine, and the actions this system will never take
# --------------------------------------------------------------------------------------


def test_an_escalated_case_accepts_no_further_transition(api) -> None:
    case = screened_case(api)
    api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        json=disposition("ESCALATE", case["case_version"]),
        headers=REVIEWER,
    )
    current = api.get(f"/v1/cases/{case['case_id']}").json()
    blocked = api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        json=disposition("REJECT_SIGNAL", current["case_version"]),
        headers=REVIEWER,
    )
    assert blocked.status_code == 409
    assert blocked.json()["code"] == "DISPOSITION_INVALID_TRANSITION"


def test_reopening_a_dismissed_case_needs_an_authorised_role(api) -> None:
    case = screened_case(api)
    api.post(
        f"/v1/cases/{case['case_id']}/dispositions",
        json=disposition("REJECT_SIGNAL", case["case_version"]),
        headers=REVIEWER,
    )
    cases, audit = get_case_store(), get_audit_store()
    dismissed = cases.get(case["case_id"])
    assert dismissed.state is CaseState.DISMISSED

    from app.service.disposition import DispositionRefused, open_for_review

    with pytest.raises(DispositionRefused, match="may not reopen"):
        open_for_review(dismissed, actor_role="reviewer", case_store=cases, audit_store=audit)

    # `auditor` was retired by ADR-0006 — its capability set was identical to this one's.
    reopened = open_for_review(
        dismissed, actor_role="senior_reviewer", case_store=cases, audit_store=audit
    )
    assert reopened.state is CaseState.IN_REVIEW

    events = audit.for_case(case["case_id"])
    assert any(e.state_after is CaseState.DISMISSED for e in events), "dismissal still visible"


def test_no_action_triggers_payment_rejection_or_sanction() -> None:
    """Out of scope by decision, and asserted so it stays that way.

    Reads the disposition service's own identifiers: a future field named `payment_status`, or a
    call to something that rejects a claim, is caught here rather than in review.

    Names are collected from the parsed syntax tree rather than by scanning the text, because the
    module's own docstring says these words in order to rule them out — a text search would flag
    the prohibition itself.
    """
    import ast
    from pathlib import Path

    source = Path(__file__).resolve().parents[1] / "app" / "service" / "disposition.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))

    identifiers: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            identifiers.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            identifiers.add(node.attr.lower())
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            identifiers.add(node.name.lower())
        elif isinstance(node, ast.arg):
            identifiers.add(node.arg.lower())

    forbidden = ("payment", "sanction", "penalty", "reject_claim", "deny", "tariff", "invoice")
    for name in sorted(identifiers):
        for word in forbidden:
            assert word not in name, (
                f"disposition service names {name!r}; this system never rejects a claim, "
                "moves a payment, or imposes a sanction"
            )
