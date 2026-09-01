# Sprint 05 — Ranking Models

**Status:** ✅ Done
**Created At:** 2026-08-30
**Gate:** G6 — Evaluation evidence · **Deadline:** 12 September 2026
**Owner:** M1 — Technical & AI
**Work spec:** WS-004 (§ 20)

## Goal

Improve prioritization over rules-only **without hiding reasons** — or establish, with
evidence, that it does not, and remove it.

## Acceptance

WS-004 acceptance, carried verbatim:

- Reproducible.
- No injection fields present.
- Produces incremental precision@K / recall@K **or is removed**.
- A text-only signal cannot produce the highest band.

## Scope (stacks involved)

- [ ] frontend · [x] backend → see [`backend/`](./backend/) · [ ] agent · [ ] mcp · [ ] mobile

## Why this sprint runs after Sprint 04

§ 20 *Initial backlog* orders WS-004 **after** WS-005 deliberately. The rules baseline must
be visible and measurable first, so the statistical layer can be judged on incremental value.
Building it earlier removes the very comparison that justifies it.

## Removal is a valid outcome

If the hybrid adds nothing measurable, **remove the ML and keep TilikKlaim as rules-only.**
`docs/canonical/01_product_decision.md` states this explicitly: *"this is not a product kill."*
Reporting that decision honestly is stronger evidence of method than a marginal gain would be.

## Constraints (non-negotiable — apply to every task in this sprint)

Source: `docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx` § 20 *Important constraints*.

- One official category: *Efisiensi Risiko pada Fasilitas Kesehatan*.
- **Synthetic data only.** No real JKN participant data, in any form, for any reason.
- The decision stays with a human. No automatic claim rejection, payment action, sanction, or code change.
- Language is **"risk / anomaly requiring review"** — never "fraud" as a finding.
- **No LLM anywhere in the risk score or status transition.**
- No production-integration claim. No live BPJS / SATUSEHAT / E-Klaim connection.
- Source, resource, and version provenance is preserved on every derived artifact.
- Every metric quoted in the proposal comes from a generated artifact, never typed by hand.

## Outcome

`packages/model` is built, tested, and behind one call site. Three of the four acceptance
clauses are met and asserted:

- **Reproducible** — a saved model reloads and reproduces identical predictions
  (`tests/test_serialization.py`), and the forest's random state is pinned to the corpus seed.
- **No injection fields present** — the leakage probe re-identifies the whole corpus and asserts
  the feature table does not move, which covers the injector suffix, the record ordinal, and
  anything else an identifier could carry.
- **A text-only signal cannot produce the highest band** — the ceiling is applied to the
  similarity *component*, so no combination of inputs routes around it.

The fourth clause — *produces incremental precision@K / recall@K **or is removed*** — is
measured in Sprint 06, which shares this sprint's G6 gate. **Removal remains a live outcome**,
and the layer was built so that taking it is a single revert: nothing outside `packages/model`
imports any module in it, and no score reaches a wire model.

Delivered: 71 tests in `packages/model`; 21 features across the six named families; a character
n-gram TF-IDF similarity baseline; an Isolation Forest over robustly scaled peer features; band
thresholds fitted on validation only, with `fit` refusing any other partition by name; and a
model card generator that states its metrics are pending rather than quoting one nobody measured.

Not yet produced: a rendered `MODEL_CARD.md` for the published corpus, which waits on the
`packages/data/build/` regeneration decision in `docs/HANDOVER.md` § 7 blocker 1.
