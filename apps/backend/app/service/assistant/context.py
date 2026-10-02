"""What one turn may read, handed in by the router — never fetched from here.

The privacy argument is the briefing's, extended by one step and kept structural: every row in
the snapshot was built by the same `to_summary` that serves `GET /v1/cases`, and `load_case`
returns exactly what `GET /v1/cases/{id}` returns to the same role. This package imports no
store; `tests/test_assistant_isolation.py` reads its syntax trees to make sure.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from tilik_domain.locale import Locale

from app.dto.cases import CaseDetailResponse, CaseSummary, QueueMetrics

CaseLoader = Callable[[str], CaseDetailResponse | None]


@dataclass(frozen=True)
class QueueSnapshot:
    """The whole queue, in the queue's own order — band first, then oldest first."""

    rows: tuple[CaseSummary, ...]
    metrics: QueueMetrics
    total: int = -1
    """Cases in the whole queue. `rows` stops at one queue page; a count must not stop with it."""

    @property
    def total_cases(self) -> int:
        return self.total if self.total >= 0 else len(self.rows)

    def position_of(self, case_id: str) -> int | None:
        """1-based, as a reviewer counts down the list. `None` for a case not in the queue."""
        for index, row in enumerate(self.rows, start=1):
            if row.case_id == case_id:
                return index
        return None

    def row(self, case_id: str) -> CaseSummary | None:
        return next((row for row in self.rows if row.case_id == case_id), None)

    def matching_prefix(self, prefix: str) -> tuple[CaseSummary, ...]:
        """Rows whose id starts with what the reviewer typed — ids are shown truncated."""
        wanted = prefix.lower()
        return tuple(row for row in self.rows if row.case_id.lower().startswith(wanted))


@dataclass(frozen=True)
class AssistantContext:
    snapshot: QueueSnapshot
    load_case: CaseLoader
    locale: Locale
