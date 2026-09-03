"""`GET /v1/cases/{case_id}/briefing` — the bounded, read-only Case Briefing (ADR-0005).

Additive: the seven frozen endpoints are untouched. Streams Server-Sent Events by default; with
`?stream=false` returns the same `CaseBriefing` as one JSON object. Reads the case exactly as
`GET /v1/cases/{id}` does — `load_case_detail` — and writes nothing.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse

from app.config import Settings, get_settings
from app.dto.briefing import EVENT_NAMES, BriefingEvent, CaseBriefing
from app.errors import ErrorCode, ErrorResponse
from app.router.cases import InjectedBundles, InjectedCases
from app.service.briefing.service import build_briefing, stream_briefing
from app.service.case_loader import load_case_detail

router = APIRouter(prefix="/v1", tags=["briefing"])

ERROR_RESPONSES: dict[int | str, dict] = {404: {"model": ErrorResponse}}

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    # Proxies (nginx, and the Rsbuild dev proxy) buffer by default; this asks them not to.
    "X-Accel-Buffering": "no",
}


def _sse(events: Iterator[BriefingEvent]) -> Iterator[str]:
    for event in events:
        yield f"event: {EVENT_NAMES[type(event)]}\ndata: {event.model_dump_json()}\n\n"


@router.get(
    "/cases/{case_id}/briefing",
    response_model=CaseBriefing,
    responses=ERROR_RESPONSES,
    summary="Read-only case briefing (non-authoritative)",
)
def get_briefing(
    case_id: str,
    cases: InjectedCases,
    bundles: InjectedBundles,
    settings: Annotated[Settings, Depends(get_settings)],
    stream: bool = True,
) -> CaseBriefing | Response:
    """Observations with source references, open questions, and an uncertainty note.

    Never a score, a band, or a state transition. Off by default; the deterministic template is
    the answer when no model is configured.
    """
    detail = load_case_detail(case_id, cases, bundles)
    if detail is None:
        envelope = ErrorResponse(code=ErrorCode.CASE_NOT_FOUND, detail=f"No case {case_id}")
        return Response(
            content=envelope.model_dump_json(),
            status_code=envelope.http_status,
            media_type="application/json",
        )
    if not stream:
        return build_briefing(detail, settings)
    return StreamingResponse(
        _sse(stream_briefing(detail, settings)), media_type="text/event-stream", headers=SSE_HEADERS
    )
