# Task 01 — "Asisten Bukti" page at `/assistant`

**Stack:** frontend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`../backend/01-assistant-service-and-endpoint.md`](../backend/01-assistant-service-and-endpoint.md)

## Files to touch

- `src/features/review/assistant/{types,api,conversation,store,useAskAssistant,useQueueCases,useSourceDrawer,labels}.ts`
- `src/features/review/assistant/components/{AnswerView,CaseCards,Citations,Composer,ContextPanel,EmptyState,ReadingSteps,ScopePicker,SuggestionChips,TurnView}.tsx`
- `src/pages/assistant/AssistantPage.tsx`, `src/App.tsx`, `src/config/menu/app-menu.ts`, `src/components/layouts/MenuIcons.tsx`
- `src/components/layouts/PageShell.tsx` (`height="fill"`), `src/components/wrappers/PerfectScrollArea.tsx` (`containerRef`)
- `src/lib/sse.ts` (shared parser; the briefing delegates to it), `src/lib/http.ts` (`requestHeaders`)
- `src/locales/{id,en}/{assistant,menu,auth}.json`, `src/features/auth/matrix.ts`
- `tests/e2e/assistant.spec.ts`, `tests/e2e/assistant-model.spec.ts`, `tests/e2e/auth-roles.spec.ts`

## TODOs

- [x] Menu entry for reviewer + senior reviewer, drawn icon (balloon + citation bracket), route wired
- [x] Empty state with scope-aware suggestions; scope picker; deep link `?case=`
- [x] Streamed reading steps → statements with numbered citations → sources → case cards → uncertainty → provenance
- [x] Resource citations open the shared source drawer; cases and the queue are real links
- [x] Refusal / not-recognised / failure states in words; codes behind *Detail teknis*
- [x] Stop, retry in the turn's own scope, new conversation; conversation cleared on persona change
- [x] No "AI", no robot or sparkle; no import from the disposition store (asserted on source)
- [x] Light, dark, English, and 1024 px checked by eye; QA shots in `docs/qa/2026-10-02-asisten-bukti/`
- [x] 38 new vitest; 13 + 4 new Playwright; tsc clean; full unit suite 428 green
