# Sprint 06 — Evaluation & Evidence Report

**Status:** 🚧 In Progress
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

**Both tasks are built and green; the sprint is not closed.** Three things stand between here and
done, and none of them is code:

1. **The official run.** `packages/data/build/` has not been regenerated — see
   `docs/HANDOVER.md` § 7 blocker 1 — so every figure produced so far is a rehearsal against a
   scratch corpus and must not be quoted. `load_build` refuses the published artifacts, which is
   the correct behaviour and was verified by running the CLI against them.
2. **The manual failure-mode write-up** over the 25 false positives and 25 false negatives the
   runner writes into `case_reports.json`.
3. **The three sign-offs** in the table above. They are separate deliberately: the person who
   produced a number should not be the only one deciding what it is allowed to claim.

Acceptance, as it stands:

- **One command rebuilds the artifacts** — `uv run python -m runner.run --build …`, and a clean
  re-run reproduces identical hashes for every deterministic artifact (asserted in
  `tests/test_run.py`).
- **Labels say synthetic** — carried on the response as `data_class`, rendered as a banner that
  is never conditional, and stated verbatim in the limitations card.
- **Per-mode results and false-positives-per-100 are reported** — for all four baselines, with
  every mode present and a status naming why any value is absent.
- **The test set is untouched during tuning** — thresholds are fitted on validation only, and
  `BandCalibration.fit` refuses any other partition by name. The test partition is read once.
- **Chart values match the JSON** — asserted by reading the numbers back out of the rendered SVG
  and, on the page, by building charts and tables from one selector through one formatter.

**What the rehearsal suggests, pending the official run.** The hybrid's macro F1 is *identical*
to rules-only: it detects nothing the rules do not. What improves is ranking — PR-AUC 0.7122 →
0.8440 and precision at the review budget 0.9565 → 1.0000 — at slightly more false positives per
100 clean claims. If that holds on the frozen test set, the incremental value is prioritisation
and not detection, and that is the only claim the proposal may make. If it does not hold, sprint
05's removal clause applies.
