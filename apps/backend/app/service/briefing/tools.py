"""The seven read-only tools — every one a slice of the `CaseDetailResponse` already built.

This is the privacy argument, and it is structural rather than procedural: the briefing cannot
see anything the reviewer cannot see on screen. No store, no bundle, no cross-case query; the
`RELATED_BUNDLE` redaction already happened upstream. The registry is closed — a name not in
`TOOL_NAMES` is refused before anything is looked up.

Deliberately absent from every tool: the priority band and the component scores. The briefing
is about evidence, and a summary that can name a score is one step from writing about it.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import Field
from tilik_domain.canonical import ResourceType
from tilik_domain.reasons import CaseState, ReasonCode, RiskMode

from app.dto.cases import (
    CaseDetailResponse,
    ClaimLineView,
    ComparisonCandidate,
    EvidenceCompleteness,
    SourceAvailability,
    SourceResource,
    TimelineEvent,
)
from app.dto.common import CounterEvidenceDto, Dto, EvidenceRefDto, ReasonDto, VersionStamp

TOOL_NAMES: tuple[str, ...] = (
    "get_case_overview",
    "list_reasons",
    "get_evidence_path",
    "get_timeline",
    "get_counter_evidence",
    "get_comparison_candidate",
    "get_source_resource",
)

COMPARISON_MODES = (RiskMode.REPEAT_BILLING, RiskMode.CLONED_DOCUMENTATION)


class UnknownTool(LookupError):
    """A name outside the closed registry. Refused before dispatch."""


class ToolArgumentError(ValueError):
    """A known tool given arguments it cannot act on — reported back, never guessed around."""


# ---- Tool outputs ---------------------------------------------------------------------------


class CaseOverview(Dto):
    case_id: str
    case_version: int
    state: CaseState
    total_amount: Decimal
    currency: str
    encounter_start: datetime
    encounter_end: datetime | None
    line_count: int
    evidence_completeness: EvidenceCompleteness
    versions: VersionStamp


class ReasonSummary(Dto):
    code: ReasonCode
    mode: RiskMode
    sentence: str
    deterministic: bool
    expected_support: tuple[ResourceType, ...]
    evidence: tuple[EvidenceRefDto, ...]
    ruleset_version: str


class ReasonList(Dto):
    reasons: tuple[ReasonSummary, ...]


class EvidencePathView(Dto):
    reason_code: ReasonCode
    cited_lines: tuple[ClaimLineView, ...]
    expected_support: tuple[ResourceType, ...]
    found: tuple[EvidenceRefDto, ...]
    missing: tuple[ResourceType, ...]


class TimelineView(Dto):
    events: tuple[TimelineEvent, ...]


class CounterEvidenceView(Dto):
    reason_code: ReasonCode
    notes: tuple[CounterEvidenceDto, ...]


class ComparisonView(Dto):
    reason_code: ReasonCode
    candidate: ComparisonCandidate | None
    note: str = Field(description="Why there is no candidate, when there is none.")


# ---- Definitions handed to the model -------------------------------------------------------

_REASON_ARG = {
    "type": "object",
    "properties": {"reason_code": {"type": "string", "enum": [code.value for code in ReasonCode]}},
    "required": ["reason_code"],
}
_NO_ARGS = {"type": "object", "properties": {}}
_SOURCE_ARG = {
    "type": "object",
    "properties": {
        "resource_type": {"type": "string", "enum": [t.value for t in ResourceType]},
        "resource_id": {"type": "string"},
    },
    "required": ["resource_type", "resource_id"],
}

TOOL_DEFINITIONS: dict[str, dict[str, Any]] = {
    "get_case_overview": {
        "description": "Ringkasan kasus: status, nominal, rentang kunjungan, kelengkapan bukti, versi mesin.",
        "parameters": _NO_ARGS,
    },
    "list_reasons": {
        "description": "Semua alasan yang teramati, terurut dari yang terkuat, dengan bukti yang dirujuk.",
        "parameters": _NO_ARGS,
    },
    "get_evidence_path": {
        "description": "Untuk satu alasan: baris yang dirujuk, jenis bukti yang diharapkan, yang ditemukan, yang tidak.",
        "parameters": _REASON_ARG,
    },
    "get_timeline": {
        "description": "Kejadian episode dalam urutan waktu.",
        "parameters": _NO_ARGS,
    },
    "get_counter_evidence": {
        "description": "Untuk satu alasan: fakta yang melemahkannya, dalam kalimat, dengan rujukan.",
        "parameters": _REASON_ARG,
    },
    "get_comparison_candidate": {
        "description": "Untuk alasan tagihan berulang atau dokumentasi salinan: pasangan pembanding.",
        "parameters": _REASON_ARG,
    },
    "get_source_resource": {
        "description": "Isi satu sumber daya yang dirujuk, sebagaimana tersedia untuk peninjau.",
        "parameters": _SOURCE_ARG,
    },
}


class ToolRegistry:
    """Seven read-only functions over one detail response. Nothing else is reachable."""

    def __init__(self, detail: CaseDetailResponse) -> None:
        self._detail = detail
        self._handlers: dict[str, Callable[[dict[str, Any]], Dto]] = {
            "get_case_overview": self._overview,
            "list_reasons": self._reasons,
            "get_evidence_path": self._evidence_path,
            "get_timeline": self._timeline,
            "get_counter_evidence": self._counter_evidence,
            "get_comparison_candidate": self._comparison,
            "get_source_resource": self._source,
        }

    @staticmethod
    def definitions() -> tuple[dict[str, Any], ...]:
        return tuple(
            {"type": "function", "function": {"name": name, **TOOL_DEFINITIONS[name]}}
            for name in TOOL_NAMES
        )

    def example_arguments(self, name: str) -> dict[str, str] | None:
        """Valid arguments for a tool on *this* case, or `None` when none exist.

        A case with no reasons has nothing a reason-scoped tool can be asked about; that is a
        fact about the case, not an error in the tool.
        """
        if name not in TOOL_NAMES:
            raise UnknownTool(name)
        if TOOL_DEFINITIONS[name]["parameters"] is _REASON_ARG:
            if not self._detail.reasons:
                return None
            return {"reason_code": str(self._detail.reasons[0].code)}
        if name == "get_source_resource":
            source = self._detail.sources[0] if self._detail.sources else None
            return (
                {"resource_type": str(source.resource_type), "resource_id": source.resource_id}
                if source
                else {"resource_type": "Encounter", "resource_id": "none"}
            )
        return {}

    def call(self, name: str, arguments: dict[str, Any]) -> Dto:
        if name not in self._handlers:
            raise UnknownTool(name)
        return self._handlers[name](arguments)

    # ---- handlers ----

    def _overview(self, _: dict[str, Any]) -> CaseOverview:
        d = self._detail
        return CaseOverview(
            case_id=d.case_id,
            case_version=d.case_version,
            state=d.state,
            total_amount=d.total_amount,
            currency=d.currency,
            encounter_start=d.encounter_start,
            encounter_end=d.encounter_end,
            line_count=len(d.lines),
            evidence_completeness=d.evidence_completeness,
            versions=d.versions,
        )

    def _reasons(self, _: dict[str, Any]) -> ReasonList:
        return ReasonList(reasons=tuple(_summarise(reason) for reason in self._detail.reasons))

    def _reason(self, arguments: dict[str, Any]) -> ReasonDto:
        code = arguments.get("reason_code")
        for reason in self._detail.reasons:
            if str(reason.code) == str(code):
                return reason
        raise ToolArgumentError(f"reason {code!r} is not on this case")

    def _evidence_path(self, arguments: dict[str, Any]) -> EvidencePathView:
        reason = self._reason(arguments)
        cited_ids = {ref.resource_id for ref in reason.evidence if ref.resource_type == ResourceType.CLAIM_LINE}
        found = tuple(ref for ref in reason.evidence if ref.resource_type != ResourceType.CLAIM_LINE)
        found_types = {ref.resource_type for ref in found}
        return EvidencePathView(
            reason_code=reason.code,
            cited_lines=tuple(line for line in self._detail.lines if line.line_id in cited_ids),
            expected_support=reason.expected_support,
            found=found,
            missing=tuple(t for t in reason.expected_support if t not in found_types),
        )

    def _timeline(self, _: dict[str, Any]) -> TimelineView:
        return TimelineView(events=self._detail.timeline)

    def _counter_evidence(self, arguments: dict[str, Any]) -> CounterEvidenceView:
        reason = self._reason(arguments)
        return CounterEvidenceView(reason_code=reason.code, notes=reason.counter_evidence_notes)

    def _comparison(self, arguments: dict[str, Any]) -> ComparisonView:
        reason = self._reason(arguments)
        if reason.mode not in COMPARISON_MODES:
            return ComparisonView(reason_code=reason.code, candidate=None,
                                  note="Alasan ini bukan alasan pembandingan; tidak ada pasangan kandidat.")
        # Comparisons travel in reason order for the two comparison-shaped modes — the same
        # positional pairing the screen uses, so the briefing and the drawer name the same pair.
        comparable = [r for r in self._detail.reasons if r.mode in COMPARISON_MODES]
        rank = next(i for i, r in enumerate(comparable) if r.code == reason.code)
        candidate = self._detail.comparisons[rank] if rank < len(self._detail.comparisons) else None
        note = "" if candidate else "Tidak ada kandidat pembanding yang tersedia untuk alasan ini."
        return ComparisonView(reason_code=reason.code, candidate=candidate, note=note)

    def _source(self, arguments: dict[str, Any]) -> SourceResource:
        wanted_type = str(arguments.get("resource_type"))
        wanted_id = str(arguments.get("resource_id"))
        for source in self._detail.sources:
            if str(source.resource_type) == wanted_type and source.resource_id == wanted_id:
                return source
        # Reported as MISSING rather than invented or dropped — the same rule the screen follows.
        try:
            resource_type = ResourceType(wanted_type)
        except ValueError as bad:
            raise ToolArgumentError(f"unknown resource type {wanted_type!r}") from bad
        return SourceResource(
            resource_type=resource_type,
            resource_id=wanted_id,
            label=f"{wanted_type} {wanted_id}",
            availability=SourceAvailability.MISSING,
            fields=(),
        )


def _summarise(reason: ReasonDto) -> ReasonSummary:
    return ReasonSummary(
        code=reason.code,
        mode=reason.mode,
        sentence=reason.sentence,
        deterministic=reason.deterministic,
        expected_support=reason.expected_support,
        evidence=reason.evidence,
        ruleset_version=reason.ruleset_version,
    )
