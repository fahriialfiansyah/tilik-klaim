# Task 01 — 90-second demo flow and fallback

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
**Foundation:** no
**Autonomous:** no — rehearsal and capture done by a person.
**Depends on:**
- [`../backend/01-demo-reset-and-health.md`](../backend/01-demo-reset-and-health.md)

## Goal

The ideal case travels ingest → evidence → detection → human review → audit in under 90
seconds, and a recorded fallback exists for when the live demo fails.

## Files to touch

- `apps/web/tests/e2e/demo-flow.spec.ts` — Playwright timing of the full path
- `docs/artifacts/screenshots/` — captured evidence for the proposal

## Skills to consult

- `docs/canonical/08_demo_runbook.md` — the 90-second and three-minute flows
- `docs/canonical/09_proposal_evidence_map.md` — which screenshot belongs on which slide

## TODOs

- [ ] Playwright test walking the full path and asserting it finishes under 90 seconds
- [ ] Rehearse the three-minute flow with the same fixture
- [ ] Screenshot: flagged case with its evidence path
- [ ] Screenshot: human disposition and the resulting audit event
- [ ] Screenshot: evaluation page with the limitations card visible
- [ ] Case study: one true injected case
- [ ] Case study: one false positive showing counter-evidence
- [ ] Recorded fallback that runs with the live application entirely down
- [ ] Verify the synthetic badge is visible in **every** captured screenshot
- [ ] Confirm no screenshot exposes anything resembling a real identifier

## Done when

The Playwright run completes the full path under 90 seconds offline; all five artifacts are
captured with the synthetic badge visible; and the fallback has been rehearsed at least once
with the application stopped.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/web.md`
