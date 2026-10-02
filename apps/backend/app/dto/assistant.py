"""`POST /v1/assistant/answers` — Asisten Bukti, the bounded evidence-cited assistant (ADR-0007).

Everything here is *about* what the reviewer can already see and never a judgement on it. A
statement without a citation cannot be constructed, an answer with more than five statements
cannot be constructed, and nothing on these models can carry a score or a state transition —
ADR-0007 § 4's gate made into types, the same way `briefing.py` made ADR-0005's.

The priority band appears on a case card only because the queue row it is copied from carries
it, verbatim. The assistant never computes, re-orders, or argues for one.
"""
from __future__ import annotations

from enum import StrEnum

from pydantic import Field, field_validator, model_validator
from tilik_domain.canonical import ResourceType

from app.dto.briefing import (
    BriefingPhase,
    ErrorEvent,
    GeneratedBy,
    StatusEvent,
    ToolCallRecord,
    ToolEvent,
)
from app.dto.cases import CaseSummary
from app.dto.common import Dto, VersionStamp

MAX_QUESTION_CHARS = 500
MAX_HISTORY_TURNS = 3
MAX_HISTORY_ANSWER_CHARS = 1500
MAX_STATEMENTS = 5
MAX_STATEMENT_CHARS = 280
MAX_CITATIONS_PER_STATEMENT = 6
MAX_CASE_CARDS = 5


class ScopeKind(StrEnum):
    """What one turn may read. Chosen by the reviewer and always shown on screen."""

    QUEUE = "QUEUE"
    CASE = "CASE"


class AssistantScope(Dto):
    kind: ScopeKind = ScopeKind.QUEUE
    case_id: str | None = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def case_scope_names_a_case(self) -> AssistantScope:
        """A case scope without a case would read nothing; a queue scope with one is ambiguous."""
        if self.kind is ScopeKind.CASE and not (self.case_id and self.case_id.strip()):
            raise ValueError("a CASE scope must name a case_id")
        if self.kind is ScopeKind.QUEUE and self.case_id is not None:
            raise ValueError("a QUEUE scope must not name a case_id")
        return self


class HistoryTurn(Dto):
    """One earlier turn, held by the browser tab — the server keeps no session (ADR-0007 § 3)."""

    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)
    answer: str = Field(default="", max_length=MAX_HISTORY_ANSWER_CHARS)


class AssistantQuestion(Dto):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)
    scope: AssistantScope = Field(default_factory=AssistantScope)
    history: tuple[HistoryTurn, ...] = Field(default=(), max_length=MAX_HISTORY_TURNS)

    @field_validator("question")
    @classmethod
    def says_something(cls, value: str) -> str:
        """Whitespace is not a question, and answering it would invent one."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("question is empty")
        return stripped


class AnswerKind(StrEnum):
    ANSWER = "ANSWER"
    """Statements about the data, every one cited."""
    REFUSAL = "REFUSAL"
    """The question asks for something this system is not entitled to say. No model was called."""
    HELP = "HELP"
    """The template did not recognise the question. It says what it can answer, never guesses."""


class AnswerIntent(StrEnum):
    """What the deterministic classifier read the question as. Shapes follow-up suggestions."""

    QUEUE_OVERVIEW = "QUEUE_OVERVIEW"
    WHERE_TO_START = "WHERE_TO_START"
    CASES_MATCHING = "CASES_MATCHING"
    CASE_OVERVIEW = "CASE_OVERVIEW"
    WHY_RAISED = "WHY_RAISED"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    COUNTER_EVIDENCE = "COUNTER_EVIDENCE"
    TIMELINE = "TIMELINE"
    COMPARISON = "COMPARISON"
    OPEN_QUESTION = "OPEN_QUESTION"
    """Free-form, answered by the model. Never produced by the template."""
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    UNRECOGNISED = "UNRECOGNISED"


class RefusalTopic(StrEnum):
    """Why a question was refused before any model saw it. One sentence of copy each."""

    VERDICT = "VERDICT"
    DECISION = "DECISION"
    CLINICAL = "CLINICAL"
    IDENTITY = "IDENTITY"
    INSTRUCTIONS = "INSTRUCTIONS"


class CitationKind(StrEnum):
    QUEUE = "QUEUE"
    """The queue as a whole — a metric or a count. Opens the Antrean Review."""
    CASE = "CASE"
    """One case. Opens its detail, or narrows the scope to it."""
    RESOURCE = "RESOURCE"
    """One resource of one case. Opens the same source drawer as every other reference."""


class Citation(Dto):
    kind: CitationKind
    case_id: str | None = None
    resource_type: ResourceType | None = None
    resource_id: str | None = None
    label: str

    @model_validator(mode="after")
    def points_at_something(self) -> Citation:
        """Each kind carries exactly what it needs to open — no more, so none can be half-built."""
        if self.kind is CitationKind.QUEUE and (self.case_id or self.resource_id):
            raise ValueError("a QUEUE citation names no case and no resource")
        if self.kind is CitationKind.CASE and (not self.case_id or self.resource_id):
            raise ValueError("a CASE citation names a case and no resource")
        if self.kind is CitationKind.RESOURCE and not (
            self.case_id and self.resource_type and self.resource_id
        ):
            raise ValueError("a RESOURCE citation names its case, type, and id")
        return self


class AssistantStatement(Dto):
    """One sentence about the data. **No citation, no statement** — ADR-0007 § 4."""

    text: str = Field(min_length=1, max_length=MAX_STATEMENT_CHARS)
    citations: tuple[Citation, ...] = Field(min_length=1, max_length=MAX_CITATIONS_PER_STATEMENT)


class CaseCard(Dto):
    """A queue row, copied verbatim, with the position the queue itself gave it.

    The position is the queue's order — band, then oldest first — and never one the assistant
    computed. "Which case first" is answered by pointing at it.
    """

    queue_position: int = Field(ge=1)
    case: CaseSummary


class AssistantAnswer(Dto):
    question: str
    scope: AssistantScope
    kind: AnswerKind
    intent: AnswerIntent
    refusal_topic: RefusalTopic | None = None
    notice: str | None = Field(
        default=None,
        description="Plain text for a REFUSAL or HELP answer. Template-authored, never generated.",
    )
    statements: tuple[AssistantStatement, ...] = Field(default=(), max_length=MAX_STATEMENTS)
    cases: tuple[CaseCard, ...] = Field(default=(), max_length=MAX_CASE_CARDS)
    uncertainty_note: str = Field(min_length=1)
    generated_by: GeneratedBy
    model_id: str | None = None
    prompt_version: str
    validation_rejected: bool = False
    rejection_reason: str | None = None
    tool_calls: tuple[ToolCallRecord, ...] = ()
    versions: VersionStamp

    @model_validator(mode="after")
    def shape_matches_kind(self) -> AssistantAnswer:
        """An ANSWER says something; a REFUSAL or HELP explains why it does not."""
        if self.kind is AnswerKind.ANSWER and not self.statements:
            raise ValueError("an ANSWER carries at least one statement")
        if self.kind is not AnswerKind.ANSWER and not self.notice:
            raise ValueError(f"a {self.kind} carries a notice")
        if (self.kind is AnswerKind.REFUSAL) != (self.refusal_topic is not None):
            raise ValueError("a refusal topic belongs to a REFUSAL and only to one")
        return self


# ---- Server-Sent Events -------------------------------------------------------------------
# `status`, `tool` and `error` are the briefing's own models: the reading log means the same
# thing on both surfaces, and one client parser reads both.


class AnswerDoneEvent(Dto):
    answer: AssistantAnswer


AssistantEvent = StatusEvent | ToolEvent | AnswerDoneEvent | ErrorEvent

EVENT_NAMES: dict[type, str] = {
    StatusEvent: "status",
    ToolEvent: "tool",
    AnswerDoneEvent: "done",
    ErrorEvent: "error",
}

__all__ = [
    "EVENT_NAMES",
    "AnswerDoneEvent",
    "AnswerIntent",
    "AnswerKind",
    "AssistantAnswer",
    "AssistantEvent",
    "AssistantQuestion",
    "AssistantScope",
    "AssistantStatement",
    "BriefingPhase",
    "CaseCard",
    "Citation",
    "CitationKind",
    "ErrorEvent",
    "GeneratedBy",
    "HistoryTurn",
    "RefusalTopic",
    "ScopeKind",
    "StatusEvent",
    "ToolCallRecord",
    "ToolEvent",
]
