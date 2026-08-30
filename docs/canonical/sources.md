> Sumber: docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx §03 + §26
> Status: canonical — read-only. Perubahan hanya lewat ADR baru.


# Sources — Research Findings & Source Register

**Cross-reference (jangan salin isinya ke sini):**

- Official rules extracted from [PDF-PG] / [PDF-PP] → [00_competition_brief.md](00_competition_brief.md)
- Data-source access limitations → [04_data_card.md](04_data_card.md)
- Open validation questions raised by these findings → [02_domain_assumptions.md](02_domain_assumptions.md)

---

# 03. Research Findings
## JKN scale and risk-efficiency context
EXTERNAL EVIDENCE. The DJSN November 2025 monitoring report recorded 283 million registered JKN participants, 232.89 million active participants, 664.3 million visits through November, and Rp172.59 trillion in health-benefit expense. In that report, the claim ratio was 108.04% and had been above 100% since 2023. [E06] BPJS’s public site later reported 284,316,178 participants as of 31 July 2026. [E07]
Interpretation: JKN operates at extraordinary volume under financial pressure, so even small improvements in prioritization or preventable claim rework could matter. The figures do not establish that fraud caused the deficit or quantify fraud losses.
## Claim evidence is becoming a national integration priority
EXTERNAL EVIDENCE. On 30 July 2026, Kemenkes described a joint circular involving KPK, Kemendagri, BPJS Kesehatan, and BSSN to accelerate RME integrated with SATUSEHAT for JKN claims. The ministry connected NIK-linked RME and electronic supporting evidence to faster claims, traceability, transparency, oversight, and prevention of deviations. [E01]
SATUSEHAT’s official claim documentation describes an end-to-end flow in which a facility registers the visit and clinical/billing resources, applies through E-Klaim, sends a signed Claim plus RME Bundle to BPJS, receives ClaimResponse, and follows up with PurificationDecision. The published resources include Account, ChargeItem, Claim, ClaimResponse, Coverage, Invoice, and PurificationDecision, plus clinical RME resources. [E02–E04]
Interpretation: this makes an evidence-integrity layer timely and architecturally grounded. It does not prove that a public production API or competition sandbox is available.
## Hospital digitalization is advanced but uneven
Kemenkes’s policy agency reported in October 2025 that 34,463 facilities were integrated with SATUSEHAT and that 3,138 of 3,239 hospitals had RME, while 495 hospitals had not implemented all six core services; infrastructure and human-resource challenges remained. [E05] Permenkes 24/2022 is the operative national medical-record regulation. [E16]
Interpretation: compatibility with published standards is strategic, but production assumptions must accommodate incomplete and heterogeneous data. The prototype should expose missing evidence rather than fail silently.
## Anti-fraud activity exists; do not pretend BPJS starts from zero
KPK described collaboration with BPJS Kesehatan and 2023 case detection involving cataract, caesarean section, and hemodialysis claims in three hospitals across two provinces. [E08] BPJS has also publicly discussed automated checking and flagging of suspected claims, although the referenced BPJS data-portal article is commentary and explicitly not official policy. [E14]
Interpretation: “BPJS has no fraud detection” would be false and strategically weak. TilikKlaim must be positioned as a standards-based evidence and human-review layer that could complement existing controls—not replace unknown internal systems.
## Public data exists, but access and representativeness are constrained
BPJS’s public data portal lists 75 datasets and describes a 2025 longitudinal sample spanning 2015–2024. [E09] A 2025 peer-reviewed analysis describes the JKN sample as approximately 1% of insured participants and containing participant, visit, diagnosis, referral, and tariff information. [E10] Public descriptions indicate registration, research-proposal, identity, and integrity-agreement steps; the exact competition-use license and current codebook must be confirmed before use. [E09]
There is no public evidence that the sample contains verified fraud labels, signed SATUSEHAT claim bundles, complete RME narratives, or every field required for the four selected modes. Therefore, it cannot be the critical path.
## Why a hybrid, explainable method is technically defensible
A 2025 systematic review of machine learning in healthcare claims fraud detection found persistent challenges around data quality, class imbalance, scarce labels, interpretability, and operational integration. [E19] A 2025 peer-reviewed study demonstrated an explainable unsupervised workflow intended to help investigators discover anomalous practitioners or groups rather than automatically decide fraud. [E20] A 2026 JKN-journal review describes supervised, unsupervised, and ensemble approaches across the field. [E18]
Interpretation: use deterministic rules for known evidence constraints and modest anomaly/similarity methods for prioritization. Complex deep models are unjustified without real, representative labels.
## AI governance is a first-class product requirement
Kemenkes has publicly emphasized responsible AI governance, privacy, quality, bias management, responsibility, and human oversight, including work through its AI committee. [E17] WHO’s 2024 guidance on large multimodal models for health warns about false or biased output, automation bias, cybersecurity, and sensitive-data risks. [E21]
Interpretation: the strongest AI story is disciplined use. TilikKlaim should ship without an LLM in the risk decision and make any later summarizer optional, grounded, and non-authoritative.
## Domain limitation and compensation plan
The team currently lacks direct access to doctors, BPJS verifiers, hospital administrators, coders, or investigators. Compensate with four controls:
- Use official mode definitions, SATUSEHAT schemas, regulations, and peer-reviewed methods as the bounded domain surface.
- Restrict the prototype to structural evidence and duplication signals that can be defined without medical-necessity adjudication.
- Maintain an assumption register and convert each clinical or workflow assumption into a validation question.
- Treat internal usability tests as interface checks only; never label them expert validation.

---

# 26. Sources
## Official competition documents — source of truth
- [PDF-PG] *Participant Guide Healthkathon 2026*, supplied official PDF, 9 pages. Relevant: objective/theme/challenge pp. 2–3; eligibility/rules pp. 4–5; detailed categories pp. 6–7; stages/timeline p. 8; disqualification p. 9.
- [PDF-PP] *Panduan Pembuatan Proposal Peserta Healthkathon 2026*, supplied official PDF, 14 pages. Relevant: format/constraints p. 2; six criteria p. 3; category references pp. 4–5; required proposal components pp. 6–14.
## Tier 1 — official government, BPJS, and public institutions
- [E01] Kementerian Kesehatan RI, 30 July 2026. Kemenkes Perkuat Tata Kelola Klaim JKN melalui Integrasi Rekam Medis Elektronik dengan SATUSEHAT.
- [E02] SATUSEHAT Platform. Interoperabilitas Klaim BPJS.
- [E03] SATUSEHAT Platform. PurificationDecision FHIR Resource.
- [E04] SATUSEHAT Platform. Interoperabilitas RME Rawat Jalan.
- [E05] Badan Kebijakan Pembangunan Kesehatan, 28 October 2025. Wajib Integrasi SATUSEHAT, Kemenkes Desak Percepatan RME di Fasyankes. Note: cite the official Permenkes 24/2022 separately because the article appears to mistype the year/number.
- [E06] Dewan Jaminan Sosial Nasional, November 2025. Laporan Monitoring Program JKN per 30 November 2025.
- [E07] BPJS Kesehatan. Official BPJS Kesehatan website — participant count displayed as of 31 July 2026 when accessed 29 August 2026.
- [E08] Komisi Pemberantasan Korupsi, 19 September 2024. Sinergi KPK–BPJS Kesehatan Kawal Layanan Kesehatan Anti-Fraud. Note: the article appears to mistype the anti-fraud regulation; use Permenkes 16/2019 as the authoritative regulation.
- [E09] BPJS Kesehatan Data Portal. Dataset landing page and portal. Confirm access terms and current codebook before use.
- [E12] BPK Database Peraturan. UU Nomor 27 Tahun 2022 tentang Pelindungan Data Pribadi.
- [E14] BPJS Kesehatan Data Portal commentary. Data dan Teknologi dalam Deteksi Kecurangan JKN. The page carries a disclaimer and is used only to avoid assuming no existing controls.
- [E15] BPJS Kesehatan. Mobile JKN account manual and biometric manual.
- [E16] Kementerian Kesehatan RI JDIH. Permenkes Nomor 24 Tahun 2022 tentang Rekam Medis.
- [E17] Kementerian Kesehatan RI. Kementerian Kesehatan Perkuat Tata Kelola AI untuk Mendukung Transformasi Kesehatan and Pemanfaatan AI Kesehatan Harus Diiringi Tata Kelola Ketat.
- [E22] SATUSEHAT Platform. Interoperabilitas Rujukan.
- [E23] BPK Database Peraturan. UU Nomor 17 Tahun 2023 tentang Kesehatan.
- [E24] BPK Database Peraturan. PP Nomor 28 Tahun 2024 tentang Peraturan Pelaksanaan UU Kesehatan.
- [E25] BPK Database Peraturan. Permenkes Nomor 16 Tahun 2019 tentang Pencegahan dan Penanganan Kecurangan serta Pengenaan Sanksi Administrasi terhadap Kecurangan dalam Pelaksanaan Program JKN.
- [E26] BPK Database Peraturan. Perpres Nomor 59 Tahun 2024 tentang Perubahan Ketiga atas Perpres 82/2018 tentang Jaminan Kesehatan.
## Tier 2 — peer-reviewed research and established technical sources
- [E10] BMC Health Services Research, 2025. Analysis using Indonesia’s National Health Insurance sample data. Used for the described approximate sample scale and variable domains; confirm the current BPJS codebook directly.
- [E11] Synthea / SyntheticMass. Synthea GitHub repository and official documentation. Apache License 2.0; synthetic records are not representative of JKN without validated localization.
- [E18] Rasyid & Shiddiq, 2026, *Jurnal Jaminan Kesehatan Nasional*. Healthcare Fraud Detection Research (2015–2025): A Bibliometric and Meta-Scientific Review, DOI 10.53756/jjkn.v6i1.447.
- [E19] du Preez et al., 2025, *Artificial Intelligence in Medicine*. Fraud detection in healthcare claims using machine learning: a systematic review, DOI 10.1016/j.artmed.2024.103061.
- [E20] De Meulemeester et al., 2025. Explainable unsupervised anomaly detection for healthcare claims.
- [E21] World Health Organization, 18 January 2024. WHO releases AI ethics and governance guidance for large multi-modal models.
## Tier 3 — credible secondary reporting, used narrowly
- [E13] Detik, report on Healthkathon 2025 winners. BPJS Kesehatan Rilis Pemenang Healthkathon 2025. Used only to establish the publicly reported title of the third-place AI solution; its detailed functionality is not established.
## Source quality cautions
- Several official news articles contain apparent regulation-number typos; this plan cites the authoritative regulation pages for legal references.
- Portal pages may change or require authentication. Capture dated copies/screenshots for proposal substantiation where permitted.
- No source above establishes a current national JKN fraud-loss figure, real-world performance for TilikKlaim, or detailed BPJS internal system capability. Do not infer those claims.
