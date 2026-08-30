# Task 01 — Review queue page

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`../../02-ingest-validation/backend/00-api-contract.md`](../../02-ingest-validation/backend/00-api-contract.md) — builds against committed fixtures

## Goal

The operator's home screen: five operational metrics, filters, and a queue whose first
column is a readable reason sentence.

## Files to touch

- `apps/web/src/pages/queue/QueuePage.tsx`
- `apps/web/src/features/review/queue/components/` — metric cards, filter bar, queue table
- `apps/web/src/features/review/queue/store.ts` — Zustand store for filters and sort
- `apps/web/src/features/review/queue/api.ts`

## Skills to consult

- `sprint/00-app-spec.md` § 3 — widgets 1–11 and the binding column order
- `brief/03_ANTREAN_REVIEW.md` § 2, § 4.3

## TODOs

- [ ] Exactly five metric cards — awaiting review, deterministic conflicts, evidence-requested, median time in queue, engine/dataset version
- [ ] Clicking a metric card applies its filter to the table
- [ ] Column order: **reason sentence first**, before any score or amount
- [ ] Mode chips, pseudonymous case ID, evidence-completeness indicator, amount, age, priority band, status
- [ ] Sort by priority, age, amount, evidence completeness
- [ ] Filters: status, mode, priority band, date range — combinable
- [ ] Active filters render as individually removable chips
- [ ] Search by pseudonymous case ID only
- [ ] Priority-band tooltip answers "why this band?"
- [ ] Pagination — never fetch the whole queue
- [ ] Filters and sort survive returning from case detail
- [ ] **Edge case — no cases at all:** empty state pointing to Ingest
- [ ] **Edge case — empty from filters:** names the filters and offers to clear them
- [ ] **Edge case — loading:** skeleton, not a blank table
- [ ] **Edge case — API failure:** honest error plus retry, never a blank table posing as "no cases"
- [ ] **Test — component:** the four empty/error states render distinctly
- [ ] **Test — accessibility smoke:** keyboard navigation, visible focus, no colour-only status

## Done when

The queue renders from committed fixtures with the reason sentence in the first column; all
four empty and error states are visually distinct; and filters plus sort survive a round
trip to case detail and back.

> Forbidden here: aggregate charts, provider league tables, national projections, "fraud
> saved", or rupiah "recovered". `docs/canonical/01_product_decision.md` § Main dashboard
> principles rules these out explicitly.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/web.md`
