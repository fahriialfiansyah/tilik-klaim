# Task 03 — Ingest and seeded demo page

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`../../02-ingest-validation/backend/00-api-contract.md`](../../02-ingest-validation/backend/00-api-contract.md)

## Goal

Prove the system works from input — five seeded cases and JSON upload, with a validation
report and exactly one way forward.

## Files to touch

- `apps/web/src/pages/ingest/IngestPage.tsx`
- `apps/web/src/features/review/ingest/components/` — upload zone, seeded list, validation report

## Skills to consult

- `sprint/00-app-spec.md` § 5 — widgets 1–11
- `brief/01_INGEST_VALIDASI.md` § 2, § 4

## TODOs

- [ ] Drag-and-drop upload zone plus file picker
- [ ] Limits shown **before** upload, not after failure
- [ ] Five seeded cases listed: clean, phantom, repeat, clone, unbundled
- [ ] Validation status: valid · valid-with-notes · invalid
- [ ] Resource counts by type
- [ ] Error list with code, resource type, resource ID, explanation
- [ ] Completeness notes shown prominently on valid-with-notes
- [ ] Input hash displayed and copyable
- [ ] **One** "Screen claim" button — no configuration wizard of any kind
- [ ] Button disabled on invalid, with the reason stated
- [ ] Identical-bundle notice linking to the existing case
- [ ] **Edge case — oversized file:** rejected client-side before upload, with the limit named
- [ ] **Edge case — service failure:** honest error plus retry, never a hanging spinner
- [ ] **Test — component:** all three validation states render correctly
- [ ] **Test — Playwright:** select seeded phantom case → screen → land on case detail

## Done when

All five seeded cases load and screen without a network connection; the three validation
states render distinctly; and an invalid bundle disables the screen button with a specific
reason.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/web.md`
