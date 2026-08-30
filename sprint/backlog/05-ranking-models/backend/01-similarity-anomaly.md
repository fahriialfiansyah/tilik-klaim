# Task 01 — Similarity and anomaly baselines with calibration

**Stack:** backend
**Sprint:** [`../sprint.md`](../sprint.md)
**Status:** 📋 Planned
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

- [ ] Feature families: evidence completeness, episode integrity, similarity, peer context, provenance, amount/quantity
- [ ] **Exclude demographics and protected characteristics** — not needed for the four modes
- [ ] TF-IDF character n-gram or MinHash similarity baseline
- [ ] Isolation Forest or LOF anomaly baseline on robust peer features
- [ ] Calibrate bands on **validation data only**
- [ ] Aggregation: `priority = max(deterministic_priority, calibrated_similarity, calibrated_anomaly)`
- [ ] **Cap:** no high band from text similarity alone
- [ ] **Cap:** missing evidence + incomplete bundle lowers certainty → request evidence
- [ ] **Cap:** exact duplicate fingerprint is high priority, still human-reviewed
- [ ] Store every component score and version, not just the aggregate
- [ ] Optional multilingual embeddings **only** after the baseline is measured
- [ ] **No LLM. No GNN.**
- [ ] **Test — group split enforcement:** training never sees test participants or provider-time blocks
- [ ] **Test — serialization:** saved model reloads and reproduces identical predictions
- [ ] **Test — feature schema:** feature table matches its declared schema
- [ ] **Test — leakage probe:** no injector metadata reachable from features
- [ ] **Test — threshold boundaries:** band assignment is correct at each boundary
- [ ] **Edge case — empty or very short notes:** similarity degrades gracefully, no crash
- [ ] **Edge case — common templates:** cannot alone reach the top band
- [ ] **Edge case — unseen provider:** peer features handle the cold start
- [ ] **Edge case — missing feature:** documented imputation, never a silent zero
- [ ] **Edge case — distribution shift:** monitored and reported, not assumed away
- [ ] Model card: intended use, prohibited use, data, metrics, limitations, fairness, human oversight, monitoring

## Done when

Predictions are reproducible from a saved model; the leakage probe finds no injector
metadata in features; a text-only signal provably cannot reach the highest band; and the
model card is complete.

**If no incremental value is measured in Sprint 06, remove this layer and record why.**

## Closing checklist

- [ ] All `## TODOs` items above are `[x]`
- [ ] Done-when assertion verified
- [ ] Top-of-file header literally reads `**Status:** ✅ Done`
- [ ] Changelog entry appended to `changelog/backend.md`
