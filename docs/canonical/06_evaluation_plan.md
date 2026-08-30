> Sumber: docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx §15
> Status: canonical — read-only. Perubahan hanya lewat ADR baru.


# 06 — Evaluation Plan

**Cross-reference (jangan salin isinya ke sini):**

- Split logic, leakage controls, injected labels → [04_data_card.md](04_data_card.md)
- Detector design and risk aggregation under test → [05_model_card.md](05_model_card.md)
- Where each evidence artifact lands in the deck → [09_proposal_evidence_map.md](09_proposal_evidence_map.md)

---

# 15. Evaluation Strategy
## Evaluation question
Can TilikKlaim detect and prioritize the injected synthetic patterns more effectively than transparent baselines while producing evidence a reviewer can act on?
## Baselines
| Baseline | Definition | Purpose |
|---|---|---|
| B0 Random review | Random ordering at the same review budget | Shows whether ranking adds any value |
| B1 Rules only | Deterministic structural, fingerprint, and time-window rules | Strong, fair baseline for known patterns |
| B2 Statistical only | Similarity/anomaly scores without deterministic rules | Tests whether ML alone is useful |
| TilikKlaim hybrid | Reason-preserving rules plus calibrated similarity/anomaly signals | Must earn complexity through measurable incremental value |


## Primary metrics
| Metric | Use | Why appropriate |
|---|---|---|
| Precision, recall, F1 per mode | Detection of injected labels | Reveals mode-specific trade-offs |
| Macro F1 | Balanced summary across four modes | Avoids domination by an easy/common injected class |
| Precision–recall AUC | Ranking under class imbalance | More informative than AUROC as a headline here |
| Precision@K and Recall@K | Fixed reviewer budget | Directly measures prioritization value |
| False positives per 100 clean claims | Workload and harm proxy | Easy for judges to understand |
| p50/p95 screening latency | Technical feasibility | Shows the vertical slice is usable |
| Evidence-reference validity | Explanation integrity | Every displayed reason must resolve to real input resources/derived edges |


AUROC may appear in an appendix but should not be the headline metric.
## Workflow and usability measures
- Time from case open to disposition on five seeded cases.
- Correct identification of the primary reason by non-domain internal reviewers.
- Number of clicks to supporting evidence and action.
- Explanation usefulness rating on a short 1–5 rubric: clear reason, relevant evidence, visible uncertainty, appropriate next action.
- Disagreement between system reason and reviewer disposition.
Label these as internal usability checks, not target-user validation.
## Experimental protocol
- Freeze generator, adapter, injection, split, and baseline definitions.
- Run schema and leakage tests.
- Tune thresholds on validation data only.
- Evaluate once on the frozen grouped test set.
- Report bootstrap confidence intervals where feasible.
- Break down results by mode, difficulty level, provider, evidence completeness, and single vs multi-label.
- Manually review at least 25 false positives and 25 false negatives; write the top failure modes.
- Re-run from a clean environment and compare artifact hashes.
## Honest impact model
Do not claim cost savings. Present a pilot measurement formula:
expected reviewed value = reviewed claim amount × observed confirmation rate × recoverable/correctable fraction
Each factor must be measured or explicitly parameterized in a future authorized pilot. Scenario estimates must be labeled assumptions and separated from results.
## What synthetic results demonstrate—and do not
| Demonstrates | Does not demonstrate |
|---|---|
| Software correctly parses the chosen schema subset | Production compatibility with BPJS/E-Klaim/SATUSEHAT |
| Detectors recover known injected patterns | Real-world JKN fraud accuracy or prevalence |
| Hybrid ranking may beat baselines on controlled cases | National savings or causal impact |
| Evidence references and audit events are reproducible | Clinical validity or legal findings |
| Prototype latency and workflow can be measured | Scale under national production load |


## Required evidence artifacts
- Table: rules-only, statistical-only, and hybrid metrics with confidence intervals.
- Chart: precision@review-budget and false positives per 100 clean claims.
- Chart: per-mode precision/recall/F1.
- Screenshot: ideal flagged case with evidence path.
- Screenshot: human disposition and audit event.
- Two case studies: one true injected case and one false positive/counter-evidence case.
- Before/after workflow diagram with steps and measured internal time.
- One limitations card that can be copied directly into the proposal.
