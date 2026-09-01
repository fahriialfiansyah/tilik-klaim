# Task 01 — Seeded demo reset and health checks

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes

## Goal

Make the demo repeatable: one command returns the system to a known seeded state, and a
health check confirms readiness before anyone presents.

## Files to touch

- `apps/backend/scripts/demo_reset.py`
- `apps/backend/app/router/health.py` — extend readiness reporting
- `docs/canonical/08_demo_runbook.md` — cross-check only; **canonical, read-only**

## TODOs

- [x] One command resets to the five seeded cases in a known state
- [x] Reset is idempotent — running it twice is safe
- [x] Health check reports database reachability, seeded-case count, and engine version
- [x] **Every demo route works with no external network** — verified with networking disabled
- [x] Reset completes fast enough to run between rehearsals
- [x] **Test:** after reset, the phantom fixture screens to the expected reason
- [x] **Test:** the health check fails loudly when the database is down, rather than reporting a false OK

## Done when

Reset restores all five seeded cases; the health check reports database, seed count, and
version; and the full demo path works with networking disabled.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/backend.md`

## Notes

**Files delivered.** `apps/backend/scripts/demo_reset.py` (reset and `--check`),
`app/service/demo_state.py` (readiness, no test-fixture dependency), `app/router/health.py`
extended, and `tests/test_demo_readiness.py` — 8 tests.

**The health check must not fail when the database does, and that is not a compromise.**
`railway.json` points its platform health probe at `/healthz`. Making that path return 5xx on an
unreachable database would restart the container in a loop *precisely when the database is
already struggling* — taking the API down on top of it. The backend is also designed to run with
no database at all, so the demo can be rehearsed offline; a probe that treated that as failure
would call a supported configuration broken.

So the two questions are answered separately. `/healthz` stays `200 · status: ok` while the
process is alive. The `readiness` block underneath reports database reachability, seeded-case
count, whether the runbook's ideal case is present and untouched, and a named problem for each
thing that is wrong. `scripts/demo_reset.py --check` reads that block and **exits non-zero** —
which is where "fails loudly" belongs, because a pre-demo check is a thing someone runs and
reads, and a container probe is not.

**Readiness checks the demo case, not just a row count.** Five cases in the database is not the
same as a demo that works: the ideal case must be present *and* in a state nobody has opened.
`test_an_opened_demo_case_makes_the_system_not_ready` holds that line — a case someone already
dispositioned is a different demo, and finding that out on stage is the failure this sprint
exists to prevent.

**Reset is idempotent by construction and takes 0.2–0.4s.** Every store is emptied together
before anything is written, so two runs leave five cases rather than ten, and no case is left
pointing at an ingestion that no longer exists — a defect this project has already had once.

It seeds from `tests/fixtures/`, as `seed_dev.py` and `export_demo_samples.py` already do: those
five files *are* the gold demo fixtures, and a second copy under `scripts/` would be a second
copy to drift. The coupling is worth naming, because a container image that excludes `tests/`
cannot run this script.

**Offline was verified by blocking the network, not by assuming it.**
`apps/web/tests/e2e/demo-flow.spec.ts` aborts every request whose host is not localhost and then
walks `/`, `/ingest`, and `/evaluation`; a request leaving the machine fails the run rather than
quietly succeeding because the presenter happened to have wifi.
