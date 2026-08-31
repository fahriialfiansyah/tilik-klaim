"""Persistence for ingested bundles: the raw submission and the canonical rows.

Both are kept, and keeping both is the point. The **raw payload** is stored verbatim so a
result can be re-derived from exactly what arrived — if the canonical model later changes, a
case screened under the old shape can still be explained. The **canonical bundle** is what
every downstream component reads, so nothing else has to re-parse a submission.

Records are addressed by their idempotency key, which folds the content hash together with the
engine and ruleset versions. That is what "already screened" means here: the same bundle under
the same rules returns the record that exists rather than creating a second case for one claim,
while a version bump deliberately produces a new one.

Two implementations satisfy the protocol. `SqlBundleStore` is what runs when a database is
reachable; `InMemoryBundleStore` keeps the API's tests and the offline demo working without
one. Downstream code depends on the protocol, never on either implementation.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict
from sqlalchemy import delete, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from tilik_domain.canonical import CanonicalBundle, DocumentRef

from app.dto.bundles import ResourceCount, ValidationStatus
from app.errors import ValidationIssue
from app.store.engine import session_scope
from app.store.tables import ingestions


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

    def history_for(
        self, participant_id: str, provider_id: str, *, exclude_bundle_id: str
    ) -> tuple[CanonicalBundle, ...]:
        """Earlier valid bundles for the same participant at the same provider.

        Repeat billing and unbundling are only visible across claims, so screening needs the
        prior ones. Scoped to a single participant and provider deliberately: a wider net would
        pull unrelated people's records into one screening for no detection benefit, which
        `docs/canonical/07_privacy_threat_model.md` calls out as unnecessary exposure.
        """
        ...

    def peer_documents_for(
        self, provider_id: str, *, exclude_bundle_id: str
    ) -> tuple[DocumentRef, ...]:
        """Clinical notes from other bundles at the same provider, across participants.

        Cloned documentation is a **per-provider** pattern: the same narrative reused for
        different patients. Scoping it per-participant, as `history_for` does, makes the
        detector inert — which is exactly the defect this method exists to fix.

        Only `DocumentRef` rows cross this boundary. Comparing notes needs their text and id;
        it never needs another patient's claim lines, diagnoses, or amounts, and pulling those
        in would be exposure without detection benefit.
        """
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

    def history_for(
        self, participant_id: str, provider_id: str, *, exclude_bundle_id: str
    ) -> tuple[CanonicalBundle, ...]:
        matches = [
            record
            for record in self._by_id.values()
            if record.bundle is not None
            and record.bundle.bundle_id != exclude_bundle_id
            and record.bundle.claim.participant_id == participant_id
            and record.bundle.claim.provider_id == provider_id
        ]
        matches.sort(key=lambda record: record.received_at)
        return tuple(record.bundle for record in matches if record.bundle)

    def peer_documents_for(
        self, provider_id: str, *, exclude_bundle_id: str
    ) -> tuple[DocumentRef, ...]:
        records = sorted(
            (
                record
                for record in self._by_id.values()
                if record.bundle is not None
                and record.bundle.bundle_id != exclude_bundle_id
                and record.bundle.claim.provider_id == provider_id
            ),
            key=lambda record: record.received_at,
        )
        return tuple(
            document
            for record in records
            if record.bundle
            for document in record.bundle.documents
        )

    def clear(self) -> None:
        """Reset between tests and for the demo-reset route."""
        self._by_id.clear()
        self._by_key.clear()


def new_ingestion_id() -> str:
    """Opaque, non-sequential. A guessable id would leak submission volume."""
    return f"ing_{uuid4().hex}"


def received_now() -> datetime:
    return datetime.now(UTC)


class SqlBundleStore:
    """Postgres-backed implementation of `BundleStore`.

    Writes go through `session_scope`, so a failure part-way rolls the whole record back rather
    than leaving a raw payload with no canonical rows beside it.
    """

    def find_by_idempotency_key(self, key: str) -> IngestionRecord | None:
        with session_scope() as session:
            row = session.execute(
                select(ingestions).where(ingestions.c.idempotency_key == key)
            ).mappings().one_or_none()
        return _to_record(row) if row else None

    def save(self, record: IngestionRecord) -> IngestionRecord:
        """Insert, or replace the row already holding this idempotency key.

        Conflict is resolved on `idempotency_key` rather than the primary key: the same content
        at the same version is the same ingestion, whatever id a retry happened to generate.
        """
        values = _to_row(record)
        statement = pg_insert(ingestions).values(**values)
        statement = statement.on_conflict_do_update(
            index_elements=[ingestions.c.idempotency_key],
            set_={
                column: values[column]
                for column in values
                if column not in {"ingestion_id", "idempotency_key"}
            },
        ).returning(ingestions)
        with session_scope() as session:
            row = session.execute(statement).mappings().one()
        return _to_record(row)

    def get(self, ingestion_id: str) -> IngestionRecord | None:
        with session_scope() as session:
            row = session.execute(
                select(ingestions).where(ingestions.c.ingestion_id == ingestion_id)
            ).mappings().one_or_none()
        return _to_record(row) if row else None

    def attach_case(self, ingestion_id: str, case_id: str) -> IngestionRecord | None:
        with session_scope() as session:
            row = session.execute(
                update(ingestions)
                .where(ingestions.c.ingestion_id == ingestion_id)
                .values(case_id=case_id)
                .returning(ingestions)
            ).mappings().one_or_none()
        return _to_record(row) if row else None

    def history_for(
        self, participant_id: str, provider_id: str, *, exclude_bundle_id: str
    ) -> tuple[CanonicalBundle, ...]:
        with session_scope() as session:
            rows = session.execute(
                select(ingestions.c.bundle_json)
                .where(
                    ingestions.c.bundle_json.is_not(None),
                    ingestions.c.bundle_json["claim"]["participant_id"].astext
                    == participant_id,
                    ingestions.c.bundle_json["claim"]["provider_id"].astext == provider_id,
                    ingestions.c.bundle_json["bundle_id"].astext != exclude_bundle_id,
                )
                .order_by(ingestions.c.received_at)
            ).scalars().all()
        return tuple(CanonicalBundle.model_validate(row) for row in rows)

    def peer_documents_for(
        self, provider_id: str, *, exclude_bundle_id: str
    ) -> tuple[DocumentRef, ...]:
        with session_scope() as session:
            rows = session.execute(
                select(ingestions.c.bundle_json)
                .where(
                    ingestions.c.bundle_json.is_not(None),
                    ingestions.c.bundle_json["claim"]["provider_id"].astext == provider_id,
                    ingestions.c.bundle_json["bundle_id"].astext != exclude_bundle_id,
                )
                .order_by(ingestions.c.received_at)
            ).scalars().all()
        return tuple(
            DocumentRef.model_validate(document)
            for row in rows
            for document in row.get("documents", ())
        )

    def clear(self) -> None:
        """Wipe every ingestion. Used by tests and the demo-reset route, never in a request."""
        with session_scope() as session:
            session.execute(delete(ingestions))


def _to_row(record: IngestionRecord) -> dict:
    return {
        "ingestion_id": record.ingestion_id,
        "input_hash": record.input_hash,
        "idempotency_key": record.idempotency_key,
        "status": str(record.status),
        "raw_payload": record.raw_payload,
        "bundle_json": record.bundle.model_dump(mode="json") if record.bundle else None,
        "issues": [issue.model_dump(mode="json") for issue in record.issues],
        "completeness_notes": list(record.completeness_notes),
        "resource_counts": [count.model_dump(mode="json") for count in record.resource_counts],
        "engine_version": record.engine_version,
        "ruleset_version": record.ruleset_version,
        "received_at": record.received_at,
        "case_id": record.case_id,
    }


def _to_record(row: Mapping) -> IngestionRecord:
    bundle_json = row["bundle_json"]
    return IngestionRecord(
        ingestion_id=row["ingestion_id"],
        input_hash=row["input_hash"],
        idempotency_key=row["idempotency_key"],
        status=ValidationStatus(row["status"]),
        raw_payload=row["raw_payload"],
        bundle=CanonicalBundle.model_validate(bundle_json) if bundle_json else None,
        issues=tuple(ValidationIssue.model_validate(item) for item in row["issues"]),
        completeness_notes=tuple(row["completeness_notes"]),
        resource_counts=tuple(
            ResourceCount.model_validate(item) for item in row["resource_counts"]
        ),
        engine_version=row["engine_version"],
        ruleset_version=row["ruleset_version"],
        received_at=row["received_at"],
        case_id=row["case_id"],
    )
