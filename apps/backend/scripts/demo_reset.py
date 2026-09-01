#!/usr/bin/env python3
"""Return the system to the known seeded state the demo runbook expects.

    uv run python scripts/demo_reset.py            # reset, then verify
    uv run python scripts/demo_reset.py --check    # verify only, change nothing

`docs/canonical/08_demo_runbook.md` § Demo reliability asks for one-click scripts for start,
health check, seed, and reset, and for a warm application reset to a known state before
presenting. This is the reset and the check.

**Idempotent by construction.** Every store is emptied before anything is written, so running it
twice leaves the same five cases rather than ten. Clearing bundles alone once left the previous
run's cases behind pointing at ingestion ids that no longer existed, and case detail answered
with no claim lines on data that looked freshly seeded — the stores are cleared together for
that reason.

**It verifies rather than assumes.** Seeding that "succeeded" while the phantom fixture screened
to nothing would be discovered on stage. The exit code is what a pre-demo check reads, so a bad
state is a non-zero exit and a named problem, never a cheerful log line.

It seeds from `tests/fixtures/`, as `seed_dev.py` and `export_demo_samples.py` already do: those
five files *are* the gold demo fixtures, and a second copy under `scripts/` would be a second
copy to drift.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.service.demo_state import DEMO_REASON, EXPECTED_CASE_COUNT, check_readiness  # noqa: E402
from app.store.registry import (  # noqa: E402
    get_audit_store,
    get_bundle_store,
    get_case_store,
    get_edge_store,
)
from tests.fixtures import SCENARIOS, load  # noqa: E402

SLOW_RESET_SECONDS = 15.0
"""Above this the reset is too slow to run between rehearsals, and says so rather than hiding it."""


def reset() -> tuple[int, float]:
    """Empty every store and re-seed the five gold scenarios. Returns count and elapsed seconds."""
    started = time.perf_counter()

    # Together, and bundles last: a case pointing at a deleted ingestion is worse than no case.
    for store in (get_case_store(), get_audit_store(), get_edge_store(), get_bundle_store()):
        store.clear()

    client = TestClient(app)
    seeded = 0
    for scenario in SCENARIOS:
        fixture = load(scenario)
        # History first: the cross-claim rules read it back out of the store.
        for prior in fixture.history:
            client.post("/v1/bundles", json=prior.model_dump(mode="json"))

        ingested = client.post(
            "/v1/bundles", json=fixture.bundle.model_dump(mode="json")
        ).json()
        screened = client.post(
            f"/v1/bundles/{ingested['ingestion_id']}/screen", json={}
        ).json()
        seeded += 1

        codes = ", ".join(reason["code"] for reason in screened["reasons"]) or "—"
        print(f"  {scenario:10s} {screened['band']['band']:22s} {codes}")

    return seeded, time.perf_counter() - started


def report(elapsed: float | None = None) -> int:
    """Print the readiness assessment and return the exit code a pre-demo check should use."""
    readiness = check_readiness()
    print(f"\nkesiapan  {readiness.summary()}")
    print(
        f"kasus     {readiness.case_count}/{readiness.expected_case_count} tersemai, "
        f"{readiness.untouched_cases} belum dibuka"
    )
    print(
        f"versi     mesin {readiness.engine_version} · aturan {readiness.ruleset_version} "
        f"· data {readiness.dataset_version}"
    )
    print(f"simpanan  {readiness.persistence}")
    if elapsed is not None:
        note = "  (lambat untuk gladi bersih)" if elapsed > SLOW_RESET_SECONDS else ""
        print(f"durasi    {elapsed:.1f}s{note}")

    for problem in readiness.problems:
        print(f"  ! {problem}")
    return 0 if readiness.ready else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify readiness without resetting; exits non-zero when the demo would not work",
    )
    args = parser.parse_args()

    if args.check:
        return report()

    print(f"Menyemai ulang {EXPECTED_CASE_COUNT} skenario demo…")
    seeded, elapsed = reset()
    if seeded != EXPECTED_CASE_COUNT:
        print(f"\n! hanya {seeded} skenario tersemai, seharusnya {EXPECTED_CASE_COUNT}")
        return 1

    exit_code = report(elapsed)
    if exit_code == 0:
        print(f"\nSiap. Kasus demo mengangkat {DEMO_REASON.value}.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
