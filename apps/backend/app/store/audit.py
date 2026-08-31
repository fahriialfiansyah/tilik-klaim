"""Append-only audit events.

Every human decision lands here and never leaves. There is no update method and no delete
method on this store — not because callers are trusted to behave, but because the operations do
not exist, and the database refuses them too (`APPEND_ONLY_TRIGGER_SQL` in `tables.py`). A
correction appends a **superseding** event that links back; the original stays visible, along
with who made it.

That asymmetry is the point. `docs/canonical/07_privacy_threat_model.md` § Human accountability
treats an editable history as no history at all: if a decision can be quietly rewritten, no one
can be answerable for it.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict
from sqlalchemy import insert, select
from tilik_domain.canonical import ResourceRef
from tilik_domain.reasons import CaseState, DispositionAction
from tilik_domain.versioning import EngineIdentity

from app.store.engine import session_scope
from app.store.tables import audit_events


class AuditWriteRefused(RuntimeError):
    """An event that would have been incomplete or unattributable. Nothing was written."""


class AuditEventRecord(BaseModel):
    """One immutable entry in a case's history."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str
    case_id: str
    event_kind: str
    actor_role: str
    action: DispositionAction | None = None
    structured_reason: str | None = None
    note: str | None = None
    evidence: tuple[ResourceRef, ...] = ()
    state_before: CaseState | None = None
    state_after: CaseState | None = None
    case_version_before: int | None = None
    case_version_after: int | None = None
    supersedes_event_id: str | None = None
    identity: EngineIdentity
    occurred_at: datetime

    def model_post_init(self, context: object, /) -> None:
        """A disposition without a reason is not an event worth keeping.

        Checked at construction as well as by the DTO and the database. Three layers is not
        excessive for the one field that makes a decision accountable — the DTO can be bypassed
        by any internal caller, and only the database catches everything.
        """
        if self.event_kind == "DISPOSITION" and not (self.structured_reason or "").strip():
            raise AuditWriteRefused(
                "a disposition event requires a structured reason; refusing to write one without"
            )


class AuditStore(Protocol):
    """Append and read. Deliberately no update, no delete."""

    def append(self, event: AuditEventRecord) -> AuditEventRecord: ...

    def for_case(self, case_id: str) -> tuple[AuditEventRecord, ...]:
        """Every event for one case, oldest first."""
        ...

    def get(self, event_id: str) -> AuditEventRecord | None: ...


class InMemoryAuditStore:
    """Reference implementation. Mirrors the database's refusal to mutate."""

    def __init__(self) -> None:
        self._events: list[AuditEventRecord] = []

    def append(self, event: AuditEventRecord) -> AuditEventRecord:
        if any(existing.event_id == event.event_id for existing in self._events):
            raise AuditWriteRefused(f"event {event.event_id} already exists; history is append-only")
        self._events.append(event)
        return event

    def for_case(self, case_id: str) -> tuple[AuditEventRecord, ...]:
        return tuple(
            sorted(
                (event for event in self._events if event.case_id == case_id),
                key=lambda event: event.occurred_at,
            )
        )

    def get(self, event_id: str) -> AuditEventRecord | None:
        return next((event for event in self._events if event.event_id == event_id), None)

    def clear(self) -> None:
        """Test and demo-reset only. Never reachable from a request path."""
        self._events.clear()


class SqlAuditStore:
    """Postgres-backed. The table's trigger refuses UPDATE and DELETE outright."""

    def append(self, event: AuditEventRecord) -> AuditEventRecord:
        with session_scope() as session:
            session.execute(insert(audit_events).values(**_to_row(event)))
        return event

    def for_case(self, case_id: str) -> tuple[AuditEventRecord, ...]:
        with session_scope() as session:
            rows = session.execute(
                select(audit_events)
                .where(audit_events.c.case_id == case_id)
                .order_by(audit_events.c.occurred_at, audit_events.c.event_id)
            ).mappings().all()
        return tuple(_from_row(row) for row in rows)

    def get(self, event_id: str) -> AuditEventRecord | None:
        with session_scope() as session:
            row = session.execute(
                select(audit_events).where(audit_events.c.event_id == event_id)
            ).mappings().one_or_none()
        return _from_row(row) if row else None

    def clear(self) -> None:
        """Truncate, used by tests and demo reset.

        `TRUNCATE` rather than `DELETE` precisely because the append-only trigger refuses row
        deletion — which is the trigger doing its job. Resetting a demo is a different act from
        editing history, and it is not reachable from any request path.
        """
        from sqlalchemy import text

        with session_scope() as session:
            session.execute(text("truncate table audit_events"))


def _to_row(event: AuditEventRecord) -> dict:
    return {
        "event_id": event.event_id,
        "case_id": event.case_id,
        "event_kind": event.event_kind,
        "actor_role": event.actor_role,
        "action": str(event.action) if event.action else None,
        "structured_reason": event.structured_reason,
        "note": event.note,
        "evidence": [ref.model_dump(mode="json") for ref in event.evidence],
        "state_before": str(event.state_before) if event.state_before else None,
        "state_after": str(event.state_after) if event.state_after else None,
        "case_version_before": event.case_version_before,
        "case_version_after": event.case_version_after,
        "supersedes_event_id": event.supersedes_event_id,
        "schema_version": event.identity.schema_version,
        "ruleset_version": event.identity.ruleset_version,
        "engine_version": event.identity.engine_version,
        "dataset_version": event.identity.dataset_version,
        "occurred_at": event.occurred_at,
    }


def _from_row(row: Mapping) -> AuditEventRecord:
    return AuditEventRecord(
        event_id=row["event_id"],
        case_id=row["case_id"],
        event_kind=row["event_kind"],
        actor_role=row["actor_role"],
        action=DispositionAction(row["action"]) if row["action"] else None,
        structured_reason=row["structured_reason"],
        note=row["note"],
        evidence=tuple(ResourceRef.model_validate(item) for item in row["evidence"]),
        state_before=CaseState(row["state_before"]) if row["state_before"] else None,
        state_after=CaseState(row["state_after"]) if row["state_after"] else None,
        case_version_before=row["case_version_before"],
        case_version_after=row["case_version_after"],
        supersedes_event_id=row["supersedes_event_id"],
        identity=EngineIdentity(
            schema_version=row["schema_version"],
            ruleset_version=row["ruleset_version"],
            engine_version=row["engine_version"],
            dataset_version=row["dataset_version"],
        ),
        occurred_at=row["occurred_at"],
    )


def new_event_id() -> str:
    return f"evt_{uuid4().hex}"


def occurred_now() -> datetime:
    return datetime.now(UTC)
