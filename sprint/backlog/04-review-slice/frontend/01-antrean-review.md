# Task 01 — Review queue page

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`../../02-ingest-validation/backend/00-api-contract.md`](../../02-ingest-validation/backend/00-api-contract.md) — built against the **live seeded API**, not fixtures: the endpoints were already complete

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

- [x] Exactly five metric cards — awaiting review, deterministic conflicts, evidence-requested, median time in queue, engine/dataset version
- [x] Clicking a metric card applies its filter to the table
- [x] Column order: **reason sentence first**, before any score or amount — asserted by a test that reads the header order back
- [x] Mode chips, pseudonymous case ID, evidence-completeness indicator, amount, age, priority band, status
- [x] Sort by priority, age, amount, evidence completeness — **server-side**; see Notes
- [x] Filters: status, mode, priority band, date range — combinable, all server-side
- [x] Active filters render as individually removable chips
- [x] Search by pseudonymous case ID only
- [x] Priority-band tooltip answers "why this band?" — one basis sentence per band, in working language
- [x] Pagination — never fetch the whole queue; every request carries `page` and `page_size=25`
- [x] Filters and sort survive returning from case detail — verified in the browser, not just by reading the store
- [x] **Edge case — no cases at all:** empty state pointing to Ingest
- [x] **Edge case — empty from filters:** names the filters and offers to clear them
- [x] **Edge case — loading:** skeleton, not a blank table
- [x] **Edge case — API failure:** honest error plus retry, never a blank table posing as "no cases" — verified by stopping the API
- [x] **Test — component:** the four empty/error states render distinctly
- [x] **Test — accessibility smoke:** keyboard navigation, visible focus, no colour-only status

## Done when

The queue renders from committed fixtures with the reason sentence in the first column; all
four empty and error states are visually distinct; and filters plus sort survive a round
trip to case detail and back.

> Forbidden here: aggregate charts, provider league tables, national projections, "fraud
> saved", or rupiah "recovered". `docs/canonical/01_product_decision.md` § Main dashboard
> principles rules these out explicitly.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/web.md`

## Notes

**Two query parameters were added to `GET /v1/cases`** — `mode` and `sort`/`order` — because
both of this page's requirements are unimplementable correctly without them. The response is
paginated, so filtering by mode or re-ordering in the client would act on one page and silently
ignore every match on the others: a reviewer sorting by amount would not be looking at the
largest amounts at all. Both additions are backward-compatible query parameters and change no
wire model, so the frozen contract in `02-ingest-validation/backend/00-api-contract.md` still
holds. Ten backend tests cover them.

**The band sort deliberately ignores `order`.** Reversing it would put "tidak ada risiko
teramati" at the top of a work list, which is a reading the system is not entitled to offer.
The server refuses the inversion and the UI does not draw the arrow.

**Search is a server-side filter too.** It was briefly client-side, and code review caught what
that cost: applied to an already-paginated page, a term matching only a case on page 2 emptied
page 1 and the empty state that followed offered nothing but "clear the filters" — the case was
unreachable. `search` is now a query parameter narrowing the whole queue. It matches the
pseudonymous case identifier alone; there is no name or national-ID field anywhere in this
system to search by.

**Code review also found the queue and the case detail disagreeing about evidence completeness
on every case** — see `changelog/backend.md`. The billed-line count is now recorded on the case
at screening (migration `d1a7c3e50f42`) instead of being inferred from the number of unsupported
lines, which had made `supported_lines` zero by construction.

**All four empty/error states were verified in the browser, not only by test.** "No cases at
all" needs an empty database, which `uv run pytest` produces as a side effect — it clears the
dev database, so running it and reloading the page shows the real state. Re-seed with
`scripts/seed_dev.py` afterwards.
