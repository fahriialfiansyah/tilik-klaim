# Task 01 — 90-second demo flow and fallback

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 🚧 In Progress
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

- [x] Playwright test walking the full path and asserting it finishes under 90 seconds
- [ ] Rehearse the three-minute flow with the same fixture
- [x] Screenshot: flagged case with its evidence path
- [x] Screenshot: human disposition and the resulting audit event
- [x] Screenshot: evaluation page with the limitations card visible
- [x] Case study: one true injected case — *draf di `docs/artifacts/case-studies.md`*
- [x] Case study: one false positive showing counter-evidence — *draf di `docs/artifacts/case-studies.md`*
- [ ] Recorded fallback that runs with the live application entirely down
- [x] Verify the synthetic badge is visible in **every** captured screenshot
- [x] Confirm no screenshot exposes anything resembling a real identifier

## Done when

The Playwright run completes the full path under 90 seconds offline; all five artifacts are
captured with the synthetic badge visible; and the fallback has been rehearsed at least once
with the application stopped.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/web.md`

## Notes

**Done, and machine-checkable.** `apps/web/tests/e2e/demo-flow.spec.ts` — three tests, ~3.5s:
the full ninety-second path timed against a budget, the evaluation beat of the three-minute
flow inside its twenty-second slot, and every demo route walked with **every non-localhost
request aborted**. The full E2E suite is 17.

Four artifacts captured to `docs/artifacts/screenshots/`: the flagged case with its evidence
path, the clone false positive with its counter-evidence, the disposition with the resulting
audit event, and the evaluation page with the limitations card. The capture script asserts on
every page that the synthetic badge is present and that nothing matching a 13- or 16-digit
identifier or the string `NIK` appears — checked rather than eyeballed.

**The budget is asserted, not assumed.** A flow that works but takes two minutes fails on stage
as surely as one that errors, and it fails in front of judges. The machine finishes in about
3.5s; the test holds it under 30s, leaving two thirds of the runbook's ninety for the person
speaking. Passing here is necessary, not sufficient — the machine does not narrate or move a
cursor.

**The spec resets itself.** Requesting evidence moves the demo case out of the state the flow
starts from, so a second run would find it already dispositioned. `test.beforeAll` runs
`scripts/demo_reset.py`, which makes the test repeatable and rehearses the reset at the same
time. The sprint's acceptance says the flow completes *from a clean reset*; this is that.

**Two behaviours the runbook does not describe, found by walking it.** Requesting evidence hands
the reviewer to `/ingest?case=…` rather than back to the queue — which is right, since that is
where the facility's replacement bundle arrives, and it is a better beat than the runbook's. And
the audit timeline reads in working language, so the test asserts *Disposisi dicatat* rather than
the raw `DISPOSITION` enum; `OPENED` once shipped untranslated into an otherwise Indonesian
history, and asserting on the enum would have let that back in.

## Still owed — a person's, not the agent's

The task header says *Autonomous: no — rehearsal and capture done by a person*, and these four
are why:

- **Rehearse the three-minute flow** end to end with narration, on the presentation machine,
  offline. The Playwright run is not a rehearsal.
- ~~Two written case studies~~ — **drafted** in `docs/artifacts/case-studies.md`: the phantom
  case the demo uses, and `BND-051b94e85142`, a clean claim flagged at similarity 0.889 by
  templating. Paired deliberately, because the question after the first is always "and when it
  is wrong?". Pending M3 validation.
- ~~The six-frame screenshot PDF~~ — **generated** as `docs/artifacts/demo-fallback-6-frames.pdf`,
  A4 landscape, each frame captioned with the presenter's line and carrying the synthetic badge.
- **The recorded fallback**, at 1080p with the same narration and cursor path, rehearsed at
  least once with the application stopped. § 22 is explicit that the fallback is played, not
  troubleshooted, so it has to exist before the day. **This one genuinely needs a person** — a
  screen recorder and a voice.
