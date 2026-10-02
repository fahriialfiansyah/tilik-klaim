# Sprint 12 — Asisten Bukti (bounded, evidence-cited assistant)

**Status:** ✅ Done
**Created At:** 2026-10-02
**Gate:** — (post-submission) · **Deadline:** —
**Owner:** M1 — Engine & API (backend) · M2 — Product & UX (frontend)
**Source:** [ADR-0007](../../../docs/canonical/decisions/ADR-0007-evidence-assistant.md) · builds on [ADR-0005](../../../docs/canonical/decisions/ADR-0005-bounded-case-briefing.md)

## Goal

One more sidebar page — **Asisten Bukti / Evidence Assistant** — where a reviewer asks about the
queue or one case in free text and every answer is cited, gated, and incapable of acting on a
case. Template-first, model optional, off by default.

## Acceptance

- Nothing in the risk path imports the assistant; the assistant imports no store, rule, or
  screening code — the router hands it projections built by `to_summary` and
  `load_case_detail` (`tests/test_assistant_isolation.py`).
- Fraud, payment, sanction, diagnosis, identity, and set-the-limits-aside questions are refused
  **before any model is called**, in Indonesian and English (`test_assistant_intents.py`,
  `test_a_refused_question_never_reaches_the_model`).
- Every statement carries ≥ 1 citation that opens; the gate rejects unsupported numbers,
  accusations and directives (ID + EN), raw enum codes, and an empty uncertainty note — the
  whole answer falls back to the template on any failure.
- `ASSISTANT_ENABLED=false` by default and separate from `BRIEFING_ENABLED`; the template answers
  every suggestion chip on the page (a backend test reads the web locale to make sure).
- `POST /v1/assistant/answers` streams SSE; `?stream=false` equals the stream terminal. All
  earlier endpoints are untouched; the frozen-paths test names the new one with its ADR.
- The page has no control that acts on a case and imports nothing from the disposition store;
  no "AI", no robot, no sparkle; no machine token on the reading surface.

## Scope (stacks involved)

- [x] backend → see [`backend/`](./backend/) · [x] frontend → see [`frontend/`](./frontend/)

## Constraints (non-negotiable — apply to every task in this sprint)

Source: `docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx` § 20 *Important constraints*.

- **Synthetic data only.** No real JKN participant data, in any form, for any reason.
- The decision stays with a human. No automatic claim rejection, payment action, sanction, or code change.
- Language is **"risk / anomaly requiring review"** — never "fraud" as a finding.
- **No LLM anywhere in the risk score or status transition.** The assistant is outside both.
- Source, resource, and version provenance is preserved on every derived artifact.

## Outcome

Landed 2 Oct 2026. Verified: backend **690** (171 new) · web unit **428** (38 new) · Playwright
**13 + 4** new (`assistant.spec.ts` on the template path; `assistant-model.spec.ts` opt-in on the
model path, run against the internal gateway) · tsc clean · ruff clean on every touched file.
`docs/api/openapi.json` and `access-matrix.json` regenerated.

**The model path was run against the real gateway** (`Qwen3.5-9B`) with the switch on in a
separate API process; `apps/backend/.env` was **not** changed and the assistant stays off by
default. Measured: 12–20 s per free-form answer — above ADR-0007's 15 s criterion on this gateway.
Four leaks found by reading real answers are closed (ADR-0007 § *As implemented*). Three
independent reviews (Python, React, security) found no critical issue; every HIGH and MEDIUM
finding was fixed in the same unit of work.

## Kill criteria

See ADR-0007 § Kill criteria. The import-direction test failing reverts the whole feature.
