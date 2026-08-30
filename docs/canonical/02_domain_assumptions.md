> Sumber: docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx §06 (red-team TilikKlaim) + §07 (assumptions) + §25
> Status: canonical — read-only. Perubahan hanya lewat ADR baru.


# 02 — Domain Assumptions, Red-Team & Validation Questions

**Cross-reference (jangan salin isinya ke sini):**

- Official rules and the disputed category mode → [00_competition_brief.md](00_competition_brief.md)
- Selected solution, scope tiers, kill criteria → [01_product_decision.md](01_product_decision.md)
- Data limitations and what cannot be obtained publicly → [04_data_card.md](04_data_card.md)
- Evidence labels [E01]..[E26] → [sources.md](sources.md)

---

> Diekstrak dari §06 — Evaluation & Red-Team Analysis.

## Red-team: A — TilikKlaim
- Why it could lose: claim-risk screening is a common idea; judges may see “another fraud detector.”
- Existing overlap: the 2025 third-place AI solution was publicly named “PRO-CLAIM: Co-Pilot AI Validasi Klaim Anti Fraud.” [E13] Detailed overlap is not public; Evidence not established.
- Data failure: public sample data may lack RME bundles or labels; synthetic patterns may be too easy.
- AI necessity: a rules-only checker may solve most MVP cases. That is acceptable; the hybrid must prove incremental ranking value or be removed.
- Measurement risk: synthetic F1 can look impressive while saying little about real JKN.
- Integration risk: no evidence of live BPJS/E-Klaim/SATUSEHAT sandbox access.
- Privacy risk: evidence screens can expose sensitive health data and create accusation harm.
- Thirty-second test: strong if the UI shows “billed item → missing evidence”; weak if the pitch starts with model names.
- Copyability: many teams can claim anomaly detection; fewer will provide reproducible injections, explicit evidence provenance, baseline comparisons, and human dispositions.
Counter-strategy: lead with the traceable evidence workflow, publish the synthetic limitations, keep the core non-generative, and position integration as standards-compatible—not connected.

---

> Diekstrak dari §07 — Selected Solution.

## Assumptions
- Published SATUSEHAT resources are sufficient to model at least three selected modes structurally.
- A hospital pre-submission workflow is acceptable to organizers as a JKN ecosystem solution.
- Synthetic FHIR plus injected patterns is acceptable when clearly disclosed.
- Reviewers value evidence traceability more than an opaque probability score.
- The team can create a stable local demo without live external connections.

---

# 25. Questions Requiring Validation
## Ask organizers first
- Which category officially owns “Kolusi & Surat Fiktif” given the conflict between the two PDFs?
- Are the two “inflated bills” entries in the Participant Guide distinct or duplicated editorially?
- What is the exact submission closing time and time zone on 19 September?
- Are prototype links, videos, QR codes, appendices, or hidden backup slides allowed and evaluated?
- Does use of the BPJS public sample require separate written permission under the competition’s real-data restriction?
- Will selected teams receive authorized datasets, a sandbox, schema package, or API documentation later?
- Should facility-category proposals target pre-submission facility controls, BPJS pre-payment verification, or either?
- Which version/profile of SATUSEHAT Claim/RME Bundle should a prototype follow?
- Does originality assessment consider similarity to previous Healthkathon finalists, including PRO-CLAIM, and can high-level functional boundaries be clarified?
- What are the later-stage dates, judging format, demo duration, internet conditions, and required deliverables?
- Are official judging weights used internally even though none are published in the proposal guide?
- What IP/usage rights apply to 2026 submissions and prototypes? The supplied guide establishes originality but does not provide a complete IP-transfer framework.
## Ask BPJS/facility/coaches when access exists
- Who performs the first substantive check before a claim is submitted, and what systems/screens do they use?
- What are the top five reasons claims are pending, corrected, or escalated, by volume and effort?
- Which selected risk modes are most valuable to detect before submission versus after submission?
- Which Claim/RME resources and link fields are reliably populated today, and where is missingness common?
- How are legitimate incomplete records, templated notes, follow-ups, and split episodes distinguished from risk?
- What is an acceptable false-positive rate and review budget for each role?
- What reviewer dispositions, evidence requests, escalation steps, and appeal/correction mechanisms exist?
- Which evidence must be visible for a verifier to trust and act on a signal?
- Which codes/crosswalks and clinical/coding guidelines may be used and redistributed?
- Are current automated flags explainable to users, and where would an evidence layer complement rather than duplicate them?
- What audit, retention, access-control, data-residency, and incident requirements would apply?
- Which facility types, regions, or service lines should a pilot include to test representativeness and fairness?
- What outcome would constitute pilot success: fewer pending claims, faster review, improved confirmed-risk yield, reduced rework, or another metric?
## Assumptions that remain unvalidated
- Pre-submission hospital casemix review is an accepted target workflow.
- The four selected modes can be represented with available electronic evidence.
- Published resource relationships approximate competition expectations.
- Synthetic injections are acceptable proposal evidence when fully disclosed.
- Evidence traceability is a meaningful current pain beyond existing tools.
- Reviewers can act on the four proposed dispositions.
- A rule-plus-similarity/anomaly hybrid improves prioritization at an acceptable false-positive rate.
- A standards-shaped sidecar architecture is a plausible future integration pattern.
