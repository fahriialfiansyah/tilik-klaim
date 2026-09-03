# Task 01 — "Ringkasan bukti" panel on `/cases/:id`

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`../backend/01-briefing-service-and-endpoint.md`](../backend/01-briefing-service-and-endpoint.md)

## Files to touch

- `src/features/review/case-briefing/{types,events,api,useCaseBriefing,labels}.ts`
- `src/features/review/case-briefing/components/{BriefingPanel,BriefingView,BriefingProgress}.tsx`
- `src/pages/case-detail/CaseDetailPage.tsx` — one slot, last in the middle column
- `src/env.d.ts` — `*?raw` module declaration for the source-guard tests
- `tests/e2e/case-briefing.spec.ts`

## TODOs

- [x] Collapsed by default; never auto-fetches; "Susun ringkasan" is the only way in
- [x] Pure SSE frame parser + event reducer, tested without a network
- [x] Stream via `fetch` + reader on the relative `/v1` base; `?stream=false` fallback, flagged on screen
- [x] Observations → questions → uncertainty → provenance, in that order; validator rejection stated
- [x] No action controls; no import from the disposition store (asserted on source)
- [x] Every reference opens through `EvidenceRefButton`; Escape returns focus
- [x] No robot / sparkle icon (asserted on source)
- [x] 16 new vitest; 3 new Playwright; tsc clean
- [x] QA screenshots `docs/qa/2026-09-03-case-briefing/`
