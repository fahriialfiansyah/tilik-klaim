"""`GET /v1/evaluations/{run_id}` — read one completed evaluation run.

The endpoint serves artifacts and computes nothing. Metrics are produced offline by
`evaluation/runner`, deliberately by an engineer against the frozen test partition; a metric
that could be produced by an HTTP request would be a metric produced more than once, and the
number in the proposal would stop being the number anyone can rebuild.

`run_id` accepts the reserved value `latest`, which resolves to the most recent complete run.
That keeps the frozen contract intact — it is a path *value*, not a new endpoint — and lets the
page open without first being told an id.
"""
from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.config import Settings, get_settings
from app.dto.evaluations import EvaluationResponse
from app.errors import ErrorCode, ErrorResponse
from app.service.evaluation_artifacts import (
    EvaluationRunNotFound,
    artifacts_root,
    read_run,
    resolve_run,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["evaluations"])

ERROR_RESPONSES: dict[int | str, dict] = {404: {"model": ErrorResponse}}


@router.get(
    "/evaluations/{run_id}",
    response_model=EvaluationResponse,
    responses=ERROR_RESPONSES,
    summary="Reproducible evaluation artifacts",
)
def get_evaluation(
    run_id: str, settings: Annotated[Settings, Depends(get_settings)]
) -> EvaluationResponse | Response:
    """Read one run. The synthetic label travels with the payload, never as UI decoration."""
    root = artifacts_root(settings.evaluation_artifacts_dir)
    try:
        return read_run(resolve_run(root, run_id))
    except EvaluationRunNotFound as absent:
        return _not_found(str(absent))
    except (OSError, ValueError, KeyError) as unreadable:
        # A partially written or hand-edited run directory is a missing run, not a broken
        # service: the honest answer is "no result to show", with the command that makes one.
        logger.warning("evaluation run %s is unreadable: %s", run_id, unreadable)
        return _not_found(
            f"evaluation run {run_id!r} could not be read; re-run the offline evaluation"
        )


def _not_found(detail: str) -> Response:
    """No run is a state the page renders, not a service failure — hence a plain 404."""
    envelope = ErrorResponse(code=ErrorCode.EVALUATION_RUN_NOT_FOUND, detail=detail)
    return Response(
        content=envelope.model_dump_json(),
        status_code=envelope.http_status,
        media_type="application/json",
    )
