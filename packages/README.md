# packages/

Shared libraries consumed by `apps/backend/` and `evaluation/`. Layout follows
`docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx` § 20 *Repository recommendation*.

| Package | Owns | Consumed by |
|---------|------|-------------|
| `domain/` | Canonical schemas, reason-code catalog, rule interfaces | `apps/backend/`, `data/`, `model/` |
| `data/` | Synthea adapter, risk-pattern injectors, generator, split manifests | `apps/backend/`, `evaluation/` |
| `model/` | Feature families, similarity, anomaly, calibration | `apps/backend/`, `evaluation/` |

**Dependency direction is one-way:** `domain/` depends on nothing; `data/` and `model/`
depend on `domain/`; `apps/backend/` and `evaluation/` depend on all three. A package must
never import from `apps/`.

**Hard boundary:** injection manifests produced by `data/` are readable by `evaluation/`
but must never reach `model/` feature tables or the detection path. See
`docs/canonical/04_data_card.md` § Leakage controls.
