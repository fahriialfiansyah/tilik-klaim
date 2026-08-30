> Sumber: docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx §12
> Status: canonical — read-only. Perubahan hanya lewat ADR baru.


# 05 — Model Card (AI/Model Strategy)

**Cross-reference (jangan salin isinya ke sini):**

- Rationale and consequences of excluding the LLM from scoring → [decisions/ADR-0002-no-llm-in-risk-score.md](decisions/ADR-0002-no-llm-in-risk-score.md)
- Component technology choices → [03_architecture.md](03_architecture.md)
- Fields, injected patterns, splits, leakage controls → [04_data_card.md](04_data_card.md)
- Baselines and metrics that test incremental value → [06_evaluation_plan.md](06_evaluation_plan.md)
- Bias, false-accusation, and LLM-hallucination controls → [07_privacy_threat_model.md](07_privacy_threat_model.md)

---

# 12. AI/Model Strategy
## Decision: AI where it earns its place
| Possible role | Decision | Rationale |
|---|---|---|
| Core detection | No LLM. Use rules + similarity/anomaly methods. | Risk signals must be repeatable, evidence-bound, and testable. |
| Explainability | Structured reason templates first | “Line X lacks Procedure Y” is clearer than generated prose. |
| Evidence summarization | Optional LLM after core works | Appropriate only for concise synthesis of supplied structured evidence with citations to resources. |
| Investigation assistance | Optional, non-authoritative | May suggest questions or missing evidence; never change score/disposition. |
| Policy reasoning | Retrieval may support lookup; human decides | Regulations and coding context can change and require expert interpretation. |
| Diagnosis/medical necessity | Out of scope | No clinical expert, real data, or validated diagnostic pathway. |


## Detector design by mode
| Mode | Transparent baseline | Hybrid enhancement | Required explanation |
|---|---|---|---|
| Phantom / billed-not-evidenced | Exact/terminology-mapped line-to-resource match; status/time rules | Peer-level anomaly on evidence completeness and service combination | Unsupported line; expected evidence type; searched resources; possible counter-evidence |
| Repeat billing | Exact claim/episode fingerprint and overlap rules | Weighted record linkage for near-duplicates with changed fields | Candidate pair; matched/different fields; time/amount overlap |
| Cloning | Character n-gram TF-IDF or MinHash similarity above validated threshold | Multilingual sentence embedding and service-sequence similarity, only if incremental value exists | Similarity components and matched fragments; templating caveat |
| Unbundling | Same participant/provider, adjacent time, shared diagnosis/episode, split service rules | Graph/temporal anomaly score for unusual episode fragmentation | Timeline, shared context, split lines/amounts, exceptions |


## Feature families
- Evidence completeness: supported billed-line ratio, missing reference count, invalid status/timestamp count.
- Episode integrity: overlapping encounters/claims, gap between related claims, repeated claim-line fingerprints.
- Similarity: note n-grams, procedure/diagnosis set similarity, service-sequence edit distance.
- Peer context: provider/service-frequency deviations within a synthetic peer group.
- Provenance: conflicting updates, missing authorship/time, bundle version inconsistencies.
- Amount/quantity: reconciliation deltas; all amounts are synthetic and illustrative.
Exclude protected or sensitive characteristics from scoring unless an authorized fairness analysis later establishes a legitimate purpose. Demographics are not necessary for the four core modes.
## Risk aggregation
Return a vector of reason-level evidence, not only a scalar. A simple prototype combiner is sufficient:
priority = max(deterministic_reason_priority, calibrated_similarity_score, calibrated_anomaly_score)
Apply caps and gates:
- no high-priority band from text similarity alone;
- missing evidence plus an incomplete bundle lowers certainty and triggers “request evidence,” not “confirm anomaly”;
- exact duplicate fingerprint is high priority but still human-reviewed;
- store all component scores and versions.
If a learned combiner is used, compare it to this simple baseline and remove it if it adds no meaningful value.
## Optional LLM guardrails
The MVP does not require an LLM. If time remains after Gate 6, an optional summary may be added with these controls:
- structured JSON evidence only; no direct raw-record prompt by default;
- local or approved deployment; no sensitive data sent to a third party;
- maximum 5-sentence output with inline resource IDs;
- fixed instruction to state uncertainty and never use “fraud” as a finding;
- reject output containing unsupported resource IDs or numbers;
- deterministic template fallback;
- human sees the raw reasons beside the summary;
- LLM output never feeds the score or status transition.
## Model/version artifacts
Every evaluation run records dataset hash, generator version, split manifest, feature version, rule version, model hyperparameters, threshold logic, code commit, environment, and result artifact hashes. A model card must state intended use, prohibited use, data, metrics, limitations, fairness considerations, human oversight, and monitoring plan.
