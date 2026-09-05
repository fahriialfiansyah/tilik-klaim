"""Synthetic staff accounts, and the append-only trail of changes made to them.

Three rows, fixed. There is no create and no delete — ADR-0006 § 7 keeps the roster at three,
so management is a role change and an active flag, and each of those appends an event that is
never edited.

**`demo_passcode` is plain text on purpose.** The login screen prints it beside the account it
belongs to, so it protects nothing; hashing a value shown on screen would be theatre, and
naming the column `password_hash` would tell a reader of this code that a security boundary
exists here when none does. It is a persona selector with a credential-shaped interface, and
`docs/canonical/decisions/ADR-0006-three-roles-and-simulated-login.md` § 3 is why.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, ConfigDict
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.service.access import Role
from app.store.engine import session_scope
from app.store.tables import user_audit_events, users


class UserRecord(BaseModel):
    """One synthetic staff account.

    `demo_passcode` lives on the record because the sign-in check needs it. It never reaches a
    response DTO — `app/dto/users.py` has no such field, and a test asserts a refused sign-in
    does not echo the value that was tried.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    user_id: str
    staff_code: str
    full_name: str
    email: str
    role: Role
    demo_passcode: str
    """Plain text, deliberately. See the module docstring."""
    is_active: bool = True
    last_signed_in_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class UserAuditRecord(BaseModel):
    """One change to one account. Append-only, like a case disposition (ADR-0001)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str
    event_kind: str
    actor_user_id: str
    actor_role: str
    target_user_id: str
    field: str
    value_before: str | None = None
    value_after: str | None = None
    occurred_at: datetime


class UserStore(Protocol):
    """Read, save, and append. No create, no delete — the roster is fixed at three."""

    def save(self, record: UserRecord) -> UserRecord: ...

    def get(self, user_id: str) -> UserRecord | None: ...

    def find_by_email(self, email: str) -> UserRecord | None:
        """Case-insensitive: an email typed with a capital is the same account."""
        ...

    def list_all(self) -> tuple[UserRecord, ...]:
        """Every account, ordered by staff code so the table never reshuffles itself."""
        ...

    def append_event(self, event: UserAuditRecord) -> UserAuditRecord: ...

    def events(self) -> tuple[UserAuditRecord, ...]:
        """Every management event, newest first — the order the panel reads them in."""
        ...


class InMemoryUserStore:
    """Reference implementation, and the one the offline demo runs on.

    `08_demo_runbook.md` requires a run with no external network, so a login screen that needed
    Postgres to accept a sign-in would take the whole demo down with the database.
    """

    def __init__(self) -> None:
        self._by_id: dict[str, UserRecord] = {}
        self._events: list[UserAuditRecord] = []

    def save(self, record: UserRecord) -> UserRecord:
        self._by_id[record.user_id] = record
        return record

    def get(self, user_id: str) -> UserRecord | None:
        return self._by_id.get(user_id)

    def find_by_email(self, email: str) -> UserRecord | None:
        wanted = email.strip().lower()
        return next(
            (user for user in self._by_id.values() if user.email.lower() == wanted), None
        )

    def list_all(self) -> tuple[UserRecord, ...]:
        return tuple(sorted(self._by_id.values(), key=lambda user: user.staff_code))

    def append_event(self, event: UserAuditRecord) -> UserAuditRecord:
        self._events.append(event)
        return event

    def events(self) -> tuple[UserAuditRecord, ...]:
        return tuple(
            sorted(self._events, key=lambda item: item.occurred_at, reverse=True)
        )

    def clear(self) -> None:
        """Test and demo-reset only. Never reachable from a request path."""
        self._by_id.clear()
        self._events.clear()


class SqlUserStore:
    """Postgres-backed. The event table's trigger refuses UPDATE and DELETE outright."""

    def save(self, record: UserRecord) -> UserRecord:
        values = _user_row(record)
        statement = pg_insert(users).values(**values)
        statement = statement.on_conflict_do_update(
            index_elements=[users.c.user_id],
            set_={k: v for k, v in values.items() if k not in {"user_id", "created_at"}},
        )
        with session_scope() as session:
            session.execute(statement)
        return record

    def get(self, user_id: str) -> UserRecord | None:
        with session_scope() as session:
            row = session.execute(
                select(users).where(users.c.user_id == user_id)
            ).mappings().one_or_none()
        return _user_record(row) if row else None

    def find_by_email(self, email: str) -> UserRecord | None:
        from sqlalchemy import func

        with session_scope() as session:
            row = session.execute(
                select(users).where(func.lower(users.c.email) == email.strip().lower())
            ).mappings().one_or_none()
        return _user_record(row) if row else None

    def list_all(self) -> tuple[UserRecord, ...]:
        with session_scope() as session:
            rows = session.execute(
                select(users).order_by(users.c.staff_code)
            ).mappings().all()
        return tuple(_user_record(row) for row in rows)

    def append_event(self, event: UserAuditRecord) -> UserAuditRecord:
        with session_scope() as session:
            session.execute(pg_insert(user_audit_events).values(**event.model_dump()))
        return event

    def events(self) -> tuple[UserAuditRecord, ...]:
        with session_scope() as session:
            rows = session.execute(
                select(user_audit_events).order_by(
                    user_audit_events.c.occurred_at.desc(), user_audit_events.c.event_id
                )
            ).mappings().all()
        return tuple(UserAuditRecord(**dict(row)) for row in rows)

    def clear(self) -> None:
        """Truncate, used by tests and demo reset.

        `TRUNCATE` on the event table rather than `DELETE`, precisely because the append-only
        trigger refuses row deletion — which is the trigger doing its job. Resetting a demo is a
        different act from editing history, and neither is reachable from a request path.
        """
        from sqlalchemy import text

        with session_scope() as session:
            session.execute(text("truncate table user_audit_events"))
            session.execute(delete(users))


def _user_row(record: UserRecord) -> dict:
    return {
        "user_id": record.user_id,
        "staff_code": record.staff_code,
        "full_name": record.full_name,
        "email": record.email,
        "role": str(record.role),
        "demo_passcode": record.demo_passcode,
        "is_active": record.is_active,
        "last_signed_in_at": record.last_signed_in_at,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def _user_record(row: Mapping) -> UserRecord:
    return UserRecord(
        user_id=row["user_id"],
        staff_code=row["staff_code"],
        full_name=row["full_name"],
        email=row["email"],
        role=Role(row["role"]),
        demo_passcode=row["demo_passcode"],
        is_active=row["is_active"],
        last_signed_in_at=row["last_signed_in_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def new_user_event_id() -> str:
    return f"uevt_{uuid4().hex}"


def now() -> datetime:
    return datetime.now(UTC)
