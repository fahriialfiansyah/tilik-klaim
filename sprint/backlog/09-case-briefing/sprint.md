# Sprint 09 — Case Briefing (bounded, read-only)

**Status:** ✅ Done
**Created At:** 2026-09-03
**Gate:** G8 — Final QA · **Deadline:** 17 September 2026
**Owner:** M1 — Engine & API (backend) · M2 — Product & UX (frontend)
**Source:** [ADR-0005](../../../docs/canonical/decisions/ADR-0005-bounded-case-briefing.md) · `docs/canonical/05_model_card.md` § Optional LLM guardrails

## Goal

One bounded, read-only briefing per case — observations with validated source references, open
questions, an uncertainty note — produced outside the risk path, off by default, streamed as
progress, and rendered as a collapsed, non-authoritative panel.

## Acceptance

- Nothing in the risk path imports the briefing; the briefing reaches no store and no rule
  (`tests/test_briefing_isolation.py`).
- Seven read-only tools, each a slice of `CaseDetailResponse`; a name outside the registry is
  refused before dispatch; tool output ⊆ what the screen shows.
- Output is Pydantic-structured; every observation carries ≥ 1 validated `source_refs`; the five
  gates reject the whole briefing on any failure and fall back to the template.
- `BRIEFING_ENABLED=false` by default; the template needs no network and passes the same gates.
- `GET /v1/cases/{id}/briefing` streams SSE (`status · tool · observation · done · error`);
  `?stream=false` returns the identical object. The seven frozen endpoints are untouched.
- The panel is collapsed, last in the middle column, has no action controls, and imports nothing
  from the disposition store.

## Scope (stacks involved)

- [x] backend → see [`backend/`](./backend/) · [x] frontend → see [`frontend/`](./frontend/)

## Constraints (non-negotiable — apply to every task in this sprint)

Source: `docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx` § 20 *Important constraints*.

- One official category: *Efisiensi Risiko pada Fasilitas Kesehatan*.
- **Synthetic data only.** No real JKN participant data, in any form, for any reason.
- The decision stays with a human. No automatic claim rejection, payment action, sanction, or code change.
- Language is **"risk / anomaly requiring review"** — never "fraud" as a finding.
- **No LLM anywhere in the risk score or status transition.** The briefing is outside both.
- No production-integration claim. No live BPJS / SATUSEHAT / E-Klaim connection.
- Source, resource, and version provenance is preserved on every derived artifact.
- Every metric quoted in the proposal comes from a generated artifact, never typed by hand.

## Outcome

Landed 3 Sep 2026. Verified: backend **403** (was 338) · web **184** (was 168) · playwright **24**
(was 21) · tsc clean · ruff clean · domain 23 · data 57 · model 71 · evaluation 47 unchanged.
`docs/api/openapi.json` regenerated (eighth `/v1` path). The LLM path was exercised only against
a scripted provider — **no real model call has been made from this repository**; enabling one is
a configuration change the owner makes deliberately.

## Kill criteria

See ADR-0005 § Kill criteria. The import-direction test failing reverts the whole feature.
