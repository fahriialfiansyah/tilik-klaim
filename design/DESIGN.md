# TilikKlaim — Arah Desain (Ringkas)

> **Status:** 🟢 **Mockup tim desain sudah masuk — token terkunci dan sudah terpasang di aplikasi.**
> **Versi:** 0.3.0 · **Tanggal:** 2026-09-01
> **Sumber:** `docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx` §14 (Figma / UX Brief)
> **Halaman & widget:** [`sprint/00-app-spec.md`](../sprint/00-app-spec.md)

Dokumen ini sengaja **tidak lengkap**. Ia hanya mengunci arah yang sudah diputuskan di master plan, supaya pekerjaan frontend bisa jalan tanpa menunggu, dan supaya tim desain punya batas yang jelas saat mengisi detailnya.

---

## Yang sudah dikunci (jangan diubah tanpa diskusi)

**Kesan produk.** Modern, profesional-kesehatan, operasional, tenang, kredibel untuk lingkungan rumah sakit dan BPJS. Rasa percaya datang dari hierarki, asal-usul data, dan kejelasan status — **bukan** dari gradien neon atau efek chatbot.

| Elemen | Arah |
|--------|------|
| Warna utama | Navy/teal gelap |
| Permukaan | Putih pudar |
| Kuning amber | "Perlu ditinjau" |
| Merah | **Hanya** untuk konflik deterministik — menandai konflik pasti, **bukan** menandai pihak yang bersalah |
| Hijau | **Hanya** untuk aksi yang selesai dan tervalidasi — tidak pernah untuk menandai klaim sebagai aman |
| Tipografi | IBM Plex Sans; **digit sejajar** untuk nominal dan cap waktu (IBM Plex Mono); ukuran teks isi **13 px** — dinaikkan dari tebakan awal 14–16 px agar cocok dengan mockup, lihat § Deviasi |
| Tata letak | Grid 12 kolom untuk desktop; kerapatan cocok untuk kerja operasional |
| Jarak | Sistem kelipatan 8 |
| Kartu | Hierarki lewat garis tepi dan latar, bukan bayangan tebal |
| Ikon | Bukti, waktu, tautan, dokumen, tinjauan manusia. **Dilarang** kepala robot atau ikon kilau/sparkle |
| Aksesibilitas | Kontras tingkat AA; navigasi papan ketik penuh; fokus selalu terlihat; status selalu punya label teks — **tidak pernah warna saja** |

**Empat keadaan wajib** untuk setiap komponen yang mengambil data: memuat, kosong, galat, nonaktif. Khusus `/cases/:id`, tambah keadaan kelima: versi usang.

**Badge "DATA SINTETIK"** wajib terlihat di setiap halaman dan tidak dapat ditutup.

---

## Berkas desain

| Berkas | Isi | Status |
|--------|-----|--------|
| `design/mockup/tilik-klaim-v2.bundle.html` | Kiriman asli tim desain. Bundel Claude Design canvas; buka langsung di peramban untuk melihat versi hidup | ✅ Masuk |
| `design/mockup/reference.html` | Turunan yang bisa dibaca: markup + CSS keempat layar. **Ini yang dipakai saat implementasi React** | ✅ Turunan |
| `design/mockup/unpack.py` | Membangkitkan ulang kedua turunan di atas dari bundel | ✅ Ada |
| `design/tokens.css` | 35 token warna × 2 tema, plus tipografi, jarak, dan alias semantik | ✅ Masuk |
| `apps/web/src/styles/tokens.css` | Salinan mentah `design/tokens.css` di dalam aplikasi. Disalin dengan `cp`, tidak diketik ulang | ✅ Terpasang |
| `apps/web/src/styles/app.css` | Pengikatan Tailwind v4 (`@theme inline`) ke token di atas, plus nama yang dipakai shadcn | ✅ Terpasang |
| Peta anotasi | Pemetaan setiap bidang di layar ke respons antarmuka | ⬜ Belum ada — `/` sudah terimplementasi tanpa peta ini, `/cases/:id` yang paling membutuhkannya |

Keempat layar ada di dalam satu berkas `reference.html`, ditandai atribut
`data-screen-label`: `Antrean Review`, `Detail Kasus`, `Ingest / Demo`, `Audit & Evaluasi`.
Placeholder `{{ ... }}` tampil apa adanya di turunan itu — justru menandai titik pengikatan data.

Kalau tim desain mengirim bundel baru, **jangan menyalin nilai dengan tangan**:

```
python3 design/mockup/unpack.py design/mockup/<bundel-baru>.html
```

Bagian tipografi, jarak, dan alias semantik di `tokens.css` ditulis tangan dan tidak ditimpa —
hanya blok warna yang perlu disegarkan.

---

## Deviasi & hal yang masih terbuka

Tiga hal di mockup tidak sejalan dengan arah yang dikunci di atas. **Ketiganya sudah selesai**
per 1 Sep 2026; tidak ada lagi yang menunggu keputusan.

Cara menyelesaikannya sengaja dibedakan: **ambang yang bisa diukur diperbaiki tanpa menunggu,
pertimbangan desain diserahkan pada pemiliknya.** Dua yang pertama ada di tabel di bawah; yang
ketiga — ukuran label mikro — ada di bagian sesudahnya karena keputusannya datang belakangan.

| Hal | Temuan | Keputusan |
|-----|--------|-----------|
| Kontras `--t-3` | Teks tersier `#6d7b79` di atas kartu putih hanya **4.41:1** — di bawah ambang AA 4.5:1 | ✅ **Diperbaiki dua kali.** 30 Agu → `#6b7977` (4.54:1 di atas `--s-card`). **1 Sep → `#63706e`**: pengukuran pertama hanya menguji satu dari tiga permukaan. Aplikasi juga memakai `--t-3` di atas `--s-sunk` (kepala tabel, **4.33:1**) dan `--s-page` (catatan kaki, **4.07:1**) — keduanya gagal. Nilai baru lulus di ketiganya: 5.16 / 4.92 / 4.63. AA adalah lantai terukur yang sudah dikunci di tabel atas, bukan preferensi |
| Ukuran teks isi | Kontrak lama menyebut 14–16 px; mockup memakai **13 px** (64 kemunculan) | ✅ **Kontraknya yang disesuaikan** menjadi 13 px. Baris 14–16 px ditulis saat dokumen ini masih berstatus "arah saja" — sebuah tebakan placeholder. Mockup adalah bukti yang lebih baru dari pihak yang memiliki keputusan kerapatan, dan 13 px koheren untuk tabel operasional. WCAG tidak menetapkan ukuran font minimum |

Sisanya lulus. Diukur ulang **pada layar yang sudah jadi**, bukan hanya dari nilai token —
di situlah kegagalan `--t-3` di atas dua permukaan lain akhirnya terlihat. Angka terendah pada
`/` (Antrean Review) setelah perbaikan: **4.63:1** pada tema terang dan **5.78:1** pada tema
gelap; kelima pita status berada jauh di atasnya (5.81–9.83).

### Label mikro — sudah diputuskan (1 Sep 2026)

Label mikro **9 px** (35 kemunculan, berpasangan dengan `letter-spacing: .13em`) **dinaikkan ke
11 px** atas keputusan pemilik proyek. Alasannya keterbacaan pada alat yang dipakai sepanjang
hari; ini bukan pelanggaran standar, karena itu keputusannya ditunggu dan tidak diambil sepihak.

Perubahan diterapkan di `design/tokens.css` (bukan ditambal di salinan aplikasi), mengikuti cara
koreksi `--t-3` ditangani. Kepala tabel antrean sudah diperiksa ulang setelah perubahan: lebar
kolom tetap muat dan tidak ada label yang terpotong.

**Prioritas untuk tim desain** kalau masih ada waktu: peta anotasi untuk `/cases/:id`
(Detail Kasus). `/` (Antrean Review) sudah terimplementasi dari mockup tanpa peta anotasi, tetapi
`/cases/:id` punya 27 widget dan jauh lebih mahal kalau salah tafsir. Keduanya yang dipakai demo
90 detik di depan juri.

---

## Uji keterpahaman (dari master plan §14)

Sebelum desain dianggap selesai, tiga pembaca non-domain harus bisa menjawab setelah melihat layar antrean:

1. **Dalam 5 detik** — ini layar apa? (jawaban yang benar: daftar kerja yang terurut)
2. **Dalam 30 detik** — kenapa baris teratas ada di atas? (jawabannya harus terbaca dari kalimat alasan, bukan dari skor)

Kalau yang pertama mereka lihat adalah skor, nama model, atau grafik agregat — desainnya belum selesai, seberapa pun rapi tampilannya.
