# Task 01 — Similarity and anomaly baselines with calibration

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** ✅ Done
**Foundation:** no
**Autonomous:** yes
**Depends on:**
- [`../../03-evidence-rules/backend/02-rule-engine.md`](../../03-evidence-rules/backend/02-rule-engine.md) — ranks on top of rule reasons
- [`../../01-synthetic-data/backend/03-split-and-leakage-controls.md`](../../01-synthetic-data/backend/03-split-and-leakage-controls.md) — needs the frozen grouped split

## Goal

Rank cases so the most informative arrive first within a fixed review budget — while every
reason stays visible.

## Files to touch

- `packages/model/src/features.py` — the six feature families
- `packages/model/src/similarity.py` — TF-IDF / character n-gram or MinHash baseline
- `packages/model/src/anomaly.py` — Isolation Forest or LOF baseline
- `packages/model/src/calibration.py` — band thresholds
- `packages/model/src/model_card.py` — model card generator
- `packages/model/tests/`

## Skills to consult

- `docs/canonical/05_model_card.md` § Feature families, § Risk aggregation
- `docs/canonical/decisions/ADR-0002-no-llm-in-risk-score.md`

## TODOs

- [x] Feature families: evidence completeness, episode integrity, similarity, peer context, provenance, amount/quantity
- [x] **Exclude demographics and protected characteristics** — not needed for the four modes
- [x] TF-IDF character n-gram or MinHash similarity baseline
- [x] Isolation Forest or LOF anomaly baseline on robust peer features
- [x] Calibrate bands on **validation data only**
- [x] Aggregation: `priority = max(deterministic_priority, calibrated_similarity, calibrated_anomaly)`
- [x] **Cap:** no high band from text similarity alone
- [x] **Cap:** missing evidence + incomplete bundle lowers certainty → request evidence
- [x] **Cap:** exact duplicate fingerprint is high priority, still human-reviewed
- [x] Store every component score and version, not just the aggregate
- [x] Optional multilingual embeddings **only** after the baseline is measured — *honoured by omission; none added, because the baseline is not measured until Sprint 06*
- [x] **No LLM. No GNN.**
- [x] **Test — group split enforcement:** training never sees test participants or provider-time blocks
- [x] **Test — serialization:** saved model reloads and reproduces identical predictions
- [x] **Test — feature schema:** feature table matches its declared schema
- [x] **Test — leakage probe:** no injector metadata reachable from features
- [x] **Test — threshold boundaries:** band assignment is correct at each boundary
- [x] **Edge case — empty or very short notes:** similarity degrades gracefully, no crash
- [x] **Edge case — common templates:** cannot alone reach the top band
- [x] **Edge case — unseen provider:** peer features handle the cold start
- [x] **Edge case — missing feature:** documented imputation, never a silent zero
- [x] **Edge case — distribution shift:** monitored and reported, not assumed away
- [x] Model card: intended use, prohibited use, data, metrics, limitations, fairness, human oversight, monitoring

## Done when

Predictions are reproducible from a saved model; the leakage probe finds no injector
metadata in features; a text-only signal provably cannot reach the highest band; and the
model card is complete.

**If no incremental value is measured in Sprint 06, remove this layer and record why.**

## Closing checklist

- [x] All `## TODOs` items above are `[x]`
- [x] Done-when assertion verified
- [x] Top-of-file header literally reads `**Status:** ✅ Done`
- [x] Changelog entry appended to `changelog/backend.md`

## Notes

**Files delivered.** `packages/model/src/tilik_model/`: `feature_schema.py` (the declared
contract), `features.py` + `measures.py` (extraction), `similarity.py`, `anomaly.py`,
`calibration.py`, `ranking.py` (the single call site), `persistence.py`, `dataset.py`,
`model_card.py`, `version.py`. 71 tests in `packages/model/tests/`.

The task named `features.py`, `similarity.py`, `anomaly.py`, `calibration.py`, and
`model_card.py`; they sit under `src/tilik_model/` rather than bare `src/`, matching
`packages/data`'s layout so the package is importable. `dataset.py`, `persistence.py`,
`ranking.py`, `measures.py`, and `version.py` were added because the five named files could not
carry the work alone — the split has to be loaded and enforced, a model has to round-trip, and
the aggregation needs one place to live.

**The model is behind exactly one call site.** `RankingModel.rank()` is the only entry point,
nothing outside `packages/model` imports any other module in it, and no score reaches a wire
model. If Sprint 06 measures no incremental value, the revert is deleting the package and one
import — which is what the sprint's removal clause requires.

**Two findings the task did not anticipate.**

1. *Training would have seen test participants.* The published split groups by
   `(participant, facility, time block)`, so one participant can legitimately appear in two
   partitions — at another facility, or in another month. Measured on the real corpus: **125 of
   140 test participants also appear in train, and 299 of 674 training bundles share a
   participant with validation or test.** The split's own guarantee holds; it is simply weaker
   than what fitting needs. `dataset.uncontaminated_training_bundles` drops the contaminated
   rows on the *training* side and returns the count, rather than re-cutting a split that was
   announced as frozen. `test_dataset.py` asserts both the split guarantee and the stronger
   property, and asserts the filter is still removing something so it cannot rot into dead code.

2. *A band raised only by a model score has no reason to show a reviewer.* The aggregation is
   specified as a plain maximum, so an anomaly score can raise a case the rules layer said
   nothing about. Suppressing those would be a fourth cap the canonical model card does not
   specify, so instead every such result carries `explained_by_reasons: false` and the model
   card names it under Limitations. Sprint 06 decides what the queue does with them.

**The leakage probe is stronger than "no injector field is copied into a column".** It
re-identifies the whole corpus — every bundle, claim, line, encounter, participant, and facility
— refits the peer profile on the renamed corpus, and asserts the feature table does not move.
That covers the injector suffix, the record ordinal, and anything else an identifier could
carry. A companion test plants an id-reading feature and confirms the probe would catch it.

**Still owed, and blocked on a decision.** No `MODEL_CARD.md` artifact has been rendered for the
published corpus, because `packages/data/build/` has not been regenerated — see
`docs/HANDOVER.md` § 7 blocker 1. The generator and its tests are complete; only the artifact
waits.
