"""Shared fixtures, and the redirect that keeps the suite off the development database.

**The suite runs against its own database.** Every store is cleared around every test, and the
stores are process-wide singletons bound to whatever `DATABASE_URL` points at — so before this
existed, `uv run pytest` emptied the developer's seeded data as a side effect. That cost real
time repeatedly: the seed looked fine, the screens came up blank, and the cause was a test run
somebody had done twenty minutes earlier.

The redirect happens in `pytest_configure`, before any test module is imported, because several
modules evaluate `skipif(not use_database())` at **collection** time. Redirecting later would
leave those decisions made against the wrong database.

If the server cannot be reached, or the test database cannot be created, nothing is redirected
and the suite behaves exactly as it did before — the integration tests skip. A missing database
is a supported configuration here: the frontend team runs these tests without one.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

TEST_DATABASE_SUFFIX = "_test"
"""Appended to the configured database name. Never the same database the developer seeds."""

MAINTENANCE_DATABASE = "postgres"
"""Connected to only in order to issue `CREATE DATABASE`, which cannot run inside a transaction."""


def pytest_configure(config: pytest.Config) -> None:
    """Point the suite at its own database before a single test module is imported."""
    redirect_to_test_database()


def suite_database_url(configured: str) -> str:
    """The suite's own database on the same server: the configured name plus a suffix.

    Deliberately not named `test_…`: pytest collects any module-level `test_*` callable it can
    import, and a helper imported into a test module would be run as a test with no arguments.
    """
    base, _, name = configured.rpartition("/")
    database, _, query = name.partition("?")
    suffixed = f"{database}{TEST_DATABASE_SUFFIX}"
    return f"{base}/{suffixed}" + (f"?{query}" if query else "")


def redirect_to_test_database() -> str | None:
    """Create the test database if needed and repoint the app at it. Returns the URL, or `None`.

    `None` means the server did not answer or the database could not be created — in which case
    the suite is left pointing where it was and the integration tests skip, as they always have.
    """
    from app.config import get_settings
    from app.store.engine import reset_engine
    from app.store.registry import reset_stores

    configured = get_settings().database_url
    target = suite_database_url(configured)
    if target == configured:
        # Refuse to run against the developer's database even if the suffix somehow collapsed.
        return None

    if not _ensure_database_exists(configured, target):
        return None

    os.environ["DATABASE_URL"] = target
    get_settings.cache_clear()
    reset_engine()
    reset_stores()

    if not _migrate(target):
        return None
    return target


def _ensure_database_exists(configured: str, target: str) -> bool:
    """`CREATE DATABASE` if it is absent. Idempotent, and silent when the server is unreachable."""
    name = target.rpartition("/")[2].partition("?")[0]
    maintenance = f"{configured.rpartition('/')[0]}/{MAINTENANCE_DATABASE}"
    try:
        engine = create_engine(
            maintenance, isolation_level="AUTOCOMMIT", connect_args={"connect_timeout": 5}
        )
        with engine.connect() as connection:
            exists = connection.execute(
                text("select 1 from pg_database where datname = :name"), {"name": name}
            ).scalar()
            if not exists:
                # Identifier quoting rather than a bind parameter: DDL cannot take one, and the
                # name is derived from configuration rather than from any request.
                connection.execute(text(f'create database "{name}"'))
        engine.dispose()
    except SQLAlchemyError:
        return False
    return True


def _migrate(target: str) -> bool:
    """Bring the test database to head. The same migrations the service runs, not a shortcut."""
    from alembic import command
    from alembic.config import Config

    root = Path(__file__).resolve().parents[1]
    try:
        config = Config(str(root / "alembic.ini"))
        config.set_main_option("script_location", str(root / "migrations"))
        command.upgrade(config, "head")
    except Exception:  # noqa: BLE001 - any migration failure means fall back to skipping
        return False
    return True


@pytest.fixture(autouse=True)
def clean_stores():
    """Empty every store around every test.

    They are process-wide singletons and, against Postgres, genuinely shared state — a test that
    leaves rows behind changes the next test's answer.
    """
    from app.store.registry import (
        get_audit_store,
        get_bundle_store,
        get_case_store,
        get_edge_store,
    )

    stores = (get_bundle_store(), get_case_store(), get_audit_store(), get_edge_store())
    for store in stores:
        store.clear()
    yield
    for store in stores:
        store.clear()


@pytest.fixture
def api() -> TestClient:
    from app.main import app

    return TestClient(app)
