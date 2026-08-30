# evaluation/

Reproducible offline evaluation. One command rebuilds every artifact from a clean
environment; the page at `/evaluation` only ever *reads* what lands in `artifacts/`.

- `runner/` — frozen-split runner producing metrics, tables, and charts from one source of values.
- `artifacts/<run_id>/` — `metrics.json`, tables CSV, charts, run manifest. Immutable once written.

**Rules** (`docs/canonical/06_evaluation_plan.md`):
- The test set is frozen before any threshold tuning.
- The five curated demo fixtures never enter metric computation.
- Chart values and table values read from the same source; a mismatch is a defect.
- Every run records dataset hash, generator version, split manifest, feature/rule/model
  versions, threshold logic, code commit, environment, and artifact hashes.
