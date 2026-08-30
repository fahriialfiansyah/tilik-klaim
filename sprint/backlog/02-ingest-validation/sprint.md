# Sprint 02 — Ingest & Validation

**Status:** 🚧 In Progress
**Created At:** 2026-08-30
**Gate:** G4 — Core engine · **Deadline:** 5 September 2026
**Owner:** M1 — Technical & AI
**Work spec:** WS-002 (§ 20)

## Goal

Accept one documented JSON bundle subset and return actionable validation, canonical
resources, and a deterministic input hash.

## Acceptance

WS-002 acceptance, carried verbatim:

- A seeded valid bundle passes.
- Malformed, oversized, and unresolved-reference bundles return **stable** error codes.
- Resubmission is idempotent.

## Scope (stacks involved)

- [ ] frontend · [x] backend → see [`backend/`](./backend/) · [ ] agent · [ ] mcp · [ ] mobile

## Workforce members touched

- `be_service` — owns the ingestion gate and the published API contract

## Cross-stack dependencies

[`backend/00-api-contract.md`](./backend/00-api-contract.md) is a **foundation task**. It
freezes the OpenAPI surface and commits response fixtures so Sprint 04's frontend can be
built in parallel rather than waiting on a working backend.

Depends on Sprint 01 [`00-canonical-schema.md`](../01-synthetic-data/backend/00-canonical-schema.md).

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

## Progress — 2026-08-30

Foundation task `00-api-contract` is `[x]`. The contract is frozen and fixtures are committed, so Sprint 04's frontend can start in parallel. One task remains.
