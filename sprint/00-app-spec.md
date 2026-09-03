# TilikKlaim — App Spec (Page-Level)

> **Project slug:** `tilik_klaim` · **Stage:** `MVP` · **Versi:** 1.0.0 · **Tanggal:** 2026-08-30
> **Sumber:** [`brief/`](../brief/00_OVERVIEW.md) (6 modul) + `docs/canonical/01_product_decision.md` § *Pages and core components* & *Main dashboard principles*
> **Turunan ke:** `design/` (mockup per page) dan `sprint/backlog/*/frontend/wire-<page>.md`

Dokumen ini **page-centric**: daftar halaman, rutenya, widget di dalamnya, dan pemetaan setiap widget ke modul brief asalnya. Bukan wireframe, bukan design token, bukan task list.

---

## 1. Page Inventory

| # | Halaman | Route | Layout | Persona | Sumber modul brief |
|---|---------|-------|--------|---------|--------------------|
| 1 | Antrean Review | `/` | List page (shell) | Petugas casemix / anti-fraud | `03_ANTREAN_REVIEW` |
| 2 | Detail Kasus | `/cases/:id` | Detail page 3-kolom (shell) | Petugas casemix / anti-fraud | `04_DETAIL_KASUS_DISPOSISI`, `02_MESIN_BUKTI_DETEKSI` |
| 3 | Ingest / Demo | `/ingest` | Form page (shell) | Petugas casemix + anggota tim demo | `01_INGEST_VALIDASI`, `06_DATA_SINTETIK` |
| 4 | Audit & Evaluasi | `/evaluation` | Detail page (shell) | Peninjau senior + tim proposal | `05_AUDIT_EVALUASI` |

**Empat halaman. Tidak lebih.** `docs/canonical/01_product_decision.md` menempatkan *many dashboards or dummy menus* di kolom OUT OF SCOPE. Menambah halaman kelima memerlukan perubahan pada canonical doc, bukan keputusan implementasi.

**Catatan layout:**
- Riwayat audit per kasus adalah **tab di dalam** `/cases/:id`, bukan route tersendiri.
- Laci perbandingan adalah **panel di dalam** `/cases/:id`, bukan route tersendiri.
- Tidak ada halaman login. Peran disimulasikan; penegakan tingkat perusahaan didokumentasikan sebagai kebutuhan produksi, tidak dibangun sekarang.

---

## 2. Elemen Global (muncul di semua halaman)

| # | Widget | Tipe | Data dari | Sumber Fitur |
|---|--------|------|-----------|--------------|
| G1 | Badge data sintetik | Indikator status warna, persisten | Penanda statis | `00_OVERVIEW` § 6.2 |
| G2 | Navigasi utama | Tile menu (4 entri) | Daftar halaman | Spec ini |
| G3 | Penanda versi mesin & data | Teks penanda yang bisa disalin | Versi aturan, model, kumpulan data aktif | `03_ANTREAN_REVIEW` § 2.1, `05_AUDIT_EVALUASI` § 2.2 |
| G4 | Penanda peran aktif | Label | Peran simulasi: analis / peninjau senior / administrator | `00_OVERVIEW` § 6.2 |

> **G1 tidak boleh dapat ditutup atau digulir keluar layar.** Ini kewajiban tata kelola dari `docs/canonical/07_privacy_threat_model.md`, bukan elemen dekoratif.

---

## 3. Page 1 — Antrean Review (`/`)

**Persona:** Petugas casemix / anti-fraud rumah sakit
**Layout:** List page — metrik ringkas di atas, bilah saringan, tabel antrean
**Sumber fitur:** `03_ANTREAN_REVIEW`

### Widget

| # | Widget | Tipe | Data dari | Sumber Fitur |
|---|--------|------|-----------|--------------|
| 1 | Kasus menunggu ditinjau | Kartu ringkasan | Cacah kasus berstatus tersaring yang belum diambil | `03` § 2.1 |
| 2 | Konflik deterministik prioritas tinggi | Kartu ringkasan | Cacah kasus dengan pelanggaran aturan integritas pasti | `03` § 2.1 |
| 3 | Kasus menunggu bukti tambahan | Kartu ringkasan | Cacah kasus berstatus menunggu bukti | `03` § 2.1 |
| 4 | Waktu tengah dalam antrean | Kartu ringkasan | Ukuran lama tunggu kasus | `03` § 2.1 |
| 5 | Penanda versi mesin & data | Teks penanda | Versi aturan/model + versi kumpulan data | `03` § 2.1 (= G3) |
| 6 | Bilah saringan | Filter bar (status, mode risiko, pita prioritas, rentang tanggal) | Nilai enum dari katalog alasan + model status | `03` § 2.3 |
| 7 | Kotak pencarian | Form input | Pencarian berdasarkan pengenal kasus pseudonim | `03` § 2.3 |
| 8 | Keping saringan aktif | Deretan keping yang bisa dihapus | Saringan yang sedang berlaku | `03` § 2.3 |
| 9 | Tabel antrean kasus | Tabel daftar dengan filter, berhalaman, bisa diurutkan | Daftar kasus: kalimat alasan, keping mode, pengenal pseudonim, kelengkapan bukti, nominal, umur, pita, status | `03` § 2.2 |
| 10 | Tombol masukkan bundel baru | Tombol aksi | — | `03` § 3.1 |
| 11 | Tampilan kosong / galat | Banner alert bervarian (belum ada kasus · kosong karena saringan · sedang memuat · layanan gagal) | Keadaan permintaan daftar | `03` § 4.3 |

### Urutan kolom tabel (mengikat)

Kolom **pertama** adalah **kalimat alasan** dalam bahasa kerja. Skor, pita, dan nominal berada di kanannya.

`Kalimat alasan → Keping mode risiko → Pengenal kasus → Kelengkapan bukti → Nominal → Umur → Pita prioritas → Status`

> Ini bukan preferensi tata letak. `03` § 2.2 dan § 10.3 menjadikan "alasan sebelum skor" sebagai kriteria keberhasilan halaman ini.

### Dilarang di halaman ini

Grafik agregat, tren nasional, peringkat fasilitas, angka "fraud dicegah", nilai rupiah "diselamatkan", proyeksi apa pun. Metrik dibatasi **lima kartu** — nomor 1 sampai 5 di atas.

### Navigasi

- **Masuk dari:** halaman muka aplikasi · dari `/cases/:id` setelah disposisi tersimpan (saringan & urutan dipertahankan) · dari `/ingest` lewat tombol kembali
- **Keluar ke:** `/cases/:id` (klik baris) · `/ingest` (klik tombol masukkan bundel) · `/evaluation` (klik penanda versi) · tetap di halaman (klik kartu metrik → saringan diterapkan; lepas keping saringan)

---

## 4. Page 2 — Detail Kasus (`/cases/:id`)

**Persona:** Petugas casemix / anti-fraud rumah sakit
**Layout:** Detail page tiga kolom — kepala kasus di atas tanpa perlu menggulir, lalu kiri/tengah/kanan
**Sumber fitur:** `04_DETAIL_KASUS_DISPOSISI` (utama), `02_MESIN_BUKTI_DETEKSI` (isi bukti), `05_AUDIT_EVALUASI` (tab audit)

### Widget — Kepala kasus (di atas lipatan)

| # | Widget | Tipe | Data dari | Sumber Fitur |
|---|--------|------|-----------|--------------|
| 1 | Pengenal kasus pseudonim | Teks penanda | Pengenal kasus | `04` § 2.1 |
| 2 | Status kasus | Indikator status warna | Model status fungsional | `04` § 2.1 |
| 3 | Nominal klaim | Angka dengan digit sejajar | Nominal sintetik ilustratif | `04` § 2.1 |
| 4 | Rentang waktu kunjungan | Teks rentang tanggal | Awal–akhir episode | `04` § 2.1 |
| 5 | Alasan utama | Teks menonjol | Kalimat alasan terkuat dari katalog alasan | `04` § 2.1 |
| 6 | Dasar keyakinan | Teks pendek yang bisa dibuka | Penjelasan "kenapa pita ini?" + komponen skor | `04` § 2.1, `02` § 2.3 |
| 7 | Empat tombol tindakan | Deretan tombol | Tolak sinyal · Minta bukti tambahan · Konfirmasi anomali · Eskalasi | `04` § 2.1 |

### Widget — Kolom kiri

| # | Widget | Tipe | Data dari | Sumber Fitur |
|---|--------|------|-----------|--------------|
| 8 | Daftar baris tagihan | Tabel daftar ringkas | Kode layanan, keterangan, jumlah, nominal, waktu layanan | `04` § 2.2 |
| 9 | Keadaan dukungan per baris | Indikator status warna | Didukung · Tidak didukung · Dukungan sebagian · Tidak dapat dinilai | `04` § 2.2 |

### Widget — Kolom tengah

| # | Widget | Tipe | Data dari | Sumber Fitur |
|---|--------|------|-----------|--------------|
| 10 | Kartu alasan | Kartu yang bisa dibuka-tutup, terurut kekuatan bukti | Daftar alasan + kode + versi aturan | `04` § 2.3, `02` § 2.4 |
| 11 | Bukti yang diharapkan | Daftar ringkas | Jenis sumber daya yang seharusnya mendukung | `04` § 2.3 |
| 12 | Bukti yang ditemukan | Daftar ringkas dengan tautan yang dapat dibuka | Sumber daya yang benar-benar ada | `04` § 2.3 |
| 13 | Bukti tandingan | Kartu terpisah dengan penanda berbeda | Rujukan yang melemahkan alasan | `04` § 2.3, `02` § 2.2 |
| 14 | Linimasa episode | **Swimlane** — empat jalur (Kunjungan · Tindakan · Obat · Penagihan) pada satu sumbu waktu; jalur kosong tetap digambar dan diberi label | Urutan kunjungan, tindakan, obat dari `timeline`; jalur Penagihan diturunkan di klien dari `lines[].service_at` | `04` § 2.3, ADR-0004 |
| 15 | Peta bukti | Diagram kecil **berfokus pada alasan yang terbuka**: satu batang (klaim → baris dirujuk) dengan simpul ujung per jenis bukti yang diharapkan, plus cabang bukti tandingan yang terpisah | Alasan terbuka + `expected_support` + `evidence` + `counter_evidence_notes` | `04` § 2.3, `02` § 2.1, ADR-0004 |
| 16 | Panel sumber asli | Drawer side panel yang bisa dibuka; **berbagi satu host dengan widget 23** sehingga keduanya tidak pernah terbuka bersamaan | Isi sumber daya apa adanya + versi aturan & model | `04` § 2.3, ADR-0004 |
| 29 | Ringkasan bukti | Panel terlipat di **paling bawah** kolom tengah, dibuka atas permintaan; pengamatan ber-rujukan, pertanyaan terbuka, catatan ketidakpastian, lalu cara disusun. **Tanpa kontrol tindakan.** | `GET /v1/cases/{id}/briefing` (SSE; `?stream=false` sebagai cadangan). Bawaan: templat deterministik tanpa model | ADR-0005, `05_model_card` § Optional LLM guardrails |
| 28 | Matriks bukti | Tabel: baris tagihan × jenis bukti yang diharapkan; empat keadaan sel — ditemukan · tidak ditemukan · rujukan tidak terselesaikan · tidak diharapkan | `lines`, `reasons[].expected_support`, `reasons[].evidence`, `sources[].availability` — tanpa perubahan kontrak | `04` § 2.3, ADR-0004 |

### Widget — Kolom kanan (panel disposisi)

| # | Widget | Tipe | Data dari | Sumber Fitur |
|---|--------|------|-----------|--------------|
| 17 | Pilihan tindakan | Deretan pilihan tunggal | Empat tindakan | `04` § 2.5 |
| 18 | Alasan terstruktur | Daftar pilihan | Alasan baku sesuai tindakan terpilih | `04` § 2.5 |
| 19 | Catatan bebas | Form input teks | Penjelasan tambahan petugas | `04` § 2.5 |
| 20 | Daftar bukti yang diminta | Daftar centang, tercentang otomatis namun dapat diubah | Jenis sumber daya yang kurang | `04` § 2.5 |
| 21 | Penanda versi kasus | Teks pendek | Versi kasus yang sedang dilihat | `04` § 2.5 |
| 22 | Tombol simpan | Tombol utama, nonaktif sampai tindakan + alasan terisi | — | `04` § 2.5 |

### Widget — Panel & tab

| # | Widget | Tipe | Data dari | Sumber Fitur |
|---|--------|------|-----------|--------------|
| 23 | Laci perbandingan | Drawer side panel, dua panel berdampingan | Pasangan kandidat, bidang cocok/berbeda, rentang tumpang tindih, komponen kemiripan | `04` § 2.4 |
| 24 | Peringatan templat | Banner alert dalam laci | Pengingat bahwa templat sah dapat terlihat serupa | `04` § 2.4, `02` § 4.4 |
| 25 | Tab riwayat audit | Timeline aktivitas vertikal | Kejadian kasus: pelaku, tindakan, alasan, waktu, bukti, versi | `05` § 2.1 |
| 26 | Kotak penegasan konfirmasi anomali | Modal detail | Teks penegasan bahwa ini **bukan temuan fraud** | `04` § 3.2 |
| 27 | Galat versi kasus tidak cocok | Banner alert | Apa yang berubah, siapa yang mengubah, tawaran muat ulang — isian dipertahankan | `04` § 4.3 |

### Aturan tampil (mengikat)

1. **Alasan sebelum skor.** Widget 5 berada di atas widget 6 secara visual dan dalam urutan pembacaan.
2. **Bukti tandingan sederajat dengan bukti pendukung.** Widget 13 tidak boleh disembunyikan di balik panel tertutup.
3. **Jalur bukti kecil dan terarah.** Widget 15 menampilkan satu jalur, bukan jaring hubungan. Bila mulai menyerupai jaring, rancangannya salah.
4. **Rujukan bukti wajib dapat dibuka.** Widget 12 yang menunjuk ke sumber daya tidak ada adalah cacat, bukan tampilan kosong yang wajar.
5. **Seluruh alur dapat diselesaikan dengan papan ketik**, termasuk membuka/menutup laci (widget 23).
7. **Ringkasan tidak pernah memimpin dan tidak pernah memutus.** Widget 29 berada di bawah widget 10–15 dan 28, terlipat, dan tidak boleh memilih tindakan, mengisi alasan, atau mencentang daftar bukti (ADR-0005).
6. **Sel kosong bukan bukti yang absen.** Pada widget 28, keadaan `tidak diharapkan` tidak boleh tampak sama dengan `tidak ditemukan` — dalam kata maupun warna. Menyamakannya memproduksi temuan yang tidak dibuat oleh data (ADR-0004).

### Navigasi

- **Masuk dari:** `/` (klik baris antrean) · `/ingest` (setelah menekan "Saring klaim") · `/evaluation` (dari entri riwayat)
- **Keluar ke:** `/` (setelah disposisi tersimpan — saringan & urutan dipertahankan) · `/ingest` (setelah "Minta bukti tambahan", membawa konteks kasus) · tetap di halaman (buka kartu alasan, buka laci perbandingan, buka panel sumber, pindah tab audit)

---

## 5. Page 3 — Ingest / Demo (`/ingest`)

**Persona:** Petugas casemix / anti-fraud + anggota tim saat demo
**Layout:** Form page — pemasukan di atas, laporan validasi di bawah
**Sumber fitur:** `01_INGEST_VALIDASI` (utama), `06_DATA_SINTETIK` (asal kasus contoh)

### Widget

| # | Widget | Tipe | Data dari | Sumber Fitur |
|---|--------|------|-----------|--------------|
| 1 | Area unggah berkas | Zona seret-dan-lepas + tombol pilih berkas | Satu berkas data terstruktur | `01` § 2.1 |
| 2 | Batas dan aturan berkas | Teks bantuan | Ukuran maksimum, tipe yang diterima, kedalaman maksimum | `01` § 2.1 |
| 3 | Daftar kasus contoh | Tabel daftar ringkas (5 baris) | Bersih · Tagihan tanpa bukti · Tagihan berulang · Dokumentasi salinan · Episode terpecah | `01` § 2.1, `06` § 5.2 |
| 4 | Status validasi | Indikator status warna | Sah · Sah dengan catatan · Tidak sah | `01` § 2.2 |
| 5 | Ringkasan cacah sumber daya | Kartu ringkasan | Cacah per jenis sumber daya yang terbaca | `01` § 2.2 |
| 6 | Daftar galat dan peringatan | Tabel daftar | Kode galat, jenis sumber daya, pengenal, penjelasan | `01` § 2.2 |
| 7 | Catatan kelengkapan berkas | Banner alert (varian kuning) | Sumber daya pendukung yang tidak hadir | `01` § 4.4 |
| 8 | Sidik digital berkas | Teks pendek yang bisa disalin | Sidik isi berkas | `01` § 2.2 |
| 9 | Tombol saring klaim | Tombol aksi tunggal, nonaktif bila tidak sah disertai alasan | — | `01` § 2.2 |
| 10 | Pemberitahuan berkas identik | Banner alert + tautan ke kasus yang sudah ada | Deteksi sidik digital yang sama | `01` § 4.2 |
| 11 | Tampilan galat layanan | Banner alert + tombol coba lagi | Keadaan permintaan | `01` § 8 |

### Dilarang di halaman ini

Wisaya konfigurasi apa pun. Tidak ada langkah pilih-detektor, pilih-ambang-batas, atau pilih-mode. Setelah validasi berhasil, tersedia **satu tombol**: saring klaim.

### Navigasi

- **Masuk dari:** `/` (tombol masukkan bundel baru) · `/cases/:id` (setelah "Minta bukti tambahan", membawa konteks kasus)
- **Keluar ke:** `/cases/:id` (setelah menekan "Saring klaim") · `/` (tombol kembali ke antrean) · tetap di halaman (buka baris galat)

---

## 6. Page 4 — Audit & Evaluasi (`/evaluation`)

**Persona:** Peninjau senior + anggota tim proposal
**Layout:** Detail page — hanya menampilkan, tidak ada kendali eksperimen
**Sumber fitur:** `05_AUDIT_EVALUASI`

### Widget

| # | Widget | Tipe | Data dari | Sumber Fitur |
|---|--------|------|-----------|--------------|
| 1 | Penanda versi | Kartu ringkasan | Versi kumpulan data, generator, model, aturan + sidik data | `05` § 2.2 |
| 2 | Badge data sintetik menonjol | Indikator status warna | Penanda statis, versi besar dari G1 | `05` § 2.2 |
| 3 | Tabel perbandingan baseline | Tabel daftar | Empat pendekatan: acak · aturan-saja · statistik-saja · hibrida | `05` § 2.2 |
| 4 | Metrik per mode | Tabel daftar | Ketepatan, keterpanggilan, F1 untuk empat mode risiko | `05` § 2.2 |
| 5 | Grafik positif palsu | Grafik batang | Positif palsu per 100 klaim bersih | `05` § 2.2 |
| 6 | Grafik ketepatan pada kapasitas review | Grafik garis tren | Ketepatan pada berbagai besaran kapasitas | `05` § 2.2 |
| 7 | Waktu pemrosesan | Kartu ringkasan | Waktu tengah dan persentil atas penyaringan | `05` § 2.2 |
| 8 | Kartu keterbatasan | Kotak catatan menonjol, dapat disalin | Yang dibuktikan vs yang tidak dibuktikan + kalimat wajib data sintetik | `05` § 2.3 |
| 9 | Tampilan belum ada evaluasi | Banner alert + perintah yang harus dijalankan | Keadaan artefak evaluasi | `05` § 3.2 |

### Aturan tampil (mengikat)

1. **Halaman ini hanya menampilkan.** Tidak ada penyetelan ambang batas, tidak ada eksperimen langsung, tidak ada kendali what-if.
2. **Nilai grafik = nilai tabel.** Keduanya membaca artefak yang sama. Ketidakcocokan adalah cacat integritas, bukan perbedaan pembulatan.
3. **Kartu keterbatasan wajib tampil** setiap kali metrik ditampilkan — tanpa kecuali, termasuk saat waktu menipis.
4. **Belum ada evaluasi ≠ nol.** Widget 9 menampilkan keterangan dan perintah, bukan angka nol yang menyesatkan.

### Navigasi

- **Masuk dari:** `/` (klik penanda versi) · navigasi utama
- **Keluar ke:** `/cases/:id` (dari entri riwayat menuju kasusnya) · `/` (navigasi utama)

---

## 7. Matriks Navigasi Konsolidasi

| Dari | Aksi | Ke | Context |
|------|------|-----|---------|
| `/` | klik baris tabel antrean | `/cases/:id` | pengenal kasus, kode alasan terkuat |
| `/` | klik kartu metrik | `/` | saringan yang sesuai kartu diterapkan |
| `/` | klik tombol "Masukkan bundel baru" | `/ingest` | kosong |
| `/` | klik penanda versi | `/evaluation` | versi mesin & data aktif |
| `/` | klik silang pada keping saringan | `/` | saringan itu dilepas, sisanya tetap |
| `/cases/:id` | klik baris tagihan | `/cases/:id` | kolom tengah memuat jejak bukti baris itu |
| `/cases/:id` | klik kartu alasan | `/cases/:id` | kartu terbuka, jalur bukti tampil |
| `/cases/:id` | klik "Bandingkan" | `/cases/:id` | laci perbandingan terbuka, pasangan kandidat |
| `/cases/:id` | klik rujukan bukti | `/cases/:id` | panel sumber asli terbuka, pengenal sumber daya |
| `/cases/:id` | pilih "Konfirmasi anomali" → simpan | `/cases/:id` | kotak penegasan muncul lebih dulu |
| `/cases/:id` | simpan disposisi (tolak / konfirmasi / eskalasi) | `/` | saringan & urutan sebelumnya dipertahankan |
| `/cases/:id` | simpan disposisi "Minta bukti tambahan" | `/ingest` | pengenal kasus + daftar bukti yang diminta |
| `/cases/:id` | klik tab Audit | `/cases/:id` | pengenal kasus, riwayat kejadian |
| `/ingest` | lepas berkas / pilih berkas | `/ingest` | laporan validasi terisi |
| `/ingest` | klik baris kasus contoh | `/ingest` | pengenal kasus contoh, laporan validasi terisi |
| `/ingest` | klik "Saring klaim" | `/cases/:id` | pengenal pemasukan, pengenal kasus |
| `/ingest` | klik "Kembali ke antrean" | `/` | tanpa konteks |
| `/ingest` | klik tautan pada pemberitahuan berkas identik | `/cases/:id` | pengenal kasus yang sudah ada |
| `/evaluation` | klik baris metrik per mode | `/evaluation` | rincian mode terbuka |
| `/evaluation` | klik entri riwayat | `/cases/:id` | pengenal kasus |

### Cek konsistensi

| Cek | Hasil |
|-----|-------|
| Setiap tujuan navigasi ada di Page Inventory | ✅ hanya `/`, `/cases/:id`, `/ingest`, `/evaluation` |
| Setiap halaman punya minimal 1 entry point | ✅ `/` halaman muka · `/cases/:id` dari 3 sumber · `/ingest` dari 2 sumber · `/evaluation` dari 2 sumber |
| Navigasi brief § 3 terwakili | ✅ seluruh entri § 3.1 dari modul `01`, `03`, `04`, `05` sudah tercakup |
| Tidak ada halaman buntu | ✅ setiap halaman punya jalan keluar |

---

## 8. Asumsi & Catatan

### 8.1 Asumsi yang diambil

| # | Asumsi | Dasar | Dampak kalau salah |
|---|--------|-------|--------------------|
| A1 | Riwayat audit adalah **tab di dalam** `/cases/:id`, bukan route tersendiri | `docs/canonical/01_product_decision.md`: *"These may be tabs rather than global navigation items"* | Bila juri mengharapkan halaman audit global, perlu satu route tambahan — perubahan kecil |
| A2 | Tidak ada halaman login | Peran disimulasikan; brief `00_OVERVIEW` § 6.2 | Bila demo menuntut peragaan peran, perlu penukar peran — cukup sebagai widget global, bukan halaman |
| A3 | Halaman `/evaluation` menggabungkan evaluasi **dan** titik masuk riwayat audit | Keduanya berbagi persona dan tujuan pertanggungjawaban | Bila terlalu padat, riwayat dapat dipisah — tetapi ini menambah halaman kelima, perlu perubahan canonical doc |
| A4 | Laci perbandingan adalah panel, bukan route | `04` § 2.4 menyebutnya laci yang kembali ke posisi baca semula | Tidak ada; keputusan ini mengikuti brief |
| A5 | Route `/cases/:id` memakai pengenal kasus pseudonim di URL | Tidak ada pengenal peserta di sistem mana pun | Tidak ada |

### 8.2 Hasil Blind Spot Review

| Cek | Temuan |
|-----|--------|
| **Orphan widget** | Tidak ada. Seluruh widget memetakan ke modul brief dengan nomor bagiannya. |
| **Missing feature** | `02_MESIN_BUKTI_DETEKSI` tidak punya halaman sendiri — **disengaja**. Modul itu adalah mesin di belakang layar; keluarannya tampil sebagai widget 10–16 dan 23–24 di `/cases/:id`. `06_DATA_SINTETIK` juga tidak punya halaman — **disengaja**, ia dijalankan lewat perintah dan hanya muncul sebagai lima kasus contoh (widget 3 di `/ingest`). |
| **Persona mismatch** | Tidak ada. `/` dan `/cases/:id` melayani petugas casemix; `/evaluation` melayani peninjau senior dan tim proposal; `/ingest` melayani keduanya. |
| **Dead-end page** | Tidak ada. Lihat tabel cek konsistensi § 7. |
| **Spec leakage** | Tidak ada nama library, warna, token, atau detail state machine. Model status fungsional dirujuk sebagai sumber data widget, tidak diuraikan di sini. |
| **Brief contradiction** | Tidak ada. Nama dan tipe widget mengikuti tabel Komponen Visual di masing-masing brief modul. |

### 8.3 Catatan untuk downstream

**Untuk `design/`:**
- `/` dan `/cases/:id` adalah dua halaman yang dipakai demo 90 detik — prioritaskan keduanya.
- `/cases/:id` adalah halaman terpadat (27 widget dalam tiga kolom + panel + tab). Kepadatan ini disengaja; membaginya menjadi beberapa halaman merusak alur "satu layar untuk menuntaskan satu alasan".
- Setiap halaman butuh varian: memuat, kosong, galat, dan — khusus `/cases/:id` — versi usang.

**Untuk `sprint-builder`:**
- Empat task `wire-<page>`, satu per halaman.
- `/cases/:id` sebaiknya dipecah menjadi beberapa task (kepala + kolom kiri/tengah, panel disposisi, laci perbandingan + tab audit) karena 27 widget melebihi batas satu hari kerja.
- Widget 25 (tab riwayat audit) bergantung pada kontrak riwayat dari `be_service` — dependensi lintas stack.
- Prasyarat semua task frontend: kontrak antarmuka dari `be_service` sudah dibekukan dan fixture-nya sudah di-commit, agar frontend dapat berjalan paralel.

---

*Spec ini turunan dari [`brief/`](../brief/00_OVERVIEW.md). Bila brief berubah, spec ini wajib diperiksa ulang.*
