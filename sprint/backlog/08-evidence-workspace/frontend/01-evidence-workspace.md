# Task 01 — Evidence Workspace on `/cases/:id`

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes — presentation over an unchanged contract.
**Depends on:**
- [`../../04-review-slice/frontend/02-detail-kasus.md`](../../04-review-slice/frontend/02-detail-kasus.md)

## Goal

Reorganise the case detail into four coordinated views over one selection, per ADR-0004.

## Files to touch

- `src/features/review/case-detail/store.ts` — workspace slice: selection + drawer union
- `src/features/review/case-detail/selectors.ts` — `buildEvidenceMatrix`, `swimlanes`, `mapForReason`
- `src/features/review/case-detail/components/EvidenceMatrix.tsx` — widget 28 (new)
- `src/features/review/case-detail/components/EpisodeSwimlane.tsx` — widget 14 (replaces `EpisodeTimeline.tsx`)
- `src/features/review/case-detail/components/EvidenceMap.tsx` — widget 15 (replaces `EvidencePath.tsx`)
- `src/features/review/case-detail/components/CaseDrawerHost.tsx` — widgets 16 · 23 · 24 host (new)
- `src/features/review/case-detail/labels.ts` — cell states, lanes, map captions
- `src/pages/case-detail/CaseDetailPage.tsx` — composition only
- `sprint/00-app-spec.md` § 4 — widget 28, re-worded 14 and 15
- `changelog/web.md`, `docs/qa/MANUAL-QA.md`

## Skills to consult

- `design/DESIGN.md` — four mandatory states plus *versi usang*; text label on every state
- `sprint/00-app-spec.md` § 4 *Aturan tampil (mengikat)*

## TODOs

- [x] Store: `workspace` slice; drawer is a discriminated union; drafts untouched by any workspace action
- [x] Selectors: matrix with four cell states; `missingEvidenceTypes()` ⊆ matrix `MISSING` columns
- [x] Selectors: four fixed lanes plus a client-derived *Penagihan* lane from `lines[].service_at`
- [x] Selectors: reason-focused map — one trunk, terminals per expected type, counter-track
- [x] `EvidenceMatrix` — real `<table>`, `<th scope>`, text label on every cell, claim-level row for reasons that cite no line
- [x] `EpisodeSwimlane` — shared time axis, empty lane drawn and labelled, every resource opens
- [x] `EvidenceMap` — dev-only single-parent invariant; no claim about missing evidence when no reason is open
- [x] `CaseDrawerHost` — one `Dialog`, source *or* comparison; existing drawer tests pass unmodified
- [x] Page rewire; delete `EvidencePath.tsx` and `EpisodeTimeline.tsx`
- [x] Vitest: 61 new tests green (168 total); 107 existing unchanged
- [x] Playwright: 17 existing green; +4 in `evidence-workspace.spec.ts` (drawn finding, reason-anchored map, keyboard matrix → drawer → back, one drawer at a time) — 21 total
- [x] `sprint/00-app-spec.md` § 4 updated; `design/DESIGN.md` one-line note
- [x] QA screenshots, five states × two themes, appended to `docs/qa/MANUAL-QA.md`
- [x] `changelog/web.md` entry with verified counts
