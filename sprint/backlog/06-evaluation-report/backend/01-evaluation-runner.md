# Task 01 — Reproducible evaluation runner and artifacts

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** no — offline evaluation run deliberately by an engineer.
**Depends on:**
- [`../../05-ranking-models/backend/01-similarity-anomaly.md`](../../05-ranking-models/backend/01-similarity-anomaly.md)

## Goal

One command, run from a clean environment, rebuilds every metric, table, and chart the
proposal will cite.

## Files to touch

- `evaluation/runner/run.py` — the single entrypoint
- `evaluation/runner/baselines.py` — B0 random · B1 rules-only · B2 statistical-only · hybrid
- `evaluation/runner/metrics.py` — the seven primary metrics
- `evaluation/runner/charts.py` — charts drawn from the same values as the tables
- `evaluation/runner/manifest.py` — run manifest
- `evaluation/runner/limitations.py` — copy-ready limitations card

## Skills to consult

- `docs/canonical/06_evaluation_plan.md` — baselines, metrics, protocol, required artifacts

## TODOs

- [x] Four baselines: B0 random, B1 rules-only, B2 statistical-only, TilikKlaim hybrid
- [x] Precision, recall, F1 **per mode**
- [x] Macro F1
- [x] Precision–recall AUC (AUROC may appear in an appendix only, never as a headline)
- [x] Precision@K and Recall@K at a fixed reviewer budget
- [x] **False positives per 100 clean claims**
- [x] p50 and p95 screening latency
- [x] Evidence-reference validity — every displayed reason resolves to real resources
- [x] Freeze generator, adapter, injection, split, and baseline definitions before running
- [x] Run schema and leakage tests **before** computing any metric
- [x] Tune thresholds on validation data only; evaluate **once** on the frozen grouped test set
- [x] Bootstrap confidence intervals where feasible
- [x] Break results down by mode, difficulty, provider, evidence completeness, and single vs multi-label
- [x] Manually review ≥25 false positives and ≥25 false negatives; write up the top failure modes — *material generated into `case_reports.json`; the human write-up is owed, see Notes*
- [x] Outputs: `metrics.json`, tables CSV, charts, case reports, run manifest
- [x] Manifest records dataset hash, generator version, split manifest, feature/rule/model versions, thresholds, code commit, environment, artifact hashes
- [x] Limitations card generated as copy-ready text, including the mandatory synthetic sentence
- [x] **Test — metric unit tests:** each metric is correct on hand-checked inputs
- [x] **Test — artifact schema:** every output validates against its schema
- [x] **Test — hash / re-run comparison:** a clean re-run reproduces identical artifact hashes
- [x] **Test — no demo fixtures in evaluation:** the five gold fixtures are provably absent
- [x] **Edge case — no positive prediction:** reported honestly, not as a divide-by-zero crash
- [x] **Edge case — multi-label case:** reported separately from single-label
- [x] **Edge case — threshold ties:** deterministic, documented tie-breaking
- [x] **Edge case — missing class:** reported as absent, never silently skipped
- [x] **Edge case — timeout:** bounded and reported

## Done when

One command rebuilds every artifact from a clean environment with identical hashes; per-mode
metrics and false-positives-per-100 are reported; the five demo fixtures are provably absent
from every metric; and chart values match `metrics.json` exactly.

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/backend.md`

## Notes

If the hybrid shows no measurable gain, publish rules-only as the headline result and record
the removal decision. § 18 lists this as the Gate 6 fallback — a planned branch, not a
failure to explain away.

**Files delivered.** `evaluation/runner/`: `run.py` (the single entrypoint), `baselines.py`,
`metrics.py`, `charts.py`, `manifest.py`, `limitations.py`, plus `preflight.py`, `report.py`, and
`ground_truth.py`. 47 tests in `evaluation/tests/`. The three extra modules exist because the
gates must run *before* any metric (`preflight.py`), because every reported value has to be
assembled once so tables and charts cannot disagree (`report.py`), and because evaluation needs
difficulty and multi-label breakdowns that `tilik_model.dataset` deliberately does not expose to
a model (`ground_truth.py`).

**`metrics.json` carries no run id and no timestamp.** It is hashed and compared across runs, so
anything that legitimately differs between two runs of one commit lives in the manifest instead.
Without that, the reproducibility check would always fail and would quietly be switched off.

**Latency is written but not hashed.** p50 and p95 measure the machine, not the method. Hashing
them makes "a clean re-run reproduces identical hashes" permanently false; `manifest.json` names
which artifacts are hashed and which are not, and says why.

**Three decisions the task left open, resolved and recorded.**

1. *A baseline with no mode attribution.* B0 and B2 produce a score, not a reason. Counting a
   flag as a correct attribution would read the answer off the ground truth, so a flag counts as
   a prediction for **all four** modes and per-mode precision falls accordingly. That is what the
   absence of attribution costs, measured rather than argued.
2. *B0's flag budget.* A random baseline that flags everything has perfect recall and useless
   precision; one that flags nothing has the reverse. B0 is given exactly as many flags as B1
   spends, so the comparison is about *which* cases each picks.
3. *Undefined metrics on the wire.* `EvaluationResponse` is frozen and its metric fields are
   plain floats, so a `null` cannot be represented. Those rows are **omitted** and the page
   renders the four known baselines and modes from its own enums, marking anything missing as
   *tidak terukur*. `metrics.json` keeps the nulls.

**A near-miss worth recording.** Evidence-reference validity first reported **39 of 140**
displayed references as unresolvable. All 39 were clone reasons pointing at a *peer* note —
another participant's, at the same facility, which is exactly where a clone reason must point.
The checker was wrong, not the detector: it searched only the bundle and its same-participant
history. Left as measured, the obvious response would have been to "fix" a working detector.
Validity is 1447/1447 once peer documents are in the resolvable set.

**Still owed.**

- The **official run** waits on the `packages/data/build/` regeneration decision
  (`docs/HANDOVER.md` § 7 blocker 1). `load_build` refuses the current artifacts, which is the
  correct behaviour and was verified by running the CLI against them.
- The **manual failure-mode write-up** over the 25 false positives and 25 false negatives in
  `case_reports.json`. The runner supplies the material and makes no claim about what it shows;
  reading them is a person's job.
- The **three sign-offs** in `../sprint.md` — experiment record, claim interpretation, visuals.

**Rehearsal figures, not results.** Run against a corpus regenerated into a scratch directory,
so they are not the frozen-test-set numbers and must not be quoted:

| Baseline | macro F1 | PR-AUC | P@budget | FP/100 clean |
|---|---|---|---|---|
| B0 random | 0.1275 | 0.2681 | 0.0870 | 63.75 |
| B1 rules only | 0.6510 | 0.7122 | 0.9565 | 51.88 |
| B2 statistical only | 0.2276 | 0.6730 | 0.7826 | 25.00 |
| Hybrid | 0.6510 | **0.8440** | **1.0000** | 52.50 |

The shape is the interesting part and it is not what the sprint assumed. **Macro F1 is identical
to rules-only** — the hybrid detects nothing the rules do not, which follows from the modes coming
from the rules. What moves is **ranking**: PR-AUC +0.13 and precision at the review budget 0.9565
→ 1.0000, bought at slightly *more* false positives per 100 clean claims. So the incremental
value, if it survives the official run, is prioritisation and not detection — and that is the
claim the proposal would have to make. No tuning was done.
