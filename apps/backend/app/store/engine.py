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

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

CONNECT_TIMEOUT_SECONDS = 5
"""Short: a demo that stalls on a dead database is worse than one that reports it."""


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
    """Whether the configured database answers. Used to choose a store, not to mask errors."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("select 1"))
    except SQLAlchemyError:
        return False
    return True


def reset_engine() -> None:
    """Drop the cached engine so a changed `DATABASE_URL` takes effect. Used by tests."""
    get_engine.cache_clear()
    get_session_factory.cache_clear()
