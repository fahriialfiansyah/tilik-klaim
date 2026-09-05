"""`POST /v1/auth/session`, `GET /v1/users`, `PATCH /v1/users/{id}` — additive to the eight.

The seven frozen endpoints and the briefing endpoint are untouched; these three sit beside them.

**The two actor headers are forgeable, and nothing here pretends otherwise.** `X-Actor-Role` and
`X-Actor-Id` are what the caller *claims*, and anyone with `curl` can claim anything. What this
router does is refuse what ADR-0006 § 2 says the claimed role may not do, and record the claim
against every change. What it does not do is verify the claim. Production enforcement — a Bearer
identity checked before the role is trusted — is a stated future requirement, not a shipped
feature, and `03_architecture.md` § Security already requires this sentence to exist somewhere a
person changing the code will read it.

The names and emails here are staff, not participants. `07_privacy_threat_model.md`'s
pseudonymity rule is about the people in the claims; these three accounts are synthetic
operators of the prototype, and their addresses use the reserved `.example` TLD so none can
resolve.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response

from app.dto.users import (
    SessionRequest,
    SessionResponse,
    UserAuditEventDto,
    UserAuditResponse,
    UserDto,
    UserListResponse,
    UserUpdateRequest,
    UserUpdateResponse,
)
from app.errors import ErrorCode, ErrorResponse
from app.service.access import (
    CODE_FOR_CAPABILITY,
    Capability,
    has_capability,
    refusal_detail,
)
from app.service.users import UserActionRefused, start_session, update_user
from app.store.registry import get_user_store
from app.store.users import UserAuditRecord, UserRecord, UserStore

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["users"])

ERROR_RESPONSES: dict[int | str, dict] = {
    code: {"model": ErrorResponse} for code in (401, 403, 404, 409, 422)
}

DEFAULT_ROLE = "reviewer"
"""Unchanged from the disposition router, and for the same reason.

Existing callers send no role header at all, and the frozen endpoints' documented behaviour
depends on this default. It is a compatibility choice, not a security one — the header is
forgeable either way (ADR-0006 § 4).
"""


def user_store() -> UserStore:
    return get_user_store()


InjectedUsers = Annotated[UserStore, Depends(user_store)]
ActorRole = Annotated[str, Header(alias="X-Actor-Role")]
ActorId = Annotated[str | None, Header(alias="X-Actor-Id")]


def _error(code: ErrorCode, detail: str) -> Response:
    envelope = ErrorResponse(code=code, detail=detail)
    return Response(
        content=envelope.model_dump_json(),
        status_code=envelope.http_status,
        media_type="application/json",
    )


def _forbid(role: str, capability: Capability) -> Response:
    return _error(CODE_FOR_CAPABILITY[capability], refusal_detail(role, capability))


@router.post(
    "/auth/session",
    response_model=SessionResponse,
    responses=ERROR_RESPONSES,
    summary="Select a persona (simulated sign-in)",
)
def create_session(request: SessionRequest, users: InjectedUsers) -> SessionResponse | Response:
    """Check the demo credentials and return the account, or refuse and say which way it failed.

    Nothing is issued: no token, no cookie, no server-side session. The client keeps the returned
    account and sends the two actor headers from it. See ADR-0006 § 3.
    """
    try:
        user = start_session(request.email, request.passcode, store=users)
    except UserActionRefused as refused:
        # The attempted passcode is never logged and never echoed — not because it is a secret
        # (it is printed on the page), but because a codebase that logs one kind of credential
        # is a codebase that will log the next kind too.
        logger.info("session refused: code=%s", refused.code)
        return _error(refused.code, refused.detail)

    logger.info("session started: user=%s role=%s", user.staff_code, user.role)
    return SessionResponse(user=_to_dto(user))


@router.get(
    "/users",
    response_model=UserListResponse,
    responses=ERROR_RESPONSES,
    summary="The synthetic staff roster",
)
def list_users(
    users: InjectedUsers, x_actor_role: ActorRole = DEFAULT_ROLE
) -> UserListResponse | Response:
    """Admin only. A reviewer has no business reading who else may review."""
    if not has_capability(x_actor_role, Capability.MANAGE_USERS):
        return _forbid(x_actor_role, Capability.MANAGE_USERS)
    return UserListResponse(users=tuple(_to_dto(user) for user in users.list_all()))


@router.get(
    "/users/audit",
    response_model=UserAuditResponse,
    responses=ERROR_RESPONSES,
    summary="User-management history",
)
def get_user_audit(
    users: InjectedUsers, x_actor_role: ActorRole = DEFAULT_ROLE
) -> UserAuditResponse | Response:
    """Newest first. Append-only — there is no endpoint that edits or removes an entry."""
    if not has_capability(x_actor_role, Capability.READ_USER_AUDIT):
        return _forbid(x_actor_role, Capability.READ_USER_AUDIT)
    return UserAuditResponse(events=tuple(_event_dto(item) for item in users.events()))


@router.patch(
    "/users/{user_id}",
    response_model=UserUpdateResponse,
    responses=ERROR_RESPONSES,
    summary="Change a role, or activate/deactivate an account",
)
def patch_user(
    user_id: str,
    request: UserUpdateRequest,
    users: InjectedUsers,
    x_actor_role: ActorRole = DEFAULT_ROLE,
    x_actor_id: ActorId = None,
) -> UserUpdateResponse | Response:
    """Apply the change and append one event per field, or refuse and write nothing."""
    if not has_capability(x_actor_role, Capability.MANAGE_USERS):
        return _forbid(x_actor_role, Capability.MANAGE_USERS)

    actor = users.get(x_actor_id) if x_actor_id else None
    if actor is None:
        # An unattributable change is worse than a refused one: the audit event would name
        # nobody, and a trail that cannot say who acted is not a trail.
        return _error(
            ErrorCode.USER_MANAGEMENT_FORBIDDEN,
            "Header X-Actor-Id harus menyebut akun yang dikenal; perubahan tanpa pelaku ditolak.",
        )

    try:
        outcome = update_user(
            user_id,
            role=request.role,
            is_active=request.is_active,
            actor=actor,
            store=users,
        )
    except UserActionRefused as refused:
        logger.info("user update refused: target=%s code=%s", user_id, refused.code)
        return _error(refused.code, refused.detail)

    logger.info(
        "user updated: target=%s actor=%s events=%d",
        user_id,
        actor.staff_code,
        len(outcome.events),
    )
    return UserUpdateResponse(
        user=_to_dto(outcome.user),
        events=tuple(_event_dto(event) for event in outcome.events),
    )


def _to_dto(user: UserRecord) -> UserDto:
    return UserDto(
        user_id=user.user_id,
        staff_code=user.staff_code,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        last_signed_in_at=user.last_signed_in_at,
    )


def _event_dto(event: UserAuditRecord) -> UserAuditEventDto:
    return UserAuditEventDto(**event.model_dump())
