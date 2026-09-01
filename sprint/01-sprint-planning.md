# Sprint Planning — TilikKlaim

Master tracking table for every sprint in this project. Update on every status change, sprint creation, or sprint move.

> **Project blueprint:** see [`brief/00_OVERVIEW.md`](../brief/00_OVERVIEW.md) — produced from `docs/canonical/`. This planning table refines that brief into sprints; it does not replace it.
> **Page-level spec:** [`00-app-spec.md`](./00-app-spec.md)
> **Work-spec source:** `docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx` § 20 (WS-001 … WS-006). The WS specs are already FRD-shaped; task files carry them, they are not rewritten.

## Deadline clock

Registration closes **14 September 2026**. Proposal submission closes **19 September 2026**.
Internal upload target is **18 September**; 19 September is emergency recovery only.

**Today is 31 August.** Gate 3 (2 Sep) and Gate 4 (5 Sep) are both **met early** — sprints 01,
02, and 03 are done. Gate 5 (9 Sep) is next: the review slice.

## Sprint table

| Sprint | Goal | Status | Gate | Deadline | Owner | Depends On | Brief | References | Created At | Started At | Completed At |
|--------|------|--------|------|----------|-------|------------|-------|------------|------------|------------|--------------|
| Sprint 00 — foundation | Repo, tooling, local stack, and canonical docs wired so every later sprint has a place to land | ✅ Done | — | 31 Agu | M1 | - | [../brief/00_OVERVIEW.md](../brief/00_OVERVIEW.md) | [./backlog/00-foundation/](./backlog/00-foundation/) | 2026-08-30 | - | - |
| Sprint 01 — synthetic-data | Reproducible generator producing ≥1.000 linked claims and ≥200 labelled injections | ✅ Done | **G3** | **2 Sep** | M1 | 00 | [../brief/06_DATA_SINTETIK.md](../brief/06_DATA_SINTETIK.md) | [./backlog/01-synthetic-data/](./backlog/01-synthetic-data/) | 2026-08-30 | 2026-08-31 | 2026-08-31 |
| Sprint 02 — ingest-validation | One documented bundle subset accepted, validated, hashed, and stored | ✅ Done | G4 | 5 Sep | M1 | 01 | [../brief/01_INGEST_VALIDASI.md](../brief/01_INGEST_VALIDASI.md) | [./backlog/02-ingest-validation/](./backlog/02-ingest-validation/) | 2026-08-30 | 2026-08-30 | 2026-08-31 |
| Sprint 03 — evidence-rules | Versioned reasons plus resolvable evidence for three risk modes | ✅ Done | G4 | 5 Sep | M1 | 02 | [../brief/02_MESIN_BUKTI_DETEKSI.md](../brief/02_MESIN_BUKTI_DETEKSI.md) | [./backlog/03-evidence-rules/](./backlog/03-evidence-rules/) | 2026-08-30 | 2026-08-30 | 2026-08-30 |
| Sprint 04 — review-slice | Queue → detail → human disposition → audit event, no dead ends | ✅ Done | G5 | 9 Sep | M2 | 03 | [../brief/03_ANTREAN_REVIEW.md](../brief/03_ANTREAN_REVIEW.md) · [04](../brief/04_DETAIL_KASUS_DISPOSISI.md) | [./backlog/04-review-slice/](./backlog/04-review-slice/) | 2026-08-30 | 2026-08-31 | 2026-09-01 |
| Sprint 05 — ranking-models | Similarity and anomaly ranking that earns its place over rules-only, or is removed | ✅ Done | G6 | 12 Sep | M1 | 04 | [../brief/02_MESIN_BUKTI_DETEKSI.md](../brief/02_MESIN_BUKTI_DETEKSI.md) | [./backlog/05-ranking-models/](./backlog/05-ranking-models/) | 2026-08-30 | - | - |
| Sprint 06 — evaluation-report | Reproducible baseline-versus-hybrid evidence with limitations, ready to cite | 📋 Planned | G6 | 12 Sep | M1 | 05 | [../brief/05_AUDIT_EVALUASI.md](../brief/05_AUDIT_EVALUASI.md) | [./backlog/06-evaluation-report/](./backlog/06-evaluation-report/) | 2026-08-30 | - | - |
| Sprint 07 — demo-hardening | Seeded demo runs reliably offline, with a rehearsed fallback | 📋 Planned | G8 | 17 Sep | M2 | 06 | [../brief/00_OVERVIEW.md](../brief/00_OVERVIEW.md) | [./backlog/07-demo-hardening/](./backlog/07-demo-hardening/) | 2026-08-30 | - | - |

**Status legend:** 📋 Planned · 🚧 In Progress · ✅ Done · ⏸ Paused · ❌ Cancelled

## Ordering note — why WS-004 comes after WS-005

Sprint 05 (ranking models, WS-004) runs **after** Sprint 04 (review UI, WS-005), following
§ 20 *Initial backlog*. The rules baseline must be visible and measurable before any
statistical layer is added, so the layer can be judged on incremental value — and removed
if it adds none. That removal is an anticipated outcome, not a failure; see the kill
criteria in `docs/canonical/01_product_decision.md`.

## Foundation tasks

Two tasks produce contracts other stacks consume. Both must be `[x]` before their dependents start.

| Foundation task | Delivers | Consumed by |
|-----------------|----------|-------------|
| [`01-synthetic-data/backend/00-canonical-schema.md`](./backlog/01-synthetic-data/backend/00-canonical-schema.md) ✅ | Canonical model, reason-code catalog, 5 gold fixtures | Sprints 02, 03, 04, 06 — **unblocked** |
| [`02-ingest-validation/backend/00-api-contract.md`](./backlog/02-ingest-validation/backend/00-api-contract.md) ✅ | OpenAPI for 7 endpoints, stable error codes | Sprint 04 frontend — **unblocked**, fixtures committed |

## Workforce

Brief Workforce Manifest contains only `be_service` and `fe_shell` — **no agent roles**.
Sprint `00-workforce-scaffold` therefore **does not exist** and must not be created;
`docs/canonical/01_product_decision.md` places *multi-agent system* in OUT OF SCOPE.
Sprint 00 uses the standard bootstrap form instead.

---

*This file is updated whenever a sprint status changes, a new sprint is added, or when a phase begins/ends.*
*Append-only: never delete a sprint row. Cancelled sprints stay visible with status `❌ Cancelled` and a one-line reason.*
