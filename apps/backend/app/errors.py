"""Stable error catalog.

Every distinct failure has one code, and that code never changes meaning. The UI branches on
these codes and the tests assert them, so renaming one is a breaking change — treat it like
a schema migration, not a rename.

WS-002 acceptance requires that malformed, oversized, and dangling-reference bundles each
return their *own* stable code. "Invalid bundle" tells an operator nothing actionable; it is
the difference between a report they can fix and one they can only resubmit and hope.
"""
from __future__ import annotations

from enum import StrEnum
from http import HTTPStatus

from pydantic import BaseModel, ConfigDict, Field


class ErrorCode(StrEnum):
    """Stable identifiers. Append new members; never repurpose an existing one."""

    # Ingestion — rejected before parsing
    BUNDLE_TOO_LARGE = "BUNDLE_TOO_LARGE"
    BUNDLE_UNSUPPORTED_CONTENT_TYPE = "BUNDLE_UNSUPPORTED_CONTENT_TYPE"
    BUNDLE_DEPTH_EXCEEDED = "BUNDLE_DEPTH_EXCEEDED"

    # Ingestion — rejected during parsing or validation
    BUNDLE_MALFORMED_JSON = "BUNDLE_MALFORMED_JSON"
    BUNDLE_SCHEMA_INVALID = "BUNDLE_SCHEMA_INVALID"
    BUNDLE_UNKNOWN_RESOURCE_TYPE = "BUNDLE_UNKNOWN_RESOURCE_TYPE"
    BUNDLE_DANGLING_REFERENCE = "BUNDLE_DANGLING_REFERENCE"
    BUNDLE_CIRCULAR_REFERENCE = "BUNDLE_CIRCULAR_REFERENCE"
    BUNDLE_DUPLICATE_RESOURCE_ID = "BUNDLE_DUPLICATE_RESOURCE_ID"
    BUNDLE_TOTAL_MISMATCH = "BUNDLE_TOTAL_MISMATCH"

    # Lookup
    INGESTION_NOT_FOUND = "INGESTION_NOT_FOUND"
    CASE_NOT_FOUND = "CASE_NOT_FOUND"
    EVALUATION_RUN_NOT_FOUND = "EVALUATION_RUN_NOT_FOUND"

    # Screening
    BUNDLE_NOT_SCREENABLE = "BUNDLE_NOT_SCREENABLE"

    # Disposition
    DISPOSITION_REASON_REQUIRED = "DISPOSITION_REASON_REQUIRED"
    CASE_VERSION_CONFLICT = "CASE_VERSION_CONFLICT"
    DISPOSITION_INVALID_TRANSITION = "DISPOSITION_INVALID_TRANSITION"

    # Access
    AUDIT_FORBIDDEN = "AUDIT_FORBIDDEN"

    # Briefing — a genuinely broken service, never "disabled" (disabled is the template, a 200)
    BRIEFING_UNAVAILABLE = "BRIEFING_UNAVAILABLE"


STATUS_FOR_CODE: dict[ErrorCode, HTTPStatus] = {
    ErrorCode.BUNDLE_TOO_LARGE: HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
    ErrorCode.BUNDLE_UNSUPPORTED_CONTENT_TYPE: HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
    ErrorCode.BUNDLE_DEPTH_EXCEEDED: HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
    ErrorCode.BUNDLE_MALFORMED_JSON: HTTPStatus.BAD_REQUEST,
    ErrorCode.BUNDLE_SCHEMA_INVALID: HTTPStatus.UNPROCESSABLE_ENTITY,
    ErrorCode.BUNDLE_UNKNOWN_RESOURCE_TYPE: HTTPStatus.UNPROCESSABLE_ENTITY,
    ErrorCode.BUNDLE_DANGLING_REFERENCE: HTTPStatus.UNPROCESSABLE_ENTITY,
    ErrorCode.BUNDLE_CIRCULAR_REFERENCE: HTTPStatus.UNPROCESSABLE_ENTITY,
    ErrorCode.BUNDLE_DUPLICATE_RESOURCE_ID: HTTPStatus.UNPROCESSABLE_ENTITY,
    ErrorCode.BUNDLE_TOTAL_MISMATCH: HTTPStatus.UNPROCESSABLE_ENTITY,
    ErrorCode.INGESTION_NOT_FOUND: HTTPStatus.NOT_FOUND,
    ErrorCode.CASE_NOT_FOUND: HTTPStatus.NOT_FOUND,
    ErrorCode.EVALUATION_RUN_NOT_FOUND: HTTPStatus.NOT_FOUND,
    ErrorCode.BUNDLE_NOT_SCREENABLE: HTTPStatus.CONFLICT,
    ErrorCode.DISPOSITION_REASON_REQUIRED: HTTPStatus.UNPROCESSABLE_ENTITY,
    ErrorCode.CASE_VERSION_CONFLICT: HTTPStatus.CONFLICT,
    ErrorCode.DISPOSITION_INVALID_TRANSITION: HTTPStatus.CONFLICT,
    ErrorCode.AUDIT_FORBIDDEN: HTTPStatus.FORBIDDEN,
    ErrorCode.BRIEFING_UNAVAILABLE: HTTPStatus.SERVICE_UNAVAILABLE,
}


class ValidationIssue(BaseModel):
    """One problem found in a submitted bundle, pointed at a specific resource.

    `resource_type` and `resource_id` are what make the ingest screen's error list
    actionable — the operator learns *which* resource to fix, not merely that something is
    wrong somewhere.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: ErrorCode
    resource_type: str | None = None
    resource_id: str | None = None
    detail: str = Field(description="Human-readable explanation. Never contains medical text.")


class ErrorResponse(BaseModel):
    """The single error envelope for every endpoint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: ErrorCode
    detail: str
    issues: tuple[ValidationIssue, ...] = ()

    @property
    def http_status(self) -> HTTPStatus:
        return STATUS_FOR_CODE[self.code]
