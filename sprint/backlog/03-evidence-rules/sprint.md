# Sprint 03 — Evidence Graph & Rule Engine

**Status:** 📋 Planned
**Created At:** 2026-08-30
**Gate:** G4 — Core engine · **Deadline:** 5 September 2026
**Owner:** M1 — Technical & AI
**Work spec:** WS-003 (§ 20)

## Goal

Return versioned reasons and resolvable evidence for phantom, repeat, and unbundling — plus
the clone baseline if it is ready.

## Acceptance

WS-003 acceptance, carried verbatim:

- Gold fixtures return the expected reason.
- Every evidence reference resolves.
- The clean fixture produces **no** injected reason.
- The same hash and version produce a deterministic result.

## Scope (stacks involved)

- [ ] frontend · [x] backend → see [`backend/`](./backend/) · [ ] agent · [ ] mcp · [ ] mobile

## Workforce members touched

- `be_service` — owns the evidence graph, the rule engine, and the reason catalog

## Cross-stack dependencies

Depends on Sprint 02 [`01-bundle-ingestion.md`](../02-ingest-validation/backend/01-bundle-ingestion.md)
and Sprint 01 [`00-canonical-schema.md`](../01-synthetic-data/backend/00-canonical-schema.md).

## Gate 4 fallback

If only an opaque score exists at the deadline, **remove the ML and ship rules first**
(§ 18 gate table). Three modes with traceable reasons beat four modes with an unexplainable
number — that trade is already decided, not open for re-litigation under time pressure.

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
