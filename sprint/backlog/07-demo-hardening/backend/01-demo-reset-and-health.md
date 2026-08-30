# Task 01 — Seeded demo reset and health checks

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
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

- [ ] One command resets to the five seeded cases in a known state
- [ ] Reset is idempotent — running it twice is safe
- [ ] Health check reports database reachability, seeded-case count, and engine version
- [ ] **Every demo route works with no external network** — verified with networking disabled
- [ ] Reset completes fast enough to run between rehearsals
- [ ] **Test:** after reset, the phantom fixture screens to the expected reason
- [ ] **Test:** the health check fails loudly when the database is down, rather than reporting a false OK

## Done when

Reset restores all five seeded cases; the health check reports database, seed count, and
version; and the full demo path works with networking disabled.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/backend.md`
