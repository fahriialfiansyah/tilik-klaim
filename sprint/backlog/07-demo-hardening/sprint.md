# Sprint 07 — Demo Hardening

**Status:** 🚧 In Progress
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

**The backend task is done; the frontend task is done except for what only a person can do.**

Acceptance, as it stands:

- **The 90-second flow completes on the phantom fixture, offline, from a clean reset** —
  `demo-flow.spec.ts` resets, walks the path, and asserts the elapsed time. It finishes in about
  3.5 s against a 30 s machine budget, leaving two thirds of the runbook's ninety seconds for
  narration.
- **A demo reset restores the seeded state in one command** —
  `uv run python scripts/demo_reset.py`, idempotent, 0.2–0.4 s, and it verifies rather than
  assuming: a seed that "succeeded" while the phantom fixture screened to nothing would exit
  non-zero here instead of being discovered on stage.
- **Health checks pass before the session starts** — `--check` reads the readiness block and
  exits non-zero when the demo would not work. `/healthz` itself never fails on a database
  outage, deliberately: Railway probes that path, and a 5xx there restarts the container in a
  loop exactly when the database is already in trouble.
- **The fallback runs without the live application at all** — ❌ **not yet**. Recording it is a
  person's job and it is the one acceptance clause still open.

Still owed, all of it human: the three-minute rehearsal with narration, two written case
studies, the recorded 1080p fallback, and the six-frame screenshot PDF.
