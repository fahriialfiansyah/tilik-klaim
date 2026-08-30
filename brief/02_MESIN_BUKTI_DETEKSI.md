# Modul Mesin Bukti & Deteksi Risiko

> **Kode modul:** `02_MESIN_BUKTI_DETEKSI` · **Prioritas:** Tinggi · **Gate:** G4 (tiga mode, 5 September) → G6 (mode keempat, 12 September)

## 1. Gambaran Umum

Ini adalah **jantung sistem**. Modul ini menerima bundel klaim yang sudah lolos validasi, lalu melakukan dua hal berurutan. Pertama, ia **merajut bukti**: membangun peta hubungan antara klaim, baris tagihan, kunjungan, dan catatan klinis pendukungnya — sehingga pertanyaan "apa dasar tagihan ini?" punya jawaban yang bisa ditelusuri sampai ke sumbernya. Kedua, ia **menguji integritas**: menjalankan sekumpulan aturan berversi yang memeriksa apakah setiap tagihan punya dukungan yang konsisten, dan menghitung sinyal statistik yang membantu mengurutkan kasus mana yang paling layak ditinjau lebih dulu.

Yang membedakan modul ini dari "detektor fraud" pada umumnya: **keluarannya bukan skor, melainkan daftar alasan**. Setiap alasan menunjuk ke sumber daya spesifik, menyebut aturan mana yang memicunya, versi berapa aturan itu, dan — ini yang jarang ada — **bukti tandingan** kalau ada hal yang justru melemahkan sinyal tersebut. Skor prioritas tetap dihasilkan, tetapi hanya sebagai alat pengurutan antrean, bukan sebagai vonis.

Modul ini **tidak pernah** menyatakan fraud, tidak pernah menolak klaim, tidak pernah mengubah kode, dan tidak pernah memutuskan kelayakan medis.

### 1.1 Tujuan Modul

| Tujuan | Deskripsi |
|--------|-----------|
| Menjadikan dasar tagihan dapat ditelusuri | Setiap baris tagihan punya jalur bukti yang bisa dibuka sampai ke sumber daya asalnya. |
| Menghasilkan alasan, bukan sekadar angka | Keluaran utama adalah daftar alasan berkode yang menyebut bukti spesifik; skor hanya alat pengurutan. |
| Menampilkan bukti tandingan | Hal yang melemahkan sebuah sinyal ditampilkan bersamaan dengan sinyal itu, bukan disembunyikan. |
| Menahan diri saat bukti tidak cukup | Berkas yang tidak lengkap menurunkan keyakinan dan mengarah ke "minta bukti", bukan naik ke pita tertinggi. |
| Menjaga hasil tetap dapat diulang | Bundel yang sama dengan versi mesin yang sama selalu menghasilkan alasan yang sama. |
| Membuat kerumitan membayar dirinya | Lapisan statistik hanya dipertahankan bila terbukti menambah nilai terukur di atas aturan-saja. |

### 1.2 Target Pengguna

| Pengguna | Kebutuhan |
|----------|-----------|
| Petugas casemix / anti-fraud rumah sakit | Tahu **mengapa** sebuah kasus muncul di urutan atas, dan bisa menelusuri sampai ke bukti aslinya. |
| Anggota tim teknis | Menambah atau mengubah aturan tanpa membongkar antarmuka, dan tahu persis versi aturan mana yang menghasilkan hasil mana. |
| Anggota tim proposal | Menjelaskan cara kerja deteksi ke juri tanpa harus mengatakan "modelnya kotak hitam". |

---

## 2. Fitur Utama

### 2.1 Perajutan Bukti

**Deskripsi**: Mengubah bundel yang datar menjadi peta hubungan — menghubungkan setiap baris tagihan ke kunjungan, tindakan, obat, pemeriksaan, dan dokumen yang seharusnya mendukungnya.

**Hubungan yang wajib dibangun dan diuji**:

| Hubungan | Arti dalam bahasa kerja |
|----------|------------------------|
| Klaim memuat baris tagihan | Satu klaim terdiri dari beberapa item yang ditagihkan |
| Baris tagihan berasal dari item biaya | Tagihan punya asal-usul pencatatan biaya |
| Klaim/baris tagihan merujuk kunjungan | Tagihan terikat pada satu kunjungan tertentu |
| Baris tagihan didukung oleh bukti klinis | Tindakan, penyerahan obat, hasil pemeriksaan, atau laporan diagnostik yang membenarkan tagihan |
| Kunjungan memiliki catatan klinis | Kondisi, tindakan, obat, dan dokumen yang tercatat pada kunjungan itu |
| Dokumen ditulis oleh tenaga medis dan terikat kunjungan | Asal-usul penulisan dokumen |
| Klaim berpotensi duplikat dengan klaim lain | Kandidat pasangan tagihan berulang |
| Dokumen mirip dengan dokumen lain | Kandidat dokumentasi salinan |
| Klaim bagian dari satu episode | Pengelompokan layanan yang seharusnya utuh |

**Setiap hubungan wajib menyimpan**: pengenal sumber daya asal, aturan yang menurunkannya, versi aturan itu, dan tingkat keyakinan bila hubungan itu disimpulkan (bukan tertulis eksplisit).

**Interaksi**: Modul ini tidak punya antarmuka sendiri. Hasil perajutan dikonsumsi modul `04_DETAIL_KASUS_DISPOSISI` sebagai jejak bukti dan linimasa episode.

### 2.2 Empat Mode Deteksi Risiko

**Deskripsi**: Empat pola risiko yang disebut resmi dalam kategori Efisiensi Risiko pada Fasilitas Kesehatan. Masing-masing punya uji deterministik sebagai dasar, dan penguat statistik sebagai lapisan kedua.

| Mode | Yang diperiksa | Bukti yang wajib ditampilkan |
|------|----------------|------------------------------|
| **Tagihan tanpa bukti tindakan** | Ada baris tagihan tindakan atau obat, tetapi tidak ada catatan tindakan/penyerahan yang selesai dan cocok — atau catatannya ditandai keliru-input | Baris yang tak didukung; jenis bukti yang diharapkan; sumber daya apa saja yang sudah dicari; bukti tandingan bila ada |
| **Tagihan berulang** | Klaim kedua untuk peserta/fasilitas/episode yang sama dengan tumpang tindih baris tagihan, meski pengenalnya berbeda | Pasangan kandidat; rentang tumpang tindih; baris dan nominal yang cocok; bidang yang berbeda |
| **Dokumentasi salinan** | Narasi klinis atau urutan layanan yang identik atau nyaris identik muncul lintas kunjungan atau lintas peserta | Nilai kemiripan berikut komponennya; potongan teks yang cocok; catatan bahwa penggunaan templat yang sah bisa terlihat serupa |
| **Pemecahan episode** | Satu episode layanan yang koheren tampak dipecah menjadi beberapa klaim berdekatan waktu | Linimasa episode; konteks yang dibagi; baris dan nominal yang terpecah; pengecualian yang berlaku |

**Interaksi**: Hasil setiap mode muncul sebagai kartu alasan di modul `04`, diurutkan berdasarkan kekuatan bukti — bukan berdasarkan nominal rupiah.

### 2.3 Peringkat dan Pita Prioritas

**Deskripsi**: Menyusun kasus ke dalam pita prioritas agar petugas dengan kapasitas review terbatas menangani yang paling informatif lebih dulu.

**Empat pita prioritas**:

| Pita | Arti | Konsekuensi |
|------|------|-------------|
| Konflik deterministik | Sebuah aturan integritas berversi dilanggar secara pasti | Naik ke prioritas tinggi — **tetapi tidak pernah ditolak otomatis** |
| Sinyal prioritas tinggi | Ambang batas dipilih untuk target ketepatan atau kapasitas review tertentu | Ditampilkan bersama sinyal pendukung **dan** sinyal yang berlawanan |
| Perlu konteks | Bukti tidak pasti atau berkas tidak lengkap | Diarahkan ke "minta bukti tambahan" atau pengambilan sampel acak |
| Tidak ada risiko teramati | Tidak ada detektor terpilih yang menyala | **Tidak pernah** dilabeli "bersih" atau "aman" — hanya "tidak ada yang teramati" |

**Pagar pengaman yang wajib berlaku**:

- Kemiripan teks **saja** tidak pernah cukup untuk mencapai pita tertinggi. Harus ada penguat dari keluarga bukti lain.
- Bukti yang hilang **ditambah** berkas yang tidak lengkap justru **menurunkan** keyakinan dan memicu "minta bukti" — bukan menaikkan sinyal.
- Sidik episode yang persis duplikat berprioritas tinggi, **tetap** wajib ditinjau manusia.
- Seluruh komponen skor dan versinya disimpan, tidak hanya angka akhirnya.
- Tidak ada ambang batas "75% = fraud" yang dipatok di awal. Pita dikalibrasi pada data validasi, dan dasarnya ditampilkan.

**Interaksi**: Pita prioritas menentukan urutan di modul `03_ANTREAN_REVIEW`. Setiap pita punya penjelasan singkat "kenapa pita ini?" yang bisa dibuka petugas.

### 2.4 Katalog Alasan Berversi

**Deskripsi**: Daftar terkelola berisi setiap kode alasan yang bisa dikeluarkan sistem, beserta kalimat penjelasnya dalam bahasa manusia dan jenis bukti yang wajib menyertainya.

**Isi tiap entri katalog**:

| Informasi | Deskripsi |
|-----------|-----------|
| Kode alasan | Penanda stabil yang dipakai antarmuka dan pengujian |
| Kalimat penjelas | Bahasa kerja yang bisa dibaca petugas, bukan jargon model |
| Mode risiko terkait | Salah satu dari empat mode |
| Jenis bukti wajib | Sumber daya apa yang harus ikut ditampilkan agar alasan ini sah |
| Versi aturan | Versi yang berlaku; hasil lama tetap merujuk versi lamanya |

**Interaksi**: Katalog ini dokumen hidup yang dibaca tim antarmuka dan tim proposal. Perubahan aturan wajib menaikkan versi — tidak boleh mengubah perilaku diam-diam.

---

## 3. Navigasi & Interaksi

### 3.1 Peta Navigasi

| Dari Layar / Komponen | User Klik / Aksi | Menuju Ke | Context yang Dibawa |
|----------------------|------------------|-----------|---------------------|
| Ingest — tombol "Saring klaim" | Menekan tombol | Detail Kasus (modul `04`), alasan terkuat sudah terbuka | Pengenal pemasukan, pengenal kasus, versi mesin |
| Detail Kasus — kartu alasan | Menekan satu kartu | Panel jejak bukti terbuka untuk alasan itu | Kode alasan, rujukan bukti, versi aturan |
| Detail Kasus — alasan tagihan berulang / salinan | Menekan "Bandingkan" | Laci perbandingan berdampingan | Pasangan kandidat, bidang yang cocok dan berbeda |
| Antrean — baris kasus | Menekan baris | Detail Kasus dengan alasan terkuat terbuka | Pengenal kasus |

### 3.2 Decision Branch

- **Bila berkas tidak lengkap**: sistem menurunkan pita, menampilkan catatan kelengkapan, dan menyarankan "minta bukti tambahan" sebagai aksi utama.
- **Bila hanya kemiripan teks yang menyala**: pita dibatasi di bawah tertinggi, disertai catatan eksplisit tentang kemungkinan penggunaan templat yang sah.
- **Bila tidak ada detektor menyala**: kasus tetap dibuat dengan status "tidak ada risiko teramati". Sistem tidak mengklaim klaim tersebut bersih.
- **Bila bundel dan versi mesin identik dengan penyaringan sebelumnya**: hasil yang sama dikembalikan, bukan dihitung ulang.

### 3.3 Navigasi Masuk dari Modul Lain

- Dari modul `01`, setelah validasi berhasil dan pengguna menekan "Saring klaim".
- Dari modul `04`, setelah pengguna memilih "minta bukti tambahan" dan berkas versi baru masuk — kasus disaring ulang dan kembali ke status tersaring.

---

## 4. Alur Bisnis

### 4.1 Alur Penyaringan (Happy Path)

```
┌────────────────────┐     ┌──────────────────────┐
│ Bundel kanonik     │────▶│ Rajut peta bukti:    │
│ (dari modul 01)    │     │ klaim → baris →      │
└────────────────────┘     │ kunjungan → bukti    │
                           └──────────┬───────────┘
                                      │
                                      ▼
                           ┌──────────────────────┐
                           │ Jalankan aturan      │
                           │ integritas berversi  │
                           │ (empat mode)         │
                           └──────────┬───────────┘
                                      │
                                      ▼
                           ┌──────────────────────┐
                           │ Hitung sinyal        │
                           │ kemiripan & anomali  │
                           │ untuk pengurutan     │
                           └──────────┬───────────┘
                                      │
                                      ▼
                           ┌──────────────────────┐
                           │ Kumpulkan alasan +   │
                           │ bukti + bukti        │
                           │ tandingan + pita     │
                           └──────────┬───────────┘
                                      │
                                      ▼
                           ┌──────────────────────┐
                           │ Buat kasus, status   │
                           │ TERSARING, masuk     │
                           │ antrean              │
                           └──────────────────────┘
```

**Penjelasan singkat:** Aturan berjalan lebih dulu dan menghasilkan alasan yang pasti; sinyal statistik datang setelahnya dan hanya membantu pengurutan. Urutan ini disengaja — bukti mendahului peringkat.

### 4.2 Alur Penyaringan Ulang setelah Bukti Tambahan Masuk

1. Petugas menandai kasus dengan aksi "minta bukti tambahan" di modul `04`.
2. Kasus berpindah ke status menunggu bukti.
3. Berkas versi baru masuk lewat modul `01`, terhubung ke kasus yang sama.
4. Modul ini menyaring ulang dengan versi mesin yang berlaku saat itu.
5. Kasus kembali ke status tersaring dengan alasan yang diperbarui.
6. Riwayat alasan versi lama **tidak dihapus** — tersimpan di jejak audit sebagai bagian dari riwayat kasus.

### 4.3 Alur Edge Case — Berkas Tidak Lengkap Menyerupai Tagihan Tanpa Bukti

```
┌────────────────────────────────────────────────────────┐
│ Baris tagihan tindakan TIDAK punya catatan pendukung   │
└────────────────────────┬───────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ Periksa kelengkapan  │
              │ berkas dari modul 01 │
              └──────────┬───────────┘
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
┌──────────────────────┐      ┌──────────────────────────┐
│ Berkas LENGKAP —     │      │ Berkas TIDAK LENGKAP —   │
│ bukti memang absen   │      │ sumber daya pendukung    │
│                      │      │ tidak dikirim            │
└──────────┬───────────┘      └──────────┬───────────────┘
           │                             │
           ▼                             ▼
┌──────────────────────┐      ┌──────────────────────────┐
│ Alasan: baris tidak  │      │ Pita DITURUNKAN ke       │
│ didukung. Pita       │      │ "perlu konteks".         │
│ prioritas tinggi.    │      │ Aksi disarankan:         │
│ Tetap wajib ditinjau │      │ MINTA BUKTI TAMBAHAN     │
│ manusia.             │      │ — bukan konfirmasi       │
└──────────────────────┘      └──────────────────────────┘
```

**Penjelasan:** Ini pembeda etis paling penting di seluruh sistem. Ketiadaan bukti dalam rekam medis yang belum lengkap **bukan** bukti bahwa layanan tidak diberikan. Sistem wajib membedakan keduanya secara struktural, bukan menyerahkannya pada kebijaksanaan petugas.

### 4.4 Alur Edge Case — Penggunaan Templat yang Sah Terlihat seperti Salinan

1. Sinyal kemiripan dokumen menyala tinggi lintas beberapa kunjungan.
2. Sistem memeriksa apakah ada penguat dari keluarga bukti lain — kelengkapan bukti, keutuhan episode, konteks sebanding antar fasilitas.
3. **Tidak ada penguat** → pita dibatasi di bawah tertinggi.
4. Kartu alasan menampilkan potongan teks yang cocok **berikut peringatan eksplisit**: dokumentasi berbasis templat yang sah dapat menghasilkan kemiripan tinggi.
5. Petugas melihat peringatan itu **sebelum** mengambil keputusan, bukan setelahnya.

---

## 5. Data yang Dikelola Modul

### 5.1 Entity Bisnis Utama

**Kasus**

| Informasi | Deskripsi |
|-----------|-----------|
| Pengenal kasus | Penanda unik |
| Kaitan ke pemasukan | Bundel asal dan sidik digitalnya |
| Status | Baru / tersaring / dalam peninjauan / menunggu bukti / ditutup-ditolak / anomali terkonfirmasi / dieskalasi / input tidak sah |
| Pita prioritas | Salah satu dari empat pita |
| Versi mesin | Versi aturan dan model yang berlaku saat penyaringan |
| Nomor versi kasus | Untuk pengunci optimistik saat disposisi |
| Durasi penyaringan | Untuk pengukuran kelayakan teknis |

**Alasan**

| Informasi | Deskripsi |
|-----------|-----------|
| Kode alasan | Merujuk katalog alasan |
| Mode risiko | Salah satu dari empat mode |
| Rujukan bukti | Daftar pengenal sumber daya yang mendasari |
| Bukti tandingan | Rujukan sumber daya yang melemahkan alasan ini |
| Komponen skor | Nilai per komponen, bukan hanya satu angka gabungan |
| Versi aturan | Versi aturan yang memicu |

**Hubungan Bukti**

| Informasi | Deskripsi |
|-----------|-----------|
| Simpul asal dan tujuan | Dua sumber daya yang dihubungkan |
| Jenis hubungan | Salah satu hubungan pada tabel 2.1 |
| Aturan penurun | Aturan yang membangun hubungan ini |
| Versi | Versi aturan penurun |
| Tingkat keyakinan | Diisi bila hubungan disimpulkan, kosong bila eksplisit |

### 5.2 Catatan untuk Tim Downstream

- Alasan disajikan sebagai **vektor**, bukan satu angka. Antarmuka wajib menampilkan alasan sebelum skor.
- Setiap rujukan bukti wajib dapat dibuka. Rujukan yang menunjuk ke sumber daya tidak ada adalah cacat, bukan sekadar tampilan kosong.
- Metadata penyuntik label dari modul `06` **dilarang keras** masuk sebagai bahan pertimbangan deteksi. Harus ada pengujian yang membuktikan ini.

---

## 6. Kebutuhan Data Eksternal

**Tidak ada.** Deteksi hanya membaca bundel yang sudah masuk dan riwayat klaim sintetik yang tersimpan. Tidak ada pemanggilan layanan luar, tidak ada pengambilan referensi daring.

---

## 7. Stack Agent Modul

**Tidak ada agent. Tidak ada LLM di jalur keputusan risiko.**

Deteksi memakai tiga jenis metode yang seluruhnya dapat diperiksa manusia:

| Metode | Peran | Batas |
|--------|-------|-------|
| Aturan deterministik berversi | Uji integritas untuk pola yang diketahui | Menghasilkan alasan pasti; tidak ada ambang tersembunyi di kode antarmuka |
| Kemiripan teks klasik | Mendeteksi dokumentasi menyerupai salinan | Tidak pernah cukup sendirian untuk pita tertinggi |
| Deteksi anomali antar-rekam | Mengurutkan pola janggal lintas rekam | Tidak berpura-pura mengetahui label fraud |

Ringkasan berbantuan LLM hanya boleh dipertimbangkan setelah Gate 6 sebagai fitur opsional, dengan syarat: hanya membaca bukti terstruktur, wajib menyebut pengenal sumber daya, keluaran ditolak bila menyebut pengenal yang tidak ada, dibatasi lima kalimat, dilarang memakai kata "fraud" sebagai temuan, dan **tidak pernah** memengaruhi skor maupun transisi status. Rasionalnya terkunci di `docs/canonical/decisions/ADR-0002-no-llm-in-risk-score.md`.

---

## 8. Konfigurasi Alert

Modul ini tidak mengirim notifikasi keluar. "Alert" di sini berarti pita prioritas yang muncul di antrean.

### 8.1 Threshold

Tidak ada ambang batas yang dipatok di awal. Ambang dipilih pada data validasi untuk mencapai target ketepatan atau kapasitas review tertentu, kemudian dibekukan sebelum evaluasi akhir. Dasar pemilihan setiap pita wajib dapat ditampilkan ke pengguna lewat penjelasan "kenapa pita ini?".

### 8.2 Severity Levels

| Pita | Penanda visual | Aksi yang disarankan sistem |
|------|----------------|------------------------------|
| Konflik deterministik | Merah — **penanda konflik pasti, bukan penanda bersalah** | Tinjau prioritas tinggi |
| Sinyal prioritas tinggi | Kuning | Tinjau dengan membaca sinyal pendukung dan penentang |
| Perlu konteks | Kuning muda | Minta bukti tambahan |
| Tidak ada risiko teramati | Netral | Tidak ada aksi; **bukan** pernyataan bahwa klaim bersih |

---

## 9. Standar Layanan yang Diharapkan

### 9.1 Kecepatan Tampil Data

Cepat. Penyaringan satu bundel harus selesai dalam hitungan detik agar perjalanan demo utama tetap di bawah 90 detik.

### 9.2 Frekuensi Pembaruan Data

Dipicu pengguna. Tidak ada penyaringan berjadwal dan tidak ada pemrosesan latar belakang berkelanjutan.

### 9.3 Ketersediaan Layanan

Berfungsi penuh tanpa jaringan eksternal.

### 9.4 Batas yang Tidak Boleh Dilanggar

Sistem **boleh**: memeriksa bentuk dan rujukan; menyorot bukti yang hilang, ganda, atau bertentangan; mengurutkan kasus untuk ditinjau; menampilkan rekam serupa; menyarankan alasan terstruktur.

Sistem **tidak boleh**: menyatakan seseorang atau fasilitas melakukan fraud; menolak klaim, menghentikan pembayaran, menjatuhkan sanksi, atau mengubah kode; memutuskan kelayakan medis atau menegakkan diagnosis; memperlakukan bukti yang hilang sebagai bukti bahwa layanan tidak diberikan; menyembunyikan ketidakpastian, bukti tandingan, atau keterbatasan data.

---

## 10. Use Case Scenarios

### 10.1 Skenario Happy Path — Tagihan Tanpa Bukti Tindakan

Sebuah bundel masuk berisi klaim dengan lima baris tagihan. Modul merajut peta bukti dan menemukan empat baris punya catatan tindakan yang selesai dan waktunya cocok, sementara satu baris tagihan tindakan tidak punya catatan pendukung sama sekali, padahal berkasnya lengkap. Aturan integritas menyala, menghasilkan alasan berkode dengan rujukan ke baris tagihan tersebut, jenis bukti yang diharapkan, dan daftar sumber daya yang sudah dicari. Pita prioritas naik ke konflik deterministik. Kasus masuk antrean di urutan atas dengan kalimat yang terbaca petugas: baris tindakan ini tidak punya catatan tindakan yang selesai.

### 10.2 Skenario Edge Case — Tindak Lanjut Sah Terlihat seperti Tagihan Berulang

Dua klaim untuk peserta dan fasilitas yang sama muncul berdekatan waktu dengan beberapa baris yang serupa. Aturan tagihan berulang menyala dan menyajikan pasangan kandidat. Namun modul juga menemukan bukti tandingan: rentang kunjungan keduanya tidak bertumpang tindih, dan ada catatan yang menunjukkan hubungan tindak lanjut yang terdokumentasi. Bukti tandingan ini ikut ditampilkan pada kartu alasan yang sama. Petugas melihat keduanya berdampingan, dan memilih menolak sinyal dengan alasan tindak lanjut yang sah — keputusan itu tercatat permanen.

### 10.3 Skenario — Tidak Ada Detektor Menyala

Sebuah bundel bersih masuk. Seluruh baris tagihan punya bukti pendukung yang konsisten, tidak ada tumpang tindih dengan klaim lain, dokumentasinya bervariasi, dan episodenya utuh. Modul membuat kasus dengan status "tidak ada risiko teramati" dan menempatkannya di pita netral. Antarmuka **tidak** menampilkan label "bersih", "aman", atau tanda centang hijau — hanya keterangan bahwa tidak ada detektor terpilih yang menyala pada versi mesin ini. Perbedaan ini kecil di layar, tetapi menentukan secara etis.

---

## 11. Referensi Implementasi

Desain detektor per mode, keluarga bahan pertimbangan, rumus penggabungan prioritas, dan pagar pengamannya ada di `docs/canonical/05_model_card.md`. Hubungan bukti kanonik dan kontrak antarmuka ada di `docs/canonical/03_architecture.md`. Keputusan mengecualikan LLM dari jalur skor ada di `docs/canonical/decisions/ADR-0002-no-llm-in-risk-score.md`.

---

*Bagian dari Dokumentasi Implementasi TilikKlaim · Versi 1.0.0 · 2026-08-30*
