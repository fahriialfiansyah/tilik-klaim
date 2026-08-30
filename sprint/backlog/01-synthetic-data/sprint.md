# Sprint 01 — Synthetic Data

**Status:** 📋 Planned
**Created At:** 2026-08-30
**Started At:** -
**Completed At:** -
**Gate:** **G3 — Data feasible**
**Deadline:** **2 September 2026, 18:00** — kill-criteria deadline, not a soft target
**Owner:** M1 — Technical & AI
**Work spec:** WS-001 (§ 20)

## Goal

A reproducible generator that produces linked, SATUSEHAT-shaped synthetic claim and RME
fixtures with labelled injected risk patterns — without any real JKN data.

## Acceptance

WS-001 acceptance, carried verbatim:

- The same seed produces identical hashes.
- At least 1.000 claims and 200 injections exist at Gate 3.
- All references resolve.
- Injector-only fields are absent from feature tables.

## Scope (stacks involved)

- [ ] frontend
- [x] backend → see [`backend/`](./backend/)
- [ ] agent · [ ] mcp · [ ] mobile — none in this project

## Workforce members touched

- `be_service` — owns the generator, the canonical model, and the split manifests

## Cross-stack dependencies

[`backend/00-canonical-schema.md`](./backend/00-canonical-schema.md) is a **foundation task**.
It publishes the canonical model, the reason-code catalog, and five gold fixtures that
Sprints 02, 03, 04, and 06 all read. Nothing downstream starts until it is `[x]`.

## Dependency graph

```
backend/00-canonical-schema.md  (foundation)
    ↓
    ├─ backend/01-synthea-adapter.md
    │       ↓
    │   backend/02-risk-injectors.md
    │       ↓
    │   backend/03-split-and-leakage-controls.md
    │
    └─ Sprint 02 (ingest) · Sprint 03 (rules) · Sprint 04 (UI fixtures) · Sprint 06 (evaluation)
```

## Kill criteria active in this sprint

Two of the five kill criteria in `docs/canonical/01_product_decision.md` resolve here, both
on **2 Sep 18:00**:

1. Published fields cannot support at least three selected modes → stop TilikKlaim, activate RujukTepat.
2. The generator cannot produce reproducible, linked claims and labels → fix for four hours; if still blocked, switch.

Whoever owns this sprint must call these explicitly at the deadline. Letting them slide
silently is the single most expensive failure mode in the plan.

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

## Notes

(Running notes during execution.)

## Outcome

(Filled in when the sprint moves to `archive/`.)
