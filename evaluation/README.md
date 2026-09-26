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

## Shipping the run the proposal cites

Runs are git-ignored (`.gitignore`, `evaluation/artifacts/*/`) — with **one exception**: the
frozen run `run-20260901T110000Z`, which is un-ignored in both `.gitignore` and `.dockerignore` and
copied into the API image (`apps/backend/Dockerfile`, `EVALUATION_ARTIFACTS_DIR`).

That exception exists because the deployed image has no runner and cannot regenerate anything. Without
a committed run, `/evaluation` shows its empty state in production, and every number quoted in the
proposal is unverifiable by anyone who does not rebuild the corpus and rerun the runner themselves.

To publish it, from the machine that holds the run:

```
git add evaluation/artifacts/run-20260901T110000Z docs/artifacts/failure-modes.md
git commit -m "docs: commit the frozen evaluation run cited by the proposal"
```

A run is complete only when `metrics.json`, `manifest.json`, and `limitations.json` are all present.
If the cited run id changes, change it in `.gitignore`, `.dockerignore`, and this file together.
