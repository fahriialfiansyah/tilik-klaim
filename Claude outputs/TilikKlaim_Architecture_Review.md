# TilikKlaim — Tinjauan Arsitektur untuk Ketua Tim
*Healthkathon 2026 · kategori Efisiensi Risiko pada Fasilitas Kesehatan · disusun 2026-09-11*

> Dokumen ini adalah hasil penelusuran menyeluruh seluruh source code, dokumentasi kanonikal, dan brief produk — disiapkan sebagai bahan pertimbangan Ketua Tim menjelang submission (18–19 September 2026).

---

## 1. Ringkasan satu paragraf

TilikKlaim adalah **lapisan integritas bukti klaim**, bukan produk penilai-fraud. Setiap sinyal risiko yang diangkat selalu disertai bukti sumber (baris tagihan, catatan klinis, rentang waktu) **dan** counter-evidence (argumen penyangkal) di layar yang sama, sistem tidak pernah menyatakan "fraud", tidak pernah menolak klaim atau menghentikan pembayaran secara otomatis — keputusan akhir selalu manusia, dan tercatat permanen dengan alasan wajib. Seluruh data bersifat sintetik.

---

## 2. Peta struktur repo

| Folder | Isi |
|---|---|
| `docs/canonical/` | Referensi & batasan produk — read-only, hanya berubah lewat ADR |
| `brief/` | Blueprint produk (6 modul), bahasa bisnis-teknis |
| `sprint/` | Spec halaman + rencana sprint + task per stack |
| `apps/backend/` | API FastAPI — ingest, bukti, aturan, peringkat, disposisi, audit |
| `apps/web/` | Antarmuka React — antrean, detail kasus, ingest, evaluasi |
| `packages/domain/` | Skema kanonik (tipe data klaim/bukti) |
| `packages/data/` | Generator & injektor data sintetik |
| `packages/model/` | Fitur & detektor statistik (opsional, di atas rules) |
| `evaluation/` | Runner evaluasi reproducible + artefak berversi |

---

## 3. Alur data end-to-end

```
packages/data (generator sintetik + injektor anomali)
        │
        ▼
apps/backend/app/router (POST /v1/bundles — ingest & validasi)
        │
        ▼
packages/domain (CanonicalBundle — skema kanonik, immutable)
        │
        ▼
apps/backend/app/service/evidence_graph.py (graf bukti — gap & similarity edges)
        │
        ▼
apps/backend/app/service/rules/* (4 detektor deterministik) ──┐
        │                                                      │
        ▼                                                      ▼
apps/backend/app/service/screening.py (band + cap)   packages/model/ (opsional: skor statistik)
        │                                                      │
        └──────────────────► combine (max + 3 cap) ◄───────────┘
        │
        ▼
apps/backend/app/store (persistensi Postgres / in-memory)
        │
        ▼
apps/web (antrean → detail kasus → disposisi manusia → audit)
        │
        ▼ (opsional)
apps/backend/app/service/briefing/* (ringkasan LLM read-only, off by default)
```

---

## 4. Domain model — `packages/domain/`

Skema kanonik yang dipakai bersama seluruh lapisan (kontrak tunggal rule engine, UI, dan test).

- **`canonical.py`** — model Pydantic (frozen, `extra="forbid"`) untuk 11 tipe sumber daya (claim, encounter, condition, procedure, medication, document, dll), meniru bentuk FHIR SATUSEHAT tanpa mengklaim kesetiaan produksi.
  - **Immutable total**: koreksi selalu membuat objek baru, tidak pernah edit in-place — kepercayaan pada audit trail bergantung pada ini.
  - `CanonicalBundle` **sengaja tidak punya field skenario/label** — metadata demo adalah tipe terpisah, tidak pernah jadi anggota, sehingga detektor **secara struktural tidak bisa melihat kunci jawaban** (dites di `test_leakage_separation.py`).
  - `EventStatus.ENTERED_IN_ERROR` dibedakan tegas dari ketiadaan — retraksi bukan sama dengan "tidak pernah tercatat".
- **`edges.py`** — 9 tipe edge kanonik. Hanya 2 tipe "inferred" (`POSSIBLE_DUPLICATE_OF`, `SIMILAR_TO`) yang **wajib** membawa confidence; sisanya **dilarang** — ditegakkan saat konstruksi objek (crash by design, bukan warning).
- **`reasons.py`** — katalog alasan tunggal. Dua aturan wording keras (dari privacy threat model): sistem melaporkan "risiko/anomali perlu ditinjau", **tidak pernah** menyatakan fraud; dan alasan mendeskripsikan *apa yang dicari dan tidak ditemukan*, bukan apa yang dilakukan seseorang.
- **`notes.py`** — katalog counter-evidence, dirender dari satu kode+parameter (bukan kalimat siap-tulis) agar tidak ada 2 salinan penjelasan yang bisa berbeda antar bahasa.
- **`locale.py`** — Bahasa Indonesia adalah bahasa kerja utama (bukan fallback); Inggris adalah rendering kedua dari satu katalog yang sama — **sinyal risiko mana yang muncul tidak pernah berbeda antar bahasa**.
- **`versioning.py`** — `SCHEMA_VERSION`/`RULESET_VERSION`/`ENGINE_VERSION` dicap di setiap artefak turunan agar hasil bisa dilacak dan tidak diam-diam diinterpretasi ulang di bawah ruleset baru.

---

## 5. Mesin deteksi — `apps/backend/app/service/rules/`

Kontrak umum (`registry.py`): setiap `ReasonHit` **wajib** membawa evidence, counter-evidence, component scores, dan versi rule. Prinsip produk: *"reviewer yang hanya melihat argumen pro tidak bisa menimbang sinyalnya."*

| Rule | Pola risiko | Logika inti |
|---|---|---|
| `phantom.py` | Klaim fantom | Baris tagihan tanpa bukti klinis selesai. Sengaja sempit — tidak pernah menyimpulkan layanan tidak diberikan. |
| `repeat.py` | Tagihan berulang | Fingerprint SHA-256 identik = duplikat kuat; overlap kode dalam 1 episode = sinyal lemah + catatan field berbeda. |
| `unbundling.py` | Fragmentasi episode | Episode dipecah ke beberapa klaim berdekatan (window 3 hari) dengan kode berbeda; selalu disertai catatan "staged care terlihat sama". |
| `clone_baseline.py` | Dokumentasi salinan | TF-IDF n-gram karakter vs peer note, threshold 0.7. **Tidak pernah** bisa mencapai band tertinggi sendirian. |

**`evidence_graph.py`** — membangun graf bukti (networkx). Gap **dicatat, tidak pernah dianggap error** (bundle tidak lengkap adalah input normal); inferensi selalu berlabel confidence.

**`screening.py`** — disebut *"kode paling safety-critical di servis"*. Urutan rule tetap agar hasil reproducible. Tiga cap keras:
1. Similarity teks saja tidak pernah bisa mencapai band tertinggi.
2. Bukti hilang + bundle tidak lengkap → **menurunkan** kepastian dan mengarah ke "minta bukti", tidak pernah ke "konfirmasi anomali".
3. Fingerprint duplikat persis = prioritas tinggi, tetap selalu ditinjau manusia.

**Tidak ada threshold "skor ini = fraud" di mana pun dalam kode.**

---

## 6. Lapisan statistik opsional — `packages/model/`

Formula: `priority = max(deterministic_reason_priority, calibrated_similarity, calibrated_anomaly)` + 3 cap yang sama filosofinya dengan `screening.py`.

- **`features.py`** — 6 keluarga fitur (kelengkapan bukti, integritas episode, similarity, konteks peer, provenance, aritmatika). **Tidak pernah membaca identifier sebagai nilai** — hanya untuk equality (diuji dengan re-identify seluruh corpus).
- **`similarity.py`** — TF-IDF n-gram karakter + cosine similarity vs peer facility (bukan riwayat pasien sendiri). Tidak ada model generatif (dilarang oleh ADR-0002).
- **`anomaly.py`** — Isolation Forest unsupervised, RobustScaler, seed dipin agar reproducible.
- **`calibration.py`** — threshold **hanya** di-fit pada partisi validation (menolak keras kalau dipanggil di training/test). Skor statistik **tidak pernah** bisa mencapai band `DETERMINISTIC_CONFLICT`.
- **`ranking.py`** — combiner tunggal, didesain agar **bisa dihapus** (satu baris import) kalau Sprint 06 tidak membuktikan manfaat inkremental — lihat hasil di §10.

---

## 7. Data sintetik — `packages/data/`

- **`generator.py`** — generator native deterministik (bukan Synthea/FHIR/Java, lihat ADR-0003). Seeding per-bundle membuat urutan generasi tidak berpengaruh pada hasil.
- **`injectors/{phantom,repeat,clone,unbundling}.py`** — setiap injektor merusak **tepat satu invariant** per kasus. Mengembalikan `None` (skip) alih-alih memaksa injeksi ke bundle yang tidak cocok.
- **`leakage.py`** — **probe kebocoran wajib**: melatih classifier trivial hanya dari ID/urutan bundle; jika mengalahkan random-chance >10 poin → **hard-fail**, bukan warning. Juga menghapus suffix ID injektor dari setiap resource, tidak hanya bundle ID.
- **`split.py`** — split train/val/test berbasis grup (participant, provider-time-block) — **bukan** random-row split, untuk mencegah kebocoran near-duplicate antar partisi. 5 fixture demo emas dikeluarkan dari semua metrik.
- **`pipeline.py`** — satu command menegakkan urutan: generate → verifikasi bersih → inject → hapus jejak → split → probe kebocoran → data card.
- **`data_card.py`** — menegakkan kalimat wajib verbatim: *"Dataset ini sintetik dan tidak merepresentasikan prevalensi JKN atau perilaku provider nyata."*

---

## 8. Persistensi — `apps/backend/app/store/`

- **`engine.py`** — engine SQLAlchemy lazy singleton; mengimpor app **tidak pernah** membuka koneksi DB (demo/test tetap jalan offline).
- **`cases.py`** — `case_version` untuk optimistic concurrency, mencegah disposisi menimpa keputusan yang dibuat di atas data basi secara diam-diam.
- **`audit.py`** — **benar-benar append-only** — tidak ada method update/delete di kode, dan ditegakkan di level DB via trigger SQL. Koreksi menambah event penyusul; yang asli tidak pernah disentuh. Ini fondasi akuntabilitas sistem.

---

## 9. Permukaan API & pipeline layanan — `apps/backend/app/router/`, `app/service/`

| Endpoint | Fungsi | Catatan desain |
|---|---|---|
| `POST /v1/bundles` | Ingest | Logging tipis — tidak pernah mencatat teks medis mentah/isi dokumen |
| `GET /v1/cases`, `/{id}` | Antrean/detail | Selalu baca hasil tersimpan — **tidak pernah** screening ulang di bawah ruleset baru |
| `POST /v1/cases/{id}/dispositions` | Disposisi manusia | Alasan wajib (ditegakkan 3x: DTO, event, DB constraint); write basi ditolak total |
| `GET /v1/cases/{id}/audit` | Audit trail | Peran datang via header `X-Actor-Role` — **sengaja dinamai agar tidak terlihat seperti kontrol keamanan** |
| `GET /v1/evaluations/{run_id}` | Evaluasi | Hanya baca artefak yang dihitung offline — tidak menghitung apa pun |
| `GET /healthz` | Liveness | Selalu 200 walau DB down (mencegah restart loop di Railway); readiness sebenarnya di blok terpisah |

**`disposition.py`** — diuji eksplisit lewat `test_no_action_triggers_payment_or_sanction`: **tidak ada jalur kode yang bisa menolak klaim, menghentikan pembayaran, atau mengubah kode.**

**`access.py`** — 3 peran (reviewer, senior_reviewer, admin). Didokumentasikan eksplisit: header peran **bisa dipalsukan** dan tanpa autentikasi nyata di prototipe ini — modul ini hanya membuat aturan yang *dinyatakan* jadi konsisten, bukan aman.

---

## 10. Frontend — `apps/web/src/`

| Feature/Page | Fungsi |
|---|---|
| `features/auth` + `pages/login` | Simulasi role/session, matrix akses (mirror `access.py`) |
| `features/admin/users` + `pages/admin-users` | Manajemen user, ekspor CSV |
| `features/review/queue` + `pages/queue` | Antrean review |
| `features/review/case-detail` + `pages/case-detail` | **Fitur terbesar** — jejak bukti, swimlane, matrix perbandingan |
| `features/review/case-briefing` | Konsumsi SSE ringkasan LLM opsional |
| `features/review/ingest` + `pages/ingest` | Upload/validasi bundle, hash sisi klien |
| `features/review/evaluation` + `pages/evaluation` | Baca & format artefak evaluasi |
| `modules/i18n`, `locales/en│id` | Dukungan bilingual (satu katalog, dua rendering) |

---

## 11. Fitur AI opsional — `service/briefing/` (case briefing)

**Mati secara default** — tanpa API key/model/`BRIEFING_ENABLED=false` → fallback ke template, bukan error ("jangan pernah bergantung pada LLM remote").

- **7 tool read-only** — seluruhnya irisan dari `CaseDetailResponse` yang sama dengan yang dilihat reviewer di layar (LLM tidak bisa melihat apa pun yang reviewer tidak lihat, dan tidak diberi priority band/skor).
- **Gate validasi wajib 5 syarat** — semua referensi resolve, semua angka terverifikasi ada di data yang disuplai (anti-halusinasi), tidak ada istilah akusatif/direktif (dengan penanganan negasi: "belum terbukti" = hedge yang diizinkan), batas panjang, catatan ketidakpastian tidak boleh kosong. **Gagal satu → seluruh briefing ditolak, fallback ke template.**
- **ADR-0002 mengunci**: tidak ada LLM di mana pun dalam skor risiko atau transisi status — briefing murni kosmetik/read-only.

---

## 12. Aturan non-negotiable dari `docs/canonical/`

> Dokumen-dokumen ini **read-only**, hanya berubah lewat ADR baru. Ini adalah batasan yang **tidak boleh dilanggar saat pitching**.

- **Label maturitas**: sebut sebagai *"functional prototype"*, **jangan pernah** klaim "MVP" ke juri — panduan proposal resmi mensyaratkan MVP tervalidasi pengguna nyata, sistem ini belum punya itu.
- **Out of scope keras**: data peserta JKN nyata, koneksi live BPJS/SATUSEHAT/E-Klaim, penolakan klaim/pembayaran/sanksi otomatis, keputusan medis/diagnostik, aplikasi mobile, IAM enterprise, sistem multi-agent, GNN.
- **Tidak ada LLM di jalur keputusan risiko** (ADR-0002) — keputusan arsitektur terkunci.
- **Bahasa wajib**: "risiko/anomali perlu ditinjau" — **tidak pernah** "fraud" sebagai temuan.
- **Kill criteria** (bertanggal, spesifik kompetisi) — misalnya jika field SATUSEHAT publik tidak mendukung ≥3 dari 4 mode pada 2 Sep → pivot ke konsep cadangan "RujukTepat"; jika juri tidak bisa membedakan ini dari "chatbot AI fraud" generik setelah pitch 30 detik pada 6 Sep → tulis ulang paksa.
- **Privacy**: ID pseudonim saja; tidak pernah teks medis mentah di log; audit append-only adalah tulang punggung akuntabilitas.

---

## 13. Status sprint & yang tersisa (per 11 Sep 2026)

Deadline: registrasi tutup **14 Sep**, submission proposal **19 Sep** (target internal **18 Sep**).

| Sprint | Status | Sisa pekerjaan |
|---|---|---|
| 00–05, 08–11 | ✅ Done | — |
| **06 — evaluation-report** | 🚧 In Progress | 3 sign-off (M1/M2/M3), review draf `failure-modes.md`, **keputusan pertahankan/hapus `packages/model/`** |
| **07 — demo-hardening** | 🚧 In Progress | Rehearsal 3 menit + narasi, 2 studi kasus tertulis, rekaman fallback 1080p, PDF 6-frame screenshot — **semua kerja manusia, kode sudah selesai** |

### Hasil evaluasi resmi (Sprint 06) — perlu keputusan Ketua Tim

| | Rules only | Hybrid | Interval 95% overlap? |
|---|---|---|---|
| Macro F1 | 0.6510 | 0.6510 | identik |
| Precision @ budget 23 | 0.9565 | 1.0000 | **ya** — overlap |
| Recall @ budget | 0.3235 | 0.3382 | beda 1 kasus |
| PR-AUC | 0.7122 | **0.8440** | tidak dihitung interval |

**Metrik per-mode identik di 4 mode.** Lapisan statistik tidak mendeteksi apa pun yang tidak terdeteksi rules. Yang berubah hanya ranking. Kriteria acceptance resmi (precision@K, recall@K) **belum terbukti signifikan** — sehingga klausul penghapusan Sprint 05 **masih aktif secara sah**, dan itu keputusan produk, bukan teknis.

---

## 14. Diferensiator kuat untuk pitch

- **Pencegahan kebocoran struktural** (probe + group split + eksklusi fixture demo) — jarang ada di level hackathon, ini argumen metodologi yang kuat.
- **Arsitektur katalog reason/edge/note** (code-first, dirender di locale, bilingual by construction) — cerita traceability yang genuinely kuat.
- **Cap band hardcoded** yang mencegah eskalasi dari sinyal tunggal/similarity-saja — safeguard anti-tuduhan-salah yang bisa didemokan langsung, bukan sekadar pernyataan kebijakan.
- **Kejujuran metodologis**: melaporkan hasil evaluasi hybrid yang tidak signifikan secara statistik — dokumen kanonikal secara eksplisit menyebut ini *"bukan produk gagal"* dan pelaporan jujur *"bukti metode yang lebih kuat daripada gain marjinal."*

## 15. Keterbatasan yang harus dinyatakan proaktif

- **Nol validasi pengguna nyata** — belum ada reviewer klaim sungguhan yang mencoba sistem ini.
- **Nol representativitas data** — data sintetik bergaya Synthea (berbasis distribusi penyakit/layanan AS), *"adapter menyamarkan bentuk, bukan representativitasnya."*
- **Threshold mode risiko ditentukan tim**, belum divalidasi pakar domain (mis. apa itu "split episode" yang wajar vs mencurigakan).
- **Autentikasi peran bisa dipalsukan sepenuhnya** — tidak ada autentikasi nyata di prototipe ini, sudah terdokumentasi di kode, sebaiknya dinyatakan proaktif ke juri daripada ditemukan sendiri.

## 16. Larangan mutlak saat menulis pitch/dokumen

- Jangan pernah sebut "MVP".
- Jangan pernah gunakan kata "fraud" sebagai temuan sistem.
- Jangan pernah menyiratkan kemampuan auto-decisioning/auto-rejection/penghentian pembayaran.
- Jangan pernah klaim angka prevalensi fraud nasional/penghematan — semua klaim harus dapat dilacak ke artefak evaluasi yang dihasilkan sistem, tidak boleh diketik manual.

---

## 17. Rekomendasi langkah berikutnya

1. **Prioritaskan Sprint 07** — rekam fallback video & lakukan rehearsal; ini kerja kalender manusia dengan risiko waktu tertinggi kalau ditunda.
2. **Paralel**, kumpulkan 3 sign-off Sprint 06 dari M1/M2/M3 berdasarkan tabel hasil di §13.
3. **Putuskan** nasib `packages/model/` (pertahankan untuk cerita "kami menguji lapisan statistik secara ilmiah" vs hapus untuk kesederhanaan) — keputusan ini harus melekat pada salah satu dari 3 sign-off di atas.
4. Pastikan narasi pitch menghormati §12, §15, §16 di atas — terutama menyatakan keterbatasan secara proaktif, bukan defensif.
