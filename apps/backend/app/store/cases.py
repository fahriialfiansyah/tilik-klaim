"""Cases produced by screening an ingested bundle.

Deliberately minimal. The queue, the disposition flow, and the audit trail belong to
`04-review-slice`, which owns the case table and its state machine. What lives here is only what
`POST /bundles/{id}/screen` must record to return a `ScreenResponse` and to let a resubmission
point at the case it already produced.

`case_version` starts at 1 and increments on every re-screen, because the disposition endpoint
uses it for optimistic concurrency: a reviewer acting on what they saw must not silently
overwrite a newer screening they never read.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict
from tilik_domain.reasons import CaseState

from app.service.screening import ScreeningResult


class CaseRecord(BaseModel):
    """One screened claim awaiting a human decision."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    case_id: str
    case_version: int
    ingestion_id: str
    state: CaseState
    result: ScreeningResult
    completeness_notes: tuple[str, ...] = ()
    """Carried from ingestion. These lower certainty for a reviewer; they never raise a signal."""
    screened_at: datetime


class CaseStore(Protocol):
    def save(self, record: CaseRecord) -> CaseRecord: ...

    def get(self, case_id: str) -> CaseRecord | None: ...

    def find_by_ingestion(self, ingestion_id: str) -> CaseRecord | None:
        """The case this ingestion already produced, if screening has run."""
        ...


class InMemoryCaseStore:
    """Reference implementation. The database-backed one lands with `04-review-slice`."""

    def __init__(self) -> None:
        self._by_id: dict[str, CaseRecord] = {}
        self._by_ingestion: dict[str, str] = {}

    def save(self, record: CaseRecord) -> CaseRecord:
        self._by_id[record.case_id] = record
        self._by_ingestion[record.ingestion_id] = record.case_id
        return record

    def get(self, case_id: str) -> CaseRecord | None:
        return self._by_id.get(case_id)

    def find_by_ingestion(self, ingestion_id: str) -> CaseRecord | None:
        case_id = self._by_ingestion.get(ingestion_id)
        return self._by_id.get(case_id) if case_id else None

    def clear(self) -> None:
        self._by_id.clear()
        self._by_ingestion.clear()


def new_case_id() -> str:
    return f"case_{uuid4().hex}"


def screened_now() -> datetime:
    return datetime.now(UTC)
