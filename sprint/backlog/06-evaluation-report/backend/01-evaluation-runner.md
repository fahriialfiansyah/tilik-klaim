# Task 01 — Reproducible evaluation runner and artifacts

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
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

- [ ] Four baselines: B0 random, B1 rules-only, B2 statistical-only, TilikKlaim hybrid
- [ ] Precision, recall, F1 **per mode**
- [ ] Macro F1
- [ ] Precision–recall AUC (AUROC may appear in an appendix only, never as a headline)
- [ ] Precision@K and Recall@K at a fixed reviewer budget
- [ ] **False positives per 100 clean claims**
- [ ] p50 and p95 screening latency
- [ ] Evidence-reference validity — every displayed reason resolves to real resources
- [ ] Freeze generator, adapter, injection, split, and baseline definitions before running
- [ ] Run schema and leakage tests **before** computing any metric
- [ ] Tune thresholds on validation data only; evaluate **once** on the frozen grouped test set
- [ ] Bootstrap confidence intervals where feasible
- [ ] Break results down by mode, difficulty, provider, evidence completeness, and single vs multi-label
- [ ] Manually review ≥25 false positives and ≥25 false negatives; write up the top failure modes
- [ ] Outputs: `metrics.json`, tables CSV, charts, case reports, run manifest
- [ ] Manifest records dataset hash, generator version, split manifest, feature/rule/model versions, thresholds, code commit, environment, artifact hashes
- [ ] Limitations card generated as copy-ready text, including the mandatory synthetic sentence
- [ ] **Test — metric unit tests:** each metric is correct on hand-checked inputs
- [ ] **Test — artifact schema:** every output validates against its schema
- [ ] **Test — hash / re-run comparison:** a clean re-run reproduces identical artifact hashes
- [ ] **Test — no demo fixtures in evaluation:** the five gold fixtures are provably absent
- [ ] **Edge case — no positive prediction:** reported honestly, not as a divide-by-zero crash
- [ ] **Edge case — multi-label case:** reported separately from single-label
- [ ] **Edge case — threshold ties:** deterministic, documented tie-breaking
- [ ] **Edge case — missing class:** reported as absent, never silently skipped
- [ ] **Edge case — timeout:** bounded and reported

## Done when

One command rebuilds every artifact from a clean environment with identical hashes; per-mode
metrics and false-positives-per-100 are reported; the five demo fixtures are provably absent
from every metric; and chart values match `metrics.json` exactly.

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/backend.md`

## Notes

If the hybrid shows no measurable gain, publish rules-only as the headline result and record
the removal decision. § 18 lists this as the Gate 6 fallback — a planned branch, not a
failure to explain away.
