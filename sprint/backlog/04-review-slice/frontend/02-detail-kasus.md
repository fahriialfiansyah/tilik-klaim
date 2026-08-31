# Task 02 — Case detail, evidence trace, and disposition panel

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`./01-antrean-review.md`](./01-antrean-review.md) — entered from the queue
- [`../backend/02-disposition-audit.md`](../backend/02-disposition-audit.md) — disposition write path

## Goal

One screen where an operator understands a single reason and records a defensible action.

## Files to touch

- `apps/web/src/pages/case-detail/CaseDetailPage.tsx`
- `apps/web/src/features/review/case-detail/components/` — header, claim lines, reason cards, evidence trace, timeline, comparison drawer, disposition panel, audit tab
- `apps/web/src/features/review/case-detail/store.ts`

## Skills to consult

- `sprint/00-app-spec.md` § 4 — widgets 1–27 and the five binding display rules
- `brief/04_DETAIL_KASUS_DISPOSISI.md` § 2, § 4

## TODOs

- [x] Header above the fold: case ID, status, amount, encounter window, primary reason, confidence basis, four action buttons
- [x] **Reason before score** — primary reason sits above the confidence basis in visual and reading order
- [x] Claim-line list with four support states, including *cannot be assessed* distinct from *unsupported*
- [x] Reason cards ordered by evidence strength; strongest opens on load
- [x] Expected evidence vs found evidence, with every reference openable
- [x] **Counter-evidence given equal standing** — never hidden behind a collapsed panel
- [x] Episode timeline
- [x] Evidence path kept small and single-track, not a tangled network
- [x] Source-resource panel showing raw resource plus rule and model version
- [x] Comparison drawer for repeat and clone candidates, with matched and differing fields
- [x] Template warning readable **before** the action buttons on clone reasons
- [x] Similarity highlights never expose another participant's identity
- [x] Disposition panel: four actions, structured reason, free-text note
- [x] Save disabled until action **and** reason are both filled
- [x] "Confirm anomaly" opens a confirmation stating this is **not** a fraud finding
- [x] "Request evidence" pre-selects missing resources but stays editable
- [x] Optimistic locking on case version
- [x] Audit tab rendering the event timeline
- [x] **Edge case — stale case:** save rejected, operator input **preserved**, reload offered
- [x] **Edge case — API failure on save:** honest error, input preserved, retry available
- [x] **Edge case — long text:** truncation with expand, no layout break
- [x] **Edge case — multiple reasons:** all cards listed, ordered
- [x] **Edge case — no counter-evidence:** section states none was found, rather than vanishing
- [x] **Test — Playwright happy path:** queue → detail → disposition → audit event visible
- [x] **Test — Playwright false-positive path:** counter-evidence leads to reject-signal
- [x] **Test — Playwright error path:** stale version rejected without losing input
- [x] **Test — accessibility smoke:** the whole flow is keyboard-operable, focus returns sensibly from the drawer

## Done when

The full path — queue → case detail → disposition → audit event — completes on the seeded
phantom fixture in under 90 seconds internally; a save on a stale version is rejected without
losing operator input; and all three Playwright paths pass.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/web.md`

## Notes

27 widgets makes this the densest page in the app. The density is deliberate: splitting it
across screens breaks the "one screen to resolve one reason" contract that the whole
workflow is built on.
