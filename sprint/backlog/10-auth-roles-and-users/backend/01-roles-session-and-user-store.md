# Task 01 — Role matrix, user store, session and user-management endpoints

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** yes — the frontend guard and menu read the same three role names.
**Autonomous:** yes — additive; no frozen contract moves.
**Depends on:**
- [`../../09-case-briefing/backend/01-briefing-service-and-endpoint.md`](../../09-case-briefing/backend/01-briefing-service-and-endpoint.md)

## Goal

Three roles defined once, enforced on every protected endpoint, and a fixed roster of three
synthetic staff that can be signed in as, promoted, and deactivated — with an append-only trail.

## Files to touch

- `app/service/access.py` — `Role`, `Capability`, the ADR-0006 § 2 matrix, stable codes
- `app/router/guards.py` — the two actor headers and one refusal helper, shared by five routers
- `app/service/disposition.py` — `AUDIT_READER_ROLES` / `REOPEN_ROLES` derived from the matrix
- `app/store/{tables,users,seed_users,registry}.py` — `users`, `user_audit_events`, both stores
- `app/service/users.py` — sign-in, role change, activate/deactivate, self-modification refusal
- `app/dto/users.py`, `app/router/users.py`, `app/main.py`, `app/errors.py`
- `migrations/versions/f2b8e91c60a7_users_and_user_audit_events.py`
- `app/service/demo_state.py`, `scripts/{seed_dev,demo_reset,export_access_matrix}.py`
- `docs/api/openapi.json` — regenerated

## TODOs

- [x] One role matrix; `disposition.py`'s two frozensets derived from it, not restated
- [x] `auditor` retired; the reopen test swaps it for `senior_reviewer` without weakening
- [x] Every protected endpoint consults `refuse_without`; five routers, one helper
- [x] `users` and append-only `user_audit_events`, sharing `tilik_audit_append_only()`
- [x] `demo_passcode` named for what it is, plain text, documented in column and docstring
- [x] `POST /v1/auth/session`, `GET /v1/users`, `GET /v1/users/audit`, `PATCH /v1/users/{id}`
- [x] Self-role-change and self-deactivation refused with `USER_SELF_MODIFICATION_REFUSED`
- [x] Seeded roster of three, `.example` TLD; `demo_reset.py` restores a toggled roster
- [x] Readiness reports `active_staff_count`; a demo that locked itself out says so
- [x] `scripts/export_access_matrix.py` + drift test — the login screen renders that matrix
- [x] 38 new tests (505 total); the frozen-path test now names paths rather than counting them
- [x] `docs/api/openapi.json` regenerated; alembic head `f2b8e91c60a7`; ruff clean

## Acceptance

Every row of the ADR-0006 § 2 matrix is exercised against the API with a forged header, in both
directions — permitted and refused — and a refusal carries the code the UI branches on.

## Notes

`X-Actor-Role` stays forgeable. That is stated in the router docstring, in `access.py`, and in
ADR-0006 § 4, and it is not a defect to be fixed here — production enforcement is a Bearer
identity checked before the role is trusted, and it is a documented future requirement.
