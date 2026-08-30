# TilikKlaim — Arah Desain (Ringkas)

> **Status:** 🟡 **Arah saja — detail visual menunggu tim desain.**
> **Versi:** 0.1.0 (placeholder) · **Tanggal:** 2026-08-30
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
| Tipografi | Sans-serif yang sangat terbaca; **digit sejajar** untuk nominal dan cap waktu; ukuran teks isi 14–16 px |
| Tata letak | Grid 12 kolom untuk desktop; kerapatan cocok untuk kerja operasional |
| Jarak | Sistem kelipatan 8 |
| Kartu | Hierarki lewat garis tepi dan latar, bukan bayangan tebal |
| Ikon | Bukti, waktu, tautan, dokumen, tinjauan manusia. **Dilarang** kepala robot atau ikon kilau/sparkle |
| Aksesibilitas | Kontras tingkat AA; navigasi papan ketik penuh; fokus selalu terlihat; status selalu punya label teks — **tidak pernah warna saja** |

**Empat keadaan wajib** untuk setiap komponen yang mengambil data: memuat, kosong, galat, nonaktif. Khusus `/cases/:id`, tambah keadaan kelima: versi usang.

**Badge "DATA SINTETIK"** wajib terlihat di setiap halaman dan tidak dapat ditutup.

---

## Yang MASIH KOSONG — untuk tim desain

| Berkas | Isi | Status |
|--------|-----|--------|
| `design/tokens.css` | Nilai warna, tipografi, jarak, radius, bayangan yang konkret | ⬜ Belum ada |
| `design/pages/*.html` | Mockup per halaman | ⬜ Belum ada |
| Peta anotasi | Pemetaan setiap bidang di layar ke respons antarmuka | ⬜ Belum ada |

**Sampai `tokens.css` ada**, frontend memakai nilai bawaan boilerplate. Task `port-design-tokens` di sprint frontend **tidak dapat ditutup** sebelum berkas ini masuk — ini dependensi yang sudah dicatat, bukan hal yang terlupa.

**Prioritas untuk tim desain**, kalau waktu terbatas: `/` (Antrean Review) dan `/cases/:id` (Detail Kasus) lebih dulu. Keduanya yang dipakai demo 90 detik di depan juri. `/ingest` dan `/evaluation` menyusul.

---

## Uji keterpahaman (dari master plan §14)

Sebelum desain dianggap selesai, tiga pembaca non-domain harus bisa menjawab setelah melihat layar antrean:

1. **Dalam 5 detik** — ini layar apa? (jawaban yang benar: daftar kerja yang terurut)
2. **Dalam 30 detik** — kenapa baris teratas ada di atas? (jawabannya harus terbaca dari kalimat alasan, bukan dari skor)

Kalau yang pertama mereka lihat adalah skor, nama model, atau grafik agregat — desainnya belum selesai, seberapa pun rapi tampilannya.
