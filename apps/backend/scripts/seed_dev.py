#!/usr/bin/env python3
"""Fill the development database with the five gold scenarios, ingested and screened.

Run it whenever you want rows to look at:

    cd apps/backend && uv run python scripts/seed_dev.py

**The test suite empties this database.** Its fixtures call `clear()` around every test, and
they run against whatever `DATABASE_URL` points at. So `uv run pytest` leaves you with empty
tables, and this script is how you get them back. That sharing is a rough edge worth fixing
later — tests should own a separate database — but knowing about it beats being surprised.

Nothing here is a demo runbook. `07-demo-hardening` owns the seeded demo and its reset route;
this is a developer convenience and says so.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.store.engine import is_database_available  # noqa: E402
from app.store.registry import (  # noqa: E402
    get_audit_store,
    get_bundle_store,
    get_case_store,
    get_edge_store,
    get_user_store,
)
from app.store.seed_users import seed_users  # noqa: E402
from tests.fixtures import SCENARIOS, load  # noqa: E402


def main() -> int:
    if not is_database_available():
        print("No database reachable. Start it first:")
        print("  docker compose up -d db && uv run alembic upgrade head")
        return 1

    # Every store is emptied, not just the bundles. Clearing bundles alone left the
    # previous run's cases behind pointing at ingestion ids that no longer existed, so
    # `GET /v1/cases/{id}` answered with empty `lines` and `timeline` — a case detail
    # screen with no claim lines on it, from data that looked seeded.
    for store in (get_case_store(), get_audit_store(), get_edge_store(), get_bundle_store()):
        store.clear()

    # The three synthetic staff go in before anything else: without them the login screen has
    # no account to accept, and a seeded database that cannot be signed into looks broken.
    user_store = get_user_store()
    user_store.clear()
    for staff in seed_users(user_store):
        print(f"  {staff.staff_token:8s} {staff.full_name:18s} {staff.role}")
    print()

    client = TestClient(app)
    for scenario in SCENARIOS:
        fixture = load(scenario)
        # History goes in first: cross-claim rules read it back out of the store.
        for prior in fixture.history:
            client.post("/v1/bundles", json=prior.model_dump(mode="json"))

        ingested = client.post(
            "/v1/bundles", json=fixture.bundle.model_dump(mode="json")
        ).json()
        screened = client.post(
            f"/v1/bundles/{ingested['ingestion_id']}/screen", json={}
        ).json()

        codes = ", ".join(reason["code"] for reason in screened["reasons"]) or "—"
        print(
            f"  {scenario:10s} {ingested['status']:16s} "
            f"{screened['band']['band']:22s} {codes}"
        )

    print("\nSeeded. Browse with:")
    print("  select ingestion_id, status, input_hash, case_id from ingestions;")
    print("  select edge_type, count(*) from evidence_edges group by 1 order by 2 desc;")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
