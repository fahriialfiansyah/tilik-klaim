"""`GET /v1/cases/{id}/briefing` — the bounded, read-only Case Briefing (ADR-0005).

Everything here is *about* evidence and never about priority: no band, no score, no state
transition. An observation without a source reference cannot be constructed, and a briefing with
more than five observations cannot be constructed — `05_model_card.md`'s five-sentence cap and
"reject output containing unsupported resource IDs" made into types.
"""
from __future__ import annotations

from enum import StrEnum

from pydantic import Field
from tilik_domain.reasons import ReasonCode

from app.dto.common import Dto, EvidenceRefDto, VersionStamp

MAX_OBSERVATIONS = 5
MAX_QUESTIONS = 3
MAX_STATEMENT_CHARS = 240


class ObservationKind(StrEnum):
    EVIDENCE_GAP = "EVIDENCE_GAP"
    CORROBORATION = "CORROBORATION"
    COUNTER_EVIDENCE = "COUNTER_EVIDENCE"
    COMPARISON = "COMPARISON"
    TIMELINE = "TIMELINE"
    COMPLETENESS = "COMPLETENESS"


class Confidence(StrEnum):
    """Never a number. A numeric confidence beside a risk band is a second score."""

    STATED = "STATED"
    INFERRED = "INFERRED"


class GeneratedBy(StrEnum):
    LLM = "LLM"
    TEMPLATE = "TEMPLATE"


class BriefingObservation(Dto):
    statement: str = Field(min_length=1, max_length=MAX_STATEMENT_CHARS)
    kind: ObservationKind
    source_refs: tuple[EvidenceRefDto, ...] = Field(min_length=1)
    reason_code: ReasonCode | None = None
    confidence: Confidence


class BriefingQuestion(Dto):
    question: str = Field(min_length=1, max_length=MAX_STATEMENT_CHARS)
    why_it_matters: str = Field(min_length=1, max_length=MAX_STATEMENT_CHARS)
    source_refs: tuple[EvidenceRefDto, ...] = Field(min_length=1)


class ToolCallRecord(Dto):
    """One function the briefing chose to read. The log *is* the transparency artifact."""

    tool: str
    arguments: dict[str, str] = Field(default_factory=dict)


class CaseBriefing(Dto):
    case_id: str
    case_version: int = Field(ge=1)
    observations: tuple[BriefingObservation, ...] = Field(max_length=MAX_OBSERVATIONS)
    open_questions: tuple[BriefingQuestion, ...] = Field(max_length=MAX_QUESTIONS)
    uncertainty_note: str = Field(min_length=1)
    generated_by: GeneratedBy
    model_id: str | None = None
    prompt_version: str
    validation_rejected: bool = False
    rejection_reason: str | None = None
    tool_calls: tuple[ToolCallRecord, ...] = ()
    versions: VersionStamp


# ---- Server-Sent Events -------------------------------------------------------------------


class BriefingPhase(StrEnum):
    STARTED = "STARTED"
    READING = "READING"
    VALIDATING = "VALIDATING"
    DONE = "DONE"


class StatusEvent(Dto):
    phase: BriefingPhase
    detail: str


class ToolEvent(Dto):
    tool: str
    arguments: dict[str, str] = Field(default_factory=dict)


class ObservationEvent(Dto):
    observation: BriefingObservation


class DoneEvent(Dto):
    briefing: CaseBriefing


class ErrorEvent(Dto):
    code: str
    detail: str


BriefingEvent = StatusEvent | ToolEvent | ObservationEvent | DoneEvent | ErrorEvent

EVENT_NAMES: dict[type, str] = {
    StatusEvent: "status",
    ToolEvent: "tool",
    ObservationEvent: "observation",
    DoneEvent: "done",
    ErrorEvent: "error",
}
