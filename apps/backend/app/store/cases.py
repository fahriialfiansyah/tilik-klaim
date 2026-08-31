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

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from tilik_domain.reasons import CaseState

from app.service.screening import ScreeningResult
from app.store.engine import session_scope
from app.store.tables import cases


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
    participant_token: str = ""
    """Pseudonymous. Never a real identifier — see `docs/canonical/07_privacy_threat_model.md`."""
    provider_token: str = ""
    total_amount: Decimal = Decimal(0)
    currency: str = "IDR"
    billed_line_count: int = 0
    """How many lines the claim billed, counted at screening.

    Kept on the case rather than recomputed from the bundle so the queue can report evidence
    completeness without reading 25 bundles to build one page — and so it reports the same
    numbers the case detail does.
    """
    screened_at: datetime


class CaseStore(Protocol):
    def save(self, record: CaseRecord) -> CaseRecord: ...

    def get(self, case_id: str) -> CaseRecord | None: ...

    def find_by_ingestion(self, ingestion_id: str) -> CaseRecord | None:
        """The case this ingestion already produced, if screening has run."""
        ...

    def list_all(self) -> tuple[CaseRecord, ...]:
        """Every case, newest first. Filtering and paging happen above this layer."""
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

    def list_all(self) -> tuple[CaseRecord, ...]:
        return tuple(
            sorted(self._by_id.values(), key=lambda case: case.screened_at, reverse=True)
        )

    def clear(self) -> None:
        self._by_id.clear()
        self._by_ingestion.clear()


def new_case_id() -> str:
    return f"case_{uuid4().hex}"


def screened_now() -> datetime:
    return datetime.now(UTC)


class SqlCaseStore:
    """Postgres-backed `CaseStore`.

    The screening result is stored whole as JSONB so case detail can explain a case without
    re-screening it — a re-screen under a newer ruleset would answer a different question than
    the one the reviewer is looking at.
    """

    def save(self, record: CaseRecord) -> CaseRecord:
        values = _case_row(record)
        statement = pg_insert(cases).values(**values)
        statement = statement.on_conflict_do_update(
            index_elements=[cases.c.case_id],
            set_={k: v for k, v in values.items() if k not in {"case_id", "created_at"}},
        )
        with session_scope() as session:
            session.execute(statement)
        return record

    def get(self, case_id: str) -> CaseRecord | None:
        with session_scope() as session:
            row = session.execute(
                select(cases).where(cases.c.case_id == case_id)
            ).mappings().one_or_none()
        return _case_record(row) if row else None

    def find_by_ingestion(self, ingestion_id: str) -> CaseRecord | None:
        with session_scope() as session:
            row = session.execute(
                select(cases).where(cases.c.ingestion_id == ingestion_id)
            ).mappings().one_or_none()
        return _case_record(row) if row else None

    def list_all(self) -> tuple[CaseRecord, ...]:
        with session_scope() as session:
            rows = session.execute(
                select(cases).order_by(cases.c.created_at.desc(), cases.c.case_id)
            ).mappings().all()
        return tuple(_case_record(row) for row in rows)

    def clear(self) -> None:
        with session_scope() as session:
            session.execute(delete(cases))


def _case_row(record: CaseRecord) -> dict:
    result = record.result
    return {
        "case_id": record.case_id,
        "ingestion_id": record.ingestion_id,
        "bundle_id": result.bundle_id,
        "case_version": record.case_version,
        "state": str(record.state),
        "band": str(result.band),
        "participant_token": record.participant_token,
        "provider_token": record.provider_token,
        "total_amount": record.total_amount,
        "currency": record.currency,
        "result": result.model_dump(mode="json"),
        "completeness_notes": list(record.completeness_notes),
        "billed_line_count": record.billed_line_count,
        "created_at": record.screened_at,
        "updated_at": record.screened_at,
    }


def _case_record(row: Mapping) -> CaseRecord:
    from app.service.screening import ScreeningResult

    return CaseRecord(
        case_id=row["case_id"],
        case_version=row["case_version"],
        ingestion_id=row["ingestion_id"],
        state=CaseState(row["state"]),
        result=ScreeningResult.model_validate(row["result"]),
        completeness_notes=tuple(row["completeness_notes"]),
        participant_token=row["participant_token"],
        provider_token=row["provider_token"],
        total_amount=row["total_amount"],
        currency=row["currency"],
        billed_line_count=row["billed_line_count"],
        screened_at=row["created_at"],
    )
