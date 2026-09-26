# TilikKlaim — Laporan Audit & Pengujian QA
*Dijalankan 2026-09-26 pada mesin Windows 11 (uv 0.11, Docker Desktop). Pengujian mencakup suite otomatis, pengujian UI langsung di browser, dan probing API. Setiap temuan di bawah punya bukti yang direproduksi, bukan asumsi. Yang tidak bisa saya verifikasi dinyatakan terpisah di §5.*

> **Catatan jujur tentang tujuan "peringkat pertama nasional":** peringkat ditentukan juri dan kompetitor, dan tidak ada audit yang bisa menjaminnya. Yang bisa dilakukan adalah menutup celah yang paling mungkin terlihat atau ditanyakan juri. §4 mengurutkan perbaikan menurut risiko itu.

---

## 0. Status perbaikan H1–H4 (diperbarui 2026-09-26)

| ID | Status | Bukti verifikasi |
|---|---|---|
| **H1** | ✅ **Diperbaiki** | 4 test regresi baru **gagal tanpa perbaikan, lulus dengan perbaikan** (stash → gagal, pulihkan → lulus). `disposition` + `ingestion` = 80 lulus, juga terhadap Postgres. |
| **H2** | ⚠️ **Sebagian: jalurnya siap, artefaknya menunggu pemilik** | Build image Docker asli (jalur Railway): path absolut dihormati; hanya run resmi yang ikut, run lokal pengecoh terkecualikan. **Run `run-20260901T110000Z` dan `failure-modes.md` tidak ada di mesin ini dan tidak pernah ada di riwayat git**, jadi saya tidak mengarang isinya. |
| **H3** | ✅ **Diperbaiki** | Venv kosong + `uv pip install -e ".[dev]"` (langkah README persis) kini memasang `tilik-domain` sendiri; 25 test lulus dari venv itu. `uv.lock` diperbarui. |
| **H4** | ✅ **Diperbaiki** | Diukur di DOM: 1024 px → 744 px penuh (sebelumnya kolom tengah **72 px**); 1366 px → 296/414/348; 1440 px → 296/488/348; 1280 px sidebar diciutkan → 296/492/348. |

### Status M1–M3

| ID | Status | Bukti verifikasi |
|---|---|---|
| **M1** | ✅ **Diperbaiki** | Diukur ujung-ke-ujung dengan Postgres mati di `localhost`: sebelumnya **setiap** `/healthz` 10,1 dtk; kini panggilan pertama 10,2 dtk (probe pertama per proses, yang memilih store) lalu **2–19 ms**. Penyebab dipastikan: `connect_timeout` berlaku **per alamat** (5,3 dtk untuk `127.0.0.1`, 10,2 dtk untuk `localhost` yang punya `::1` + `127.0.0.1`), diulang tiap permintaan. 3 test baru. |
| **M2** | ✅ **Diperbaiki sebagian** | `note` ≤ 2000, `structured_reason` ≤ 200, `requested_evidence` ≤ jumlah tipe resource; body non-ingestion ≤ 256 KiB → **413 `REQUEST_TOO_LARGE`** (termasuk body *chunked* tanpa Content-Length); textarea UI dibatasi 2000. Test gagal tanpa perbaikan (8 gagal tanpa middleware, 3 gagal tanpa batas DTO). **`structured_reason` masih teks bebas** (lihat catatan koreksi di bawah). |
| **M3** | ✅ **Header diperbaiki**, ⚠️ **default identitas sengaja tidak diubah** | `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, CSP `default-src 'none'` (dikecualikan untuk `/docs`/`/redoc`), `Cache-Control: no-store` untuk `/v1/*` (tidak menimpa `no-cache` milik stream briefing); banner `server:` hilang lewat `--no-server-header` di `start.sh` (terverifikasi: 0 baris). Alur simpan disposisi lewat UI nyata tetap berjalan. |

**Dua rekomendasi saya sebelumnya saya koreksi setelah membaca kodenya:**

1. **"Tolak bila header identitas tidak ada" (M3) tidak saya terapkan.** Perilaku "tanpa header = Peninjau" adalah keputusan terdokumentasi (ADR-0006 § 4), sengaja diuji (`test_a_request_with_no_role_header_is_still_a_reviewer`), dan menjaga kompatibilitas tujuh endpoint beku. Karena header sendiri bisa dipalsukan, membuatnya wajib tidak menambah keamanan, hanya gesekan. Jika Anda tetap menginginkannya, itu keputusan produk yang butuh ADR baru, bukan hardening.
2. **"Validasi `structured_reason` terhadap daftar yang dikirim UI" (M2) tidak dilakukan.** UI mengirim **teks label yang sudah dilokalkan** (Indonesia atau Inggris), dan daftarnya hanya ada di berkas locale frontend; backend tidak punya katalog. Memvalidasinya berarti mengubah kontrak menjadi kode alasan stabil (`REQUEST_EVIDENCE_INCOMPLETE_FILE`, dst.) di frontend, backend, dan data audit yang ada. Itu perubahan kontrak, bukan pengetatan; saya rekomendasikan sebagai pekerjaan terpisah. Panjang teksnya kini dibatasi.

Regresi keseluruhan setelah perbaikan H1–H4 dan M1–M3: backend **535 lulus, 1 gagal** (sebelumnya 495 lulus / 3 gagal; sisa 1 kegagalan adalah M7, encoding Windows, di luar cakupan), frontend **386 lulus**, `tsc` hanya menyisakan error lama (L1), ruff bersih pada semua berkas yang diubah.

**Yang harus dilakukan pemilik untuk menutup H2** (dari mesin yang memegang run, yaitu Mac asal repo):

```
git add evaluation/artifacts/run-20260901T110000Z docs/artifacts/failure-modes.md
git commit -m "docs: commit the frozen evaluation run cited by the proposal"
```

Tanpa langkah ini halaman **Audit & Evaluasi** di aplikasi yang dideploy tetap kosong. Jika id run resmi berbeda, ubah di `.gitignore`, `.dockerignore`, dan `evaluation/README.md` sekaligus.

---

## 1. Ringkasan eksekutif

| Area | Hasil |
|---|---|
| Backend (pytest) | **495 lulus, 3 gagal, 15 dilewati** (run pertama: 4 gagal; satu di antaranya flaky) |
| Paket `domain` | 92 lulus |
| Paket `data` | Tanpa kegagalan (dijalankan lewat venv backend; tidak bisa berdiri sendiri, lihat L3) |
| Paket `model` | **Tidak bisa dijalankan** di mesin ini (Application Control memblokir DLL scikit-learn) |
| Frontend (vitest) | **385 lulus / 51 berkas** |
| Frontend (`tsc --noEmit`) | **Gagal**, 1 error (kode keluar 2) |
| Lint (ruff) | 33 temuan, semuanya bisa di-`--fix` |
| Build produksi web | Bersih; JS ≈ 713 kB mentah / ≈ 220 kB gzip |
| API hardening | Kuat pada validasi, batas ukuran, RBAC, konkurensi; **ada 1 celah integritas serius** (H1) |

**4 temuan tingkat tinggi**, **7 sedang**, **6 rendah**. Kekuatan yang terverifikasi ada di §3.

---

## 2. Temuan

### 🔴 Tinggi

#### H1 — Saring-ulang melewati kontrol "buka kembali" dan menghapus keputusan final  ✅ diperbaiki
**Bukti (semua sebagai peran `reviewer`):**
1. Kasus fantom didisposisi `REJECT_SIGNAL` → status `DISMISSED`, versi 6.
2. `POST /v1/bundles/{id}/screen` dengan bundel yang sidik digitalnya identik → status kembali `SCREENED`, versi 7, event `RESCREENED` ditambahkan.
3. Peninjau lalu bisa mendisposisi lagi → versi 9.
4. Jalur resmi: disposisi pada kasus `DISMISSED` sebagai peninjau ditolak (`"A dismissed case must be reopened..."`), dan matriks akses login menyatakan **Peninjau: Tidak** untuk "Buka kembali kasus ditolak".

**Dampak:** kontrol pemisahan tugas (hanya Peninjau Senior yang boleh membuka kembali) bisa dilewati, dan keputusan final manusia bisa "terhapus" dari status kasus tanpa bukti baru (bundelnya identik). Jejak audit tetap utuh (append-only bekerja), tetapi status kasus dan antrean menyesatkan. Ini menyentuh klaim inti produk: akuntabilitas keputusan manusia.
**Perbaikan:** saring-ulang bundel dengan sidik identik pada kasus berstatus terminal (`DISMISSED`, `CONFIRMED_ANOMALY`, `ESCALATED`) harus idempoten dan tidak mengubah status; atau mensyaratkan capability `REOPEN_DISMISSED_CASE`. Tambahkan test regresi. Butuh ADR karena README menyebut "menyaring ulang memperbarui kasus yang sudah ada".

#### H2 — Bukti evaluasi tidak bisa diverifikasi dan tidak tampil di aplikasi yang dideploy  ⚠️ jalur siap, menunggu artefak
**Bukti:**
- Halaman **Audit & Evaluasi** menampilkan keadaan kosong ("Belum ada evaluasi yang dijalankan"); `GET /v1/evaluations/latest` → 404.
- `.gitignore` mengabaikan `evaluation/artifacts/*/` ("never committed"), dan `apps/backend/Dockerfile` hanya menyalin `packages/domain` dan `apps/backend`. Aplikasi di Railway **tidak akan pernah** punya artefak evaluasi.
- Angka yang dikutip di deck (PR-AUC 0,7122→0,8440; precision@K 0,9565→1,0000) hanya ada di **fixture test** dan **prosa changelog**. `git grep` tidak menemukan artefak sumbernya.
- `docs/artifacts/failure-modes.md`, yang dirujuk hasil Sprint 06, **tidak ada** di repo.

**Dampak:** aturan proyek sendiri ("setiap metrik berasal dari artefak yang dihasilkan") tidak bisa dibuktikan oleh juri atau reviewer. Aset kredibilitas terkuat tim tidak terlihat saat demo.
**Perbaikan:** commit satu artefak "run terbekukan" berukuran kecil (metrics/manifest/limitations JSON) dan salin ke image Docker; kecualikan run resmi itu dari `.gitignore`. Tambahkan `docs/artifacts/failure-modes.md` atau hapus rujukannya.

#### H3 — Klon baru tidak bisa menjalankan backend maupun test-nya  ✅ diperbaiki
**Bukti:** mengikuti README (`uv pip install -e ".[dev]"`) lalu `pytest` → `ModuleNotFoundError: No module named 'tilik_domain'`. `apps/backend/pyproject.toml` tidak mendeklarasikan `tilik-domain`; komentar di Dockerfile mengakuinya ("belum tercatat sebagai dependensi").
**Perbaikan:** deklarasikan dependensi lewat `[tool.uv.sources]` (pola yang sudah dipakai `packages/data`) atau workspace uv di root. Ini tepat hal pertama yang dialami juri teknis yang mencoba menjalankan repo.

#### H4 — Halaman detail kasus rusak pada lebar 1024–~1280 px (lebar proyektor umum)  ✅ diperbaiki
**Bukti:** DOM diukur pada viewport 1024 px: `grid-template-columns: 296px 72px 348px`. Kolom alasan/bukti (inti produk) menyusut jadi **72 px**, teks turun satu kata per baris. Penyebab: `lg:grid-cols-[296px_minmax(0,1fr)_348px]` aktif di viewport ≥1024 px tetapi mengabaikan sidebar 220 px. Pada 1440 px tata letak benar.
**Perbaikan:** naikkan breakpoint ke `xl:`, gunakan container query, atau ciutkan sidebar otomatis di bawah ~1280 px.

### 🟠 Sedang

| ID | Temuan | Bukti | Perbaikan |
|---|---|---|---|
| **M1** ✅ | `/healthz` butuh **10,1 detik per panggilan** saat Postgres tidak terjangkau (rute non-DB: 0,2 detik). Bertentangan dengan klaim dokumen bahwa endpoint ini tidak terganggu masalah DB. | Diukur dua kali berturut-turut: 10,116 s dan 10,072 s. `CONNECT_TIMEOUT_SECONDS = 5` × 2 probe. Dengan DB sehat: 0,18 s. | Satu probe, hasil di-cache dengan TTL singkat, timeout lebih pendek khusus health. |
| **M2** ✅ | Field `note` **tanpa batas panjang**; `structured_reason` menerima **teks bebas** apa pun. | Catatan 20 MB lolos validasi skema (ditolak hanya karena transisi tidak sah). `structured_reason: "Bukti pendukung ditemukan"` (bukan opsi UI) diterima dan tersimpan. Pada transisi sah, teks itu tersimpan **permanen** di log append-only. | `max_length` pada `note`, `structured_reason`, `requested_evidence`; batas ukuran body global. *(Validasi enum `structured_reason` ditarik: butuh kode alasan stabil, lihat §0.)* |
| **M3** ✅/⚠️ | Tanpa header identitas = **diizinkan** (fail-open), dan tidak ada header keamanan. | `GET /v1/cases` tanpa `X-Actor-Role` → 200 dengan seluruh data. Respons hanya berisi `server: uvicorn`; tidak ada `X-Content-Type-Options`, CSP/`X-Frame-Options`, `Referrer-Policy`. | Tambahkan middleware header keamanan dan `--no-server-header`. *(Usulan "default tolak" ditarik: kontrak ADR-0006 § 4 yang sengaja diuji, dan header bisa dipalsukan sehingga tidak menambah keamanan; lihat §0.)* |
| **M4** | Ganti bahasa saat runtime **tidak me-refetch** data yang dilokalisasi server. | Setelah beralih ke English, `lang`/judul/label berubah tetapi kalimat alasan di antrean tetap Indonesia. Backend benar (`Accept-Language: en` → kalimat Inggris). Setelah muat ulang, semuanya Inggris. | Invalidasi cache query saat locale berubah. Fitur dwibahasa adalah nilai jual; juri yang mencobanya akan melihat bahasa campuran. |
| **M5** | Tampilan ponsel (375 px) tidak layak pakai. | Sidebar tetap 220 px, konten tersisa **155 px** dan terpotong; tidak ada tombol hamburger. Ponsel memang di luar lingkup produk, tetapi tampilannya terlihat rusak jika dibuka. | Sidebar sebagai drawer di bawah `md`, atau tampilkan pesan "gunakan layar lebih lebar". |
| **M6** | Test urutan audit **flaky**, dan penyebabnya bug nyata. | `test_deactivating_and_reactivating_each_append_their_own_kind` gagal di run pertama, lulus di run kedua. 2000 panggilan `datetime.now()` berurutan menghasilkan **1** nilai berbeda di Windows. `sorted(..., reverse=True)` bersifat stabil, jadi seri mempertahankan urutan sisip (terlama dulu). Store Postgres mengurutkan `occurred_at desc, event_id` (id acak). | Tambahkan nomor urut monoton sebagai tie-breaker pada kedua store. |
| **M7** | 3 test gagal di Windows / tanpa DB, dan skrip ekspor **bisa merusak** berkas yang di-commit. | `test_access`: `read_text()`/`write_text()` tanpa `encoding` (locale cp1252). Berkas tersimpan UTF-8 dan benar; hasil baca cp1252 berbeda. Menjalankan `export_access_matrix.py` di Windows menulis byte cp1252 ke JSON milik frontend. Dua test readiness gagal tanpa Postgres padahal README menjanjikan test integrasi di-**skip**. | `encoding="utf-8"` eksplisit; tambahkan `skipif` pada test yang butuh DB. |

### 🟡 Rendah

| ID | Temuan | Perbaikan |
|---|---|---|
| **L1** | `npm run typecheck` (gerbang yang didokumentasikan README) gagal: `config.test.ts(1,21): 'beforeEach' is declared but its value is never read`. | Hapus import tak terpakai. |
| **L2** | 33 temuan ruff (12 `UP007`, 4 `UP035`, sisanya `RUF100`, `RUF022`, `I001`), semuanya auto-fixable. | `uv run ruff check . --fix`. |
| **L3** | Test `packages/data` mengimpor `app.service.screening` (lapisan backend) tanpa dideklarasikan, sehingga paket itu tidak bisa diuji sendiri (`networkx` hilang). Inversi lapisan. | Pindahkan test integrasi ke backend, atau deklarasikan dependensinya. |
| **L4** | Jebakan dual-stack Windows: dev server web terikat IPv4, sementara aplikasi lain memegang `::1:3000`, sehingga `localhost:3000` menampilkan **aplikasi yang salah** (saya menemukan "Bimbel Cerdas – HRIS"). `DATABASE_URL` bawaan `localhost:5432` juga terkena Postgres lain di `::1`. | Gunakan `127.0.0.1` di `.env.example` dan proxy; catat jebakan ini di README. |
| **L5** | Peringatan Node `MODULE_TYPELESS_PACKAGE_JSON` pada setiap build/dev. | Tambahkan `"type": "module"` di `apps/web/package.json`. |
| **L6** | **Ketidakselarasan pitch vs produk.** Footer antrean menyatakan halaman "sengaja tidak memuat ... angka rupiah 'diselamatkan'", sedangkan deck (slide 17–19) menjadikan "Rp 56,9 juta diselamatkan", "Rp 324 M", "Rp 1,04 T" sebagai headline. Juri yang membaca keduanya bisa melihat ketegangan itu. | Sampaikan angka ROI eksplisit sebagai skenario pilot di luar aplikasi, atau samakan wording. |

---

## 3. Yang terverifikasi kuat (pertahankan)

- **Validasi input & batas ukuran:** bundel 9 MiB → **413** dalam 30 ms *sebelum* parsing; kedalaman 200 → **413** `BUNDLE_DEPTH_EXCEEDED`; JSON rusak → 400; enum tidak valid → 422 dengan daftar nilai sah; parameter query berisi SQL → 422; jalur traversal → 404.
- **RBAC ditegakkan di server:** peran palsu, admin membaca kasus, peninjau membuka manajemen pengguna, admin ingest → semuanya **403** dengan kode galat stabil.
- **Konkurensi optimistis:** disposisi dengan versi basi → **409** dengan pesan yang menjelaskan ("kasus pindah ke versi 3 saat Anda meninjau versi 1").
- **Ingest idempoten:** bundel sama dikirim dua kali → `ingestion_id` dan hash identik.
- **Jejak audit append-only:** tetap utuh melewati semua uji, termasuk saring-ulang (`RESCREENED` ditambahkan, tidak ada yang dihapus).
- **UX validasi:** tombol simpan nonaktif sampai tindakan dan alasan dipilih, progres 0/2 → 2/2, peringatan `aria-live`, opsi alasan menyesuaikan tindakan.
- **Bahasa ketidakpastian konsisten:** "Tidak ada risiko teramati... bukan pernyataan bahwa klaimnya bersih"; tidak ada kata "fraud" sebagai temuan di layar yang saya lihat.
- **Aksesibilitas dasar:** `lang` benar, satu `h1`, tidak ada gambar tanpa `alt`, tidak ada kontrol tanpa nama (diperiksa lewat DOM; tampilan pohon aksesibilitas alat browser sempat menyesatkan, dan saya verifikasi ulang sebelum melaporkan).
- **Performa (hanya ukuran bundel yang diukur):** JS ≈ 220 kB gzip total (React 45 kB, kode aplikasi 68 kB, satu chunk vendor 107 kB, router 8,5 kB), CSS 10,6 kB; build 0,6 detik. Belum ada pemecahan kode per rute (hanya 4 berkas JS), tetapi ukurannya masih wajar untuk prototipe.
- **Kualitas suite:** 495 + 385 + 92 test lulus; komentar kode menjelaskan alasan desain, dan test menegakkan aturan etika (mis. tidak ada jalur kode yang menolak klaim atau menghentikan pembayaran).

---

## 4. Rencana perbaikan berprioritas (paling berisiko dilihat juri lebih dulu)

| Urutan | Item | Usaha | Alasan |
|---|---|---|---|
| 1 | **H2** commit artefak evaluasi + salin ke image | Kecil | Aset kredibilitas terkuat saat ini tidak terlihat dan tidak terbukti |
| 2 | **H1** saring-ulang tidak boleh mengubah kasus terminal | Kecil–sedang | Menyentuh klaim inti (keputusan manusia final) dan RBAC |
| 3 | **H4** breakpoint detail kasus | Kecil | Layar utama demo rusak di proyektor 1024 px |
| 4 | **H3** deklarasi dependensi `tilik-domain` | Kecil | Kesan pertama juri teknis yang menjalankan repo |
| 5 | **M4** refetch saat ganti bahasa | Kecil | Fitur dwibahasa harus terlihat mulus |
| 6 | **M1, M2, M3** health cache, batas `note`, fail-closed | Kecil | Kredibilitas hardening |
| 7 | **L1, L2, M6, M7** gerbang hijau (tsc, ruff, flaky, Windows) | Kecil | CI hijau dan bisa dijalankan di Windows |
| 8 | **L6** selaraskan narasi ROI vs prinsip produk | Kecil | Konsistensi pesan |

---

## 5. Cakupan: apa yang **tidak** saya verifikasi

- **`packages/model` dan runner evaluasi tidak bisa dijalankan** di mesin ini: kebijakan Windows Application Control memblokir DLL native (`_ctypes`, `sklearn._loss`) dan launcher `uvicorn.exe`. Akibatnya **angka di slide 13 tidak bisa direproduksi oleh saya**. Saya hanya bisa memastikan angka itu ada di fixture test dan changelog. Ini batasan lingkungan, bukan cacat proyek.
- **Test end-to-end Playwright tidak dijalankan.** Klaim "alur 90 detik selesai ~3,5 detik" belum saya buktikan.
- **Halaman Manajemen Pengguna (admin) dan alur Peninjau Senior** hanya diuji lewat API (403/200), bukan lewat UI.
- **Audit aksesibilitas formal** (kontras warna, keyboard trap, pembaca layar) tidak dilakukan; hanya pemeriksaan struktur dasar.
- **Tile "Versi mesin & data"** di antrean tampak pudar pada render pertama di viewport 800 px; saya tidak memverifikasi apakah itu gaya yang disengaja atau keadaan yang berubah setelah pemuatan.
- Tidak ada uji beban, uji penetrasi, maupun uji Postgres yang tidak tersedia.

## 6. Perubahan yang saya buat

**Fase audit (tidak mengubah kode):** memasang `tilik-domain`/`tilik-data`/`tilik-model`/`pytest`/`pyyaml` sebagai editable ke `apps/backend/.venv` (tidak masuk git); mengisi database proyek dengan 5 kasus demo (`demo_reset.py`, data sintetik).

**Fase perbaikan H1–H4 — 12 berkas berubah** (`git diff --stat` untuk melihatnya):

| Berkas | Perubahan |
|---|---|
| `apps/backend/app/router/bundles.py` | **H1** guard `RESCREENABLE_STATES` (dibaca dari `ALLOWED_TRANSITIONS`); kasus yang sudah diputuskan dikembalikan apa adanya |
| `apps/backend/tests/test_disposition.py` | **H1** 5 test baru (3 kasus terminal, bypass peran, loop `EVIDENCE_REQUESTED` yang sah) |
| `apps/web/src/locales/{id,en}/ingest.json` | **H1** teks banner sidik-duplikat tidak lagi menjanjikan "memperbarui" kasus yang sudah diputuskan |
| `apps/backend/pyproject.toml`, `uv.lock` | **H3** dependensi `tilik-domain` + `[tool.uv.sources]` |
| `.gitignore`, `.dockerignore`, `apps/backend/Dockerfile`, `evaluation/README.md` | **H2** jalur pengiriman run terbekukan ke image + petunjuk untuk pemilik |
| `apps/web/src/pages/case-detail/CaseDetailPage.tsx`, `.../CaseDetailPlaceholders.tsx` | **H4** container query `@min-[1060px]` menggantikan breakpoint viewport `lg:` |

**Fase perbaikan M1–M3 — 12 berkas berubah, 3 berkas baru:**

| Berkas | Perubahan |
|---|---|
| `apps/backend/app/store/engine.py` | **M1** `database_availability()`: pembacaan ter-cache (TTL 10 dtk), basi dilayani seketika dengan satu refresh latar belakang |
| `apps/backend/app/service/demo_state.py`, `tests/test_demo_readiness.py` | **M1** memakai pembacaan ter-cache; urutan `use_database()` lebih dulu agar probe pertama tidak berlipat |
| `apps/backend/tests/test_health_latency.py` *(baru)* | **M1** 3 test: tidak mem-probe ulang, refresh tunggal, `/healthz` cepat walau probe 1 dtk |
| `apps/backend/app/middleware.py` *(baru)* | **M2/M3** `BodyLimitMiddleware` dan `SecurityHeadersMiddleware` (ASGI murni agar stream SSE tidak di-buffer) |
| `apps/backend/app/main.py`, `config.py`, `errors.py` | **M2/M3** registrasi (batas ukuran di dalam CORS, header di paling luar), `max_request_bytes`, kode `REQUEST_TOO_LARGE` |
| `apps/backend/app/dto/dispositions.py` | **M2** batas `note`/`structured_reason`/`requested_evidence` |
| `apps/backend/tests/test_request_hardening.py` *(baru)* | **M2/M3** 15 test |
| `apps/backend/scripts/start.sh` | **M3** `--no-server-header` |
| `apps/web/.../types.ts`, `DispositionPanel.tsx`, `DispositionPanel.test.tsx` | **M2** `maxLength` 2000 pada textarea catatan + 1 test |

**Pembersihan:** semua server, image Docker verifikasi, venv uji, direktori probe, dan `apps/web/dist` yang saya buat sudah dihapus; database demo di-reset ke 5 kasus tersemai. **Tidak ada yang di-commit**; semua perubahan (H1–H4 dan M1–M3) masih di working tree agar Anda tinjau.
