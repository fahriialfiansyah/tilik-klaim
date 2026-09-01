"""Demo readiness, and the difference between "alive" and "ready to present".

`docs/canonical/08_demo_runbook.md` § Demo reliability asks for a health check that runs before
anyone presents. The failure it exists to prevent is a running service pointed at an empty
database: alive by every liveness definition, and unable to complete the ninety-second flow.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from tilik_domain.reasons import CaseState

from app.main import app
from app.service import demo_state
from app.service.demo_state import DEMO_REASON, EXPECTED_CASE_COUNT, check_readiness
from app.store.registry import get_case_store

client = TestClient(app)


@pytest.fixture
def seeded():
    """Reset to the five gold scenarios, exactly as `scripts/demo_reset.py` does."""
    import scripts.demo_reset as reset_script

    reset_script.reset()
    yield
    get_case_store().clear()


def test_liveness_never_depends_on_the_database(monkeypatch) -> None:
    """`railway.json` probes this path. A 5xx when Postgres blips restarts the container.

    The restart loop would happen precisely when the database is already struggling, which is
    the worst possible moment to take the API down as well.
    """
    monkeypatch.setattr(demo_state, "is_database_available", lambda: False)
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_an_unreachable_database_is_reported_loudly_rather_than_as_a_false_ok(
    monkeypatch,
) -> None:
    """The status stays `ok`; readiness must not."""
    monkeypatch.setattr(demo_state, "is_database_available", lambda: False)
    readiness = client.get("/healthz").json()["readiness"]

    assert readiness["ready"] is False
    assert readiness["database_reachable"] is False
    assert any("basis data" in problem for problem in readiness["problems"])


def test_an_empty_system_is_not_ready_and_says_what_to_run() -> None:
    """A cheerful "ok" on an empty database is the exact failure this check exists to prevent."""
    get_case_store().clear()
    readiness = check_readiness()

    assert readiness.ready is False
    assert readiness.case_count == 0
    assert any("demo_reset" in problem for problem in readiness.problems)


def test_the_health_check_reports_seed_count_and_engine_version(seeded) -> None:
    payload = client.get("/healthz").json()

    assert payload["engine_version"]
    assert payload["ruleset_version"]
    assert payload["data_class"] == "synthetic"
    assert payload["readiness"]["case_count"] == EXPECTED_CASE_COUNT
    assert payload["readiness"]["ready"] is True


def test_after_reset_the_phantom_fixture_screens_to_the_expected_reason(seeded) -> None:
    """The runbook's ideal case. If this reason is missing the ninety-second flow has no story."""
    raised = {
        reason.code
        for case in get_case_store().list_all()
        for reason in case.result.reasons
    }
    assert DEMO_REASON in raised


def test_reset_is_idempotent(seeded) -> None:
    """Running it twice must leave five cases, not ten."""
    import scripts.demo_reset as reset_script

    first = {case.case_id for case in get_case_store().list_all()}
    assert len(first) == EXPECTED_CASE_COUNT

    reset_script.reset()
    second = get_case_store().list_all()

    assert len(second) == EXPECTED_CASE_COUNT
    assert not first & {case.case_id for case in second}, "old case ids survived the reset"


def test_an_opened_demo_case_makes_the_system_not_ready(seeded) -> None:
    """A demo starts from untouched cases. A case someone already opened is a different demo."""
    store = get_case_store()
    for case in store.list_all():
        if any(reason.code is DEMO_REASON for reason in case.result.reasons):
            store.save(case.model_copy(update={"state": CaseState.IN_REVIEW}))

    readiness = check_readiness()
    assert readiness.demo_case_present is False
    assert readiness.ready is False


def test_the_check_mode_exit_code_is_what_a_pre_demo_script_reads(seeded) -> None:
    """Loud means a non-zero exit, not a log line somebody has to notice."""
    import scripts.demo_reset as reset_script

    assert reset_script.report() == 0

    get_case_store().clear()
    assert reset_script.report() == 1


def test_a_process_on_memory_while_the_database_is_up_is_reported(monkeypatch) -> None:
    """The failure this check actually caught: started before Postgres, cached that choice.

    `use_database()` caches for the life of the process on purpose, so two stores can never
    disagree about where an ingestion lives. The consequence is that a seed script writing to
    Postgres and an API serving memory are two different worlds, and every screen looks
    plausibly wrong. Re-seeding does not help; only a restart does, and the check must say so.
    """
    monkeypatch.setattr(demo_state, "use_database", lambda: False)
    monkeypatch.setattr(demo_state, "is_database_available", lambda: True)

    readiness = check_readiness()

    assert readiness.ready is False
    assert readiness.database_reachable is True
    assert readiness.persistence == "in-memory"
    assert any("Mulai ulang API" in problem for problem in readiness.problems)
