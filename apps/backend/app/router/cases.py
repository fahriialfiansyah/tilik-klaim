"""`GET /v1/cases` and `GET /v1/cases/{id}` — the queue and the case detail.

Both read from the stored screening result rather than re-screening. A case explained under a
newer ruleset than the one that raised it would answer a different question than the reviewer is
looking at, and the audit event citing it would no longer match.
"""
from __future__ import annotations

import logging
from datetime import datetime
from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from tilik_domain.reasons import CaseState, PriorityBand, ReasonCode, RiskMode
from tilik_domain.versioning import EngineIdentity

from app.dto.cases import CaseDetailResponse, CaseQueueResponse
from app.errors import ErrorCode, ErrorResponse
from app.service.case_query import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    SortKey,
    filter_cases,
    paginate,
    queue_metrics,
    sort_cases,
    to_detail,
    to_summary,
)
from app.store.bundles import BundleStore
from app.store.cases import CaseStore
from app.store.registry import get_bundle_store, get_case_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["cases"])


class SortOrder(StrEnum):
    """Direction for the sortable queue columns. Ignored by the band sort — see `sort_cases`."""

    ASC = "asc"
    DESC = "desc"

ERROR_RESPONSES: dict[int | str, dict] = {
    code: {"model": ErrorResponse} for code in (400, 403, 404, 409, 422)
}


def case_store() -> CaseStore:
    return get_case_store()


def bundle_store() -> BundleStore:
    return get_bundle_store()


InjectedCases = Annotated[CaseStore, Depends(case_store)]
InjectedBundles = Annotated[BundleStore, Depends(bundle_store)]


@router.get(
    "/cases",
    response_model=CaseQueueResponse,
    responses=ERROR_RESPONSES,
    summary="Review queue",
)
def list_cases(
    cases: InjectedCases,
    state: CaseState | None = None,
    band: PriorityBand | None = None,
    reason: ReasonCode | None = None,
    mode: RiskMode | None = None,
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    search: str | None = Query(default=None, max_length=128),
    sort: SortKey = SortKey.BAND,
    order: SortOrder = SortOrder.DESC,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
) -> CaseQueueResponse:
    """The ordered work list. Pseudonymous fields only; no narrative text."""
    everything = cases.list_all()
    matching = sort_cases(
        filter_cases(
            everything,
            state=state,
            band=band,
            reason=reason,
            mode=mode,
            created_after=created_after,
            created_before=created_before,
            search=search,
        ),
        key=sort,
        descending=order is SortOrder.DESC,
    )
    window, page_info = paginate(matching, page, page_size)

    return CaseQueueResponse(
        # Metrics describe the whole queue, not the current page — a reviewer needs to know how
        # much work exists, not how much fits on one screen.
        metrics=queue_metrics(everything, EngineIdentity()),
        items=tuple(to_summary(case) for case in window),
        page=page_info,
    )


@router.get(
    "/cases/{case_id}",
    response_model=CaseDetailResponse,
    responses=ERROR_RESPONSES,
    summary="Case detail",
)
def get_case(
    case_id: str, cases: InjectedCases, bundles: InjectedBundles
) -> CaseDetailResponse | Response:
    """Claim lines, reasons with evidence and counter-evidence, timeline, and comparisons."""
    case = cases.get(case_id)
    if case is None:
        envelope = ErrorResponse(code=ErrorCode.CASE_NOT_FOUND, detail=f"No case {case_id}")
        return Response(
            content=envelope.model_dump_json(),
            status_code=envelope.http_status,
            media_type="application/json",
        )

    ingestion = bundles.get(case.ingestion_id)
    if ingestion is None or ingestion.bundle is None:
        return to_detail(case, ingestion)

    # The other submissions the rules compared this one against. Without them a reference to a
    # prior claim or a peer note resolves to nothing, and the screen would report a genuine
    # comparison as an evidence-integrity defect.
    claim = ingestion.bundle.claim
    history = bundles.history_for(
        claim.participant_id, claim.provider_id, exclude_bundle_id=ingestion.bundle.bundle_id
    )
    peer_documents = bundles.peer_documents_for(
        claim.provider_id, exclude_bundle_id=ingestion.bundle.bundle_id
    )
    return to_detail(case, ingestion, history, peer_documents, bundles.case_id_for_bundle)
