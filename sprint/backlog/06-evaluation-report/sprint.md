# Sprint 06 — Evaluation & Evidence Report

**Status:** 📋 Planned
**Created At:** 2026-08-30
**Gate:** G6 — Evaluation evidence · **Deadline:** 12 September 2026
**Owner:** M1 — Technical & AI
**Work spec:** WS-006 (§ 20)

## Goal

Produce proposal-ready, reproducible baseline-versus-hybrid evidence, with its limitations
attached.

## Acceptance

WS-006 acceptance, carried verbatim:

- One command rebuilds the artifacts.
- Labels say **synthetic**.
- Per-mode results and false-positives-per-100 are reported.
- The test set is untouched during tuning.
- Chart values match the JSON.

## Scope (stacks involved)

- [x] frontend → see [`frontend/`](./frontend/) · [x] backend → see [`backend/`](./backend/)

## Sign-off (§ 20 Definition of done)

| Artifact | Signed by |
|----------|-----------|
| Experiment record | M1 — Technical & AI |
| Claim interpretation | M3 — Research, Proposal & PM |
| Visuals | M2 — Product, UX & Data |

Three separate signatures, deliberately. The person who produced a number should not be the
only one deciding what it is allowed to claim.

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
