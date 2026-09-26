# TilikKlaim — Peta Hubungan Seluruh Dokumen Healthkathon 2026
*Disusun 2026-09-11, diperbarui 2026-09-11 (revisi 4) sebagai pelengkap [TilikKlaim_Architecture_Review.md](./TilikKlaim_Architecture_Review.md)*

> **Revisi 2**: `TilikKlaim_Healthkathon2026_FINAL_MERGED.pptx` diterbitkan — hasil perbandingan isi kedua draf 20-slide dan penggabungan bagian terbaik masing-masing. Ini sekarang **sumber kebenaran untuk materi submission**, menggantikan kedua file draf.
>
> **Revisi 3**: `FINAL_MERGED.pptx` diperbarui lagi — frasa "MVP to Market" (slide 15) diganti **"Prototipe ke Pasar"** untuk mematuhi larangan kanon, dan seluruh deck diberi font konsisten **Space Grotesk (heading, bold)** + **Inter (body)**, termasuk di level theme. File lama yang sempat korup akibat konflik lock PowerPoint sudah dihapus dan digantikan versi bersih ini.
>
> **Revisi 4**: hasil audit [`TilikKlaim_Audit_ROI_dan_Metodologi.md`](./TilikKlaim_Audit_ROI_dan_Metodologi.md) ditindaklanjuti — klaim cakupan "8 dari 20 sub-kategori" diturunkan jujur jadi "4 mode aktif + 3 Tahap 2" di 5 slide, angka Rp 342 M diperbaiki jadi Rp 324 M, dan angka Rp 1,04 T di `ROI_Simulation.xlsx` sekarang tertelusur ke sel formula (bukan diketik manual). Lihat §2.10.

Dokumen ini memetakan **semua file terkait Healthkathon** di repo — dari pedoman resmi panitia sampai draf slide terbaru — dan menjelaskan bagaimana satu menurunkan yang lain. Tujuannya: Ketua Tim tahu **dokumen mana adalah sumber kebenaran** untuk klaim/angka/batasan tertentu, dan mana yang sekadar turunan/draf.

---

## 1. Rantai penurunan (derivation chain)

```
┌─────────────────────────────────────────────────────────────┐
│ SUMBER RESMI PANITIA (tidak boleh diubah, hanya dibaca)       │
├─────────────────────────────────────────────────────────────┤
│ docs/Pedoman_Healthkathon_2026.docx                           │
│   → pedoman & aturan kompetisi resmi dari BPJS Kesehatan +    │
│     Asosiasi Health Tech Indonesia (AHI)                      │
└───────────────────────┬───────────────────────────────────────┘
                         │ dianalisis & diterjemahkan jadi strategi
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ STRATEGI TIM (dokumen kerja, bukan resmi panitia)              │
├─────────────────────────────────────────────────────────────┤
│ docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx                │
│   → keputusan produk (TilikKlaim), 4 mode risiko, kill         │
│     criteria, backup concept RujukTepat, § 20 constraints      │
└───────────────────────┬───────────────────────────────────────┘
                         │ dipecah jadi dokumen kanonikal per topik
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ KANON PRODUK (read-only, hanya berubah lewat ADR)               │
├─────────────────────────────────────────────────────────────┤
│ docs/canonical/00_competition_brief.md      ← ringkasan brief   │
│ docs/canonical/01_product_decision.md       ← keputusan & scope │
│ docs/canonical/02_domain_assumptions.md                          │
│ docs/canonical/03_architecture.md                                │
│ docs/canonical/04_data_card.md                                   │
│ docs/canonical/05_model_card.md                                  │
│ docs/canonical/06_evaluation_plan.md                              │
│ docs/canonical/07_privacy_threat_model.md                         │
│ docs/canonical/08_demo_runbook.md                                  │
│ docs/canonical/09_proposal_evidence_map.md                         │
│ docs/canonical/10_risk_register.md                                  │
│ docs/canonical/decisions/ADR-0001 … ADR-0006  ← keputusan terkunci   │
└───────────────────────┬───────────────────────────────────────┘
                         │ diterjemahkan ke bahasa bisnis-teknis per modul
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ BRIEF PRODUK (6 modul, bahasa Indonesia)                          │
├─────────────────────────────────────────────────────────────┤
│ brief/00_OVERVIEW.md              ← pitch & blueprint 5-lapis      │
│ brief/01_INGEST_VALIDASI.md                                        │
│ brief/02_MESIN_BUKTI_DETEKSI.md                                    │
│ brief/03_ANTREAN_REVIEW.md                                         │
│ brief/04_DETAIL_KASUS_DISPOSISI.md                                 │
│ brief/05_AUDIT_EVALUASI.md                                         │
│ brief/06_DATA_SINTETIK.md                                          │
└───────────────────────┬───────────────────────────────────────┘
                         │ dipecah jadi rencana eksekusi per sprint
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ EKSEKUSI (sprint & kode)                                         │
├─────────────────────────────────────────────────────────────┤
│ sprint/00-app-spec.md            ← spesifikasi halaman           │
│ sprint/01-sprint-planning.md     ← tabel status 12 sprint          │
│ sprint/backlog/00…11-*/           ← task per stack per sprint       │
│ apps/, packages/                  ← kode aktual (lihat Architecture │
│                                      Review untuk detail)            │
└───────────────────────┬───────────────────────────────────────┘
                         │ status kerja & serah-terima antar sesi
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ OPERASIONAL SESI (state tracking, bukan untuk juri)               │
├─────────────────────────────────────────────────────────────┤
│ docs/HANDOVER.md          ← snapshot state utk sesi baru           │
│ docs/CONTINUE-PROMPT.md   ← prompt siap-tempel lanjutkan kerja      │
│ docs/qa/MANUAL-QA.md      ← checklist QA visual manual              │
│ docs/plans/*.md           ← rencana implementasi per fitur (arsip)  │
│ docs/prompts/*.md         ← arsip prompt task tertentu              │
│ changelog/{backend,web,mobile,sprint-planning}.md ← log historis    │
│ docs/api/openapi.json     ← kontrak API yang dihasilkan otomatis    │
└───────────────────────┬───────────────────────────────────────┘
                         │ dirangkum jadi materi presentasi
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ MATERI SUBMISSION (deliverable ke juri)                            │
├─────────────────────────────────────────────────────────────┤
│ Bagian7_TilikKlaim_Healthkathon2026.pptx        ← 3 slide, parsial   │
│                                                                         │
│ ★ Claude outputs/TilikKlaim_Healthkathon2026_FINAL_MERGED.pptx        │
│   ← SUMBER KEBENARAN SAAT INI — gabungan terbaik kedua draf +          │
│     perbaikan "MVP" + font Space Grotesk/Inter (§2.7–2.9)              │
│                                                                         │
│ TilikKlaim_Healthkathon2026_DRAFT.pptx          ← draf lama, SUPERSEDED│
│   (di root, 709 KB, 11 Sep 16:20 — basis utama file MERGED)            │
│ Claude outputs/TilikKlaim_Healthkathon2026_Draft.pptx                  │
│   ← draf lama lain, SUPERSEDED (112 KB, 11 Sep 16:38 — 2 kalimat       │
│      klaimnya diambil ke dalam file MERGED)                            │
│                                                                         │
│ Claude outputs/TilikKlaim_Cover_Preview.jpg     ← preview cover        │
│ Claude outputs/TilikKlaim_MethodologyNote_ExpectedCostMatrix.docx      │
│ Claude outputs/TilikKlaim_ROI_Simulation.xlsx                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Detail per lapisan

### 2.1 Sumber resmi panitia
| Dokumen | Isi | Status |
|---|---|---|
| [`docs/Pedoman_Healthkathon_2026.docx`](docs/Pedoman_Healthkathon_2026.docx) | Pedoman kompetisi resmi dari BPJS Kesehatan + AHI. Tema: *Efisiensi Risiko pada Pelayanan Kesehatan Program JKN*. Latar belakang: 90%+ faskes terkoneksi SATUSEHAT, 270 juta rekam medis elektronik, proyeksi WHO kekurangan 11 juta nakes global 2030. | **Otoritatif** — tidak boleh disimpulkan ulang, hanya dikutip |

### 2.2 Strategi tim
| Dokumen | Isi | Status |
|---|---|---|
| [`docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx`](docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx) | Dokumen strategi 122.000+ karakter: keputusan tanggal 29 Agustus, nama produk **TilikKlaim**, judul proposal usulan, tagline, 4 label evidence (OFFICIAL PDF / WEBINAR SIGNAL / EXTERNAL EVIDENCE / ANALYSIS / ASSUMPTION — dipakai konsisten di seluruh dokumen turunan), § 20 constraints (sumber tunggal semua batasan "tidak boleh" yang berulang di canonical/*), § 22 Demo Plan (basis Sprint 07). | **Kerja tim, bukan resmi panitia** — tapi jadi rujukan tunggal untuk semua batasan proyek |

### 2.3 Kanon produk (`docs/canonical/`)
Dijelaskan detail di [Architecture Review §12](./TilikKlaim_Architecture_Review.md#12-aturan-non-negotiable-dari-docscanonical). Setiap file adalah pemecahan satu topik dari master plan, ditambah 6 ADR yang mengunci keputusan arsitektur spesifik (mis. ADR-0002 = tidak ada LLM di skor risiko, ADR-0006 = 3 peran simulasi login).

### 2.4 Brief produk (`brief/`)
6 modul dalam bahasa Indonesia, "diterjemahkan" dari kanon jadi bentuk yang lebih mudah dibaca product/business — dipakai sprint planning sebagai referensi (lihat kolom "Brief" di tabel sprint).

### 2.5 Sprint & kode
`sprint/01-sprint-planning.md` adalah tabel master 12 sprint dengan status, sudah dibahas mendalam di percakapan sebelumnya (Sprint 06 & 07 masih 🚧).

### 2.6 Dokumen operasional sesi
Ini **bukan untuk juri** — ini catatan serah-terima antar sesi kerja AI/developer:
- **`HANDOVER.md`** — paling penting: state snapshot lengkap, termasuk peringatan tegas *"every sprint's code is finished... if you go looking for a feature to build, you will build something nobody asked for."* Ini konfirmasi independen atas kesimpulan saya sebelumnya bahwa sisa kerja adalah non-teknis.
- **`CONTINUE-PROMPT.md`** — prompt siap pakai untuk melanjutkan sesi, mengonfirmasi tanggal kerja **4 September** (jadi ini agak usang dibanding tanggal repo sekarang 11 September — beberapa commit sudah terjadi setelah dokumen ini ditulis, termasuk Sprint 08-11 yang kini ✅ Done).
- **`qa/MANUAL-QA.md`** — checklist visual manual pemilik produk.
- **`docs/plans/`, `docs/prompts/`** — arsip rencana/prompt untuk fitur spesifik (evidence workspace, auth roles) — riwayat, bukan rencana aktif.
- **`changelog/*.md`** — log historis per stack.

### 2.7 Materi submission (paling relevan untuk kamu sekarang)
| File | Lokasi | Ukuran | Waktu ubah | Status |
|---|---|---|---|---|
| `Bagian7_TilikKlaim_Healthkathon2026.pptx` | root | 131 KB | 6 Sep 17:36 | Hanya **3 slide** — bagian/section terpisah, bukan deck lengkap. Belum diperiksa isinya |
| **`Claude outputs/TilikKlaim_Healthkathon2026_FINAL_MERGED.pptx`** | Claude outputs | ~700 KB | 11 Sep (terbaru) | ★ **SUMBER KEBENARAN** — lihat §2.8 untuk rincian |
| `TilikKlaim_Healthkathon2026_DRAFT.pptx` | root | 709 KB | 11 Sep 16:20 | SUPERSEDED — basis utama file MERGED, disarankan diarsipkan |
| `Claude outputs/TilikKlaim_Healthkathon2026_Draft.pptx` | Claude outputs | 112 KB | 11 Sep 16:38 | SUPERSEDED — 2 kalimatnya sudah diambil ke MERGED, disarankan diarsipkan |
| `Claude outputs/TilikKlaim_Cover_Preview.jpg` | Claude outputs | 63 KB | 10 Sep 21:59 | Preview gambar cover saja |
| `Claude outputs/TilikKlaim_MethodologyNote_ExpectedCostMatrix.docx` | Claude outputs | 16 KB | 11 Sep 13:59 | Catatan metodologi "Expected Cost Matrix" — lampiran pendukung Tahap 2 (belum berkode, lihat §2.10). Sudah diaudit, tidak diubah |
| `Claude outputs/TilikKlaim_ROI_Simulation.xlsx` | Claude outputs | ~13 KB | 11 Sep (diaudit & diperbaiki) | ✅ Sudah diaudit — lihat [TilikKlaim_Audit_ROI_dan_Metodologi.md](./TilikKlaim_Audit_ROI_dan_Metodologi.md) dan §2.10. Ditambah 3 baris formula baru di sheet "Dampak Nasional" |

### 2.8 Hasil perbandingan & penggabungan dua draf 20-slide

Kedua draf lama (`.../DRAFT.pptx` di root vs `Claude outputs/.../Draft.pptx`) dibandingkan slide-per-slide. Slide 2–12, 16, 17, 19 identik persis di keduanya. Perbedaan yang ditemukan dan cara diselesaikan di file **FINAL_MERGED**:

| Perbedaan | Draf root | Draf Claude outputs | Keputusan di FINAL_MERGED |
|---|---|---|---|
| Slide 1 — judul | "Kendali Risiko Klaim JKN di Tangan Faskes" | "Pre-Submission Claim Integrity System..." | Dipakai versi **root** |
| Slide 15 — klaim integrasi Fase 3 | "Integrasi SATUSEHAT & HL7/FHIR R4" (berisiko overclaim) | "Integrasi 1 vendor SIM RS" (lebih aman) | **Diganti** ke versi Claude outputs — lebih patuh larangan "no production-integration claim" |
| Slide 18 — baris dampak finansial tambahan | Ada blok "Rp PAYER / VALUE for BPJS / SUSTAINABILITY" | Diganti kalimat "Semua proyeksi berbasis asumsi transparan — akan divalidasi di pilot Fase 1–2" | **Diganti** ke versi Claude outputs — eksplisit melabeli asumsi, sesuai `06_evaluation_plan.md` |
| Slide 20 — profil tim | Nama **asli**: Luthfi (Ketua Tim), Fahri, Dany + role masing-masing | Placeholder "[Nama Anggota 1/2/3]" — belum diisi | Dipakai versi **root** (satu-satunya yang punya data nyata) |
| Gaya ikon | Simbol geometris (▶●■✓×) | Emoji (🔍👤🔒📋✅❌) | Dipakai versi **root** (konsisten dipertahankan di seluruh deck) |

⚠️ **Belum diverifikasi secara visual** (hanya lewat ekstraksi teks XML) — sebelum submit, buka file MERGED di PowerPoint untuk memastikan slide 18 tidak tampak kosong/timpang di area yang teksnya diganti, dan pastikan tata letak slide 15 masih rapi setelah teks "Integrasi 1 vendor / SIM RS" menggantikan baris asli.

### 2.9 Revisi 3 — perbaikan "MVP" & standarisasi font

- **Slide 15**: frasa nama fase "MVP to Market" diganti **"Prototipe ke Pasar"** — sebelumnya melanggar langsung larangan `01_product_decision.md`: *"jangan pernah klaim MVP ke juri, sebut functional prototype."* Istilah baru konsisten dengan kata "Prototipe" yang sudah dipakai di skala TRL pada slide yang sama.
- **Font di seluruh 20 slide** diseragamkan berdasarkan pola yang sudah ada di deck asli (heading pernah pakai Cambria, body pakai Calibri — keduanya diganti 1:1):
  - **Space Grotesk, bold** → seluruh teks heading (38 run teks: judul slide, nama besar "TilikKlaim", dll)
  - **Inter** → seluruh teks body (491 run teks: deskripsi, label, angka statistik, dll)
  - Diterapkan di level run (`<a:latin>`, `<a:ea>`, `<a:cs>`) **dan** di level theme (`majorFont`/`minorFont`) agar konsisten kalau ada placeholder yang menarik font dari theme.
  - ⚠️ **Font akan tampil benar hanya jika Space Grotesk dan Inter terinstall** di komputer yang membuka file (keduanya font Google Fonts, gratis) — kalau belum terinstall, PowerPoint otomatis fallback ke font default sampai diinstall.
- File lama sempat korup akibat konflik file-lock saat proses edit bertepatan dengan file sedang terbuka di PowerPoint — sudah dibersihkan; `FINAL_MERGED.pptx` saat ini adalah hasil regenerasi bersih.

### 2.10 Revisi 4 — tindak lanjut audit ROI & Methodology Note

Audit lengkap ada di [TilikKlaim_Audit_ROI_dan_Metodologi.md](./TilikKlaim_Audit_ROI_dan_Metodologi.md). Ringkasan keputusan Ketua Tim dan hasil eksekusi:

**Keputusan**: fitur *Inflated Bills*, *Upcoding*, *Manipulasi Kelas Perawatan* (dideskripsikan rinci di `MethodologyNote_ExpectedCostMatrix.docx` tapi nol implementasi di kode) **tidak dikejar untuk dibangun sebelum submission**. Fokus tetap pada 4 rule yang sudah berkode dan teruji (phantom, repeat, unbundling, cloning). Ketiga fitur itu dijadikan **"Tahap 2 — dilanjutkan jika lolos seleksi proposal"**.

**Perubahan di `FINAL_MERGED.pptx`** (5 slide):
- Slide 2: "CAKUPAN (8 dari 20 sub-kategori)" → "**4 mode inti** aktif berkode (5 dari 20 sub-kategori)"; 3 item non-kode diberi tanda `→ (Tahap 2)`
- Slide 6: "4 Mode: ...7 item..." (kontradiktif) → "**4 Mode Aktif**...+3 mode Tahap 2"
- Slide 10: "Digunakan sebagai Expected Cost Matrix" → "Basis rencana Expected Cost Matrix (Tahap 2)"
- Slide 11: judul "8 Sub-Kategori" → "Metode Deteksi — Tahap 1 (Aktif) & Tahap 2 (Direncanakan)"
- Slide 15: **Fase 0 dan Fase 1 tadinya tertukar** (Fase 0/Sekarang mengklaim fitur yang belum ada, Fase 1 malah mengklaim fitur yang sudah ada) — sudah ditukar ke urutan yang benar

**Perbaikan angka finansial** (slide 18 + `ROI_Simulation.xlsx`):
- Rp 342 M → **Rp 324 M** (net benefit bersih yang benar, sebelumnya salah pakai angka kotor)
- `ROI_Simulation.xlsx` sheet "Dampak Nasional" ditambah 3 baris formula baru (asumsi 3% anomali + 20% tercegah, keduanya berlabel biru "ASUMSI — belum divalidasi", plus baris formula yang menghasilkan Rp 1,04 T) — angka ini sekarang **tertelusur ke artefak**, bukan diketik manual di slide

Methodology note **tidak dihapus** — tetap dilampirkan sebagai bukti metodologi Tahap 2 sudah siap, bukan sebagai klaim fitur aktif.

⚠️ Sisa item terbuka dari audit: Temuan #5 (opsional, ringan) — metodologi ROI di xlsx berbeda dari formula resmi `06_evaluation_plan.md` (`expected reviewed value = reviewed claim amount × observed confirmation rate × recoverable/correctable fraction`). Tidak wajib diubah, tapi bisa ditambah satu kalimat penjelas di lampiran.

---

## 3. Konsistensi lintas dokumen — apa yang sudah dan belum tervalidasi

| Aspek | Sumber kebenaran | Konsisten di eksekusi? |
|---|---|---|
| Nama produk & tagline | Master Plan | ✅ Konsisten di FINAL_MERGED |
| 4 mode risiko | Master Plan → `01_product_decision.md` → `service/rules/*.py` | ✅ **Diperbaiki** — slide 2 FINAL_MERGED kini menyebut "4 mode inti aktif" dengan 3 fitur tambahan jelas ditandai Tahap 2 (lihat §2.10) |
| "Tidak pernah fraud" | Master Plan §20 → `reasons.py`, `briefing/validation.py` | ✅ Ditegakkan di kode; slide 12 FINAL_MERGED eksplisit menulis "Sinyal adalah indikator, bukan bukti fraud" |
| Klaim overclaim integrasi | `01_product_decision.md` OUT OF SCOPE ("live BPJS/SATUSEHAT connection") | ✅ **Diperbaiki** di FINAL_MERGED slide 15 (lihat §2.8) |
| Klaim fitur yang belum berkode (Inflated Bills/Upcoding/Kelas Perawatan) | Kode aktual (`apps/backend/app/service/rules/`) | ✅ **Diperbaiki** — diturunkan jadi "Tahap 2" di 5 slide (lihat §2.10) |
| Larangan klaim penghematan biaya tanpa label asumsi / tanpa artefak | `06_evaluation_plan.md`, aturan §12 "generated artifact, never typed by hand" | ✅ **Diperbaiki** — Rp 342M→324M, Rp 1,04T kini tertelusur ke formula xlsx (lihat §2.10). ⚠️ Slide 17 (ROI 19× per RS) masih figur simulasi headline tanpa kalimat "asumsi" langsung di slide itu sendiri — pertimbangkan tambah 1 baris label serupa slide 18 |
| Label "prototype" bukan "MVP" | `01_product_decision.md` | ✅ **Diperbaiki** — slide 15 FINAL_MERGED kini memakai "Prototipe ke Pasar" (lihat §2.9) |
| Angka hasil evaluasi hybrid vs rules (Sprint 06) | Sprint 06 outcome (lihat Architecture Review §13) | ⚠️ Belum diperbaiki — deck tidak menyebut hasil evaluasi hybrid-vs-rules sama sekali (precision@K, recall@K, PR-AUC). Pertimbangkan menambah 1 slide bukti evaluasi kalau juri menilai rigor teknis |
| Nama tim di slide profil | Data internal tim | ✅ Nama asli dipakai di FINAL_MERGED slide 20 |

---

## 4. Rekomendasi tindak lanjut

1. ~~Bandingkan dua file draf pptx 20-slide~~ — **selesai**, lihat §2.8. `FINAL_MERGED.pptx` adalah acuan; kedua draf lama disarankan diarsipkan/dihapus dari folder submission agar tidak ada kebingungan versi.
2. ~~Ganti frasa "MVP to Market" di slide 15~~ — **selesai**, lihat §2.9.
3. ~~Standarisasi font~~ — **selesai**, lihat §2.9. **Perlu dicek**: apakah Space Grotesk & Inter sudah terinstall di komputer yang akan dipakai membuka/mempresentasikan file, agar tidak fallback ke font default saat presentasi/upload.
4. ~~Audit `TilikKlaim_ROI_Simulation.xlsx` dan `MethodologyNote_ExpectedCostMatrix.docx`~~ — **selesai**, lihat §2.10 dan [file audit lengkap](./TilikKlaim_Audit_ROI_dan_Metodologi.md). Klaim cakupan diturunkan jujur ke Tahap 1/2, angka Rp 342M dan Rp 1,04T diperbaiki & ditelusurkan ke artefak.
5. **Pertimbangkan menambah kalimat "asumsi" langsung di slide 17** (ROI 19×) — saat ini kalimat asumsi ada di bagian atas slide tapi headline angka ROI-nya sendiri tidak punya penanda eksplisit seperti yang sudah ditambahkan di slide 18.
6. **Pertimbangkan menambah slide bukti evaluasi Sprint 06** (precision@K, recall@K, PR-AUC hybrid vs rules-only) — deck saat ini tidak mengutip hasil evaluasi teknis resmi sama sekali, padahal itu salah satu aset paling kredibel yang dimiliki tim (lihat Architecture Review §13).
7. **`docs/CONTINUE-PROMPT.md` sudah usang** (bertanggal 4 September) — kalau masih dipakai untuk onboarding sesi kerja baru, sebaiknya diperbarui merujuk status sprint terkini (11 September, Sprint 08-11 sudah selesai).
8. **Verifikasi visual `FINAL_MERGED.pptx` di PowerPoint dan `ROI_Simulation.xlsx` di Excel** — semua perubahan teks, font, & formula dilakukan lewat edit terprogram (python-pptx/openpyxl); tata letak/pemformatan belum dicek mata langsung, terutama slide 2, 11, 15, 18, dan baris baru di sheet "Dampak Nasional".
