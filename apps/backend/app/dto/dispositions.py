"""`POST /v1/cases/{id}/dispositions` and `GET /v1/cases/{id}/audit`."""
from __future__ import annotations

from datetime import datetime

from pydantic import Field, field_validator
from tilik_domain.canonical import ResourceType
from tilik_domain.reasons import CaseState, DispositionAction

from app.dto.common import Dto, EvidenceRefDto, VersionStamp


class DispositionRequest(Dto):
    """A human decision. Never accepted without a reason.

    `expected_case_version` is the optimistic lock. Overwriting a colleague's recorded
    decision without knowing is an accountability failure, not a concurrency inconvenience —
    so the version is required, not optional.
    """

    action: DispositionAction
    structured_reason: str = Field(min_length=1, description="Chosen from the action's reason list.")
    note: str | None = Field(default=None, description="Optional free-text elaboration.")
    expected_case_version: int = Field(ge=1)
    requested_evidence: tuple[ResourceType, ...] = Field(
        default=(),
        description="For REQUEST_EVIDENCE: resource types being asked for. Editable by the reviewer.",
    )

    @field_validator("structured_reason")
    @classmethod
    def reason_must_not_be_blank(cls, value: str) -> str:
        """Whitespace is not a reason.

        Enforced here *and* at the storage layer — the UI can be bypassed, so a check that
        lives only in the client is not a guarantee.
        """
        if not value.strip():
            raise ValueError("structured_reason must not be blank")
        return value


class DispositionResponse(Dto):
    """The immutable event that was written, and the case's new state."""

    event_id: str
    case_id: str
    new_state: CaseState
    new_case_version: int = Field(ge=1)
    recorded_at: datetime


class AuditEvent(Dto):
    """One entry in the case history. Append-only; never edited in place."""

    event_id: str
    case_id: str
    event_kind: str = Field(description="CREATED | SCREENED | DISPOSITION | RESCREENED | SUPERSEDE")
    actor_role: str
    action: DispositionAction | None = None
    structured_reason: str | None = None
    note: str | None = None
    evidence: tuple[EvidenceRefDto, ...] = ()
    state_before: CaseState | None = None
    state_after: CaseState | None = None
    supersedes_event_id: str | None = Field(
        default=None,
        description=(
            "Set on a correction. The superseded event stays visible; history is appended to, "
            "never rewritten."
        ),
    )
    versions: VersionStamp
    occurred_at: datetime


class AuditResponse(Dto):
    """Ordered history for one case. Readable only by an authorized role."""

    case_id: str
    events: tuple[AuditEvent, ...]
