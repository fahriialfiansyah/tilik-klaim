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

1. ~~The official run~~ — **done.** The corpus was regenerated with the owner's go-ahead and
   `test_set_digest` came back unchanged, so the frozen split was not re-frozen. Run
   `run-20260901T110000Z`.
2. ~~The manual failure-mode write-up~~ — **drafted** in `docs/artifacts/failure-modes.md`,
   pending M1 validation.
3. **The three sign-offs** in the table above — still open. They are separate deliberately: the
   person who produced a number should not be the only one deciding what it is allowed to claim.

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

**What the official run measured — and why the removal clause is live.**

| | Rules only | Hybrid | 95% intervals overlap? |
|---|---|---|---|
| Macro F1 | 0.6510 | 0.6510 | identical |
| Precision @ budget 23 | 0.9565 | 1.0000 | **yes** — [0.870, 1.000] vs [0.913, 1.000] |
| Recall @ budget | 0.3235 | 0.3382 | a one-case difference |
| PR-AUC | 0.7122 | **0.8440** | no interval computed |

**Per-mode metrics are identical across all four modes.** The statistical layer detects nothing
the rules do not. What moves is ranking.

The acceptance clause names **precision@K and recall@K**, and on those the improvement is *not
statistically established* — the intervals overlap and recall differs by one case. PR-AUC shows a
real gap but is not the stated criterion and carries no interval.

So sprint 05's removal clause is genuinely live, and that decision belongs to the sign-offs.
`docs/canonical/01_product_decision.md`: *"this is not a product kill."* Reporting it honestly is
stronger evidence of method than a marginal gain would be.
