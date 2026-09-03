# Sprint 08 — Evidence Workspace

**Status:** ✅ Done
**Created At:** 2026-09-03
**Gate:** G8 — Final QA · **Deadline:** 17 September 2026
**Owner:** M2 — Product, UX & Data
**Source:** [ADR-0004](../../../docs/canonical/decisions/ADR-0004-evidence-workspace.md) · `sprint/00-app-spec.md` § 4

## Goal

`/cases/:id` lets a reviewer see the **shape** of a finding in one read: which billed lines lack
which evidence, where in the episode the billed service sits against an empty lane, and one
reason-focused path from claim to expected evidence — with one drawer that follows the selection.

## Acceptance

- The Evidence Matrix (widget 28) derives from `CaseDetailResponse` alone; no API, DTO, token,
  or contract-fixture change.
- The four cell states `FOUND · MISSING · UNRESOLVED · NOT_EXPECTED` are distinct in words as
  well as colour; `NOT_EXPECTED` never reads as absent evidence.
- The Episode Timeline renders four lanes on one shared time axis; an empty lane is drawn and
  labelled, never collapsed away.
- The Evidence Map is anchored on the open reason, keeps a single trunk, and terminals never link
  to each other (display rule 3).
- Source and comparison share one drawer host; two drawers cannot be open at once by construction.
- Display rules 1–5 hold; all 107 vitest and 17 Playwright specs stay green, plus the new ones.
- QA screenshots of all five states in `docs/qa/2026-09-03-evidence-workspace/`.

## Scope (stacks involved)

- [x] frontend → see [`frontend/`](./frontend/) · [ ] backend — **none, by decision**

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

## Kill criteria

See ADR-0004 § Kill criteria. Each one reverts a named widget, and the whole change is a
frontend-only `git revert`.

## Outcome

Landed 3 Sep 2026 as frontend-only commits. Verified: web 168 · playwright 21 · tsc clean; every
Python suite unchanged (338 · 23 · 57 · 71 · 47). No API, DTO, token, or fixture moved.
One defect found only by opening the page (an un-cited billed line drawn as a broken reference)
and fixed before merge — recorded in `changelog/web.md` and `docs/qa/MANUAL-QA.md` § 1e.
