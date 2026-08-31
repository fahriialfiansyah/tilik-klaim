"""Route declarations for the seven frozen endpoints.

The contract is frozen here; the behaviour arrives in later tasks. Each handler returns
`501 Not Implemented` naming the sprint task that fills it in, so the OpenAPI surface is
complete and honest at the same time — a client can generate against it today and will get an
unambiguous answer if it calls too early.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.dto.evaluations import EvaluationResponse
from app.errors import ErrorResponse

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


# `POST /bundles` is implemented in `app.router.bundles`; its placeholder was removed when
# sprint 02 / 01-bundle-ingestion landed. The remaining handlers below are still pending.


@router.get(
    "/evaluations/{run_id}",
    response_model=EvaluationResponse,
    responses=ERROR_RESPONSES,
    summary="Reproducible evaluation artifacts",
)
def get_evaluation(run_id: str) -> EvaluationResponse:
    """Reads generated artifacts. The synthetic label is displayed prominently."""
    raise _pending("sprint 06 / 01-evaluation-runner")
