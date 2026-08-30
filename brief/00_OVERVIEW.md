# TilikKlaim — Dokumentasi Implementasi

> **Project slug:** `tilik_klaim` — canonical project ID, dipakai downstream sebagai `MCP_HUB_GROUP`.
> **Stage:** `MVP`
> **Sumber brief:** disintesis dari `docs/canonical/` (hasil ekstraksi `docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx`). Keputusan produk sudah final — brief ini menerjemahkan keputusan itu ke bahasa bisnis-teknis, bukan membuka ulang diskusinya.

---

## Catatan Stage — kenapa `MVP`, bukan `PoC`

Dua sumbu berbeda, jangan tertukar:

| Sumbu | Nilai | Penjelasan |
|-------|-------|------------|
| **Stage pipeline** (`.claude/rules/project-scope.md`) | `MVP` | Sistem butuh backend nyata (layer logika + layer data persisten + audit append-only). Aturan `PoC` melarang backend terpisah dan mewajibkan mock data di dalam project web — itu tidak cukup untuk audit trail immutable dan evaluasi reproducible. |
| **Maturity label ke juri** (Panduan Proposal) | `functional prototype` | Belum ada pengguna target terotorisasi yang memakai sistem dengan data representatif. Klaim "MVP" ke juri akan menyalahi definisi resmi panduan. |

Konsekuensi: kerja backend **diizinkan dan diperlukan**. Data yang mengalir di dalamnya tetap 100% sintetik. Naikkan maturity label ke juri hanya setelah minimal satu pengguna target terotorisasi menyelesaikan tugas inti dengan data representatif.

---

## Ringkasan Eksekutif

TilikKlaim adalah **lapisan integritas bukti klaim** untuk tim casemix dan anti-fraud rumah sakit. Sebelum sebuah klaim JKN dikirim ke BPJS, sistem membaca berkas klaim beserta rekam medis elektroniknya, menelusuri apakah setiap item yang ditagihkan benar-benar punya bukti klinis yang konsisten, lalu menandai empat pola risiko yang secara resmi disebut dalam kategori Efisiensi Risiko pada Fasilitas Kesehatan: tagihan tanpa bukti tindakan (phantom billing), tagihan berulang (repeat billing), dokumentasi hasil salinan (cloning), dan pemecahan episode (unbundling/fragmentation).

Nilai utamanya bukan skor. Nilai utamanya adalah **bukti yang bisa ditelusuri dan keputusan yang bisa dipertanggungjawabkan**. Setiap penandaan risiko selalu menunjuk ke sumber buktinya — baris tagihan mana, catatan klinis mana, rentang waktu mana — berikut bukti tandingannya kalau ada. Sistem tidak pernah menyatakan fraud, tidak pernah menolak klaim, dan tidak pernah menghentikan pembayaran. Keputusan akhir selalu di tangan manusia terlatih, dan setiap keputusan itu tercatat permanen beserta alasannya.

---

## 1. Visi dan Tujuan Sistem

### 1.1 Visi

Menjadikan risiko klaim JKN **terlihat, dapat ditinjau, dan dapat diaudit** sebelum klaim dikirim — sehingga koreksi terjadi di hulu, bukan menjadi sengketa di hilir.

### 1.2 Tujuan Utama

| Tujuan | Deskripsi |
|--------|-----------|
| Bukti sebelum skor | Setiap penandaan risiko harus menunjuk ke bukti sumber yang bisa dibuka, bukan berhenti di angka. |
| Prioritas kerja yang jujur | Petugas punya kapasitas review terbatas; sistem mengurutkan kasus yang paling informatif lebih dulu, bukan menampilkan semua sekaligus. |
| Keputusan tetap milik manusia | Sistem menyiapkan bahan; petugas yang memutuskan. Tidak ada penolakan, sanksi, atau perubahan kode secara otomatis. |
| Ketidakpastian yang ditampilkan | Bukti tandingan dan keterbatasan data ditampilkan di layar yang sama dengan sinyal risikonya — bukan disembunyikan. |
| Jejak audit yang tidak bisa diubah | Setiap disposisi menghasilkan catatan permanen berisi pelaku, waktu, alasan, bukti, dan versi aturan yang berlaku saat itu. |
| Bukti kinerja yang reproducible | Klaim performa apa pun harus lahir dari artefak evaluasi yang bisa dibangun ulang dari nol dengan satu perintah. |

---

## 2. Komponen Sistem Level Tinggi

> Deskripsi peran/fungsi setiap komponen, BUKAN teknologi spesifik. Penentuan teknologi ada di `docs/canonical/03_architecture.md` dan task file sprint.

### 2.1 Layer Sistem

```
┌─────────────────────────────────────────────────────────────────┐
│                     LAYER ANTARMUKA PENGGUNA                    │
│  [Antrean Review]  [Detail Kasus]  [Ingest/Demo]  [Audit&Eval]  │
├─────────────────────────────────────────────────────────────────┤
│                     LAYER LOGIKA APLIKASI                       │
│  [Validasi Bundel] [Perajut Bukti] [Mesin Aturan]               │
│  [Peringkat Risiko] [Disposisi & Audit]                         │
├─────────────────────────────────────────────────────────────────┤
│                     LAYER ANALITIK (bukan LLM)                  │
│  [Kemiripan dokumen] [Deteksi anomali antar-rekam]              │
│  [Kalibrasi ambang batas]                                       │
├─────────────────────────────────────────────────────────────────┤
│                     LAYER DATA                                  │
│  [Simpanan bundel mentah] [Model kanonik] [Jejak audit]         │
│  [Artefak evaluasi]                                             │
├─────────────────────────────────────────────────────────────────┤
│                     LAYER SUMBER DATA                           │
│  [Generator data sintetik] — TIDAK ADA integrasi eksternal      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Peran Komponen Utama

| Komponen | Peran |
|----------|-------|
| Antarmuka Pengguna | Menampilkan antrean kasus terurut prioritas, membuka satu kasus beserta jejak buktinya, dan menerima keputusan petugas berikut alasannya. |
| Layer Logika Aplikasi | Memvalidasi bentuk berkas masuk, merajut hubungan antara baris tagihan dan bukti klinis, menjalankan aturan integritas berversi, menyusun peringkat, dan menulis jejak audit. |
| Layer Analitik | Mengukur kemiripan dokumentasi dan kejanggalan pola lintas rekam untuk membantu pengurutan. **Bukan** kecerdasan generatif — tidak ada model bahasa di jalur keputusan risiko. |
| Layer Data | Menyimpan berkas asli apa adanya, bentuk kanonik yang bisa dikueri, jejak audit yang hanya bisa ditambah, dan artefak hasil evaluasi berversi. |
| Layer Sumber Data | Menghasilkan data sintetik yang reproducible berikut label pola risiko yang disuntikkan. Tidak ada koneksi ke sistem BPJS, SATUSEHAT, maupun E-Klaim. |

> **CATATAN PENTING**: Brief ini sengaja tidak menyebut teknologi spesifik. Keputusan teknologi ada di `docs/canonical/03_architecture.md` (canonical, read-only) dan diturunkan ke task file oleh `sprint-builder`.

---

## 3. Modul Sistem

### 3.1 Daftar Modul

| No | Modul | Kode | Prioritas |
|----|-------|------|-----------|
| 1 | Ingest & Validasi Bundel | `01_INGEST_VALIDASI` | Tinggi |
| 2 | Mesin Bukti & Deteksi Risiko | `02_MESIN_BUKTI_DETEKSI` | Tinggi |
| 3 | Antrean Review | `03_ANTREAN_REVIEW` | Tinggi |
| 4 | Detail Kasus & Disposisi | `04_DETAIL_KASUS_DISPOSISI` | Tinggi |
| 5 | Audit & Evaluasi | `05_AUDIT_EVALUASI` | Sedang |
| 6 | Data Sintetik | `06_DATA_SINTETIK` | Tinggi |

> Modul 6 adalah **fondasi**, bukan fitur pengguna. Tanpa data sintetik yang reproducible dan berlabel, modul 2 tidak punya bahan uji dan modul 5 tidak punya bahan ukur. Modul ini dikerjakan paling awal.

### 3.2 Integrasi Antar Modul

```
                    ┌──────────────────────────┐
                    │  06_DATA_SINTETIK        │
                    │  (Fondasi — sumber data) │
                    └────────────┬─────────────┘
                                 │ bundel + label ground-truth
                                 ▼
                    ┌──────────────────────────┐
                    │  01_INGEST_VALIDASI      │
                    │  (Gerbang masuk)         │
                    └────────────┬─────────────┘
                                 │ bundel kanonik + sidik input
                                 ▼
                    ┌──────────────────────────┐
                    │  02_MESIN_BUKTI_DETEKSI  │
                    │  (Pusat orkestrasi)      │
                    └────────────┬─────────────┘
                                 │ kasus + alasan + rujukan bukti
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐   ┌────────────────────────┐   ┌────────────────┐
│ 03_ANTREAN_   │──▶│ 04_DETAIL_KASUS_       │──▶│ 05_AUDIT_      │
│    REVIEW     │   │    DISPOSISI           │   │    EVALUASI    │
└───────────────┘   └────────────┬───────────┘   └────────────────┘
                                 │ disposisi manusia
                                 ▼
                    ┌──────────────────────────┐
                    │  Jejak audit permanen    │
                    │  (hanya bisa ditambah)   │
                    └──────────────────────────┘
```

Alur integrasi: modul 6 memasok bahan; modul 1 menjadi satu-satunya gerbang masuk dan menolak berkas yang bentuknya tidak sah; modul 2 adalah pusat orkestrasi yang mengubah bundel sah menjadi kasus berisi alasan dan rujukan bukti; modul 3 menyusun kasus jadi antrean kerja; modul 4 tempat keputusan manusia terjadi; modul 5 membaca jejak keputusan itu dan hasil pengukuran offline. Umpan balik disposisi dari modul 4 kembali ke modul 5 sebagai bahan kualitas label di masa depan — bukan sebagai auto-tuning ambang batas.

---

## 4. Konsolidasi Kebutuhan Data Eksternal

**Tidak ada.**

Data yang dipakai sistem ini **100% sintetik**, dihasilkan dari Synthea (Apache 2.0) yang diproses oleh adapter deterministik menjadi bentuk menyerupai SATUSEHAT. Tidak ada koneksi ke BPJS, SATUSEHAT, E-Klaim, V-Klaim, maupun sumber data eksternal lain — baik saat pengembangan, saat demo, maupun saat penjurian.

| Aspek | Keputusan |
|-------|-----------|
| Sumber data operasional | Generator sintetik internal (modul `06_DATA_SINTETIK`) |
| Integrasi eksternal | Tidak ada. Seluruh rute demo wajib berjalan tanpa jaringan eksternal. |
| Data peserta JKN nyata | Dilarang. Tanpa kecuali. |
| Statistik publik (DJSN, BPS) | Boleh dipakai untuk **narasi urgensi di proposal** — tidak pernah masuk sebagai record atau data latih. |

Konsekuensi untuk tim downstream: tidak ada crawler, tidak ada connector, tidak ada penjadwalan sinkronisasi. Detail sumber, lisensi, dan keterbatasannya ada di `docs/canonical/04_data_card.md`.

---

## 5. Konsolidasi Stack Agent

**Tidak ada agent.**

Deteksi risiko memakai aturan deterministik ditambah metode statistik klasik (kemiripan teks dan deteksi anomali). **Tidak ada model bahasa (LLM) di jalur keputusan risiko** — ini keputusan arsitektur yang dikunci di `docs/canonical/decisions/ADR-0002-no-llm-in-risk-score.md`, bukan preferensi yang bisa dinegosiasi saat implementasi.

Alasannya: sinyal risiko harus dapat diulang, terikat bukti, dan dapat diuji. Bahasa yang terdengar meyakinkan dari sebuah LLM bisa melampaui bukti yang sebenarnya ada — dan dalam konteks tuduhan terhadap fasilitas kesehatan, itu bahaya nyata, bukan sekadar cacat teknis.

Ringkasan klaim yang dibantu LLM **boleh** dipertimbangkan sebagai fitur opsional setelah Gate 6, dengan pagar ketat (hanya membaca bukti terstruktur, wajib mengutip ID sumber, keluaran ditolak kalau menyebut ID yang tidak ada, tidak pernah memengaruhi skor maupun transisi status). Ini kategori *nice to have*, bukan bagian dari lingkup wajib.

### Workforce Manifest

| Role | Peran | Catatan |
|------|-------|---------|
| `be_service` | Layer logika + data: ingest, validasi, perajutan bukti, mesin aturan, peringkat, disposisi, jejak audit, artefak evaluasi. | Satu-satunya penulis ke penyimpanan kanonik. |
| `fe_shell` | Antarmuka operasional: antrean review, detail kasus, ingest/demo, audit & evaluasi. | Murni konsumen kontrak dari `be_service`. |

> **Manifest ini sengaja hanya berisi dua baris.** Jangan menambahkan role agent apa pun (orchestrator, monitor, validator, notifier, crawler, analyzer, reporter). `sprint-builder` akan memaksa sprint `00-workforce-scaffold` — lengkap dengan management plane agent — begitu ada satu saja role agent di tabel ini. Sprint itu **tidak boleh ada** di project ini, karena `docs/canonical/01_product_decision.md` menempatkan *multi-agent system* di kolom OUT OF SCOPE.

---

## 6. Standar Layanan

### 6.1 Standar Pengalaman Pengguna

| Aspek | Standar Diharapkan |
|-------|---------------------|
| Kecepatan tampil halaman | Cepat — antrean dan detail kasus harus terasa responsif saat didemokan langsung. |
| Kecepatan penyaringan satu bundel | Cepat — satu bundel harus selesai disaring dalam hitungan detik, bukan menit. |
| Pembaruan data | Manual — penyaringan berjalan saat dipicu pengguna, bukan berkala. Tidak ada aliran data masuk otomatis. |
| Respons interaksi | Cepat — setiap aksi memberi umpan balik langsung; status memuat, kosong, dan gagal selalu punya tampilan sendiri. |
| Perjalanan demo utama | Satu bundel harus menempuh ingest → bukti → deteksi → review manusia → audit di bawah 90 detik. |

### 6.2 Standar Keamanan dan Akses

| Aspek | Standar Diharapkan |
|-------|---------------------|
| Identitas dalam sistem | Pseudonim. Tidak ada nama, tidak ada NIK, tidak ada pengenal peserta asli — di layar maupun di log. |
| Otentikasi pengguna | Simulasi peran untuk prototipe (analis, peninjau senior, administrator). Penegakan tingkat perusahaan didokumentasikan sebagai kebutuhan produksi, tidak dibangun sekarang. |
| Pengaturan akses | Berbasis peran. Jejak audit hanya dapat dibaca peran yang berwenang. |
| Audit log | Wajib, permanen, hanya bisa ditambah. Koreksi dilakukan dengan menambah kejadian baru yang menggantikan — tidak pernah menimpa riwayat. |
| Isi log sistem | Tidak boleh memuat teks medis mentah. Hanya ID permintaan, durasi, galat, versi aturan/model/skema, dan jumlah. |
| Batas berkas masuk | Ukuran, tipe, dan kedalaman struktur dibatasi. Berkas yang diunggah tidak pernah dieksekusi atau diperlakukan sebagai instruksi. |
| Penandaan data | Badge "DATA SINTETIK" wajib terlihat di setiap halaman, tanpa kecuali. |

### 6.3 Standar Ketersediaan

| Aspek | Standar Diharapkan |
|-------|---------------------|
| Jam operasional | Sesuai kebutuhan demo dan pengembangan. Bukan layanan produksi. |
| Toleransi downtime | Tinggi untuk pengembangan; **nol untuk sesi demo penjurian**. |
| Konteks | Demo berjalan lokal dan wajib berfungsi penuh tanpa jaringan eksternal. Tersedia pemulihan data demo (reset ke kondisi awal) dan pemeriksaan kesehatan sistem sebelum sesi dimulai. |

---

## 7. Roadmap Implementasi

> Roadmap ini mengikuti tenggat kompetisi, bukan siklus bulanan. Definisi gate lengkap ada di `docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx` §18.

### Fase 1: Fondasi Data (30–31 Agu → Gate 3, 2 Sep)

- Kerangka repositori, integrasi berkelanjutan, lingkungan lokal.
- Modul `06_DATA_SINTETIK`: generator reproducible, minimal 1.000 klaim dan 200 kasus bersuntikan label.
- Lima berkas contoh terkurasi untuk demo: bersih, phantom, repeat, clone, unbundled.

### Fase 2: Mesin Inti (1–5 Sep → Gate 4, 5 Sep)

- Modul `01_INGEST_VALIDASI`: gerbang masuk, validasi bentuk, sidik input.
- Modul `02_MESIN_BUKTI_DETEKSI`: perajutan bukti dan tiga mode risiko berjalan dengan alasan yang bisa ditelusuri.
- Jejak audit sudah menulis.

### Fase 3: Alur Kerja Lengkap (5–9 Sep → Gate 5, 9 Sep)

- Modul `03_ANTREAN_REVIEW` dan `04_DETAIL_KASUS_DISPOSISI`.
- Perjalanan antrean → detail → keputusan → audit berjalan tanpa jalan buntu.

### Fase 4: Bukti Kinerja (9–12 Sep → Gate 6, 12 Sep)

- Lapisan peringkat statistik; mode risiko keempat aktif.
- Modul `05_AUDIT_EVALUASI`: perbandingan terukur antara pendekatan aturan-saja dan hibrida, berikut keterbatasannya.

### Fase 5: Pengerasan Demo & Penyerahan (12–18 Sep → Gate 7–8)

- Skenario demo, pemulihan data, rencana cadangan bila demo langsung gagal.
- Pembekuan isi proposal; QA berkas akhir. Target unggah internal 18 September.

---

## 8. Struktur Dokumen

| File | Deskripsi |
|------|-----------|
| `00_OVERVIEW.md` | Dokumen ini — gambaran umum sistem |
| `01_INGEST_VALIDASI.md` | Gerbang masuk bundel klaim: unggah/pilih, validasi bentuk, laporan hasil |
| `02_MESIN_BUKTI_DETEKSI.md` | Perajutan bukti dan empat mode deteksi risiko berikut alasannya |
| `03_ANTREAN_REVIEW.md` | Antrean kerja terurut prioritas — layar utama petugas |
| `04_DETAIL_KASUS_DISPOSISI.md` | Pemeriksaan satu kasus dan pencatatan keputusan manusia |
| `05_AUDIT_EVALUASI.md` | Riwayat keputusan permanen dan bukti kinerja terukur |
| `06_DATA_SINTETIK.md` | Fondasi data: generator reproducible dan penyuntikan label |

Dokumen pendamping (canonical, read-only, bukan bagian brief):

| File | Isi |
|------|-----|
| `docs/canonical/00_competition_brief.md` | Aturan resmi kompetisi dan batasan penyerahan |
| `docs/canonical/01_product_decision.md` | Solusi terpilih, tingkatan lingkup, kriteria pembatalan |
| `docs/canonical/03_architecture.md` | Pilihan teknologi, kontrak antarmuka, keamanan |
| `docs/canonical/04_data_card.md` | Skema, generator, pembagian data, keterbatasan |
| `docs/canonical/05_model_card.md` | Desain detektor, ambang batas, penggunaan terlarang |
| `docs/canonical/06_evaluation_plan.md` | Baseline, metrik, protokol eksperimen |
| `docs/canonical/07_privacy_threat_model.md` | Kontrol privasi, skenario ancaman, akuntabilitas |

---

## 9. Blind Spot Review

### 9.1 Gap Teridentifikasi

- **Belum ada validasi pengguna target.** Seluruh alur kerja disusun dari penalaran domain dan dokumen kebijakan, bukan dari observasi petugas casemix sungguhan. Uji keterpahaman internal (§15) adalah pengganti sementara, bukan validasi pengguna.
- **Definisi mode risiko belum diverifikasi ahli.** Empat mode diambil apa adanya dari daftar resmi kompetisi, tetapi batas operasionalnya (kapan sebuah episode "terpecah", seberapa mirip dokumen baru disebut "salinan") ditetapkan sendiri oleh tim.
- **Representativitas data sintetik nol.** Synthea bermodel Amerika Serikat. Distribusi penyakit, alur layanan, dan asumsi penagihannya tidak mewakili JKN. Adapter menyamarkan bentuknya, bukan memperbaiki representativitasnya.
- **Kesenjangan sebagian besar tidak bisa ditutup sebelum tenggat** dan sudah didaftarkan sebagai pertanyaan validasi di `docs/canonical/02_domain_assumptions.md`.

### 9.2 Asumsi Belum Tervalidasi

| Asumsi | Dampak Kalau Salah |
|--------|---------------------|
| Sumber daya SATUSEHAT yang terpublikasi cukup untuk mengamati minimal tiga dari empat mode risiko | Lingkup harus dipersempit ke mode yang tersisa, atau solusi cadangan RujukTepat diaktifkan. Tenggat pembuktian: 2 September pukul 18.00. |
| Petugas casemix rumah sakit memang melakukan review pra-kirim, dan review itu punya kapasitas terbatas yang layak diprioritaskan | Premis prioritisasi runtuh; nilai produk turun jadi sekadar alat validasi bentuk berkas. |
| Kemiripan dokumentasi cukup untuk membedakan penyalinan dari penggunaan templat yang sah | Tingkat positif palsu melonjak pada mode cloning; kebijakan "kemiripan teks saja tidak boleh mencapai pita tertinggi" jadi satu-satunya pengaman. |
| Lapisan statistik memberi nilai tambah terukur di atas aturan-saja | Bukan pembatalan produk — lapisan statistik dibuang dan sistem tetap dikirim sebagai aturan-saja. Ini keputusan yang sudah direncanakan, bukan kegagalan. |
| Tidak ada tumpang tindih fungsional signifikan dengan PRO-CLAIM 2025 | Diferensiasi harus dinarasikan ulang. Bukti publik tidak tersedia; pertanyaan sudah disiapkan untuk penyelenggara. |

### 9.3 Risiko yang Ditandai

- **Bahaya tuduhan.** Sistem ini menandai fasilitas kesehatan. Setiap pergeseran bahasa dari "risiko yang perlu ditinjau" menjadi "fraud" mengubah alat bantu kerja menjadi alat tuduhan. Ini risiko produk, bukan sekadar risiko penulisan.
- **Bukti yang tidak lengkap disalahartikan.** Rekam medis elektronik yang belum lengkap terlihat identik dengan tagihan tanpa bukti tindakan. Sistem wajib menampilkan kelengkapan berkas dan mengarahkan ke "minta bukti", bukan ke "konfirmasi anomali".
- **Kebocoran data pada evaluasi sintetik.** Metrik yang terlalu bagus dari data buatan sendiri adalah tanda bahaya, bukan prestasi. Pembagian data berbasis grup, pembuangan metadata penyuntik, dan uji klasifikasi sepele adalah pengaman wajib.
- **Tenggat sangat ketat.** Gate 3 jatuh pada 2 September — tiga hari dari sekarang. Fondasi data adalah jalur kritis; keterlambatan di sana menggeser seluruh rantai gate.

### 9.4 Tingkat Kepercayaan Agent

**Confidence Level**: `high`

Brief ini bukan hasil penggalian dari pemangku kepentingan, melainkan sintesis dari dokumen perencanaan sepanjang 16.800 kata yang sudah memuat keputusan produk, batasan, dan spesifikasi teknis secara eksplisit. Ketidakpastian yang tersisa berada di domain (validitas definisi mode, perilaku pengguna nyata) — bukan di ruang lingkup produk. Ketidakpastian domain itu sudah didaftarkan terbuka di 9.1 dan 9.2, bukan disamarkan.

### 9.5 Status Brief

**Status**: `ready_for_execution`

---

## 10. Kontak dan Dukungan

| Tim | Peran | Tanggung Jawab |
|-----|-------|----------------|
| Member 1 | Teknis & AI | Arsitektur, mesin deteksi, kontrak antarmuka, evaluasi |
| Member 2 | Produk, UX & Data | Alur kerja, antarmuka, katalog data, berkas contoh, QA |
| Member 3 | Riset, Proposal & PM | Aturan, bukti, tata kelola, pelacakan gate, dek proposal |

---

*Dokumen ini merupakan bagian dari Dokumentasi Implementasi TilikKlaim*
*Versi: 1.0.0 | Terakhir diperbarui: 2026-08-30*
