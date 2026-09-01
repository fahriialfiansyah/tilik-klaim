# packages/model

Similarity and anomaly baselines that rank cases **on top of** the rule reasons, never instead
of them. Every reason stays visible; this package only proposes a queue position.

- `features.py` — the six feature families, with a declared schema and documented imputation
- `similarity.py` — character n-gram TF-IDF baseline over clinical notes
- `anomaly.py` — Isolation Forest over robust peer features
- `calibration.py` — band thresholds fitted on **validation data only**, plus drift reporting
- `ranking.py` — the single call site, the aggregation, and the three caps
- `persistence.py` — save and reload a fitted model with identical predictions
- `dataset.py` — load a `packages/data/build` directory and enforce the grouped split
- `model_card.py` — the model card generator

**No LLM and no GNN** anywhere in this package (ADR-0002).

**Removal is a designed outcome.** If Sprint 06 measures no incremental precision@K / recall@K
over rules-only, this layer is deleted and TilikKlaim ships rules-only. Nothing outside this
package may import it except one call site, so that revert stays a single edit.
