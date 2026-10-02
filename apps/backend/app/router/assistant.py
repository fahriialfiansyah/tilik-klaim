"""`POST /v1/assistant/answers` — Asisten Bukti, the bounded evidence-cited assistant (ADR-0007).

Additive: the frozen seven, the briefing, and the user endpoints are untouched. This router is
the only place the feature touches a store, and it touches them exactly the way the queue and
case-detail endpoints do — `sort_cases` and `to_summary` build the snapshot, `load_case_detail`
builds every case read — so the assistant can only ever see what those endpoints already show
the same role. Nothing is written.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse
from tilik_domain.versioning import EngineIdentity

from app.config import Settings, get_settings
from app.dto.assistant import (
    EVENT_NAMES,
    AssistantAnswer,
    AssistantEvent,
    AssistantQuestion,
    ScopeKind,
)
from app.errors import ErrorCode, ErrorResponse
from app.router.cases import InjectedBundles, InjectedCases
from app.router.guards import DEFAULT_ROLE, ActorRole, error_response, refuse_without
from app.router.locale import RequestLocale
from app.service.access import Capability
from app.service.assistant.context import AssistantContext, QueueSnapshot
from app.service.assistant.service import answer_question, stream_answer
from app.service.case_loader import load_case_detail
from app.service.case_query import MAX_PAGE_SIZE, queue_metrics, sort_cases, to_summary

router = APIRouter(prefix="/v1", tags=["assistant"])

ERROR_RESPONSES: dict[int | str, dict] = {
    code: {"model": ErrorResponse} for code in (403, 404, 422)
}

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    # Proxies (nginx, and the Rsbuild dev proxy) buffer by default; this asks them not to.
    "X-Accel-Buffering": "no",
}


def _sse(events: Iterator[AssistantEvent]) -> Iterator[str]:
    for event in events:
        yield f"event: {EVENT_NAMES[type(event)]}\ndata: {event.model_dump_json()}\n\n"


@router.post(
    "/assistant/answers",
    response_model=AssistantAnswer,
    responses=ERROR_RESPONSES,
    summary="Ask the evidence assistant (non-authoritative, cited)",
)
def ask_assistant(
    body: AssistantQuestion,
    cases: InjectedCases,
    bundles: InjectedBundles,
    locale: RequestLocale,
    settings: Annotated[Settings, Depends(get_settings)],
    stream: bool = True,
    x_actor_role: ActorRole = DEFAULT_ROLE,
) -> AssistantAnswer | Response:
    """Statements about the queue or one case, each citing what it was read from.

    Never a score, a band of its own, a decision, or a state transition. Questions about fraud,
    payment, sanctions, diagnosis or identities are refused before any model is called. Off by
    default; the deterministic template answers when no model is configured.
    """
    refused = refuse_without(x_actor_role, Capability.ASK_ASSISTANT)
    if refused is not None:
        return refused

    # Bounded like the queue endpoint itself — the snapshot is never larger than one queue page.
    # The metrics, as on the queue, describe the whole queue rather than the bounded rows.
    everything = cases.list_all()
    ordered = sort_cases(everything)[:MAX_PAGE_SIZE]
    ctx = AssistantContext(
        snapshot=QueueSnapshot(
            rows=tuple(to_summary(case, locale) for case in ordered),
            metrics=queue_metrics(everything, EngineIdentity()),
            total=len(everything),
        ),
        load_case=lambda case_id: load_case_detail(case_id, cases, bundles, locale),
        locale=locale,
    )

    scoped = None
    if body.scope.kind is ScopeKind.CASE:
        scoped = ctx.load_case(str(body.scope.case_id))
        if scoped is None:
            return error_response(ErrorCode.CASE_NOT_FOUND, f"No case {body.scope.case_id}")

    if not stream:
        return answer_question(body, ctx, settings, scoped)
    return StreamingResponse(
        _sse(stream_answer(body, ctx, settings, scoped)),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
