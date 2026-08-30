"""Route declarations for the seven frozen endpoints.

The contract is frozen here; the behaviour arrives in later tasks. Each handler returns
`501 Not Implemented` naming the sprint task that fills it in, so the OpenAPI surface is
complete and honest at the same time — a client can generate against it today and will get an
unambiguous answer if it calls too early.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.dto.bundles import IngestBundleResponse, ScreenRequest, ScreenResponse
from app.dto.cases import CaseDetailResponse, CaseQueueResponse
from app.dto.dispositions import AuditResponse, DispositionRequest, DispositionResponse
from app.dto.evaluations import EvaluationResponse
from app.errors import ErrorResponse
from tilik_domain.reasons import CaseState, PriorityBand, RiskMode

router = APIRouter(prefix="/v1")

ERROR_RESPONSES: dict[int | str, dict] = {
    400: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    409: {"model": ErrorResponse},
    413: {"model": ErrorResponse},
    415: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
}


def _pending(task: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"Contract frozen; implementation lands in {task}.",
    )


@router.post(
    "/bundles",
    response_model=IngestBundleResponse,
    responses=ERROR_RESPONSES,
    summary="Submit one synthetic bundle for validation",
)
def ingest_bundle() -> IngestBundleResponse:
    """Validate a bundle and return counts, issues, and a deterministic input hash.

    The optional demo scenario label never enters detector features.
    """
    raise _pending("sprint 02 / 01-bundle-ingestion")


@router.post(
    "/bundles/{ingestion_id}/screen",
    response_model=ScreenResponse,
    responses=ERROR_RESPONSES,
    summary="Screen an ingested bundle",
)
def screen_bundle(ingestion_id: str, request: ScreenRequest) -> ScreenResponse:
    """Idempotent for the same input hash and engine version."""
    raise _pending("sprint 03 / 02-rule-engine")


@router.get(
    "/cases",
    response_model=CaseQueueResponse,
    responses=ERROR_RESPONSES,
    summary="Paginated review queue",
)
def list_cases(
    state: CaseState | None = None,
    mode: RiskMode | None = None,
    band: PriorityBand | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
) -> CaseQueueResponse:
    """Pseudonymous fields only. Never returns raw medical text."""
    raise _pending("sprint 04 / 01-case-endpoints")


@router.get(
    "/cases/{case_id}",
    response_model=CaseDetailResponse,
    responses=ERROR_RESPONSES,
    summary="One case with evidence, counter-evidence, and timeline",
)
def get_case(case_id: str) -> CaseDetailResponse:
    raise _pending("sprint 04 / 01-case-endpoints")


@router.post(
    "/cases/{case_id}/dispositions",
    response_model=DispositionResponse,
    responses=ERROR_RESPONSES,
    status_code=status.HTTP_201_CREATED,
    summary="Record a human disposition",
)
def create_disposition(case_id: str, request: DispositionRequest) -> DispositionResponse:
    """Optimistic locking on `expected_case_version`; a reason is required.

    No disposition triggers claim rejection, payment action, sanction, or code change.
    """
    raise _pending("sprint 04 / 02-disposition-audit")


@router.get(
    "/cases/{case_id}/audit",
    response_model=AuditResponse,
    responses=ERROR_RESPONSES,
    summary="Append-only case history",
)
def get_audit(case_id: str) -> AuditResponse:
    """Authorized role only. Corrections append a superseding event; nothing is overwritten."""
    raise _pending("sprint 04 / 02-disposition-audit")


@router.get(
    "/evaluations/{run_id}",
    response_model=EvaluationResponse,
    responses=ERROR_RESPONSES,
    summary="Reproducible evaluation artifacts",
)
def get_evaluation(run_id: str) -> EvaluationResponse:
    """Reads generated artifacts. The synthetic label is displayed prominently."""
    raise _pending("sprint 06 / 01-evaluation-runner")
