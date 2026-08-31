"""`POST /v1/cases/{id}/dispositions` and `GET /v1/cases/{id}/audit`.

The actor's role arrives in a header. That is **role simulation for a prototype**, not
authentication — `docs/canonical/01_product_decision.md` puts enterprise IAM out of scope and the
demo has no login. It is named `X-Actor-Role` rather than dressed up as a token so nobody mistakes
it for a security control; a real deployment replaces it with the Bearer identity the
architecture already specifies.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response
from tilik_domain.reasons import CaseState

from app.dto.common import EvidenceRefDto, VersionStamp
from app.dto.dispositions import (
    AuditEvent,
    AuditResponse,
    DispositionRequest,
    DispositionResponse,
)
from app.errors import ErrorCode, ErrorResponse
from app.service.disposition import (
    DispositionRefused,
    apply_disposition,
    may_read_audit,
    open_for_review,
)
from app.store.audit import AuditEventRecord, AuditStore
from app.store.cases import CaseStore
from app.store.registry import get_audit_store, get_case_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["dispositions"])

ERROR_RESPONSES: dict[int | str, dict] = {
    code: {"model": ErrorResponse} for code in (403, 404, 409, 422)
}

DEFAULT_ROLE = "reviewer"


def case_store() -> CaseStore:
    return get_case_store()


def audit_store() -> AuditStore:
    return get_audit_store()


InjectedCases = Annotated[CaseStore, Depends(case_store)]
InjectedAudit = Annotated[AuditStore, Depends(audit_store)]
ActorRole = Annotated[str, Header(alias="X-Actor-Role")]


def _error(code: ErrorCode, detail: str) -> Response:
    envelope = ErrorResponse(code=code, detail=detail)
    return Response(
        content=envelope.model_dump_json(),
        status_code=envelope.http_status,
        media_type="application/json",
    )


@router.post(
    "/cases/{case_id}/dispositions",
    response_model=DispositionResponse,
    responses=ERROR_RESPONSES,
    summary="Record a human disposition",
)
def create_disposition(
    case_id: str,
    request: DispositionRequest,
    cases: InjectedCases,
    audit: InjectedAudit,
    x_actor_role: ActorRole = DEFAULT_ROLE,
) -> DispositionResponse | Response:
    """Record the reviewer's decision, or refuse and write nothing.

    Nothing this endpoint does rejects a claim, releases or stops a payment, imposes a sanction,
    or alters a code. It moves a case's state and appends an event, and that is the whole of it.
    """
    case = cases.get(case_id)
    if case is None:
        return _error(ErrorCode.CASE_NOT_FOUND, f"No case {case_id}")

    try:
        # A screened case has to be opened before it can be dispositioned; doing it here keeps
        # the reviewer from having to make two calls to record one decision.
        if case.state is CaseState.SCREENED:
            case = open_for_review(
                case, actor_role=x_actor_role, case_store=cases, audit_store=audit
            )
            if request.expected_case_version == case.case_version - 1:
                # The reviewer was looking at the screened version; opening it is our doing,
                # not a concurrent edit, so their version is still current.
                request = request.model_copy(
                    update={"expected_case_version": case.case_version}
                )

        outcome = apply_disposition(
            case,
            action=request.action,
            structured_reason=request.structured_reason,
            expected_case_version=request.expected_case_version,
            actor_role=x_actor_role,
            note=request.note,
            requested_evidence=request.requested_evidence,
            case_store=cases,
            audit_store=audit,
        )
    except DispositionRefused as refused:
        logger.info("disposition refused: case=%s code=%s", case_id, refused.code)
        return _error(refused.code, refused.detail)

    logger.info(
        "disposition recorded: case=%s action=%s state=%s version=%d",
        case_id,
        request.action,
        outcome.case.state,
        outcome.case.case_version,
    )
    return DispositionResponse(
        event_id=outcome.event.event_id,
        case_id=case_id,
        new_state=outcome.case.state,
        new_case_version=outcome.case.case_version,
        recorded_at=outcome.event.occurred_at,
    )


@router.get(
    "/cases/{case_id}/audit",
    response_model=AuditResponse,
    responses=ERROR_RESPONSES,
    summary="Case history",
)
def get_audit(
    case_id: str,
    cases: InjectedCases,
    audit: InjectedAudit,
    x_actor_role: ActorRole = DEFAULT_ROLE,
) -> AuditResponse | Response:
    """The full history. Restricted, because it names people and their decisions."""
    if not may_read_audit(x_actor_role):
        return _error(
            ErrorCode.AUDIT_FORBIDDEN,
            f"Role {x_actor_role!r} may not read case history.",
        )
    if cases.get(case_id) is None:
        return _error(ErrorCode.CASE_NOT_FOUND, f"No case {case_id}")

    return AuditResponse(
        case_id=case_id,
        events=tuple(_to_dto(event) for event in audit.for_case(case_id)),
    )


def _to_dto(event: AuditEventRecord) -> AuditEvent:
    return AuditEvent(
        event_id=event.event_id,
        case_id=event.case_id,
        event_kind=event.event_kind,
        actor_role=event.actor_role,
        action=event.action,
        structured_reason=event.structured_reason,
        note=event.note,
        evidence=tuple(
            EvidenceRefDto(
                resource_type=ref.resource_type,
                resource_id=ref.resource_id,
                label=f"{ref.resource_type} {ref.resource_id}",
            )
            for ref in event.evidence
        ),
        state_before=event.state_before,
        state_after=event.state_after,
        supersedes_event_id=event.supersedes_event_id,
        versions=VersionStamp(**event.identity.model_dump()),
        occurred_at=event.occurred_at,
    )
