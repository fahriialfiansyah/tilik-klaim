"""`POST /v1/bundles` — accept, validate, and record one submission.

The route reads the request body as bytes rather than letting FastAPI bind a model, because the
size and depth guards have to run *before* anything parses the payload. A limit enforced after
parsing is not a limit.

Logging here is deliberately thin. `docs/canonical/07_privacy_threat_model.md` requires that no
raw medical text reaches a log line, so this module logs identifiers, counts, and codes — never
a document body, a diagnosis, or a validation error that echoes an offending value.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response
from tilik_domain.versioning import SCHEMA_VERSION

from app.config import get_settings
from app.dto.bundles import IngestBundleResponse, ValidationStatus
from app.errors import ErrorResponse
from app.service.hashing import idempotency_key, input_hash
from app.service.validation import (
    BundleRejected,
    guard_content_type,
    guard_size,
    parse_json,
    validate_bundle,
)
from app.store.bundles import (
    IngestionRecord,
    InMemoryBundleStore,
    new_ingestion_id,
    received_now,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["bundles"])

ERROR_RESPONSES: dict[int | str, dict] = {
    code: {"model": ErrorResponse} for code in (400, 409, 413, 415, 422)
}
"""Documented failure shapes, so a generated client handles them without guessing."""

STORE = InMemoryBundleStore()
"""Process-local store. Swapped for the database implementation when one is reachable."""


@router.post(
    "/bundles",
    response_model=IngestBundleResponse,
    responses=ERROR_RESPONSES,
    summary="Submit one synthetic bundle for validation",
)
async def ingest_bundle(request: Request) -> IngestBundleResponse | Response:
    """Validate a bundle and return counts, issues, and a deterministic input hash."""
    settings = get_settings()

    try:
        guard_content_type(request.headers.get("content-type"))
        raw = await request.body()
        guard_size(raw, settings.max_bundle_bytes)
        payload = parse_json(raw, settings.max_json_depth)
        outcome = validate_bundle(payload)
    except BundleRejected as rejected:
        logger.info(
            "bundle rejected before validation: code=%s issues=%d",
            rejected.code,
            len(rejected.issues),
        )
        envelope = ErrorResponse(
            code=rejected.code, detail=rejected.detail, issues=rejected.issues
        )
        return Response(
            content=envelope.model_dump_json(),
            status_code=envelope.http_status,
            media_type="application/json",
        )

    content_hash = input_hash(payload)
    key = idempotency_key(content_hash, settings.engine_version, settings.ruleset_version)

    existing = STORE.find_by_idempotency_key(key)
    if existing is not None:
        logger.info(
            "bundle already ingested: ingestion_id=%s status=%s",
            existing.ingestion_id,
            existing.status,
        )
        return _to_response(existing)

    record = IngestionRecord(
        ingestion_id=new_ingestion_id(),
        input_hash=content_hash,
        idempotency_key=key,
        status=outcome.status,
        raw_payload=raw.decode("utf-8", errors="replace"),
        bundle=outcome.bundle,
        issues=outcome.issues,
        completeness_notes=outcome.completeness_notes,
        resource_counts=outcome.resource_counts,
        engine_version=settings.engine_version,
        ruleset_version=settings.ruleset_version,
        received_at=received_now(),
    )
    STORE.save(record)

    logger.info(
        "bundle ingested: ingestion_id=%s status=%s resources=%d notes=%d",
        record.ingestion_id,
        record.status,
        sum(count.count for count in record.resource_counts),
        len(record.completeness_notes),
    )
    return _to_response(record)


def _to_response(record: IngestionRecord) -> IngestBundleResponse:
    return IngestBundleResponse(
        ingestion_id=record.ingestion_id,
        status=record.status,
        input_hash=record.input_hash,
        resource_counts=record.resource_counts,
        issues=record.issues,
        completeness_notes=record.completeness_notes,
        is_screenable=record.status is not ValidationStatus.INVALID,
        existing_case_id=record.case_id,
        schema_version=SCHEMA_VERSION,
    )
