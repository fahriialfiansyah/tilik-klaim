"""`/healthz` must not pay for a dead database on every request.

Measured before this existed: with Postgres unreachable, every `/healthz` took 10.1 seconds
(two addresses for `localhost`, five seconds of `connect_timeout` each), while a route that never
touches the database took 0.2. The platform probes this path, and the probe is fastest to retry
exactly when the database is down.
"""
from __future__ import annotations

import itertools
import time

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.store import engine
from app.store.registry import use_database


@pytest.fixture(autouse=True)
def clean_reading():
    engine.reset_engine()
    yield
    # A background refresh that outlives its test would write its answer into the next one's
    # reading, so wait for it before clearing.
    deadline = time.monotonic() + 3
    while engine._refreshing and time.monotonic() < deadline:
        time.sleep(0.02)
    engine.reset_engine()


def wait_for_refresh() -> None:
    deadline = time.monotonic() + 3
    while engine._refreshing and time.monotonic() < deadline:
        time.sleep(0.02)


def test_a_second_reading_reuses_the_first_instead_of_probing_again(monkeypatch) -> None:
    probes: list[int] = []
    monkeypatch.setattr(engine, "is_database_available", lambda: probes.append(1) or False)

    readings = [engine.database_availability() for _ in range(5)]

    assert readings == [False] * 5
    assert len(probes) == 1


def test_a_stale_reading_is_served_at_once_and_refreshed_once_in_the_background(
    monkeypatch,
) -> None:
    answers = itertools.chain([False, True], itertools.repeat(True))
    probes: list[int] = []

    def slow_probe() -> bool:
        probes.append(1)
        time.sleep(0.4)
        return next(answers)

    monkeypatch.setattr(engine, "is_database_available", slow_probe)
    monkeypatch.setattr(engine, "HEALTH_PROBE_TTL_SECONDS", 0.0)

    assert engine.database_availability() is False, "the first reading has nothing to serve"

    started = time.perf_counter()
    burst = [engine.database_availability() for _ in range(10)]
    elapsed = time.perf_counter() - started

    assert burst == [False] * 10, "the stale answer, until the refresh lands"
    assert elapsed < 0.2, f"ten stale readings took {elapsed:.2f}s; they must not wait on a probe"

    wait_for_refresh()
    assert len(probes) == 2, "ten callers, one refresh"
    assert engine.database_availability() is True


def test_healthz_stays_fast_while_a_dead_database_is_slow_to_answer(monkeypatch) -> None:
    use_database()  # the process-wide store choice is made once, before any request is timed

    def slow_dead_database() -> bool:
        time.sleep(1.0)
        return False

    monkeypatch.setattr(engine, "is_database_available", slow_dead_database)
    monkeypatch.setattr(engine, "HEALTH_PROBE_TTL_SECONDS", 0.0)
    engine.database_availability()  # the one reading that is allowed to wait

    started = time.perf_counter()
    response = TestClient(app).get("/healthz")
    elapsed = time.perf_counter() - started

    assert response.status_code == 200
    assert response.json()["readiness"]["database_reachable"] is False
    assert elapsed < 0.5, f"/healthz took {elapsed:.2f}s with a database that needs 1s to answer"
