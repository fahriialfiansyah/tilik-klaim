# Modul Data Sintetik

> **Kode modul:** `06_DATA_SINTETIK` · **Prioritas:** Tinggi · **Gate:** G3 (2 September) — **jalur kritis**

## 1. Gambaran Umum

Modul ini adalah **fondasi seluruh sistem**, dan sekaligus bagian yang paling sering diremehkan. Ia tidak punya antarmuka pengguna dan tidak akan terlihat di demo — tetapi tanpa modul ini, modul deteksi tidak punya bahan uji, modul evaluasi tidak punya bahan ukur, dan seluruh klaim kinerja dalam proposal kehilangan dasarnya.

Fungsinya: menghasilkan berkas klaim dan rekam medis buatan yang **saling terhubung secara konsisten**, dalam jumlah yang cukup untuk pengukuran statistik, dengan **pola risiko yang sengaja disuntikkan dan diberi label** — sehingga hasil deteksi bisa dinilai benar atau salah secara objektif.

Ada satu sifat yang menentukan segalanya di sini: **reproducibility**. Benih acak yang sama harus menghasilkan data yang persis sama, dengan sidik digital yang sama. Tanpa itu, hasil evaluasi tidak bisa dibangun ulang, dan angka apa pun yang masuk proposal tidak bisa dipertahankan bila ditanya juri.

Kejujuran tentang batas modul ini juga menentukan. Data yang dihasilkan **tidak mewakili JKN**. Sumbernya bermodel Amerika Serikat; distribusi penyakit, alur layanan, dan asumsi penagihannya berbeda. Adapter menyamarkan bentuknya agar menyerupai standar Indonesia — ia **tidak** membuatnya menjadi representatif. Setiap penyajian angka wajib menyertakan batas ini.

### 1.1 Tujuan Modul

| Tujuan | Deskripsi |
|--------|-----------|
| Menyediakan data terhubung tanpa data nyata | Rekam klinis dan tagihan yang konsisten satu sama lain, tanpa satu pun data peserta JKN sungguhan. |
| Menjadikan hasil dapat dibangun ulang | Benih acak yang sama menghasilkan data dan sidik digital yang sama, setiap kali. |
| Menyediakan kebenaran dasar untuk pengukuran | Pola risiko disuntikkan dengan label, sehingga deteksi bisa dinilai benar atau salah. |
| Mencegah kebocoran yang memalsukan hasil | Jejak penyuntik dibuang dari bahan pertimbangan; hasil yang terlalu bagus adalah tanda bahaya. |
| Menyediakan kasus demo yang andal | Lima berkas terkurasi, terpisah dari data pengukuran. |
| Menyatakan keterbatasan secara terbuka | Kartu data mencantumkan bias dan batasnya sebagai bagian dari keluaran, bukan lampiran. |

### 1.2 Target Pengguna

| Pengguna | Kebutuhan |
|----------|-----------|
| Anggota tim teknis | Menghasilkan ulang kumpulan data yang persis sama untuk menguji perubahan aturan. |
| Anggota tim produk/data | Menyusun kasus demo terkurasi yang menunjukkan tiap mode risiko dengan jelas. |
| Anggota tim proposal | Menjelaskan asal data ke juri tanpa mengklaim representativitas yang tidak ada. |

---

## 2. Fitur Utama

### 2.1 Pembuatan Rekam Klinis Dasar

**Deskripsi**: Menghasilkan rekam klinis buatan yang saling terhubung — peserta, kunjungan, kondisi, tindakan, obat, pemeriksaan, dan dokumen — memakai pembangkit rekam sintetik berlisensi terbuka (Synthea, Apache 2.0).

**Keluaran yang dihasilkan**:

| Keluaran | Isi |
|----------|-----|
| Rekam klinis dasar | Peserta, kunjungan, kondisi, tindakan, obat, pemeriksaan, dokumen |
| Manifes pembuatan | Benih acak, versi pembangkit, jumlah per jenis sumber daya |

**Sifat yang wajib dipenuhi**:

- Benih acak yang sama → keluaran yang sama, dengan sidik digital yang sama.
- Seluruh rujukan antar sumber daya dapat diselesaikan; tidak ada rujukan menggantung.
- Urutan waktu masuk akal: tindakan tidak mendahului kunjungannya.

### 2.2 Adapter ke Bentuk Menyerupai Standar Indonesia

**Deskripsi**: Mengubah rekam klinis dasar menjadi bentuk yang menyerupai standar interoperabilitas kesehatan Indonesia, dan menambahkan lapisan penagihan yang konsisten.

**Yang dikerjakan adapter**:

| Langkah | Penjelasan |
|---------|------------|
| Penyamaran ulang pengenal | Seluruh pengenal disamarkan ulang ke ruang nama demo |
| Pemilihan subset sumber daya | Hanya jenis sumber daya yang terdokumentasi yang dipertahankan |
| Pembangunan lapisan penagihan | Akun, item biaya, faktur, dan klaim yang saling terhubung |
| Penetapan nominal | Nominal rupiah yang konsisten secara internal dan bersifat ilustratif |
| Penulisan manifes | Versi adapter, aturan pemetaan, jumlah keluaran |

**Sifat yang wajib dipenuhi**:

- Total klaim sama dengan jumlah nominal barisnya, dalam batas toleransi pembulatan.
- Setiap tindakan yang ditagihkan punya catatan tindakan yang selesai, dengan kunjungan dan waktu yang cocok — ini keadaan **bersih** sebelum penyuntikan.
- Setiap klaim termasuk dalam satu episode, kecuali ada hubungan tindak lanjut yang terdokumentasi.
- Narasi dan urutan layanan bervariasi antar kunjungan — agar deteksi salinan punya dasar pembanding yang wajar.

### 2.3 Penyuntikan Pola Risiko Berlabel

**Deskripsi**: Setelah episode bersih terbentuk, pola risiko disuntikkan secara terkendali dan diberi label kebenaran dasar.

| Pola yang disuntikkan | Perubahan yang dilakukan | Bukti yang seharusnya terlihat |
|----------------------|--------------------------|-------------------------------|
| Tagihan tanpa bukti tindakan | Menambah baris tagihan tindakan atau obat tanpa catatan pendukung yang selesai; atau menandai buktinya sebagai keliru-input | Baris tak didukung, rujukan pendukung absen atau tidak sah, jenis bukti yang diharapkan |
| Tagihan berulang | Membuat klaim kedua untuk peserta/fasilitas/episode yang sama dengan tumpang tindih baris; pengenal diubah, beberapa bidang kecil diubah | Pasangan kandidat, rentang tumpang tindih, baris dan nominal yang cocok, bidang yang berbeda |
| Dokumentasi salinan | Menyalin atau sedikit mengubah narasi atau urutan layanan lintas peserta atau lintas kunjungan | Nilai kemiripan, potongan yang cocok, pengenal rekam yang berbeda |
| Pemecahan episode | Memecah layanan satu episode koheren menjadi beberapa klaim berdekatan waktu | Linimasa episode, konteks yang dibagi, nominal yang terpecah, sinyal penghubung |

**Label yang wajib disimpan per penyuntikan**:

| Informasi | Deskripsi |
|-----------|-----------|
| Pengenal penyuntikan | Penanda unik |
| Jenis pola | Salah satu dari empat |
| Rekam bersih asal | Rekam sebelum diubah |
| Rekam sasaran | Rekam hasil perubahan |
| Versi penyuntik | Versi kode penyuntik |
| Benih acak | Benih yang dipakai |
| Aturan yang seharusnya dilanggar | Aturan integritas mana yang mestinya menyala |
| Rujukan bukti yang diharapkan | Sumber daya mana yang mestinya ditampilkan |
| Tingkat kesulitan | Jelas / sedang / halus |
| Status banyak-label | Apakah rekam ini kena lebih dari satu pola |
| Penanda pengecualian bahan pertimbangan | Penanda bahwa metadata ini **dilarang** masuk ke bahan deteksi |

> **Label ini adalah label kebenaran penyuntikan, bukan label fraud.** Perbedaan istilah ini wajib dijaga di kode, di dokumen, dan di proposal.

### 2.4 Pembagian Data dan Pengendalian Kebocoran

**Deskripsi**: Membagi data untuk pelatihan, validasi, dan pengujian dengan cara yang mencegah hasil evaluasi terlihat lebih baik daripada kenyataannya.

**Aturan pembagian**:

| Aturan | Alasan |
|--------|--------|
| 60% latih, 20% validasi, 20% uji | Proporsi baku |
| Dibagi berdasarkan peserta dan blok waktu fasilitas | Mencegah rekam yang berkerabat tersebar lintas bagian |
| Detektor tak-terawasi dilatih terutama pada rekam bersih | Mencegah model belajar dari pola suntikan |
| Suntikan validasi hanya untuk memilih ambang batas | Bukan untuk melatih |
| Kumpulan uji dibekukan sebelum penyetelan apa pun | Mencegah penyetelan ke kumpulan uji |
| Lima kasus demo di luar seluruh perhitungan metrik | Mencegah kasus yang sudah dipoles memengaruhi angka |

**Pengendalian kebocoran yang wajib**:

| Pengendalian | Penjelasan |
|--------------|------------|
| Buang manifes penyuntikan dari tabel bahan pertimbangan | Sumber kebocoran paling langsung |
| Buang pengenal berurutan hasil penyuntikan | Pengenal berurutan membocorkan label |
| Buang cap waktu perubahan | Cap waktu mutasi membocorkan label |
| Bangkitkan ulang pengenal dan urutan penyimpanan setelah penyuntikan | Menghapus jejak urutan |
| Uji klasifikasi sepele terhadap pengenal dan urutan | Hasil nyaris sempurna adalah **alarm kebocoran**, bukan prestasi |
| Hindari pembagian baris acak | Gunakan pembagian berkelompok dan berbasis waktu |

### 2.5 Kartu Data

**Deskripsi**: Dokumen keluaran yang menyertai setiap kumpulan data, memuat asal, lisensi, cara pembuatan, dan keterbatasannya.

**Isi yang wajib ada**: sumber dan lisensinya; versi generator dan adapter; skema; populasi; logika penyuntikan; logika pembagian; bidang yang kosong; bias yang diketahui; penggunaan yang dilarang; dan kalimat wajib — kumpulan data ini bersifat sintetik dan tidak mewakili prevalensi JKN maupun perilaku fasilitas kesehatan yang sebenarnya.

---

## 3. Navigasi & Interaksi

Modul ini **tidak memiliki antarmuka pengguna**. Ia dijalankan lewat perintah oleh tim teknis.

### 3.1 Alur Antar Modul

| Dari | Aksi | Menuju | Yang dibawa |
|------|------|--------|-------------|
| Modul `06` | Perintah pembuatan data dijalankan | Berkas bundel dan manifes tersimpan | Bundel, manifes penyuntikan, manifes pembagian |
| Berkas bundel | Dimasukkan lewat modul `01` | Modul `01_INGEST_VALIDASI` | Isi bundel |
| Lima kasus demo | Terdaftar di layar Ingest | Modul `01` | Pengenal kasus contoh |
| Manifes penyuntikan | Dibaca proses evaluasi | Modul `05_AUDIT_EVALUASI` | Label kebenaran dasar |

> **Pemisahan yang wajib dijaga**: manifes penyuntikan boleh dibaca proses evaluasi, tetapi **dilarang keras** menyentuh jalur deteksi. Pemisahan ini harus terjaga secara struktural, bukan bergantung pada kedisiplinan penulis kode.

---

## 4. Alur Bisnis

### 4.1 Alur Pembuatan Data (Happy Path)

```
┌──────────────────┐     ┌────────────────────────┐
│ Tim teknis       │────▶│ Jalankan perintah      │
│                  │     │ dengan benih acak      │
└──────────────────┘     └───────────┬────────────┘
                                     │
                                     ▼
                         ┌────────────────────────┐
                         │ Bangkitkan rekam       │
                         │ klinis dasar           │
                         └───────────┬────────────┘
                                     │
                                     ▼
                         ┌────────────────────────┐
                         │ Adapter: samarkan ID,  │
                         │ pilih subset, bangun   │
                         │ lapisan penagihan      │
                         └───────────┬────────────┘
                                     │
                                     ▼
                         ┌────────────────────────┐
                         │ Verifikasi keadaan     │
                         │ BERSIH dulu            │
                         └───────────┬────────────┘
                                     │
                                     ▼
                         ┌────────────────────────┐
                         │ Suntikkan empat pola   │
                         │ + tulis label          │
                         └───────────┬────────────┘
                                     │
                                     ▼
                         ┌────────────────────────┐
                         │ Bangkitkan ulang ID &  │
                         │ urutan penyimpanan     │
                         └───────────┬────────────┘
                                     │
                                     ▼
                         ┌────────────────────────┐
                         │ Bagi data berkelompok  │
                         │ + tulis kartu data     │
                         └────────────────────────┘
```

**Penjelasan singkat:** Urutan ini tidak boleh diubah. Keadaan bersih wajib diverifikasi **sebelum** penyuntikan — kalau data dasarnya sudah tidak konsisten, label suntikan kehilangan makna.

### 4.2 Alur Pembuatan Ulang untuk Verifikasi

1. Tim teknis menjalankan perintah yang sama dengan benih acak yang sama, di lingkungan bersih.
2. Sistem menghasilkan kumpulan data baru.
3. Sidik digital keluaran dibandingkan dengan sidik yang tersimpan.
4. Sidik **wajib identik**. Perbedaan sekecil apa pun berarti ada sumber ketidakpastian yang belum terkendali — dan itu cacat yang harus diperbaiki, bukan toleransi yang bisa diterima.

### 4.3 Alur Edge Case — Uji Kebocoran Menyala

```
┌──────────────────────────────────────────────┐
│ Latih klasifikasi sepele HANYA memakai       │
│ pengenal rekam dan urutan penyimpanan        │
└────────────────────┬─────────────────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
┌────────────────────┐  ┌────────────────────────┐
│ Kinerja setara     │  │ Kinerja nyaris         │
│ tebakan acak       │  │ SEMPURNA               │
└─────────┬──────────┘  └───────────┬────────────┘
          │                         │
          ▼                         ▼
┌────────────────────┐  ┌────────────────────────────────────┐
│ Aman — lanjutkan   │  │ ALARM KEBOCORAN.                   │
│                    │  │ • HENTIKAN evaluasi                │
│                    │  │ • Telusuri jejak penyuntik yang    │
│                    │  │   tersisa di bahan pertimbangan    │
│                    │  │ • Bangkitkan ulang, uji lagi       │
│                    │  │ • JANGAN laporkan metrik apa pun   │
│                    │  │   sebelum uji ini lolos            │
└────────────────────┘  └────────────────────────────────────┘
```

**Penjelasan:** Angka yang terlalu bagus dari data buatan sendiri hampir selalu berarti model menemukan jejak penyuntik, bukan menemukan pola risiko. Uji ini adalah pengaman terakhir sebelum tim tanpa sadar memasukkan angka palsu ke proposal.

### 4.4 Alur Edge Case — Rekam Terkena Lebih dari Satu Pola

1. Penyuntik memilih rekam sasaran yang ternyata sudah terkena pola lain.
2. Sistem mengizinkannya, **dengan syarat** rekam itu ditandai berlabel banyak.
3. Proporsi rekam berlabel banyak dibatasi dan didokumentasikan.
4. Evaluasi melaporkan hasil rekam berlabel tunggal dan berlabel banyak **secara terpisah**.

**Penjelasan:** Rekam berlabel banyak mencerminkan kenyataan, tetapi mengaburkan metrik per mode bila dicampur. Memisahkannya adalah kejujuran metodologis, bukan kerumitan yang tidak perlu.

---

## 5. Data yang Dikelola Modul

### 5.1 Skala yang Ditargetkan

| Tahap | Klaim | Peserta | Fasilitas | Kasus bersuntikan |
|-------|-------|---------|-----------|-------------------|
| Minimum Gate 3 (2 Sep) | 1.000 | ≥ 300 | 8 | 200 |
| Target evaluasi | 10.000 | ≥ 3.000 | 12–20 | 1.200 |

Sekitar 300 kasus per pola risiko, ditambah sejumlah kecil rekam berlabel banyak yang terdokumentasi.

> **Proporsi suntikan ini adalah pilihan rancangan pengujian.** Ia **tidak boleh** disebut sebagai prevalensi JKN — di kode, di dokumen, maupun di proposal.

### 5.2 Lima Kasus Demo Terkurasi

| Kasus | Isi | Dipakai untuk |
|-------|-----|---------------|
| Bersih | Seluruh baris tagihan punya bukti pendukung konsisten | Membuktikan sistem tidak menandai kasus wajar |
| Tagihan tanpa bukti | Satu baris tindakan tanpa catatan tindakan yang selesai | Kasus demo utama |
| Tagihan berulang | Dua klaim satu episode dengan tumpang tindih baris | Menunjukkan laci perbandingan |
| Dokumentasi salinan | Catatan disalin lintas kunjungan | Menunjukkan komponen kemiripan dan peringatan templat |
| Episode terpecah | Satu episode dipecah jadi klaim berdekatan | Menunjukkan linimasa episode |

Kelima kasus ini **berada di luar seluruh perhitungan metrik**. Pemisahan ini wajib diuji, bukan sekadar disepakati.

### 5.3 Catatan untuk Tim Downstream

- Nominal rupiah bersifat **ilustratif**, konsisten secara internal, dan tidak mencerminkan tarif JKN yang berlaku.
- Pembangkit rekam dasar (Synthea) berlisensi terbuka dan menghasilkan rekam sintetik — bukan rekam pasien nyata.
- Adapter **tidak pernah** boleh mengklaim data hasilnya representatif untuk Indonesia. Klaim itu salah dan mudah dibantah.
- Manifes penyuntikan disimpan terpisah dari data yang dibaca jalur deteksi, dengan pemisahan struktural.

---

## 6. Kebutuhan Data Eksternal

**Tidak ada koneksi daring.** Pembangkit rekam dasar dipasang secara lokal. Tidak ada data peserta JKN nyata dalam bentuk apa pun.

Statistik agregat publik (misalnya laporan pemantauan nasional atau data kependudukan) boleh dipakai sebagai **rentang parameter** saat menyusun demografi buatan, dan boleh dikutip untuk narasi urgensi di proposal. Statistik itu **tidak pernah** menjadi rekam data maupun data latih. Pelokalan agregat tidak membuat alur klinisnya menjadi representatif.

---

## 7. Stack Agent Modul

**Tidak ada agent.** Pembuatan data berjalan sebagai proses deterministik yang dijalankan lewat perintah. Tidak ada model generatif, tidak ada LLM, tidak ada keputusan probabilistik di luar benih acak yang tercatat.

---

## 8. Konfigurasi Alert

Modul ini tidak berjalan di lingkungan produksi. Kegagalan muncul sebagai kegagalan pengujian.

| Kondisi | Konsekuensi |
|---------|-------------|
| Sidik digital berbeda pada benih yang sama | Uji determinisme gagal — **cacat yang menghentikan pekerjaan** |
| Ada rujukan menggantung | Uji integritas rujukan gagal |
| Total klaim tidak sama dengan jumlah barisnya | Uji rekonsiliasi nominal gagal |
| Urutan waktu tidak masuk akal | Uji kronologi gagal |
| Aturan yang seharusnya dilanggar ternyata tidak menyala | Uji invarian per penyuntik gagal |
| Uji klasifikasi sepele nyaris sempurna | **Alarm kebocoran — evaluasi dihentikan** |
| Kasus demo terdeteksi di kumpulan evaluasi | Uji pemisahan data gagal |

---

## 9. Standar Layanan yang Diharapkan

### 9.1 Kecepatan

Toleran. Pembuatan data adalah proses luring; berjalan beberapa menit dapat diterima. Yang tidak dapat ditawar adalah **determinismenya**, bukan kecepatannya.

### 9.2 Frekuensi

Dijalankan sesuai kebutuhan oleh tim teknis. Tidak ada penjadwalan otomatis.

### 9.3 Ketersediaan

Sepenuhnya luring. Pembangkit rekam dasar dipasang lokal; tidak ada ketergantungan pada layanan daring mana pun.

### 9.4 Batas yang Tidak Boleh Dilanggar

- **Tidak ada** data peserta JKN nyata, dalam bentuk apa pun, dengan alasan apa pun.
- Proporsi suntikan **tidak pernah** disebut prevalensi.
- Metadata penyuntik **tidak pernah** masuk ke bahan pertimbangan deteksi.
- Kartu data **wajib** menyertai setiap kumpulan data yang dipakai untuk menghasilkan angka.

---

## 10. Use Case Scenarios

### 10.1 Skenario Happy Path — Menyiapkan Data Gate 3

Tim teknis menjalankan satu perintah dengan benih acak tetap. Beberapa menit kemudian tersedia seribu klaim yang saling terhubung, tersebar pada lebih dari tiga ratus peserta dan delapan fasilitas, dengan dua ratus kasus yang disuntikkan pola risiko berikut labelnya. Manifes mencatat benih, versi adapter, jenis penyuntikan, dan bukti yang diharapkan. Seluruh uji lolos: determinisme, integritas rujukan, rekonsiliasi nominal, kronologi, dan invarian per penyuntik. Kartu data diperbarui. Gate 3 terpenuhi.

### 10.2 Skenario Edge Case — Determinisme Gagal

Seorang anggota tim menjalankan ulang perintah dengan benih yang sama di mesin berbeda, dan mendapat sidik digital yang berbeda. Penelusuran menemukan penyebabnya: urutan iterasi pada satu bagian kode tidak terjamin stabil. Ini **bukan** ketidakcocokan kecil yang bisa diabaikan — tanpa determinisme, hasil evaluasi tidak dapat dibangun ulang dan tidak ada angka yang boleh dikutip proposal. Pekerjaan berhenti sampai penyebabnya diperbaiki dan sidik digital kembali identik.

### 10.3 Skenario — Alarm Kebocoran Sebelum Evaluasi

Menjelang penyusunan laporan evaluasi, tim menjalankan uji kebocoran: melatih klasifikasi sepele yang **hanya** memakai pengenal rekam dan urutan penyimpanan. Hasilnya nyaris sempurna. Ini alarm. Penelusuran menemukan cap waktu perubahan masih tertinggal di tabel bahan pertimbangan. Tim membuang kolom itu, membangkitkan ulang pengenal dan urutan, lalu mengulang uji — kali ini kinerjanya setara tebakan acak. Evaluasi baru dilanjutkan setelah itu. Bila uji ini dilewati, tim akan melaporkan angka yang mengesankan tetapi palsu, dan pertanyaan pertama dari juri yang teliti akan meruntuhkannya.

---

## 11. Referensi Implementasi

Skema minimum, rencana data sintetik, aturan pembagian, pengendalian kebocoran, dan kriteria penerimaan kartu data ada di `docs/canonical/04_data_card.md`. Keluarga bahan pertimbangan yang membaca data ini ada di `docs/canonical/05_model_card.md`. Protokol eksperimen yang mengonsumsi pembagian data ini ada di `docs/canonical/06_evaluation_plan.md`.

---

*Bagian dari Dokumentasi Implementasi TilikKlaim · Versi 1.0.0 · 2026-08-30*
