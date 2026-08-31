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
from time import perf_counter
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from tilik_domain.canonical import ResourceRef
from tilik_domain.reasons import CaseState
from tilik_domain.versioning import SCHEMA_VERSION, EngineIdentity

from app.config import get_settings
from app.dto.bundles import (
    IngestBundleResponse,
    ScreenRequest,
    ScreenResponse,
    ValidationStatus,
)
from app.dto.common import BandExplanation, EvidenceRefDto, ReasonDto, VersionStamp
from app.errors import ErrorCode, ErrorResponse
from app.service.evidence_graph import build_evidence_graph
from app.service.hashing import idempotency_key, input_hash
from app.service.rules.registry import ReasonHit
from app.service.screening import Certainty, screen_bundle
from app.service.validation import (
    BundleRejected,
    guard_content_type,
    guard_size,
    parse_json,
    validate_bundle,
)
from app.store.audit import AuditEventRecord, new_event_id, occurred_now
from app.store.bundles import BundleStore, IngestionRecord, new_ingestion_id, received_now
from app.store.cases import CaseRecord, CaseStore, new_case_id, screened_now
from app.store.registry import get_audit_store, get_bundle_store, get_case_store, get_edge_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["bundles"])

ERROR_RESPONSES: dict[int | str, dict] = {
    code: {"model": ErrorResponse} for code in (400, 409, 413, 415, 422)
}
"""Documented failure shapes, so a generated client handles them without guessing."""

def bundle_store() -> BundleStore:
    """Injected so a test can substitute a store without reaching into module state."""
    return get_bundle_store()


InjectedStore = Annotated[BundleStore, Depends(bundle_store)]


@router.post(
    "/bundles",
    response_model=IngestBundleResponse,
    responses=ERROR_RESPONSES,
    summary="Submit one synthetic bundle for validation",
)
async def ingest_bundle(
    request: Request, store: InjectedStore
) -> IngestBundleResponse | Response:
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

    existing = store.find_by_idempotency_key(key)
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
    store.save(record)

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


def case_store() -> CaseStore:
    return get_case_store()


InjectedCases = Annotated[CaseStore, Depends(case_store)]


@router.post(
    "/bundles/{ingestion_id}/screen",
    response_model=ScreenResponse,
    responses=ERROR_RESPONSES,
    summary="Screen an ingested bundle",
)
def screen_ingested_bundle(
    ingestion_id: str,
    request: ScreenRequest,
    store: InjectedStore,
    cases: InjectedCases,
) -> ScreenResponse | Response:
    """Screen a validated bundle and return its reasons, band, and case.

    Idempotent for the same input hash and engine version: re-screening returns the existing
    case with its version bumped, rather than creating a second case for one claim.
    """
    record = store.get(ingestion_id)
    if record is None:
        return _error(ErrorCode.INGESTION_NOT_FOUND, f"No ingestion {ingestion_id}")

    if record.bundle is None or record.status is ValidationStatus.INVALID:
        return _error(
            ErrorCode.BUNDLE_NOT_SCREENABLE,
            "This bundle did not pass validation and cannot be screened",
        )

    started = perf_counter()
    history = store.history_for(
        record.bundle.claim.participant_id,
        record.bundle.claim.provider_id,
        exclude_bundle_id=record.bundle.bundle_id,
    )
    # Clone detection is a per-provider pattern, so it needs notes from other participants at
    # this provider. Only documents cross that boundary — never whole bundles.
    peer_documents = store.peer_documents_for(
        record.bundle.claim.provider_id, exclude_bundle_id=record.bundle.bundle_id
    )
    identity = EngineIdentity(
        engine_version=request.engine_version or record.engine_version,
        ruleset_version=record.ruleset_version,
    )
    result = screen_bundle(record.bundle, history, peer_documents, identity=identity)
    elapsed_ms = int((perf_counter() - started) * 1000)

    # Persist the derived graph so case detail can resolve every reason's evidence without
    # re-deriving it. Keyed by ruleset version, so re-screening replaces this slice and an
    # older version's edges stay resolvable for the audit events that cite them.
    graph = build_evidence_graph(
        record.bundle, history=history, peer_documents=peer_documents
    )
    get_edge_store().replace(record.bundle.bundle_id, record.ruleset_version, graph.edges)

    existing = cases.find_by_ingestion(ingestion_id)
    case = CaseRecord(
        case_id=existing.case_id if existing else new_case_id(),
        case_version=existing.case_version + 1 if existing else 1,
        ingestion_id=ingestion_id,
        state=CaseState.SCREENED,
        result=result,
        # The ingestion's notes travel with the case: they lower a reviewer's certainty about
        # what the record can support, and never raise a signal on their own.
        completeness_notes=record.completeness_notes,
        participant_token=record.bundle.claim.participant_id,
        provider_token=record.bundle.claim.provider_id,
        total_amount=record.bundle.claim.total_amount,
        currency=record.bundle.claim.currency,
        billed_line_count=len(record.bundle.lines),
        screened_at=screened_now(),
    )
    cases.save(case)
    # The screening itself is a history event: a reviewer opening the audit trail must be able
    # to see when the case was raised and under which engine version, not only what a human did.
    get_audit_store().append(
        AuditEventRecord(
            event_id=new_event_id(),
            case_id=case.case_id,
            event_kind="RESCREENED" if existing else "SCREENED",
            actor_role="system",
            state_after=CaseState.SCREENED,
            case_version_before=existing.case_version if existing else None,
            case_version_after=case.case_version,
            identity=result.identity,
            occurred_at=occurred_now(),
        )
    )
    store.attach_case(ingestion_id, case.case_id)

    logger.info(
        "bundle screened: case_id=%s version=%d band=%s reasons=%d latency_ms=%d",
        case.case_id,
        case.case_version,
        result.band,
        len(result.reasons),
        elapsed_ms,
    )
    return _to_screen_response(case, elapsed_ms)


def _error(code: ErrorCode, detail: str) -> Response:
    envelope = ErrorResponse(code=code, detail=detail)
    return Response(
        content=envelope.model_dump_json(),
        status_code=envelope.http_status,
        media_type="application/json",
    )


def _to_screen_response(case: CaseRecord, elapsed_ms: int) -> ScreenResponse:
    reasons = tuple(_to_reason_dto(hit) for hit in case.result.reasons)
    return ScreenResponse(
        case_id=case.case_id,
        case_version=case.case_version,
        state=str(case.state),
        primary_reason=reasons[0] if reasons else None,
        reasons=reasons,
        band=_to_band(case),
        versions=VersionStamp(**case.result.identity.model_dump()),
        latency_ms=elapsed_ms,
    )


def _to_reason_dto(hit: ReasonHit) -> ReasonDto:
    return ReasonDto(
        code=hit.code,
        mode=hit.mode,
        sentence=hit.sentence_id,
        deterministic=hit.deterministic,
        evidence=tuple(_to_ref(ref) for ref in hit.evidence),
        counter_evidence=tuple(
            _to_ref(ref) for note in hit.counter_evidence for ref in note.refs
        ),
        component_scores=dict(hit.component_scores),
        ruleset_version=hit.ruleset_version,
    )


def _to_ref(ref: ResourceRef) -> EvidenceRefDto:
    return EvidenceRefDto(
        resource_type=ref.resource_type,
        resource_id=ref.resource_id,
        label=f"{ref.resource_type} {ref.resource_id}",
    )


def _to_band(case: CaseRecord) -> BandExplanation:
    """Say how the band was reached, including any cap that held it down."""
    result = case.result
    caps: list[str] = []
    if result.reasons and all(not hit.deterministic for hit in result.reasons):
        caps.append(
            "Kemiripan teks saja tidak pernah mencapai pita tertinggi."
        )
    if result.certainty is Certainty.REDUCED_INCOMPLETE_BUNDLE:
        caps.append(
            "Bundel tidak lengkap menurunkan tingkat keyakinan dan mengarahkan ke "
            "permintaan bukti tambahan."
        )
    if case.completeness_notes:
        caps.append(
            f"{len(case.completeness_notes)} catatan kelengkapan terbawa dari pemasukan berkas."
        )

    basis = (
        "Tidak ada sinyal yang teramati pada versi mesin ini."
        if not result.reasons
        else f"{len(result.reasons)} alasan teramati; pita mengikuti alasan terkuat."
    )
    return BandExplanation(band=result.band, basis=basis, caps_applied=tuple(caps))
