# Task 01 — Case list and case detail endpoints

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
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

- [ ] `GET /v1/cases` with state, reason, priority, and date filters
- [ ] Paginated queue summary — **pseudonymous fields only**
- [ ] **No raw medical text in the list response**
- [ ] `GET /v1/cases/{id}` returning claim lines, reasons, graph/timeline, comparisons, counter-evidence, versions
- [ ] Reason sentences come from the catalog, so queue and detail can never disagree
- [ ] Case version included for optimistic locking
- [ ] **Test:** the list response contains no raw medical text field
- [ ] **Test:** every evidence reference in the detail response resolves
- [ ] **Test:** pagination bounds hold under a large queue

## Done when

Both endpoints match the frozen contract; the list response is provably free of raw medical
text; and every evidence reference in the detail response resolves to a real resource.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/backend.md`
