# Task 01 — Assistant service, guards, gate, and SSE endpoint

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes — additive; no earlier contract moves.
**Depends on:**
- [`../../09-case-briefing/backend/01-briefing-service-and-endpoint.md`](../../09-case-briefing/backend/01-briefing-service-and-endpoint.md)

## Goal

`POST /v1/assistant/answers`, off by default, template-first, model-optional, gated.

## Files to touch

- `app/dto/assistant.py` — question, scope, citations, statements, case cards, answer, SSE events
- `app/service/assistant/{context,citations,intents,queue_tools,template,validation,runner,service,wording}.py`
- `app/router/assistant.py`, `app/main.py`, `app/config.py`, `app/errors.py`, `app/service/access.py`, `.env.example`
- `docs/api/openapi.json`, `apps/web/src/features/auth/access-matrix.json` — regenerated

## TODOs

- [x] ADR-0007 written and accepted before code
- [x] Deterministic refusal guard (ID + EN, NFKC, zero-width stripped) runs before any model
- [x] Template answers for nine intents over five gold scenarios, both languages, every citation openable
- [x] Queue projections carry screen labels, never enum codes or participant/provider tokens
- [x] Planned reads + one guided-decoding call; `citations` enum of ids read, `minItems: 1`
- [x] Gate: citations resolve · whole-number match on tool output · ID + EN lexicon · machine tokens · caps · note
- [x] History quoted as untrusted context; poisoned turns dropped; concurrency cap on model calls
- [x] `ASK_ASSISTANT` capability for reviewer + senior reviewer; administrator refused
- [x] Isolation AST guard; frozen-paths test names the endpoint
- [x] 171 new tests; full suite 690 green; ruff clean on touched files
- [x] Real-gateway run measured and recorded in ADR-0007 § As implemented
