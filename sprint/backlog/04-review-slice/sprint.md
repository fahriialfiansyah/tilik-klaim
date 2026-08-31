# Sprint 04 — Review Vertical Slice

**Status:** 🚧 In Progress
**Created At:** 2026-08-30
**Started At:** 2026-08-31
**Progress:** backend ✅ both tasks · frontend ✅ `00-port-design-tokens`, ✅ `01-antrean-review` · 📋 `02-detail-kasus`, `03-ingest-page`
**Gate:** G5 — Web vertical slice · **Deadline:** 9 September 2026
**Owner:** M2 — Product, UX & Data
**Work spec:** WS-005 (§ 20)

## Goal

Queue → evidence → human action → audit, end to end, with no dead ends.

## Acceptance

WS-005 acceptance, carried verbatim:

- The ideal case completes in **under 90 seconds** internally.
- Reason is shown **before** score.
- An action **requires** a reason.
- Conflict and version errors are handled.
- The synthetic badge is **always** visible.

## Scope (stacks involved)

- [x] frontend → see [`frontend/`](./frontend/) · [x] backend → see [`backend/`](./backend/)
- [ ] agent · [ ] mcp · [ ] mobile

## Workforce members touched

- `fe_shell` — queue, case detail, ingest, and audit tab
- `be_service` — case list/detail, disposition, and audit endpoints

## Cross-stack dependencies

Frontend was planned to build against the fixtures frozen in Sprint 02
[`00-api-contract.md`](../02-ingest-validation/backend/00-api-contract.md) so it could run
**in parallel** with the backend tasks here. In the event the backend landed first, so the
frontend builds against the **live seeded API** instead. That is strictly better — the screens
are exercised by real responses rather than by fixtures that can drift from them.

## Dependency graph

```
02-ingest-validation/backend/00-api-contract.md  (foundation, committed fixtures)
    ↓
    ├─ frontend/01-antrean-review.md ─┬─ frontend/02-detail-kasus.md
    │                                 └─ frontend/03-ingest-page.md
    └─ backend/01-case-endpoints.md ──── backend/02-disposition-audit.md
```

## Gate 5 fallback

On a contract mismatch: freeze the fixtures and the API, and drop a non-core view.
Do **not** drop the disposition or the audit write — those are the vertical slice.

## Constraints (non-negotiable — apply to every task in this sprint)

Source: `docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx` § 20 *Important constraints*.

- One official category: *Efisiensi Risiko pada Fasilitas Kesehatan*.
- **Synthetic data only.** No real JKN participant data, in any form, for any reason.
- The decision stays with a human. No automatic claim rejection, payment action, sanction, or code change.
- Language is **"risk / anomaly requiring review"** — never "fraud" as a finding.
- **No LLM anywhere in the risk score or status transition.**
- No production-integration claim. No live BPJS / SATUSEHAT / E-Klaim connection.
- Source, resource, and version provenance is preserved on every derived artifact.
- Every metric quoted in the proposal comes from a generated artifact, never typed by hand.

## Outcome

(Filled in when the sprint moves to `archive/`.)
