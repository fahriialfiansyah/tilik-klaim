# Task 01 — Case list and case detail endpoints

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`../../03-evidence-rules/backend/02-rule-engine.md`](../../03-evidence-rules/backend/02-rule-engine.md) — serves what the engine produced

## Goal

Serve the queue and the case detail with pseudonymous fields only, honouring the frozen
contract.

## Files to touch

- `apps/backend/app/router/cases.py` — `GET /v1/cases`, `GET /v1/cases/{id}`
- `apps/backend/app/service/case_query.py` — filtering, sorting, pagination
- `apps/backend/tests/test_case_endpoints.py`

## TODOs

- [x] `GET /v1/cases` with state, reason, priority, and date filters
- [x] Paginated queue summary — **pseudonymous fields only**
- [x] **No raw medical text in the list response**
- [x] `GET /v1/cases/{id}` returning claim lines, reasons, graph/timeline, comparisons, counter-evidence, versions
- [x] Reason sentences come from the catalog, so queue and detail can never disagree
- [x] Case version included for optimistic locking
- [x] **Test:** the list response contains no raw medical text field
- [x] **Test:** every evidence reference in the detail response resolves
- [x] **Test:** pagination bounds hold under a large queue

## Done when

Both endpoints match the frozen contract; the list response is provably free of raw medical
text; and every evidence reference in the detail response resolves to a real resource.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/backend.md`

## Notes

**The no-medical-text assertion is made against the serialised response, not field by field.** A
future field that accidentally carried a note would slip past a field-name check. The test
compares four-word phrases from the fixture note rather than single words: reason sentences come
from the catalog and legitimately share common Indonesian words with clinical notes, so matching
on `dengan` would fail on the catalog's own wording and prove nothing about leakage.

**`NOT_ASSESSABLE` is kept distinct from `UNSUPPORTED`.** "We could not judge this" and "the
evidence is absent" lead to different actions — requesting a document versus questioning whether
a service happened. A thin bundle marks its lines not-assessable; only a complete one can mark
them unsupported.

Queue order is band first, then **oldest first within a band**. Sorting purely by band would let
an old case sit behind a stream of newer ones indefinitely.

Both endpoints read the stored screening result rather than re-screening. A case explained under
a newer ruleset than the one that raised it would answer a different question than the reviewer
is looking at, and the audit event citing it would no longer match.
