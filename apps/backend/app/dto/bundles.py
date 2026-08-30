"""`POST /v1/bundles` and `POST /v1/bundles/{id}/screen`."""
from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from app.dto.common import BandExplanation, Dto, ReasonDto, VersionStamp
from app.errors import ValidationIssue


class ValidationStatus(StrEnum):
    """Three outcomes, not two.

    `VALID_WITH_NOTES` exists because an incomplete record and a billed-but-unevidenced
    service look identical at the schema level. Collapsing them into "valid" or "invalid" is
    how this system would produce false accusations, so the distinction is in the type.
    """

    VALID = "VALID"
    VALID_WITH_NOTES = "VALID_WITH_NOTES"
    INVALID = "INVALID"


class ResourceCount(Dto):
    resource_type: str
    count: int = Field(ge=0)


class IngestBundleResponse(Dto):
    """Result of submitting one bundle."""

    ingestion_id: str
    status: ValidationStatus
    input_hash: str = Field(description="SHA-256 of the canonical payload. Drives idempotency.")
    resource_counts: tuple[ResourceCount, ...]
    issues: tuple[ValidationIssue, ...] = ()
    completeness_notes: tuple[str, ...] = Field(
        default=(),
        description=(
            "Supporting resources absent from the submission. Travels with the case and "
            "lowers certainty downstream rather than raising a signal."
        ),
    )
    is_screenable: bool = Field(description="False when status is INVALID; the UI disables the button.")
    existing_case_id: str | None = Field(
        default=None,
        description="Set when this exact payload and engine version were already screened.",
    )
    schema_version: str


class ScreenRequest(Dto):
    """Screening carries no options.

    There is deliberately no detector, threshold, or mode selection — the ingest screen offers
    one button, and a configuration wizard would let a presenter tune their way to a result.
    """

    engine_version: str | None = Field(
        default=None, description="Pin a version for reproducibility. Defaults to current."
    )


class ScreenResponse(Dto):
    """Result of screening one ingested bundle."""

    case_id: str
    case_version: int = Field(ge=1, description="Required by the disposition endpoint.")
    state: str
    primary_reason: ReasonDto | None = Field(
        default=None, description="Strongest reason, opened first by the case detail screen."
    )
    reasons: tuple[ReasonDto, ...] = ()
    band: BandExplanation
    versions: VersionStamp
    latency_ms: int = Field(ge=0)
