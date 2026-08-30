# Sprint 07 — Demo Hardening

**Status:** 📋 Planned
**Created At:** 2026-08-30
**Gate:** G8 — Final QA · **Deadline:** 17 September 2026
**Owner:** M2 — Product, UX & Data
**Source:** § 22 *Demo Plan*

## Goal

The seeded demo runs reliably offline, and a rehearsed fallback exists for when it does not.

## Acceptance

- The 90-second flow completes on the phantom-billing fixture, offline, from a clean reset.
- A demo reset restores the seeded state in one command.
- Health checks pass before the session starts.
- The fallback runs without the live application at all.

## Scope (stacks involved)

- [x] frontend → see [`frontend/`](./frontend/) · [x] backend → see [`backend/`](./backend/)

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
