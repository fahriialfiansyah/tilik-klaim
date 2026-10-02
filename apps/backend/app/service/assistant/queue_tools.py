"""The three queue-scope reads — projections of what `GET /v1/cases` already shows the role.

Same discipline as the briefing's seven: a closed registry, a name not on the list refused
before dispatch, and arguments outside the queue reported back rather than guessed around.

**What the model reads is what a reviewer reads.** Bands, states and patterns arrive as the
screen's own words in the reader's language, never as enum codes. Measured on 2 Oct 2026: given
`"band": "DETERMINISTIC_CONFLICT"`, the model wrote "band DETERMINISTIC_CONFLICT" into its prose
— a raw machine token on the reading surface. A code the model never sees is a code it never
repeats; the validator's machine-token gate is the second line, not the first.

Rows are also narrower than the queue row on screen: the pseudonymous participant and provider
tokens are left out, because nothing a reviewer asks of the queue needs them, and a field the
model never sees is a field it can never repeat.

Case reads are capped per turn. "Why is the top case there" needs one; comparing a pattern across
a handful needs a few; reading the whole queue's evidence in one turn is a different product,
and the cap is what keeps it from quietly becoming one.
"""
from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import Any

from tilik_domain.locale import Locale
from tilik_domain.reasons import CaseState, PriorityBand, RiskMode

from app.dto.cases import CaseDetailResponse, CaseSummary, EvidenceCompleteness
from app.dto.common import Dto, EvidenceRefDto
from app.service.assistant import wording as w
from app.service.assistant.context import CaseLoader, QueueSnapshot
from app.service.briefing.tools import ToolArgumentError, UnknownTool

MAX_CASE_READS = 3
MAX_FOUND_ROWS = 10
DEFAULT_FOUND_ROWS = 5


class QueueOverview(Dto):
    total_cases: int
    rows_counted: int
    """How many queue rows the per-band, per-status and per-pattern counts cover — one page."""
    awaiting_review: int
    deterministic_conflicts: int
    evidence_requested: int
    median_time_in_queue_hours: float
    cases_by_band: dict[str, int]
    cases_by_status: dict[str, int]
    cases_by_pattern: dict[str, int]


class QueueRowView(Dto):
    case_id: str
    queue_position: int
    band: str
    status: str
    patterns: tuple[str, ...]
    reason_sentence: str
    total_amount: Decimal
    currency: str
    supported_lines: int
    total_lines: int


class FoundCases(Dto):
    total_matching: int
    rows: tuple[QueueRowView, ...]
    note: str = ""


class ReasonView(Dto):
    sentence: str
    pattern: str
    deterministic: bool
    expected_support: tuple[str, ...]
    evidence: tuple[EvidenceRefDto, ...]
    counter_evidence: tuple[str, ...]


class CaseReasonsView(Dto):
    case_id: str
    queue_position: int | None
    band_basis: str
    reasons: tuple[ReasonView, ...]
    evidence_completeness: EvidenceCompleteness


def view_of(row: CaseSummary, position: int, locale: Locale) -> QueueRowView:
    completeness = row.evidence_completeness
    return QueueRowView(
        case_id=row.case_id,
        queue_position=position,
        band=w.band_label(row.band, locale),
        status=w.state_label(row.state, locale),
        patterns=tuple(w.mode_label(mode, locale) for mode in row.modes),
        reason_sentence=row.reason_sentence,
        total_amount=row.total_amount,
        currency=row.currency,
        supported_lines=completeness.supported_lines,
        total_lines=completeness.total_lines,
    )


def reasons_of(detail: CaseDetailResponse, position: int | None, locale: Locale) -> CaseReasonsView:
    return CaseReasonsView(
        case_id=detail.case_id,
        queue_position=position,
        band_basis=detail.band.basis,
        reasons=tuple(
            ReasonView(
                sentence=reason.sentence,
                pattern=w.mode_label(reason.mode, locale),
                deterministic=reason.deterministic,
                expected_support=tuple(w.resource_label(t, locale) for t in reason.expected_support),
                evidence=reason.evidence,
                counter_evidence=tuple(note.note for note in reason.counter_evidence_notes),
            )
            for reason in detail.reasons
        ),
        evidence_completeness=detail.evidence_completeness,
    )


def rows_matching(
    snapshot: QueueSnapshot,
    *,
    modes: tuple[RiskMode, ...] = (),
    bands: tuple[PriorityBand, ...] = (),
    states: tuple[CaseState, ...] = (),
) -> tuple[tuple[int, CaseSummary], ...]:
    """Positioned rows that satisfy every filter given. Queue order is kept, never re-sorted."""
    out = []
    for position, row in enumerate(snapshot.rows, start=1):
        if modes and not any(mode in row.modes for mode in modes):
            continue
        if bands and row.band not in bands:
            continue
        if states and row.state not in states:
            continue
        out.append((position, row))
    return tuple(out)


class QueueToolRegistry:
    """Three read-only functions over one queue snapshot. Nothing else is reachable."""

    def __init__(self, snapshot: QueueSnapshot, load_case: CaseLoader, locale: Locale) -> None:
        self._snapshot = snapshot
        self._load_case = load_case
        self._locale = locale
        self._read: dict[str, CaseDetailResponse] = {}
        self._handlers: dict[str, Callable[[dict[str, Any]], Dto]] = {
            "get_queue_overview": self._overview,
            "find_cases": self._find,
            "get_case_reasons": self._case_reasons,
        }

    @property
    def details_read(self) -> dict[str, CaseDetailResponse]:
        """Every case read this turn — the only cases whose resources an answer may cite."""
        return dict(self._read)

    def call(self, name: str, arguments: dict[str, Any]) -> Dto:
        if name not in self._handlers:
            raise UnknownTool(name)
        return self._handlers[name](arguments)

    # ---- handlers ----

    def _overview(self, _: dict[str, Any]) -> QueueOverview:
        rows, metrics, loc = self._snapshot.rows, self._snapshot.metrics, self._locale

        def counted(values: list[str]) -> dict[str, int]:
            return {value: values.count(value) for value in dict.fromkeys(values)}

        return QueueOverview(
            total_cases=self._snapshot.total_cases,
            rows_counted=len(rows),
            awaiting_review=metrics.awaiting_review,
            deterministic_conflicts=metrics.deterministic_conflicts,
            evidence_requested=metrics.evidence_requested,
            median_time_in_queue_hours=metrics.median_time_in_queue_hours,
            cases_by_band=counted([w.band_label(row.band, loc) for row in rows]),
            cases_by_status=counted([w.state_label(row.state, loc) for row in rows]),
            cases_by_pattern=counted([w.mode_label(mode, loc) for row in rows for mode in row.modes]),
        )

    def _find(self, arguments: dict[str, Any]) -> FoundCases:
        try:
            modes = (RiskMode(arguments["mode"]),) if arguments.get("mode") else ()
            bands = (PriorityBand(arguments["band"]),) if arguments.get("band") else ()
            states = (CaseState(arguments["state"]),) if arguments.get("state") else ()
            limit = int(arguments.get("limit") or DEFAULT_FOUND_ROWS)
        except (ValueError, TypeError) as bad:
            raise ToolArgumentError(f"invalid filter: {bad}") from bad
        limit = max(1, min(limit, MAX_FOUND_ROWS))
        matching = rows_matching(self._snapshot, modes=modes, bands=bands, states=states)
        note = "" if matching else w.pick(
            self._locale,
            "Tidak ada kasus yang cocok dengan filter ini.",
            "No case matches this filter.",
        )
        return FoundCases(
            total_matching=len(matching),
            rows=tuple(view_of(row, position, self._locale) for position, row in matching[:limit]),
            note=note,
        )

    def _case_reasons(self, arguments: dict[str, Any]) -> CaseReasonsView:
        case_id = str(arguments.get("case_id") or "")
        position = self._snapshot.position_of(case_id)
        if position is None:
            raise ToolArgumentError(f"case {case_id!r} is not in the queue")
        if case_id not in self._read and len(self._read) >= MAX_CASE_READS:
            raise ToolArgumentError(
                f"at most {MAX_CASE_READS} cases may be read per answer; already read "
                f"{', '.join(self._read)}"
            )
        detail = self._read.get(case_id) or self._load_case(case_id)
        if detail is None:
            raise ToolArgumentError(f"case {case_id!r} could not be loaded")
        self._read[case_id] = detail
        return reasons_of(detail, position, self._locale)
