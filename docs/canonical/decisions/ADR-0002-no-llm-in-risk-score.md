> Sumber: docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx §12 + §20 (Important constraints)
> Status: canonical — read-only. Perubahan hanya lewat ADR baru.

# ADR-0002 — No LLM in the risk score

- **Status:** Accepted
- **Scope:** Risk detection, risk aggregation, and case-state transitions
- **Owner section:** [05_model_card.md](../05_model_card.md)

**Cross-reference (jangan salin isinya ke sini):**

- Detector design by mode, feature families, risk aggregation, guardrails → [05_model_card.md](../05_model_card.md)
- Component technology choices → [03_architecture.md](../03_architecture.md)
- LLM-hallucination and prompt/data-leakage controls → [07_privacy_threat_model.md](../07_privacy_threat_model.md)
- Baselines that test whether the hybrid earns its complexity → [06_evaluation_plan.md](../06_evaluation_plan.md)

---

## Context

§12 decision table, verbatim rows that bind this ADR:

| Possible role | Decision | Rationale |
|---|---|---|
| Core detection | No LLM. Use rules + similarity/anomaly methods. | Risk signals must be repeatable, evidence-bound, and testable. |
| Explainability | Structured reason templates first | “Line X lacks Procedure Y” is clearer than generated prose. |
| Evidence summarization | Optional LLM after core works | Appropriate only for concise synthesis of supplied structured evidence with citations to resources. |
| Investigation assistance | Optional, non-authoritative | May suggest questions or missing evidence; never change score/disposition. |
| Policy reasoning | Retrieval may support lookup; human decides | Regulations and coding context can change and require expert interpretation. |
| Diagnosis/medical necessity | Out of scope | No clinical expert, real data, or validated diagnostic pathway. |

§20 "Important constraints", verbatim:

> One category; synthetic data only; human decision; risk language; no automatic denial; no LLM in score; no production integration claim; preserve source/resource/version provenance; proposal metrics must be generated artifacts.

§20 "Explicitly out of scope", verbatim:

> Live BPJS/SATUSEHAT connection, real participant data, clinical diagnosis/necessity, enterprise IAM, national-scale load claims, GNN/blockchain/multi-agent architecture, mobile app, and generic chatbot.

## Decision

1. **No LLM participates in the risk score.** Core detection uses rules plus similarity/anomaly methods only.
2. Explanations are produced by **structured reason templates**, not generated prose.
3. An LLM summary is **optional and post-Gate-6 only**. §12: "The MVP does not require an LLM."
4. **LLM output never feeds the score or status transition** (§12 guardrails), and investigation assistance may "never change score/disposition".
5. Diagnosis and medical-necessity reasoning are out of scope.

## Consequences

- Every risk signal is repeatable, evidence-bound, and testable, which is the rationale §12 gives for the exclusion.
- The hybrid must justify itself against transparent baselines; §12: "If a learned combiner is used, compare it to this simple baseline and remove it if it adds no meaningful value." Baseline definitions live in [06_evaluation_plan.md](../06_evaluation_plan.md).
- Any optional summarizer inherits the §12 guardrails in full (structured JSON evidence only, local/approved deployment, five-sentence cap with inline resource IDs, rejection of unsupported IDs/numbers, deterministic template fallback, raw reasons shown beside the summary) → [05_model_card.md](../05_model_card.md).
- The prototype ships without a generic chatbot; §20 lists one as explicitly out of scope.
- Reversing this ADR requires a new ADR; the checklist item "AI supports human decisions; it never silently rejects, sanctions, or accuses" in [00_competition_brief.md](../00_competition_brief.md) is a competition rule and is not overridable by an ADR.
