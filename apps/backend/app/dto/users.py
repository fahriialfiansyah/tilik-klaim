"""`POST /v1/auth/session`, `GET /v1/users`, and `PATCH /v1/users/{id}`.

**No response model here carries `demo_passcode`.** The login page prints the three demo
passcodes from its own constant, so the API never has to hand one back — and a sign-in that was
refused must not echo the value that was tried, which `test_users_endpoints.py` asserts.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.dto.common import Dto
from app.service.access import Role


class SessionRequest(Dto):
    """Credential-shaped, and checked — but this selects a persona, it does not authenticate.

    See `docs/canonical/decisions/ADR-0006-three-roles-and-simulated-login.md` § 3. Nothing is
    issued on success: there is no token, no cookie, and no server-side session to invalidate.
    """

    email: str = Field(min_length=3, max_length=254)
    passcode: str = Field(min_length=1, max_length=64)


class UserDto(Dto):
    """One account as the UI sees it. Never carries the passcode."""

    user_id: str
    staff_code: str
    full_name: str
    email: str
    role: Role
    is_active: bool
    last_signed_in_at: datetime | None = None


class SessionResponse(Dto):
    """The selected persona. The client stores this and sends the two actor headers from it."""

    user: UserDto


class UserListResponse(Dto):
    users: tuple[UserDto, ...]


class UserUpdateRequest(Dto):
    """A role change, an active-flag change, or both. Omitted fields are left alone.

    `None` means *not requested* rather than *set to null* — there is no nullable field here to
    confuse it with, and sending neither is refused rather than treated as a successful no-op.
    """

    role: Role | None = None
    is_active: bool | None = None


class UserAuditEventDto(Dto):
    """One recorded change. Append-only: there is no endpoint that edits or removes one."""

    event_id: str
    event_kind: str
    actor_user_id: str
    actor_role: str
    target_user_id: str
    field: str
    value_before: str | None = None
    value_after: str | None = None
    occurred_at: datetime


class UserAuditResponse(Dto):
    events: tuple[UserAuditEventDto, ...]


class UserUpdateResponse(Dto):
    user: UserDto
    events: tuple[UserAuditEventDto, ...]
