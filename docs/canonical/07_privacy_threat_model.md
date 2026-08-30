> Sumber: docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx §16
> Status: canonical — read-only. Perubahan hanya lewat ADR baru.


# 07 — Privacy, Security, Ethics & Governance (Threat Model)

**Cross-reference (jangan salin isinya ke sini):**

- Security and observability by design → [03_architecture.md](03_architecture.md)
- Prohibited use and model/version artifacts → [05_model_card.md](05_model_card.md)
- Official privacy/originality rules → [00_competition_brief.md](00_competition_brief.md)
- Regulatory sources [E12], [E16], [E23]–[E24] → [sources.md](sources.md)

---

# 16. Privacy, Security, Ethics & Governance
## Regulatory anchor
UU 27/2022 classifies health data, biometric data, and genetic data as specific personal data and regulates rights, processing duties, controllers/processors, transfers, sanctions, and related governance. [E12] Permenkes 24/2022 governs medical records; UU 17/2023 and PP 28/2024 provide the broader health-law framework. [E16, E23–E24] The proposal must not pretend this section is legal advice; production design requires BPJS/Kemenkes legal and security review.
## Product controls
| Risk area | Prototype control | Production requirement |
|---|---|---|
| Real participant data | Use synthetic records only | Written authority, lawful basis, role definition, DPIA/risk assessment |
| Identification | Pseudonymous IDs; no names/NIK | Tokenization service, controlled re-identification, separation of duties |
| Data minimization | Only fields needed for the selected reasons | Field-by-field purpose and retention schedule |
| Access | Simulated analyst/reviewer roles | Enterprise IAM, least privilege, MFA, periodic review |
| Transmission/storage | Local synthetic demo | TLS, encryption at rest, key management, backup and recovery |
| Logging | No raw health text in logs | Central secure logs, retention, tamper detection, incident monitoring |
| Audit | Append-only disposition events | Immutable/controlled ledger, review and appeal process |
| Model bias | Exclude demographics from core scoring; subgroup test where meaningful | Representative validation, fairness monitoring, documented response |
| False accusation | “Risk/anomaly requiring review”; human confirmation | Policy, training, appeal, evidence threshold, legal review |
| LLM hallucination | No LLM in decision; optional bounded summary | Approved deployment, prompt/output validation, monitoring, red-team |
| Prompt/data leakage | No external LLM default; structured inputs | Data-loss prevention, tenant isolation, provider agreements |
| Model misuse | UI and API prohibit automatic denial/sanction | Authorization, downstream-use controls, contractual limitations |


## Threat scenarios and response
- Incomplete RME looks like phantom billing. Display bundle completeness and counter-evidence; route to “request evidence,” not accusation.
- Legitimate templating looks like cloning. Require cross-feature corroboration; text similarity alone cannot reach the highest band.
- Reviewer anchors on red score. Show reason before score, include counter-evidence, and require a reason for confirmation.
- Adversary learns thresholds. Version rules, monitor distribution shift, combine deterministic and peer signals, and limit detail by role.
- Sensitive text appears in logs or exports. Redact by default, test logging, and restrict case export.
- Model performance drifts. Track feature and reason distributions; sample low-risk cases; require revalidation before model changes.
- A disposition is edited after the fact. Append a superseding event; never overwrite history.
## Human accountability
AI detects and prioritizes → evidence and uncertainty are shown → a trained human reviews → the human confirms, rejects, requests evidence, or escalates → the system records the decision, rationale, evidence, and version. The future operating policy must specify who may make each decision and how affected facilities can respond or appeal.
## Governance deliverables
- Data card and model card.
- System purpose and prohibited-use statement.
- Role/access matrix.
- Threat model and privacy impact checklist.
- Rule/model change-control process.
- Audit schema and retention proposal.
- Incident and false-positive response runbook.
- Pilot ethics and expert-validation plan.
