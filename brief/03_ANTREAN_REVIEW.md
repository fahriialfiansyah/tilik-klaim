# Modul Antrean Review

> **Kode modul:** `03_ANTREAN_REVIEW` · **Prioritas:** Tinggi · **Gate:** G5 (9 September)

## 1. Gambaran Umum

Modul ini adalah **layar utama** petugas — halaman pertama yang dibuka setiap kali mereka mulai bekerja. Fungsinya menjawab satu pertanyaan operasional: **apa yang harus saya tinjau berikutnya?**

Prinsip perancangannya tegas: **antrean inilah dasbornya**. Tidak ada halaman ringkasan terpisah berisi grafik agregat, tidak ada peringkat fasilitas, tidak ada proyeksi nasional, tidak ada angka "potensi penghematan". Metrik yang ditampilkan di atas antrean dibatasi hanya pada hal yang benar-benar mengubah tindakan petugas hari itu. Segala sesuatu yang menarik untuk dipandang tetapi tidak mengubah keputusan justru merugikan — ia mengambil ruang layar dan perhatian dari pekerjaan yang sebenarnya.

Setiap baris di antrean dibuka dengan **kalimat alasan dalam bahasa kerja**, bukan dengan skor. Petugas harus bisa membaca "baris tindakan ini tidak punya catatan tindakan yang selesai" sebelum melihat angka apa pun.

### 1.1 Tujuan Modul

| Tujuan | Deskripsi |
|--------|-----------|
| Menjawab "tinjau apa berikutnya" | Urutan antrean langsung mencerminkan kasus yang paling layak ditangani dengan kapasitas yang ada. |
| Menampilkan alasan sebelum angka | Baris antrean dibuka dengan kalimat yang terbaca, bukan dengan skor atau nama model. |
| Membatasi metrik pada yang mengubah tindakan | Maksimal lima metrik, semuanya operasional. |
| Menghindari dasbor hiasan | Tidak ada grafik agregat, peringkat fasilitas, atau proyeksi yang tidak bisa ditindaklanjuti. |
| Menjaga kejujuran status | Kasus tanpa sinyal tidak pernah dilabeli "bersih" atau "aman". |

### 1.2 Target Pengguna

| Pengguna | Kebutuhan |
|----------|-----------|
| Petugas casemix / anti-fraud rumah sakit | Membuka satu layar dan langsung tahu kasus mana yang harus ditangani lebih dulu, tanpa menafsirkan grafik. |
| Peninjau senior | Melihat sebaran beban kerja dan kasus yang sedang menunggu bukti tambahan. |
| Juri / penonton demo | Memahami dalam lima detik apa yang sedang dilihat, tanpa penjelasan lisan. |

---

## 2. Fitur Utama

### 2.1 Metrik Operasional Ringkas

**Deskripsi**: Lima angka di bagian atas layar. Bukan lebih. Masing-masing dipilih karena mengubah tindakan petugas, bukan karena menarik dipandang.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Kasus menunggu ditinjau | Kartu ringkasan | Cacah kasus berstatus tersaring yang belum diambil siapa pun | Saat halaman dimuat / disegarkan manual |
| Konflik deterministik prioritas tinggi | Kartu ringkasan | Cacah kasus dengan pelanggaran aturan integritas yang pasti | Saat halaman dimuat |
| Kasus menunggu bukti tambahan | Kartu ringkasan | Cacah kasus yang sudah diminta kelengkapannya | Saat halaman dimuat |
| Waktu tengah dalam antrean | Kartu ringkasan | Ukuran berapa lama kasus rata-rata menunggu | Saat halaman dimuat |
| Versi mesin dan data aktif | Teks penanda versi | Versi aturan/model dan versi kumpulan data yang sedang berlaku | Statis per sesi |

**Interaksi**:

- Petugas membaca lima angka ini dalam sekali pandang, lalu turun ke tabel.
- Menekan salah satu kartu menerapkan saringan yang sesuai ke tabel di bawahnya.
- Penanda versi bisa disalin — dipakai saat melaporkan hasil atau membandingkan sesi.

> **Dilarang ditampilkan di sini**: jumlah "fraud yang dicegah", nilai rupiah yang "diselamatkan", peringkat fasilitas, proyeksi nasional, atau grafik tren yang tidak bisa ditindaklanjuti.

### 2.2 Tabel Antrean Kasus

**Deskripsi**: Daftar kerja utama. Setiap baris adalah satu kasus, dibuka dengan kalimat alasannya.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Kalimat alasan terkuat | Teks utama tiap baris | Kalimat bahasa kerja dari katalog alasan — **kolom pertama, sebelum angka apa pun** | Saat dimuat |
| Keping mode risiko | Label berwarna | Salah satu dari empat mode; lebih dari satu bila kasus punya banyak alasan | Saat dimuat |
| Pengenal kasus pseudonim | Teks pendek | Penanda kasus tanpa identitas peserta | Saat dimuat |
| Indikator kelengkapan bukti | Indikator status warna | Seberapa lengkap berkas pendukung kasus ini | Saat dimuat |
| Nominal klaim | Angka dengan digit sejajar | Nominal sintetik dan ilustratif | Saat dimuat |
| Umur kasus | Teks relatif | Berapa lama sejak kasus dibuat | Saat dimuat |
| Pita prioritas | Indikator status warna | Salah satu dari empat pita, dengan penjelasan yang bisa dibuka | Saat dimuat |
| Status kasus | Label | Posisi kasus dalam alur kerja | Saat dimuat |

**Interaksi**:

- Menekan satu baris membuka Detail Kasus dengan alasan terkuat sudah terbuka — **bukan** halaman profil umum.
- Mengurutkan berdasarkan prioritas, umur, nominal, atau kelengkapan bukti.
- Mengarahkan penunjuk ke pita prioritas memunculkan penjelasan "kenapa pita ini?".
- Nominal ditampilkan dengan digit sejajar agar mudah dibandingkan antar baris.

### 2.3 Penyaringan dan Pencarian

**Deskripsi**: Alat mempersempit antrean sesuai cara petugas membagi pekerjaannya.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Saringan status | Bilah saringan pilihan | Status kasus dalam alur kerja | Langsung saat dipilih |
| Saringan mode risiko | Bilah saringan pilihan | Empat mode risiko | Langsung |
| Saringan pita prioritas | Bilah saringan pilihan | Empat pita | Langsung |
| Saringan rentang tanggal | Pemilih rentang tanggal | Periode pembuatan kasus | Langsung |
| Pencarian | Kotak pencarian | Pencarian berdasarkan pengenal kasus pseudonim | Saat dikirim |
| Penanda saringan aktif | Deretan keping yang bisa dihapus | Saringan yang sedang berlaku | Langsung |

**Interaksi**:

- Beberapa saringan bisa aktif bersamaan; setiap saringan aktif muncul sebagai keping yang bisa dilepas satu per satu.
- Saringan yang tidak menghasilkan apa pun memunculkan tampilan kosong yang menjelaskan penyebabnya dan menawarkan pembersihan saringan — bukan tabel kosong tanpa keterangan.
- Pencarian hanya menerima pengenal pseudonim. **Tidak ada** pencarian berdasarkan nama atau nomor identitas — bidang itu memang tidak ada di sistem.

---

## 3. Navigasi & Interaksi

### 3.1 Peta Navigasi

| Dari Layar / Komponen | User Klik / Aksi | Menuju Ke | Context yang Dibawa |
|----------------------|------------------|-----------|---------------------|
| Antrean — baris kasus | Menekan baris | Detail Kasus (modul `04`) dengan alasan terkuat terbuka | Pengenal kasus, kode alasan terkuat |
| Antrean — kartu metrik | Menekan kartu | Tetap di Antrean, saringan diterapkan | Saringan yang sesuai kartu |
| Antrean — tombol "Masukkan bundel baru" | Menekan tombol | Layar Ingest (modul `01`), kosong | Tanpa konteks |
| Antrean — penanda versi | Menekan penanda | Layar Audit & Evaluasi (modul `05`), bagian versi | Versi mesin dan data aktif |
| Antrean — keping saringan | Menekan tanda silang | Tetap di Antrean, saringan itu dilepas | Sisa saringan tetap aktif |

### 3.2 Decision Branch

- **Saat antrean kosong**: bila belum ada kasus sama sekali → tampilan kosong mengarahkan ke layar Ingest. Bila kosong karena saringan → tampilan kosong menyebut saringan mana yang menyaring habis dan menawarkan pembersihan.
- **Saat layanan tidak merespons**: tampilkan galat yang jujur berikut tombol coba lagi. Jangan tampilkan tabel kosong yang menyamar sebagai "tidak ada kasus".
- **Saat kasus sedang ditinjau orang lain**: baris tetap tampil dengan status dalam peninjauan; petugas tahu kasus itu sudah ada yang menangani.

### 3.3 Navigasi Masuk dari Modul Lain

- Dari modul `01`, tombol "Kembali ke antrean" setelah pemasukan.
- Dari modul `04`, setelah disposisi tercatat — pengguna kembali ke antrean dengan saringan yang sama seperti sebelum masuk.

---

## 4. Alur Bisnis

### 4.1 Alur Memilih Kasus (Happy Path)

```
┌──────────────┐     ┌────────────────────────┐
│ Petugas buka │────▶│ Baca lima metrik       │
│ antrean      │     │ operasional            │
└──────────────┘     └───────────┬────────────┘
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │ Pindai kalimat alasan  │
                     │ baris teratas          │
                     └───────────┬────────────┘
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │ (opsional) Persempit   │
                     │ dengan saringan        │
                     └───────────┬────────────┘
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │ Tekan satu baris       │
                     └───────────┬────────────┘
                                 │
                                 ▼
                     ┌────────────────────────┐
                     │ Detail Kasus terbuka   │
                     │ pada alasan terkuat    │
                     └────────────────────────┘
```

**Penjelasan singkat:** Perjalanan dari membuka layar sampai membaca alasan konkret harus terjadi tanpa langkah menafsirkan grafik.

### 4.2 Alur Kembali setelah Disposisi

1. Petugas menyelesaikan keputusan di modul `04`.
2. Sistem mencatat kejadian audit dan memindahkan kasus ke status yang sesuai.
3. Petugas kembali ke antrean — **dengan saringan dan urutan yang sama** seperti sebelum ia masuk.
4. Kasus yang barusan ditangani berpindah posisi sesuai statusnya yang baru.
5. Metrik di atas ikut menyesuaikan.

> Mempertahankan saringan adalah hal kecil yang menentukan kenyamanan kerja berulang. Kehilangan saringan setiap kali kembali membuat alat ini melelahkan dipakai.

### 4.3 Alur Edge Case — Antrean Kosong dan Layanan Gagal

```
┌──────────────────────┐
│ Petugas buka antrean │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Minta daftar kasus   │
└──────────┬───────────┘
           │
    ┌──────┴───────┬──────────────────┬────────────────────┐
    ▼              ▼                  ▼                    ▼
┌─────────┐  ┌────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ Sedang  │  │ Belum ada  │  │ Kosong karena   │  │ Layanan tidak    │
│ memuat  │  │ kasus sama │  │ saringan        │  │ merespons        │
│         │  │ sekali     │  │                 │  │                  │
└────┬────┘  └─────┬──────┘  └────────┬────────┘  └────────┬─────────┘
     │             │                  │                    │
     ▼             ▼                  ▼                    ▼
┌─────────┐  ┌────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ Kerangka│  │ Ajakan ke  │  │ Sebut saringan  │  │ Galat jujur +    │
│ tampilan│  │ layar      │  │ penyebab +      │  │ tombol coba lagi │
│ bergerak│  │ Ingest     │  │ tombol bersih   │  │                  │
└─────────┘  └────────────┘  └─────────────────┘  └──────────────────┘
```

**Penjelasan:** Empat keadaan ini terlihat mirip di layar — tabel tanpa isi — tetapi penyebabnya berbeda dan tindak lanjutnya berbeda. Menyamakan keempatnya adalah cacat antarmuka yang paling sering terjadi dan paling merusak kepercayaan saat demo.

---

## 5. Data yang Dikelola Modul

Modul ini **tidak memiliki entity sendiri**. Ia membaca kasus dan alasan yang dihasilkan modul `02_MESIN_BUKTI_DETEKSI` dan menyajikannya sebagai daftar kerja.

### 5.1 Catatan untuk Tim Downstream

- Daftar antrean hanya boleh memuat bidang pseudonim. **Tidak ada** teks medis mentah di respons daftar — teks lengkap hanya muncul di layar detail, dan itu pun hanya bagian yang relevan dengan alasan.
- Daftar wajib berhalaman. Menarik seluruh kasus sekaligus bukan pilihan.
- Kalimat alasan berasal dari katalog alasan modul `02`, bukan dirumuskan ulang di sisi antarmuka. Kalimat yang berbeda antara antrean dan detail adalah cacat.

---

## 6. Kebutuhan Data Eksternal

**Tidak ada.**

---

## 7. Stack Agent Modul

**Tidak ada agent.** Urutan antrean sepenuhnya ditentukan pita prioritas dan komponen skor dari modul `02`. Tidak ada pengurutan adaptif, tidak ada personalisasi, tidak ada pembelajaran dari perilaku petugas.

---

## 8. Konfigurasi Alert

Modul ini tidak mengirim notifikasi. Seluruh penandaan terjadi secara visual di layar.

### 8.1 Severity Levels

| Pita | Penanda visual | Arti |
|------|----------------|------|
| Konflik deterministik | Merah | Aturan integritas dilanggar secara pasti. **Merah menandai konflik, bukan kesalahan pihak mana pun.** |
| Sinyal prioritas tinggi | Kuning | Perlu ditinjau; baca sinyal pendukung dan penentangnya |
| Perlu konteks | Kuning muda | Bukti belum cukup; kemungkinan perlu meminta kelengkapan |
| Tidak ada risiko teramati | Netral | Tidak ada detektor menyala. **Bukan** pernyataan bahwa klaim bersih. |

> Hijau hanya dipakai untuk aksi yang sudah selesai dan tervalidasi — tidak pernah untuk menandai klaim sebagai aman.

---

## 9. Standar Layanan yang Diharapkan

### 9.1 Kecepatan Tampil Data

Cepat. Antrean adalah layar pertama yang dilihat juri; kelambatan di sini merusak kesan seluruh sistem.

### 9.2 Frekuensi Pembaruan Data

Saat dimuat dan saat disegarkan manual. Tidak ada pembaruan otomatis berkala — pembaruan yang menggeser baris saat petugas sedang membaca justru mengganggu.

### 9.3 Ketersediaan Layanan

Berfungsi penuh tanpa jaringan eksternal.

### 9.4 Standar Aksesibilitas

- Kontras warna memenuhi tingkat AA.
- Seluruh tabel dapat dinavigasi dengan papan ketik; fokus selalu terlihat.
- Status **tidak pernah** disampaikan lewat warna saja — selalu ada label teks pendamping.
- Nominal dan cap waktu memakai digit sejajar agar terbandingkan antar baris.

---

## 10. Use Case Scenarios

### 10.1 Skenario Happy Path — Memulai Hari Kerja

Petugas membuka TilikKlaim pada pagi hari. Lima metrik di atas memberitahu: dua belas kasus menunggu ditinjau, tiga di antaranya konflik deterministik, dua sedang menunggu bukti tambahan. Ia menekan kartu "konflik deterministik" — tabel langsung menyaring ke tiga kasus itu. Baris teratas berbunyi: baris tindakan ini tidak punya catatan tindakan yang selesai. Ia menekan baris tersebut dan langsung masuk ke bukti. Tidak ada satu pun grafik yang perlu ia tafsirkan sepanjang alur ini.

### 10.2 Skenario Edge Case — Saringan Menyaring Habis

Petugas mengaktifkan saringan mode "dokumentasi salinan" digabung rentang tanggal minggu ini. Tidak ada kasus yang cocok. Layar menampilkan keterangan bahwa kombinasi kedua saringan itu tidak menghasilkan kasus, menampilkan kedua keping saringan yang aktif, dan menawarkan tombol untuk melepas keduanya. Petugas melepas saringan tanggal dan hasil muncul. Yang penting di sini: ia tidak pernah dibiarkan menduga apakah sistemnya rusak atau memang tidak ada data.

### 10.3 Skenario — Momen Juri dalam Lima Detik

Seorang juri melihat layar antrean untuk pertama kali tanpa penjelasan lisan. Dalam lima detik ia harus bisa menyimpulkan: ini daftar kerja, terurut berdasarkan sesuatu, dan baris teratas menjelaskan dirinya sendiri dalam bahasa yang ia pahami. Bila yang pertama ia lihat adalah skor, nama model, atau grafik agregat, rancangan layar ini gagal — terlepas dari sebagus apa mesin di belakangnya.

---

## 11. Referensi Implementasi

Prinsip dasbor dan daftar komponen per halaman ada di `docs/canonical/01_product_decision.md` bagian *Pages and core components* dan *Main dashboard principles*. Kontrak daftar kasus dan batasan bidang pseudonim ada di `docs/canonical/03_architecture.md`.

---

*Bagian dari Dokumentasi Implementasi TilikKlaim · Versi 1.0.0 · 2026-08-30*
