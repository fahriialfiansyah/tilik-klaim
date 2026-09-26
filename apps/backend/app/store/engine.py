"""Database engine and session handling.

One engine per process, created lazily so importing the app never opens a connection — the
frontend team runs the API's tests without a database, and the offline demo must not fail at
import time because Postgres is absent.

`is_database_available()` exists for that same reason: it answers whether the configured
database can be reached, so callers can fall back to the in-memory store rather than crash.
It is a capability probe, never a health check that hides a real failure — once a store is
bound to the database, its errors propagate.
"""
from __future__ import annotations

import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

CONNECT_TIMEOUT_SECONDS = 5
"""Short: a demo that stalls on a dead database is worse than one that reports it."""

HEALTH_PROBE_TTL_SECONDS = 10.0
"""How long a health reading of the database is reused before a background refresh.

An unreachable host costs `CONNECT_TIMEOUT_SECONDS` *per address*: 5s for one, 10s for `localhost`
(`::1` and `127.0.0.1`). Paid on every `/healthz` request, that made the health endpoint the
slowest route in the API at exactly the moment the database was down — which is when a platform
probe polls it hardest.
"""

_availability_lock = threading.Lock()
_availability: tuple[bool, float] | None = None
"""The last probe outcome and when it was taken (monotonic seconds)."""
_refreshing = False


@lru_cache
def get_engine() -> Engine:
    """The process-wide engine. Cached so pooling actually pools."""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
    )


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


@contextmanager
def session_scope() -> Iterator[Session]:
    """A transaction that commits on success and rolls back on any failure.

    Rolling back rather than leaving a partial write is what keeps a half-stored ingestion —
    raw payload saved, canonical rows missing — from ever existing.
    """
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def is_database_available() -> bool:
    """Whether the configured database answers, asked afresh. Used to choose a store.

    Blocks for as long as the probe takes. Anything on a request path that only wants to *report*
    reachability should use `database_availability()` instead.
    """
    try:
        with get_engine().connect() as connection:
            connection.execute(text("select 1"))
    except SQLAlchemyError:
        available = False
    else:
        available = True
    _record_availability(available)
    return available


def database_availability() -> bool:
    """The last known answer to "does the database answer?", refreshed off the request path.

    Only the very first call ever waits on a probe. After that a stale answer is returned at once
    while a single background thread asks again, so an unreachable database costs a health
    request nothing. The price is that a change is reported up to one TTL late, which is the right
    trade for a readiness display and the wrong one for choosing a store — that keeps using
    `is_database_available()`.
    """
    global _refreshing
    with _availability_lock:
        known = _availability
        stale = known is not None and time.monotonic() - known[1] >= HEALTH_PROBE_TTL_SECONDS
        start_refresh = stale and not _refreshing
        if start_refresh:
            _refreshing = True

    if known is None:
        available = is_database_available()
        _record_availability(available)
        return available
    if start_refresh:
        threading.Thread(target=_refresh_availability, name="db-probe", daemon=True).start()
    return known[0]


def _record_availability(available: bool) -> None:
    global _availability
    with _availability_lock:
        _availability = (available, time.monotonic())


def _refresh_availability() -> None:
    global _refreshing
    try:
        _record_availability(is_database_available())
    finally:
        with _availability_lock:
            _refreshing = False


def reset_engine() -> None:
    """Drop the cached engine so a changed `DATABASE_URL` takes effect. Used by tests."""
    global _availability
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    with _availability_lock:
        _availability = None
