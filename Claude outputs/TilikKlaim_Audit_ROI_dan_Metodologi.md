# Audit: ROI Simulation & Methodology Note
*Disusun 2026-09-11 — audit terhadap `TilikKlaim_ROI_Simulation.xlsx` dan `TilikKlaim_MethodologyNote_ExpectedCostMatrix.docx`, dibandingkan dengan kode aktual dan aturan `docs/canonical/`*
*Diperbarui 2026-09-11 (revisi 2): Temuan #1, #2, #3 sudah ditindaklanjuti dan diperbaiki di `FINAL_MERGED.pptx` + `ROI_Simulation.xlsx`.*

> **Keputusan Ketua Tim untuk Temuan #1**: fokus submission tetap pada 4 rule yang sudah berkode (phantom, repeat, unbundling, cloning). Inflated Bills, Upcoding, dan Manipulasi Kelas Perawatan dijadikan **Tahap 2 — dilanjutkan jika lolos seleksi proposal** — bukan diklaim sudah berjalan. Methodology note (`ExpectedCostMatrix.docx`) tetap dilampirkan sebagai bukti kesiapan metodologi untuk Tahap 2, bukan sebagai fitur yang sudah aktif.

---

## ✅ Temuan Kritis #1 — Fitur "Inflated Bills" tidak ada di kode — **DIPERBAIKI**

Dokumen [`TilikKlaim_MethodologyNote_ExpectedCostMatrix.docx`](./TilikKlaim_MethodologyNote_ExpectedCostMatrix.docx) mendeskripsikan secara rinci sebuah **detektor "Inflated Bills"** berbasis Expected Cost Matrix (mean + 2σ per provinsi × kelas × usia, dari 6 tabel DJSN 2014–2018), lengkap dengan formula risk score, kategorisasi risiko (RENDAH/SEDANG/TINGGI), dan pipeline konstruksi data 4 langkah.

**Masalah**: saya sudah menelusuri **seluruh** kode backend (`apps/backend/app/service/rules/`) dan `packages/model/` — sistem TilikKlaim yang benar-benar berjalan **hanya punya 4 rule**: `phantom.py`, `repeat.py`, `unbundling.py`, `clone_baseline.py`. Saya mencari di seluruh `apps/` dan `packages/` untuk istilah "Expected Cost Matrix", "Inflated", "DJSN", "upcoding" — **nol hasil**. Tidak ada baris kode yang mengimplementasikan:
- Expected Cost Matrix (data DJSN, faktor koreksi provinsi/kelas/usia)
- Detektor Inflated Bills (z-score, threshold mean+2σ)
- Detektor Upcoding
- Detektor Manipulasi Kelas Perawatan

**Dampak ke materi pitch**: slide 2 deck (`FINAL_MERGED.pptx`) mengklaim **"CAKUPAN (8 dari 20 sub-kategori resmi BPJS)"** dengan 8 checkmark (✓), termasuk *Inflated bills*, *Upcoding*, dan *Manipulasi kelas perawatan*. Dari 8 klaim tersebut, **hanya 4 yang punya kode kerja** (phantom, repeat, unbundling/pemecahan episode, cloning). Tiga item (*Inflated bills*, *Upcoding*, *Manipulasi kelas perawatan*) hanya didukung oleh satu dokumen metodologi dan satu spreadsheet simulasi — **tidak ada implementasi, tidak ada demo, tidak ada test**.

⚠️ **Ini risiko terbesar dari seluruh audit** — kalau juri bertanya "tunjukkan detektor Inflated Bills-nya jalan," tidak ada yang bisa ditunjukkan. Ini juga bertentangan langsung dengan prinsip kejujuran yang justru jadi diferensiator TilikKlaim sendiri (lihat slide 13: *"Kami tidak mengklaim lebih dari yang ada. Justru itulah yang membuat kami kredibel."*).

**Tindakan yang diambil** (opsi 1 dari rekomendasi semula — turunkan klaim, bukan bangun kode baru, sesuai arahan Ketua Tim untuk fokus ke 4 rule yang sudah ada):

| Slide | Sebelum | Sesudah |
|---|---|---|
| 2 | "CAKUPAN (**8** dari 20 sub-kategori)" — 8 checkmark ✓ | "CAKUPAN: **4 mode inti** aktif berkode (**5** dari 20 sub-kategori)" — Inflated bills/Upcoding/Manipulasi kelas diberi tanda `→ (Tahap 2)`, bukan ✓ |
| 6 | "4 Mode: Phantom · Repeat · Inflated Bills · Upcoding · Unbundling · Cloning · Kelas Perawatan" (kontradiktif — 7 item disebut "4 Mode") | "**4 Mode Aktif**: Phantom · Repeat · Unbundling · Cloning **(+3 mode Tahap 2)**" |
| 10 | "→ Digunakan sebagai Expected Cost Matrix" (menyiratkan sudah beroperasi) | "→ **Basis rencana** Expected Cost Matrix **(Tahap 2)**" |
| 11 | Judul "**8** Sub-Kategori yang Dicakup" | "Metode Deteksi — **Tahap 1 (Aktif) & Tahap 2 (Direncanakan)**" — box yang aktif diberi ✓, box Inflated Bills/Upcoding diberi label `(Tahap 2)` |
| 15 | Fase 0 (Sekarang) mengklaim "Expected Cost Matrix berjalan" + skenario "Inflated Bills" — **padahal belum ada**; sementara Fase 1 malah mengklaim "4 mode deteksi aktif" — **yang justru sudah ada SEKARANG** | **Ditukar**: Fase 0 sekarang benar-benar menyatakan "4 mode deteksi aktif (rules engine)"; Expected Cost Matrix & Inflated Bills dipindah ke Fase 1 sebagai Tahap 2 |

Methodology note (`ExpectedCostMatrix.docx`) **tidak dihapus** — tetap jadi lampiran pendukung yang membuktikan metodologi Tahap 2 sudah dirancang matang (bukan ide kosong), hanya saja tidak lagi diklaim sebagai kapasitas yang sudah aktif di Fase 0/Healthkathon.

---

## ✅ Temuan #2 — Angka Rp 342 M di slide 18 salah label, bukan "net benefit" — **DIPERBAIKI**

Perhitungan xlsx (`sheet Dampak Nasional`) dan slide `FINAL_MERGED.pptx` #18 tidak konsisten:

| | Formula | Hasil |
|---|---|---|
| **Net benefit** per xlsx (`Per Faskes` sheet, baris 6) | Nilai terselamatkan − Biaya subscription = Rp 56.970.564 − Rp 3.000.000 | **Rp 53.970.564**/bulan/faskes |
| **Yang dipakai di slide 18** ("500 faskes × Rp 57 juta **net benefit**/bulan") | Memakai Rp 57 juta, yaitu **nilai terselamatkan SEBELUM dikurangi biaya subscription**, bukan net benefit sesungguhnya | Rp 56.970.564 (dibulatkan ke 57 juta) |
| **Konsekuensi** | Rp 53.970.564 × 500 × 12 = **Rp 323,8 M** (net benefit sungguhan) | Rp 56.970.564 × 500 × 12 = **Rp 341,8 M** (≈ **Rp 342 M** — cocok dengan angka slide, tapi labelnya salah) |

**Jadi**: angka **Rp 342 M** yang tercetak di slide memang bisa direproduksi dari xlsx — tapi hanya kalau kolom "nilai terselamatkan" (kotor, sebelum biaya) disalahlabeli sebagai "net benefit" (bersih, setelah biaya). Kalau memakai definisi net benefit yang benar (sesuai definisi si spreadsheet sendiri), angka yang seharusnya tercetak di slide adalah **Rp 323,8 M**, bukan Rp 342 M — selisih **Rp 18 miliar (5,3%)**, cukup besar untuk dipertanyakan auditor internal atau juri yang teliti membaca lampiran.

**Tindakan yang diambil**: slide 18 diperbaiki — **Rp 342 M → Rp 324 M** (net benefit bersih, dibulatkan dari Rp 323,8 M), dan "Rp 57 juta net benefit/bulan" → **"Rp 54 juta net benefit/bulan"**. Formula di xlsx (`Per Faskes` sheet) sendiri sudah benar sejak awal — masalahnya murni di angka yang dikutip ke slide, sekarang sudah cocok.

---

## ✅ Temuan Kritis #3 — Angka Rp 1,04 T tidak tertelusur ke artefak manapun — **DIPERBAIKI**

Slide 18 punya angka kedua: **"Rp 1,04 T — Potensi efisiensi sistem JKN/tahun — 20% dari 3% anomali klaim Rp 172,59 T (asumsi konservatif)"**.

Saya verifikasi: `20% × 3% × Rp 172.590.000.000.000 = Rp 1.035.540.000.000` ✅ — secara matematis benar untuk formulanya sendiri.

**Tapi**: asumsi **"3% anomali klaim"** dan **"20% dari anomali dapat dicegah"** **sama sekali tidak muncul** di sheet manapun dalam `TilikKlaim_ROI_Simulation.xlsx`. Tidak ada sel input, tidak ada sumber, tidak ada catatan. Ini angka yang **diketik langsung di slide**, bukan dihitung dari spreadsheet yang katanya jadi "artefak yang dihasilkan" (generated artifact).

Ini melanggar langsung aturan §12 di `docs/canonical/01_product_decision.md` / `09_proposal_evidence_map.md`: *"Every metric quoted in the proposal comes from a generated artifact, never typed by hand."* Angka Rp 1,04 T ini secara harfiah "diketik manual" — tidak ada baris formula yang menghasilkannya di file Excel yang seharusnya jadi sumber kebenaran.

**Tindakan yang diambil**: sheet `Dampak Nasional` di `ROI_Simulation.xlsx` ditambah 3 baris baru:
- Baris 12 — sel input biru: "Asumsi anomali klaim nasional" = 3%, sumber ditandai eksplisit **"ASUMSI — belum divalidasi"**
- Baris 13 — sel input biru: "Asumsi proporsi tercegah oleh TilikKlaim" = 20%, sumber juga **"ASUMSI — belum divalidasi"**
- Baris 14 — sel formula: `=B9*B12*B13` → menghasilkan Rp 1.035.540.000.000 (≈ Rp 1,04 T, cocok dengan slide)

Slide 18 juga diperkuat: "(asumsi konservatif)" → **"(asumsi ilustratif — belum divalidasi)"**, dan baris peringatan di xlsx diperluas mencakup kedua proyeksi (per-faskes dan top-down). Angka Rp 1,04 T sekarang **tertelusur penuh ke sel formula**, bukan lagi berdiri sendiri di slide.

---

## 🟢 Temuan #4 — Hal yang sudah dilakukan dengan BAIK

Beberapa praktik di xlsx dan docx justru patut dipuji dan dipertahankan:

- **Sheet `Asumsi`** memisahkan input (sel biru) dari formula (sel hitam) dengan jelas — praktik model transparan yang baik.
- **Setiap parameter punya kolom "Sumber" dan "Catatan"** — termasuk yang jujur mengakui keterbatasan, contoh: *"Tidak ada data nasional terpublikasi; 6% = estimasi konservatif dari literatur JKN"* untuk rejection rate awal.
- **Sheet `Dampak Nasional`** sudah punya baris peringatan eksplisit: *"Proyeksi ini bersifat ilustratif dan berbasis asumsi transparansi penuh. Akan divalidasi di pilot Fase 1–2."* — ini persis semangat yang diminta `06_evaluation_plan.md`.
- **Sheet `Skenario`** menyediakan 3 skenario (konservatif/base/optimistis) alih-alih hanya 1 angka tunggal — memperlihatkan sensitivitas asumsi, bukan menyembunyikannya.
- **`MethodologyNote_ExpectedCostMatrix.docx` bagian 6.1 "Keterbatasan yang Diakui"** sangat jujur — poin (b) eksplisit menyebut σ yang dipakai adalah "proxy konservatif," bukan distribusi individual sesungguhnya; poin (d) eksplisit menyebut "belum tervalidasi pada data klaim nyata." Ini kualitas metodologi yang bagus **seandainya fiturnya benar-benar ada di kode** (lihat Temuan #1).
- Metodologi Expected Cost Matrix eksplisit menyatakan filosofi "tidak pernah menyatakan fraud" — konsisten dengan seluruh kanon produk.

---

## 🟡 Temuan #5 — Metodologi ROI tidak memakai formula resmi dari `06_evaluation_plan.md`

`docs/canonical/06_evaluation_plan.md` mensyaratkan formula spesifik untuk klaim nilai pilot:

> `expected reviewed value = reviewed claim amount × observed confirmation rate × recoverable/correctable fraction`

Sementara `TilikKlaim_ROI_Simulation.xlsx` memakai metodologi berbeda: **penurunan rejection rate** (klaim yang tadinya ditolak BPJS, jadi tidak ditolak karena sudah dibersihkan lebih dulu oleh TilikKlaim). Ini bukan formula yang sama — tidak melibatkan "confirmation rate" (berapa persen sinyal yang dikonfirmasi benar oleh reviewer) atau "recoverable fraction" (berapa persen nilai klaim yang benar-benar bisa diperbaiki).

Ini bukan berarti pendekatan xlsx salah — hanya **berbeda** dari yang secara eksplisit diminta kanon. Kalau juri familiar dengan `06_evaluation_plan.md` (dokumen ini memang bukan untuk dibaca juri, tapi prinsipnya konsisten dengan pedoman resmi soal "tidak boleh klaim penghematan tanpa metodologi terukur"), penurunan-rejection-rate murni asumsi (khususnya parameter B1 "penurunan rejection 40%") yang **100% tidak berdasar data** — labelnya sendiri di sheet `Asumsi` jujur menyebut "Asumsi TilikKlaim (konservatif)" tanpa sumber eksternal apa pun.

**Rekomendasi**: tidak wajib diubah (skema saat ini sudah cukup jujur dengan pelabelan asumsi), tapi pertimbangkan menambah satu kalimat di slide atau lampiran yang menjelaskan **mengapa** metodologi "penurunan rejection rate" dipilih dibanding formula resmi `06_evaluation_plan.md`, supaya tidak terlihat seperti dua bagian tim (produk vs evaluasi) memakai standar berbeda.

---

## Ringkasan prioritas perbaikan

| # | Temuan | Tingkat | Status |
|---|---|---|---|
| 1 | Fitur "Inflated Bills/Upcoding/Kelas Perawatan" tidak ada di kode, tapi diklaim ✓ di slide 2 | 🔴 Kritis | ✅ **Selesai** — klaim diturunkan ke 4 mode aktif + label "Tahap 2" di 5 slide |
| 2 | Rp 342 M salah label (pakai angka kotor, bukan net benefit bersih) | 🟡 Sedang | ✅ **Selesai** — diganti Rp 324 M |
| 3 | Rp 1,04 T tidak tertelusur ke xlsx sama sekali (diketik manual) | 🔴 Kritis (melanggar aturan kanon eksplisit) | ✅ **Selesai** — ditambahkan sel formula & label asumsi di xlsx |
| 4 | Praktik transparansi asumsi sudah baik | 🟢 Pertahankan | Tidak berubah |
| 5 | Formula ROI beda dari formula resmi `06_evaluation_plan.md` | 🟡 Ringan | ⏳ Belum ditindaklanjuti — opsional |

**Sisa item terbuka**: hanya Temuan #5 (ringan, opsional — menambah satu kalimat penjelas kenapa metodologi ROI berbeda dari formula resmi `06_evaluation_plan.md`). Kedua temuan kritis (#1 dan #3) yang paling berisiko dianggap *overclaiming* oleh juri **sudah ditangani** di `FINAL_MERGED.pptx` dan `ROI_Simulation.xlsx` per 11 September.

**Verifikasi yang masih perlu dilakukan manusia**: buka kedua file di aplikasi asli (PowerPoint & Excel) untuk memastikan tata letak/pemformatan tidak berantakan setelah edit terprogram — terutama slide 2, 11, 15, 18, dan baris baru di sheet "Dampak Nasional".
