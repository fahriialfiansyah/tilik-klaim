# Task 01 — Briefing service, tools, validator, and SSE endpoint

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes — additive; no frozen contract moves.
**Depends on:**
- [`../../08-evidence-workspace/frontend/01-evidence-workspace.md`](../../08-evidence-workspace/frontend/01-evidence-workspace.md)

## Goal

`GET /v1/cases/{case_id}/briefing`, off by default, template-first, LLM-optional, validated.

## Files to touch

- `app/dto/briefing.py` — `CaseBriefing`, observations, questions, SSE event models
- `app/service/case_loader.py` — `load_case_detail`, shared by the cases router and the briefing
- `app/service/briefing/{tools,template,validation,runner,service,labels}.py`
- `app/service/llm_provider.py` — the one `httpx` call; OpenAI-compatible chat completions
- `app/router/briefing.py`, `app/main.py`, `app/config.py`, `app/errors.py`, `pyproject.toml`, `.env.example`
- `docs/api/openapi.json` — regenerated

## TODOs

- [x] Template path complete and passing the validator **before** any LLM code
- [x] Seven read-only tools; closed registry; unknown name refused before dispatch
- [x] Five gates: refs resolve · numbers supplied · lexicon · caps · uncertainty note
- [x] Bounded runner: ≤ `BRIEFING_MAX_TOOL_CALLS` reads, one `submit_briefing`, whole-object fallback
- [x] SSE endpoint with `X-Accel-Buffering: no`; `?stream=false` equals the stream terminal
- [x] Import-direction AST guard (risk path → briefing: never)
- [x] 65 new tests; 338 existing unchanged; ruff clean
- [x] `httpx` promoted to a runtime dependency; `uv.lock` updated
