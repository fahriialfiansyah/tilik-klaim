"""Sign-in, the roster, and the append-only trail of changes made to it.

None of this is authentication, and the tests are written so that reading them cannot leave
anyone thinking otherwise: the passcodes are constants printed on the login page, the header
that carries the role is forged freely, and nothing is issued on success. What *is* asserted is
that the refusals are real, that a change is always attributable, and that a response never
carries a passcode back.
"""
from __future__ import annotations

import pytest

from app.service.access import Role
from app.store.seed_users import SEEDED_STAFF

ADMIN_ROLE = "admin"
SARI_EMAIL = "sari.wulandari@rsud-demo.example"
SARI_PASSCODE = "demo-reviewer-2026"
RINA_ID = "usr_rina_hartati"


def admin_headers(staff) -> dict[str, str]:
    return {"X-Actor-Role": ADMIN_ROLE, "X-Actor-Id": staff[Role.ADMIN].user_id}


# --------------------------------------------------------------------------------------
# The roster itself
# --------------------------------------------------------------------------------------


def test_the_seeded_roster_is_exactly_three(api, staff) -> None:
    """Fixed at three by ADR-0006 § 7 — there is no create and no delete."""
    assert len(SEEDED_STAFF) == 3
    listed = api.get("/v1/users", headers=admin_headers(staff)).json()["users"]
    assert len(listed) == 3
    assert {user["role"] for user in listed} == {"reviewer", "senior_reviewer", "admin"}


def test_every_seeded_email_uses_the_reserved_example_tld(staff) -> None:
    """RFC 2606 `.example` can never resolve, the way the vLLM tests use `gateway.invalid`."""
    for _, _, _, email, _, _ in SEEDED_STAFF:
        assert email.endswith(".example"), email


def test_demo_reset_restores_a_roster_a_demo_toggled(api, staff) -> None:
    """A rehearsal that deactivated an account must not leave the next one locked out."""
    headers = admin_headers(staff)
    api.patch(f"/v1/users/{staff[Role.REVIEWER].user_id}", json={"is_active": False},
              headers=headers)

    import scripts.demo_reset as reset_script

    reset_script.reset()

    listed = api.get("/v1/users", headers=headers).json()["users"]
    assert len(listed) == 3
    assert all(user["is_active"] for user in listed)


# --------------------------------------------------------------------------------------
# Sign-in
# --------------------------------------------------------------------------------------


def test_a_valid_persona_can_be_selected(api, staff) -> None:
    response = api.post(
        "/v1/auth/session", json={"email": SARI_EMAIL, "passcode": SARI_PASSCODE}
    )
    assert response.status_code == 200
    user = response.json()["user"]
    assert user["staff_code"] == "PTG-01"
    assert user["role"] == "reviewer"


def test_a_wrong_passcode_is_refused_and_never_echoed(api, staff) -> None:
    """The attempted value must not come back — not because it is secret, but because a codebase
    that echoes one kind of credential will echo the next kind too."""
    attempted = "wrong-passcode-9999"
    response = api.post(
        "/v1/auth/session", json={"email": SARI_EMAIL, "passcode": attempted}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "SESSION_INVALID_CREDENTIALS"
    assert attempted not in response.text
    assert SARI_PASSCODE not in response.text


def test_an_unknown_email_answers_exactly_as_a_wrong_passcode_does(api, staff) -> None:
    """Telling the two apart would report which addresses exist, for no gain."""
    unknown = api.post(
        "/v1/auth/session", json={"email": "tidak.ada@rsud-demo.example", "passcode": "apa saja"}
    )
    wrong = api.post("/v1/auth/session", json={"email": SARI_EMAIL, "passcode": "salah"})
    assert unknown.status_code == wrong.status_code == 401
    assert unknown.json() == wrong.json()


def test_a_deactivated_account_cannot_start_a_session(api, staff) -> None:
    """Told apart from a wrong passcode on purpose: the credentials were right."""
    api.patch(
        f"/v1/users/{staff[Role.REVIEWER].user_id}",
        json={"is_active": False},
        headers=admin_headers(staff),
    )
    response = api.post(
        "/v1/auth/session", json={"email": SARI_EMAIL, "passcode": SARI_PASSCODE}
    )
    assert response.status_code == 403
    assert response.json()["code"] == "SESSION_ACCOUNT_DEACTIVATED"
    assert "PTG-01" in response.json()["detail"]


def test_no_response_anywhere_carries_a_passcode(api, staff) -> None:
    """`UserDto` has no such field; this asserts the property rather than trusting the shape."""
    session = api.post(
        "/v1/auth/session", json={"email": SARI_EMAIL, "passcode": SARI_PASSCODE}
    )
    listed = api.get("/v1/users", headers=admin_headers(staff))
    for _, _, _, _, _, passcode in SEEDED_STAFF:
        assert passcode not in session.text
        assert passcode not in listed.text


# --------------------------------------------------------------------------------------
# Who may manage users
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("role", ["reviewer", "senior_reviewer"])
def test_a_reviewing_role_may_not_read_or_change_the_roster(api, staff, role) -> None:
    headers = {"X-Actor-Role": role, "X-Actor-Id": staff[Role.REVIEWER].user_id}
    listed = api.get("/v1/users", headers=headers)
    assert listed.status_code == 403
    assert listed.json()["code"] == "USER_MANAGEMENT_FORBIDDEN"

    changed = api.patch(
        f"/v1/users/{staff[Role.REVIEWER].user_id}", json={"role": "admin"}, headers=headers
    )
    assert changed.status_code == 403
    assert changed.json()["code"] == "USER_MANAGEMENT_FORBIDDEN"

    audit = api.get("/v1/users/audit", headers=headers)
    assert audit.status_code == 403


def test_a_change_with_no_known_actor_is_refused(api, staff) -> None:
    """An audit event that names nobody is not an audit event."""
    response = api.patch(
        f"/v1/users/{staff[Role.REVIEWER].user_id}",
        json={"role": "senior_reviewer"},
        headers={"X-Actor-Role": ADMIN_ROLE},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "USER_MANAGEMENT_FORBIDDEN"


# --------------------------------------------------------------------------------------
# The changes themselves, and their trail
# --------------------------------------------------------------------------------------


def test_a_role_change_appends_an_event_with_actor_target_and_both_values(api, staff) -> None:
    headers = admin_headers(staff)
    target = staff[Role.REVIEWER]
    response = api.patch(
        f"/v1/users/{target.user_id}", json={"role": "senior_reviewer"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "senior_reviewer"

    events = api.get("/v1/users/audit", headers=headers).json()["events"]
    assert len(events) == 1
    event = events[0]
    assert event["event_kind"] == "USER_ROLE_CHANGED"
    assert event["actor_user_id"] == RINA_ID
    assert event["target_user_id"] == target.user_id
    assert event["value_before"] == "reviewer"
    assert event["value_after"] == "senior_reviewer"
    assert event["occurred_at"]


def test_deactivating_and_reactivating_each_append_their_own_kind(api, staff) -> None:
    headers = admin_headers(staff)
    target = staff[Role.SENIOR_REVIEWER]

    api.patch(f"/v1/users/{target.user_id}", json={"is_active": False}, headers=headers)
    api.patch(f"/v1/users/{target.user_id}", json={"is_active": True}, headers=headers)

    events = api.get("/v1/users/audit", headers=headers).json()["events"]
    # Newest first — the order the panel reads them in.
    assert [event["event_kind"] for event in events] == [
        "USER_REACTIVATED",
        "USER_DEACTIVATED",
    ]


def test_an_admin_may_not_change_their_own_role(api, staff) -> None:
    """Locking the only administrator out of the only administrative page is a defect."""
    headers = admin_headers(staff)
    response = api.patch(f"/v1/users/{RINA_ID}", json={"role": "reviewer"}, headers=headers)
    assert response.status_code == 409
    assert response.json()["code"] == "USER_SELF_MODIFICATION_REFUSED"
    assert api.get("/v1/users", headers=headers).status_code == 200


def test_an_admin_may_not_deactivate_themselves(api, staff) -> None:
    headers = admin_headers(staff)
    response = api.patch(f"/v1/users/{RINA_ID}", json={"is_active": False}, headers=headers)
    assert response.status_code == 409
    assert response.json()["code"] == "USER_SELF_MODIFICATION_REFUSED"


def test_a_refused_change_writes_no_event(api, staff) -> None:
    """Refuse and write nothing — the same guarantee a refused disposition gives."""
    headers = admin_headers(staff)
    api.patch(f"/v1/users/{RINA_ID}", json={"role": "reviewer"}, headers=headers)
    assert api.get("/v1/users/audit", headers=headers).json()["events"] == []


def test_an_unknown_target_is_not_found(api, staff) -> None:
    response = api.patch(
        "/v1/users/usr_nobody", json={"role": "reviewer"}, headers=admin_headers(staff)
    )
    assert response.status_code == 404
    assert response.json()["code"] == "USER_NOT_FOUND"


def test_setting_a_field_to_its_current_value_records_nothing(api, staff) -> None:
    """An event saying reviewer became reviewer is noise in a trail meant to be read."""
    headers = admin_headers(staff)
    response = api.patch(
        f"/v1/users/{staff[Role.REVIEWER].user_id}", json={"role": "reviewer"}, headers=headers
    )
    assert response.status_code == 422
    assert response.json()["code"] == "USER_NO_CHANGE_REQUESTED"
    assert api.get("/v1/users/audit", headers=headers).json()["events"] == []


def test_signing_in_records_the_time(api, staff) -> None:
    """The roster's `terakhir masuk` column, and the only thing a sign-in writes."""
    headers = admin_headers(staff)
    before = api.get("/v1/users", headers=headers).json()["users"]
    assert all(user["last_signed_in_at"] is None for user in before)

    api.post("/v1/auth/session", json={"email": SARI_EMAIL, "passcode": SARI_PASSCODE})

    after = api.get("/v1/users", headers=headers).json()["users"]
    sari = next(user for user in after if user["staff_code"] == "PTG-01")
    assert sari["last_signed_in_at"] is not None
