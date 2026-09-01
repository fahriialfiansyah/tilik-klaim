"""The suite must never run against the database a developer seeds.

Every store is cleared around every test, so pointing the suite at the development database
empties it — which is exactly what used to happen. The symptom was indirect and expensive: the
seed looked fine, the screens came up blank, and the cause was a `pytest` run somebody had done
twenty minutes earlier.

A redirect that works today and quietly stops working is worse than none, because the trap comes
back without the warning in the handover. These tests are the alarm.
"""
from __future__ import annotations

import pytest

from app.config import get_settings
from app.store.registry import use_database
from tests.conftest import TEST_DATABASE_SUFFIX, suite_database_url


@pytest.mark.skipif(not use_database(), reason="no database to be isolated from")
def test_the_suite_runs_against_its_own_database() -> None:
    """The one assertion that matters: this is not the database anyone seeds."""
    active = get_settings().database_url
    name = active.rpartition("/")[2].partition("?")[0]

    assert name.endswith(TEST_DATABASE_SUFFIX), (
        f"the suite is pointed at {name!r}; clearing stores would empty a developer's seeded data"
    )


def test_the_derived_url_changes_only_the_database_name() -> None:
    """Same server, same credentials, different database — nothing else may move."""
    source = "postgresql+psycopg://tilik:tilik@localhost:55432/tilik_klaim"

    derived = suite_database_url(source)

    assert derived == f"{source}{TEST_DATABASE_SUFFIX}"
    assert derived.rpartition("/")[0] == source.rpartition("/")[0]


def test_a_query_string_survives_the_derivation() -> None:
    """Managed providers append `?sslmode=require`; losing it would break the connection."""
    derived = suite_database_url("postgresql+psycopg://u:p@host/appdb?sslmode=require")

    assert derived == "postgresql+psycopg://u:p@host/appdb_test?sslmode=require"


def test_the_derivation_never_returns_the_source_database() -> None:
    """The redirect refuses to proceed when the two names match; this is why it can trust that."""
    for source in (
        "postgresql+psycopg://u:p@host/tilik_klaim",
        "postgresql+psycopg://u:p@host/x",
        "postgresql+psycopg://u:p@host/db?a=b",
    ):
        assert suite_database_url(source) != source
