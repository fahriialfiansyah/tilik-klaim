# Modul Ingest & Validasi Bundel

> **Kode modul:** `01_INGEST_VALIDASI` · **Prioritas:** Tinggi · **Gate:** G4 (5 September)

## 1. Gambaran Umum

Modul ini adalah **satu-satunya gerbang masuk** data ke TilikKlaim. Sebuah berkas klaim — berisi header klaim, baris-baris tagihan, dan sumber daya rekam medis elektronik yang menyertainya — masuk lewat sini, diperiksa bentuknya, lalu diubah menjadi bentuk kanonik yang bisa diproses modul berikutnya. Berkas yang bentuknya tidak sah ditolak di sini, dengan pesan yang memberi tahu persis apa yang salah.

Modul ini ada karena dua alasan. Pertama, **kepercayaan pada hasil deteksi bergantung pada kepastian input**: kalau bundel yang rusak diam-diam lolos, alasan risiko yang muncul di hilir tidak bisa dipertanggungjawabkan. Kedua, **reproducibility**: setiap berkas masuk menghasilkan sidik digital, sehingga penyaringan yang sama atas berkas yang sama dengan versi mesin yang sama selalu memberi hasil identik. Ini yang memungkinkan hasil demo dan hasil evaluasi bisa dibangun ulang kapan saja.

### 1.1 Tujuan Modul

| Tujuan | Deskripsi |
|--------|-----------|
| Menolak lebih awal, bukan gagal di tengah | Bundel cacat berhenti di gerbang dengan pesan galat yang stabil dan bisa ditindaklanjuti — bukan menyebabkan kegagalan misterius saat penyaringan. |
| Memberi kepastian sebelum penyaringan | Petugas tahu apakah berkasnya bisa disaring sebelum menunggu proses deteksi berjalan. |
| Menjadikan hasil dapat diulang | Sidik digital atas isi berkas membuat setiap hasil penyaringan bisa dibangun ulang dan dibandingkan. |
| Menjaga batas keamanan | Berkas yang diunggah diperlakukan murni sebagai data — tidak pernah dieksekusi, tidak pernah ditafsirkan sebagai instruksi. |
| Menyediakan titik awal demo yang andal | Lima kasus contoh terkurasi selalu tersedia, sehingga demo tidak bergantung pada keberhasilan unggah manual. |

### 1.2 Target Pengguna

| Pengguna | Kebutuhan |
|----------|-----------|
| Petugas casemix / anti-fraud rumah sakit | Memasukkan satu berkas klaim dan segera tahu apakah berkas itu layak disaring atau perlu diperbaiki dulu. |
| Anggota tim saat demo | Memilih satu kasus contoh terkurasi dan menjalankan penyaringan tanpa risiko kegagalan unggah di depan juri. |
| Penguji internal | Mengirim berkas yang sengaja dirusak dan memastikan sistem menolaknya dengan cara yang sama setiap kali. |

---

## 2. Fitur Utama

### 2.1 Pemasukan Bundel

**Deskripsi**: Pengguna memasukkan satu berkas klaim, baik dengan mengunggah berkas sendiri maupun memilih dari daftar kasus contoh yang sudah disiapkan.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Area unggah berkas | Zona seret-dan-lepas dengan tombol pilih berkas | Satu berkas data terstruktur; batas ukuran dan tipe ditampilkan sebelum unggah | Manual |
| Daftar kasus contoh | Tabel daftar ringkas | Lima kasus terkurasi: satu bersih, satu tagihan tanpa bukti, satu tagihan berulang, satu dokumentasi salinan, satu episode terpecah | Statis |
| Badge data sintetik | Indikator status warna | Penanda permanen bahwa seluruh data di sistem adalah data buatan | Statis, selalu tampil |
| Batas dan aturan berkas | Teks bantuan ringkas | Ukuran maksimum, tipe yang diterima, kedalaman struktur maksimum | Statis |

**Interaksi**:

- Pengguna menyeret berkas ke area unggah, atau menekan tombol untuk memilih dari perangkat.
- Pengguna memilih salah satu dari lima kasus contoh; pilihan langsung memuat berkas itu tanpa unggah.
- Pengguna melihat batas ukuran dan tipe **sebelum** mencoba unggah, bukan setelah gagal.
- Berkas yang melewati batas ditolak segera di sisi antarmuka, sebelum dikirim.

### 2.2 Laporan Hasil Validasi

**Deskripsi**: Setelah berkas masuk, sistem menampilkan hasil pemeriksaan bentuk — berapa banyak sumber daya yang terbaca, mana yang bermasalah, dan apakah berkas ini layak disaring.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Status validasi | Indikator status warna | Tiga kemungkinan: sah, sah dengan catatan, tidak sah | Setelah pemasukan |
| Ringkasan jumlah sumber daya | Kartu ringkasan | Cacah per jenis sumber daya yang terbaca: klaim, baris tagihan, kunjungan, tindakan, obat, pemeriksaan, dokumen | Setelah pemasukan |
| Daftar galat dan peringatan | Tabel daftar | Kode galat, jenis sumber daya, pengenal sumber daya, penjelasan singkat | Setelah pemasukan |
| Sidik digital berkas | Teks pendek yang bisa disalin | Sidik isi berkas — penanda bahwa hasil bisa dibangun ulang | Setelah pemasukan |
| Tombol saring klaim | Tombol aksi tunggal | Aktif hanya bila status sah; nonaktif dengan alasan bila tidak | Setelah pemasukan |

**Interaksi**:

- Pengguna membaca status validasi lebih dulu, sebelum daftar galat — status menentukan apakah perlu membaca detail sama sekali.
- Pengguna membuka satu baris galat untuk melihat sumber daya mana yang bermasalah.
- Pengguna menyalin sidik digital berkas untuk dicocokkan dengan hasil penyaringan nanti.
- Pengguna menekan satu tombol untuk menjalankan penyaringan. **Tidak ada wisaya konfigurasi** — tidak ada langkah pilih-detektor, pilih-ambang, atau pilih-mode.
- Bila berkas tidak sah, pengguna diarahkan untuk memperbaiki dan mengirim ulang; sistem tidak menawarkan "saring saja sebagian".

---

## 3. Navigasi & Interaksi

### 3.1 Peta Navigasi

| Dari Layar / Komponen | User Klik / Aksi | Menuju Ke | Context yang Dibawa |
|----------------------|------------------|-----------|---------------------|
| Ingest — area unggah | Melepas berkas / memilih berkas | Tetap di layar Ingest, bagian laporan validasi terisi | Isi berkas, sidik digital, hasil pemeriksaan |
| Ingest — daftar kasus contoh | Menekan satu baris kasus | Tetap di layar Ingest, laporan validasi terisi | Pengenal kasus contoh, label skenario (khusus demo) |
| Ingest — laporan validasi | Menekan "Saring klaim" | Layar Detail Kasus modul `04` | Pengenal pemasukan, pengenal kasus hasil penyaringan |
| Ingest — laporan validasi | Menekan "Kembali ke antrean" | Layar Antrean Review modul `03` | Tanpa konteks tambahan |
| Ingest — baris galat | Menekan satu baris galat | Panel detail galat terbuka di tempat | Pengenal sumber daya bermasalah |

### 3.2 Decision Branch

- **Setelah validasi**: status sah → tombol "Saring klaim" aktif; status sah-dengan-catatan → tombol aktif, tapi catatan ditampilkan menonjol dan ikut terbawa ke kasus; status tidak sah → tombol nonaktif disertai alasan spesifik.
- **Saat pengiriman ulang berkas yang sama**: sidik digital dan versi mesin identik → sistem mengembalikan hasil penyaringan yang sudah ada, bukan membuat kasus duplikat. Pengguna diberi tahu bahwa ini hasil yang sudah pernah dibuat.
- **Label skenario pada kasus contoh**: hanya dipakai untuk penamaan di layar demo. **Tidak pernah** masuk sebagai bahan pertimbangan deteksi — ini pengaman anti-kecurangan yang wajib diuji.

### 3.3 Navigasi Masuk dari Modul Lain

- Dari modul `03_ANTREAN_REVIEW`, tombol "Masukkan bundel baru" → masuk ke layar Ingest dalam keadaan kosong.
- Dari modul `04_DETAIL_KASUS_DISPOSISI`, aksi "Minta bukti tambahan" → mengarahkan ke Ingest dengan konteks kasus asal, sehingga berkas versi baru terhubung ke kasus yang sama.

---

## 4. Alur Bisnis

### 4.1 Alur Pemasukan Berhasil (Happy Path)

```
┌──────────────┐     ┌──────────────────┐     ┌───────────────────────┐
│ Petugas      │────▶│ Pilih kasus      │────▶│ Sistem baca isi       │
│ casemix      │     │ contoh / unggah  │     │ berkas                │
└──────────────┘     └──────────────────┘     └───────────┬───────────┘
                                                          │
                                                          ▼
                                              ┌───────────────────────┐
                                              │ Periksa bentuk,       │
                                              │ rujukan antar-sumber, │
                                              │ dan batas ukuran      │
                                              └───────────┬───────────┘
                                                          │
                                                          ▼
                                              ┌───────────────────────┐
                                              │ Hitung sidik digital  │
                                              │ + simpan bentuk       │
                                              │ kanonik               │
                                              └───────────┬───────────┘
                                                          │
                                                          ▼
                                              ┌───────────────────────┐
                                              │ Tampilkan status SAH  │
                                              │ + cacah sumber daya   │
                                              └───────────┬───────────┘
                                                          │
                                                          ▼
                                              ┌───────────────────────┐
                                              │ Petugas tekan         │
                                              │ "Saring klaim"        │
                                              └───────────────────────┘
```

**Penjelasan singkat:** Berkas masuk, diperiksa, disidik, disimpan, dan pengguna diberi satu tombol untuk melanjutkan. Tidak ada langkah konfigurasi di antaranya.

### 4.2 Alur Pengiriman Ulang Berkas Identik

1. Petugas memasukkan berkas yang isinya persis sama dengan yang pernah dimasukkan.
2. Sistem menghitung sidik digital dan menemukan sidik yang sama sudah ada, dengan versi mesin yang sama.
3. Sistem **tidak** membuat kasus baru. Sistem mengembalikan hasil penyaringan yang sudah ada.
4. Layar memberi tahu: berkas ini identik dengan pemasukan sebelumnya, beserta waktu dan pengenal kasusnya.
5. Petugas bisa langsung membuka kasus lama, atau membatalkan.

> Perilaku ini penting untuk demo: menekan tombol dua kali tidak menghasilkan dua kasus kembar di antrean.

### 4.3 Alur Edge Case — Berkas Cacat

```
┌──────────────┐     ┌──────────────────┐
│ Petugas      │────▶│ Unggah berkas    │
└──────────────┘     └────────┬─────────┘
                              │
                              ▼
                   ┌──────────────────────┐
                   │ Periksa bentuk       │
                   └──────────┬───────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐  ┌────────────────────┐  ┌────────────────────┐
│ Berkas rusak  │  │ Rujukan menggantung│  │ Ukuran/kedalaman   │
│ tak terbaca   │  │ (menunjuk sumber   │  │ melampaui batas    │
│               │  │  daya yang absen)  │  │                    │
└───────┬───────┘  └─────────┬──────────┘  └─────────┬──────────┘
        │                    │                       │
        ▼                    ▼                       ▼
┌────────────────────────────────────────────────────────────────┐
│ Status TIDAK SAH + kode galat stabil + daftar sumber daya      │
│ bermasalah. Tombol "Saring klaim" NONAKTIF disertai alasan.    │
│ TIDAK ADA kasus yang dibuat. TIDAK ADA penyaringan sebagian.   │
└────────────────────────────────────────────────────────────────┘
```

**Penjelasan:** Tiga jenis kegagalan yang berbeda menghasilkan tiga kode galat yang berbeda dan stabil — kode yang sama untuk kegagalan yang sama, setiap kali. Pengguna melihat sumber daya mana yang bermasalah, bukan sekadar "berkas tidak valid". Tidak ada kasus setengah jadi yang masuk ke antrean.

### 4.4 Alur Edge Case — Berkas Tidak Lengkap tapi Bentuknya Sah

1. Berkas lolos pemeriksaan bentuk, tetapi sebagian sumber daya pendukung memang tidak ada — bukan rusak, memang tidak dikirim.
2. Sistem memberi status **sah dengan catatan**, bukan tidak sah.
3. Catatan kelengkapan berkas ikut tersimpan bersama kasus.
4. Di modul `02` dan `04`, kelengkapan ini menurunkan tingkat keyakinan dan mengarahkan ke aksi "minta bukti", bukan ke "konfirmasi anomali".

**Penjelasan:** Ini pembeda yang menentukan. Rekam medis yang belum lengkap terlihat sama persis dengan tagihan tanpa bukti tindakan. Membedakan keduanya adalah kewajiban etis modul ini, bukan kehalusan opsional.

---

## 5. Data yang Dikelola Modul

### 5.1 Entity Bisnis Utama

**Pemasukan Bundel**

| Informasi | Deskripsi |
|-----------|-----------|
| Pengenal pemasukan | Penanda unik untuk satu kali pemasukan berkas |
| Sidik digital isi | Sidik atas isi berkas — dasar reproducibility dan pencegahan duplikat |
| Status validasi | Sah / sah dengan catatan / tidak sah |
| Cacah sumber daya | Jumlah per jenis sumber daya yang terbaca |
| Daftar galat | Kode galat, jenis sumber daya, pengenal, penjelasan |
| Catatan kelengkapan | Sumber daya pendukung apa saja yang tidak hadir |
| Versi skema | Versi bentuk kanonik yang berlaku saat pemasukan |
| Waktu pemasukan | Cap waktu |
| Label skenario | **Khusus demo.** Ditandai terpisah dan dilarang keras masuk ke bahan pertimbangan deteksi. |

**Berkas Mentah**

| Informasi | Deskripsi |
|-----------|-----------|
| Isi asli apa adanya | Berkas disimpan utuh, tanpa modifikasi, untuk penelusuran balik |
| Kaitan ke pemasukan | Hubungan ke pengenal pemasukan |

### 5.2 Sample Data atau Dummy Data

Lima kasus contoh terkurasi wajib tersedia sejak awal dan **terpisah dari data evaluasi**:

| Kasus contoh | Isi | Dipakai untuk |
|--------------|-----|---------------|
| Bersih | Semua baris tagihan punya bukti pendukung yang konsisten | Membuktikan sistem tidak menandai kasus wajar |
| Tagihan tanpa bukti | Satu baris tagihan tindakan tanpa catatan tindakan yang selesai | Kasus demo utama |
| Tagihan berulang | Dua klaim untuk episode yang sama dengan tumpang tindih baris | Uji perbandingan pasangan kandidat |
| Dokumentasi salinan | Catatan yang disalin lintas kunjungan berbeda | Uji kemiripan dokumen |
| Episode terpecah | Satu episode layanan dipecah jadi beberapa klaim berdekatan | Uji linimasa episode |

### 5.3 Catatan untuk Tim Downstream

- Kelima kasus contoh **tidak boleh** ikut dalam perhitungan metrik evaluasi apa pun. Ini pemisahan wajib, bukan preferensi.
- Label skenario pada kasus contoh harus disimpan di kolom yang secara struktural terpisah dari bahan pertimbangan deteksi, sehingga kebocoran tidak bisa terjadi karena kelalaian.
- Kode galat harus stabil lintas versi — layar antarmuka dan pengujian otomatis bergantung padanya.

---

## 6. Kebutuhan Data Eksternal

**Tidak ada.** Seluruh berkas berasal dari modul `06_DATA_SINTETIK` atau unggahan manual berkas sintetik. Tidak ada pemanggilan ke SATUSEHAT, BPJS, E-Klaim, maupun layanan luar mana pun.

---

## 7. Stack Agent Modul

**Tidak ada agent.** Validasi berjalan sebagai pemeriksaan deterministik atas bentuk berkas — tidak ada model, tidak ada LLM, tidak ada keputusan probabilistik di modul ini.

---

## 8. Konfigurasi Alert

Modul ini tidak mengirim notifikasi ke luar. Umpan balik seluruhnya terjadi di layar, saat itu juga.

| Kondisi | Tampilan |
|---------|----------|
| Berkas melampaui batas ukuran | Ditolak di sisi antarmuka sebelum dikirim, dengan angka batas yang jelas |
| Berkas tidak sah | Status merah, daftar galat, tombol lanjut nonaktif disertai alasan |
| Berkas sah dengan catatan | Status kuning, catatan kelengkapan ditampilkan menonjol |
| Berkas identik sudah pernah masuk | Pesan informasi disertai tautan ke kasus yang sudah ada |
| Layanan penyaringan tidak merespons | Pesan galat yang jujur berikut tombol coba lagi — bukan status memuat yang menggantung selamanya |

---

## 9. Standar Layanan yang Diharapkan

### 9.1 Kecepatan Tampil Data

Cepat. Pemeriksaan bentuk satu bundel harus selesai dalam hitungan detik. Bila lebih lama, indikator kemajuan wajib tampil — bukan layar diam.

### 9.2 Frekuensi Pembaruan Data

Manual. Tidak ada pemasukan otomatis, tidak ada penjadwalan, tidak ada aliran data masuk berkelanjutan.

### 9.3 Ketersediaan Layanan

Wajib berfungsi penuh tanpa jaringan eksternal. Kasus contoh harus dapat dimuat meski seluruh koneksi luar terputus — ini syarat keandalan demo, bukan optimasi.

### 9.4 Batas yang Tidak Boleh Dilanggar

- Berkas yang diunggah **tidak pernah** dieksekusi dan **tidak pernah** ditafsirkan sebagai instruksi bagi sistem.
- Log sistem **tidak pernah** memuat isi teks medis dari berkas.
- Label skenario **tidak pernah** memengaruhi hasil deteksi.

---

## 10. Use Case Scenarios

### 10.1 Skenario Happy Path — Persiapan Demo

Seorang anggota tim membuka layar Ingest sebelum sesi penjurian. Ia memilih kasus contoh "tagihan tanpa bukti" dari daftar. Dalam hitungan detik, layar menampilkan status sah, cacah sumber daya yang terbaca, dan sidik digital berkas. Ia menekan "Saring klaim" dan langsung dibawa ke layar Detail Kasus dengan alasan risiko sudah terbuka. Total waktu di layar ini: di bawah sepuluh detik.

### 10.2 Skenario Edge Case — Berkas Rujukan Menggantung

Seorang penguji internal sengaja menghapus satu catatan tindakan dari berkas, tetapi membiarkan baris tagihan tetap merujuk ke catatan itu. Ia mengunggah berkas tersebut. Sistem menampilkan status tidak sah dengan kode galat rujukan menggantung, menyebut pengenal sumber daya yang hilang. Tombol "Saring klaim" nonaktif. Tidak ada kasus yang masuk ke antrean. Penguji mengulang unggah berkas yang sama dan mendapat kode galat yang persis sama — perilaku yang stabil inilah yang diuji.

### 10.3 Skenario — Berkas Sah tapi Tidak Lengkap

Petugas casemix memasukkan berkas klaim yang rekam medis pendukungnya belum seluruhnya terisi. Sistem memberi status sah dengan catatan, menampilkan sumber daya pendukung apa saja yang tidak hadir, dan tetap mengaktifkan tombol penyaringan. Di layar Detail Kasus nanti, catatan kelengkapan ini muncul berdampingan dengan sinyal risiko, dan aksi yang disarankan sistem adalah "minta bukti tambahan" — bukan "konfirmasi anomali".

---

## 11. Referensi Implementasi

Kontrak antarmuka, batas keamanan, dan aturan sidik digital ada di `docs/canonical/03_architecture.md`. Skema kanonik minimum ada di `docs/canonical/04_data_card.md`. Kontrol privasi dan skenario ancaman ada di `docs/canonical/07_privacy_threat_model.md`.

---

*Bagian dari Dokumentasi Implementasi TilikKlaim · Versi 1.0.0 · 2026-08-30*
