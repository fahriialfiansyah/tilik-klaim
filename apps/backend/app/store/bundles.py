"""Persistence for ingested bundles: the raw submission and the canonical rows.

Both are kept, and keeping both is the point. The **raw payload** is stored verbatim so a
result can be re-derived from exactly what arrived — if the canonical model later changes, a
case screened under the old shape can still be explained. The **canonical bundle** is what
every downstream component reads, so nothing else has to re-parse a submission.

Records are addressed by their idempotency key, which folds the content hash together with the
engine and ruleset versions. That is what "already screened" means here: the same bundle under
the same rules returns the record that exists rather than creating a second case for one claim,
while a version bump deliberately produces a new one.

As with `app.store.edges`, the SQLAlchemy implementation is deferred: no project database is
reachable in this environment, and the demo runs offline. The protocol is what downstream code
depends on, so swapping the implementation is a local change.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict
from tilik_domain.canonical import CanonicalBundle

from app.dto.bundles import ResourceCount, ValidationStatus
from app.errors import ValidationIssue


class IngestionRecord(BaseModel):
    """One accepted submission, and everything needed to explain or repeat it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ingestion_id: str
    input_hash: str
    idempotency_key: str
    status: ValidationStatus
    raw_payload: str
    """The submission exactly as it arrived, so a result stays re-derivable."""
    bundle: CanonicalBundle | None
    """Absent when the submission was invalid; the raw payload is kept regardless."""
    issues: tuple[ValidationIssue, ...] = ()
    completeness_notes: tuple[str, ...] = ()
    resource_counts: tuple[ResourceCount, ...] = ()
    engine_version: str
    ruleset_version: str
    received_at: datetime
    case_id: str | None = None
    """Set once this ingestion has been screened, so a resubmission can point at the case."""


class BundleStore(Protocol):
    """What ingestion needs from persistence."""

    def find_by_idempotency_key(self, key: str) -> IngestionRecord | None:
        """The existing record for this content and version, if one was already accepted."""
        ...

    def save(self, record: IngestionRecord) -> IngestionRecord:
        """Persist a record. Re-saving the same idempotency key replaces it in place."""
        ...

    def get(self, ingestion_id: str) -> IngestionRecord | None: ...

    def attach_case(self, ingestion_id: str, case_id: str) -> IngestionRecord | None:
        """Record which case a screening produced, so a resubmission can point at it."""
        ...


class InMemoryBundleStore:
    """Reference implementation, used by tests and the offline demo."""

    def __init__(self) -> None:
        self._by_id: dict[str, IngestionRecord] = {}
        self._by_key: dict[str, str] = {}

    def find_by_idempotency_key(self, key: str) -> IngestionRecord | None:
        ingestion_id = self._by_key.get(key)
        return self._by_id.get(ingestion_id) if ingestion_id else None

    def save(self, record: IngestionRecord) -> IngestionRecord:
        previous = self._by_key.get(record.idempotency_key)
        if previous is not None and previous != record.ingestion_id:
            self._by_id.pop(previous, None)
        self._by_id[record.ingestion_id] = record
        self._by_key[record.idempotency_key] = record.ingestion_id
        return record

    def get(self, ingestion_id: str) -> IngestionRecord | None:
        return self._by_id.get(ingestion_id)

    def attach_case(self, ingestion_id: str, case_id: str) -> IngestionRecord | None:
        record = self._by_id.get(ingestion_id)
        if record is None:
            return None
        updated = record.model_copy(update={"case_id": case_id})
        self._by_id[ingestion_id] = updated
        return updated

    def clear(self) -> None:
        """Reset between tests and for the demo-reset route."""
        self._by_id.clear()
        self._by_key.clear()


def new_ingestion_id() -> str:
    """Opaque, non-sequential. A guessable id would leak submission volume."""
    return f"ing_{uuid4().hex}"


def received_now() -> datetime:
    return datetime.now(UTC)
