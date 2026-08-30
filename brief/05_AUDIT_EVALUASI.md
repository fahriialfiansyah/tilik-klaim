# Modul Audit & Evaluasi

> **Kode modul:** `05_AUDIT_EVALUASI` · **Prioritas:** Sedang · **Gate:** G6 (12 September)

## 1. Gambaran Umum

Modul ini menjawab dua pertanyaan yang berbeda tetapi sama-sama tentang pertanggungjawaban.

Pertanyaan pertama: **apa yang sudah terjadi pada satu kasus?** Riwayat audit menampilkan setiap kejadian secara berurutan — siapa melakukan apa, kapan, dengan alasan apa, atas dasar bukti mana, dan pada versi aturan berapa. Riwayat ini hanya bisa ditambah; koreksi dilakukan dengan menambah kejadian baru yang menggantikan, tidak pernah dengan menimpa yang lama.

Pertanyaan kedua: **seberapa baik sistem ini sebenarnya bekerja?** Halaman evaluasi menampilkan perbandingan terukur antara pendekatan aturan-saja dan pendekatan hibrida, dipecah per mode risiko, berikut tingkat positif palsu, waktu pemrosesan, versi data dan model, serta — bagian yang tidak boleh hilang — **kartu keterbatasan** yang menyatakan dengan jelas apa yang tidak dibuktikan oleh angka-angka tersebut.

Modul ini punya nilai strategis melebihi fungsinya. Ia adalah **bukti tata kelola yang dapat dilihat juri**: bahwa keputusan dicatat, bahwa kinerja diukur terhadap baseline yang adil, dan bahwa tim mengetahui persis batas klaimnya sendiri.

### 1.1 Tujuan Modul

| Tujuan | Deskripsi |
|--------|-----------|
| Menjadikan keputusan dapat dipertanggungjawabkan | Setiap disposisi punya jejak lengkap yang tidak bisa diubah diam-diam. |
| Membuktikan kerumitan membayar dirinya | Lapisan statistik dibandingkan terbuka dengan aturan-saja; bila tidak menambah nilai, ia dibuang. |
| Menyediakan angka yang bisa dikutip proposal | Metrik lahir dari artefak yang dihasilkan mesin, bukan diketik ulang manusia. |
| Menyatakan keterbatasan secara terbuka | Kartu keterbatasan menempel pada angka, bukan disembunyikan di lampiran. |
| Menjaga hasil dapat dibangun ulang | Satu perintah membangun ulang seluruh artefak dari lingkungan bersih. |

### 1.2 Target Pengguna

| Pengguna | Kebutuhan |
|----------|-----------|
| Peninjau senior | Menelaah kembali keputusan yang sudah dibuat berikut dasar dan versinya. |
| Anggota tim teknis | Melihat apakah lapisan statistik benar-benar menambah nilai terukur. |
| Anggota tim proposal | Mengambil angka dan grafik yang boleh dikutip, berikut kalimat keterbatasannya. |
| Juri | Melihat bukti bahwa sistem ini diukur, bukan sekadar didemokan. |

---

## 2. Fitur Utama

### 2.1 Riwayat Audit Kasus

**Deskripsi**: Tab di dalam layar Detail Kasus. Menampilkan seluruh kejadian pada satu kasus secara berurutan waktu.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Linimasa kejadian | Diagram waktu vertikal | Setiap kejadian pada kasus, terurut dari awal | Saat dimuat |
| Rincian kejadian | Kartu per kejadian | Pelaku, tindakan, alasan, waktu, rujukan bukti, versi aturan dan model | Saat dimuat |
| Penanda kejadian pengganti | Sorotan visual | Menandai kejadian yang menggantikan kejadian sebelumnya, keduanya tetap tampil | Saat dimuat |
| Perubahan status | Label transisi | Status sebelum dan sesudah tiap kejadian | Saat dimuat |

**Interaksi**:

- Riwayat hanya bisa dibaca. **Tidak ada** tombol sunting atau hapus — bukan karena disembunyikan, melainkan karena kemampuan itu memang tidak ada.
- Menekan satu kejadian membuka rincian penuh berikut rujukan buktinya.
- Ketika ada kejadian pengganti, **keduanya tetap terlihat** dengan penanda hubungan yang jelas.

### 2.2 Halaman Evaluasi

**Deskripsi**: Satu halaman kecil berisi bukti kinerja terukur. Sengaja tidak dibuat besar — ini bukan pusat analitik.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Penanda versi | Kartu ringkasan | Versi kumpulan data, generator, model, aturan, dan sidik data | Per jalannya evaluasi |
| Badge data sintetik | Indikator status menonjol | Penanda bahwa seluruh angka berasal dari data buatan | Selalu tampil |
| Tabel perbandingan baseline | Tabel daftar | Empat pendekatan: acak, aturan-saja, statistik-saja, hibrida | Per jalannya evaluasi |
| Metrik per mode | Tabel daftar | Ketepatan, keterpanggilan, dan F1 untuk masing-masing dari empat mode | Per jalannya evaluasi |
| Grafik positif palsu | Grafik batang | Positif palsu per 100 klaim bersih | Per jalannya evaluasi |
| Grafik ketepatan pada kapasitas review | Grafik garis | Ketepatan pada berbagai besaran kapasitas review | Per jalannya evaluasi |
| Waktu pemrosesan | Kartu ringkasan | Waktu tengah dan waktu persentil atas untuk penyaringan | Per jalannya evaluasi |
| Kartu keterbatasan | Kotak catatan menonjol | Apa yang **tidak** dibuktikan angka-angka ini | Statis |

**Interaksi**:

- Halaman ini **hanya menampilkan**; tidak ada penyetelan ambang batas, tidak ada eksperimen langsung.
- Nilai pada grafik dan nilai pada tabel berasal dari sumber yang sama. Grafik yang tidak cocok dengan tabelnya adalah cacat serius, bukan perbedaan pembulatan.
- Kartu keterbatasan disusun agar bisa disalin langsung ke proposal tanpa penyuntingan.

### 2.3 Kartu Keterbatasan

**Deskripsi**: Bagian yang paling mudah dipangkas saat waktu menipis, dan justru paling menentukan kredibilitas.

**Isi yang wajib ada**:

| Yang dibuktikan | Yang tidak dibuktikan |
|-----------------|----------------------|
| Perangkat lunak membaca subset skema yang dipilih dengan benar | Kesesuaian dengan sistem BPJS, E-Klaim, atau SATUSEHAT di lingkungan nyata |
| Detektor menemukan kembali pola yang sengaja disuntikkan | Ketepatan atau prevalensi fraud JKN di dunia nyata |
| Peringkat hibrida dapat mengungguli baseline pada kasus terkendali | Penghematan nasional atau dampak sebab-akibat |
| Rujukan bukti dan kejadian audit dapat dibangun ulang | Validitas klinis atau temuan hukum |
| Waktu pemrosesan dan alur kerja dapat diukur | Skala pada beban produksi nasional |

**Kalimat yang wajib tercantum**: kumpulan data ini bersifat sintetik dan tidak mewakili prevalensi JKN maupun perilaku fasilitas kesehatan yang sebenarnya.

**Interaksi**: Kartu ini tampil di halaman evaluasi dan tersedia dalam bentuk yang bisa disalin. Ia bukan lampiran.

---

## 3. Navigasi & Interaksi

### 3.1 Peta Navigasi

| Dari Layar / Komponen | User Klik / Aksi | Menuju Ke | Context yang Dibawa |
|----------------------|------------------|-----------|---------------------|
| Detail Kasus — tab Audit | Menekan tab | Riwayat audit kasus itu | Pengenal kasus |
| Riwayat audit — kartu kejadian | Menekan kartu | Rincian kejadian terbuka | Pengenal kejadian, rujukan bukti |
| Riwayat audit — rujukan bukti | Menekan rujukan | Panel sumber asli terbuka | Pengenal sumber daya |
| Antrean — penanda versi | Menekan penanda | Halaman Evaluasi, bagian versi | Versi mesin dan data aktif |
| Evaluasi — baris metrik | Menekan baris | Rincian metrik per mode terbuka | Mode risiko yang dipilih |

### 3.2 Decision Branch

- **Bila belum pernah ada evaluasi dijalankan**: halaman menampilkan keterangan bahwa belum ada hasil, berikut perintah persis yang harus dijalankan. Bukan angka nol yang menyesatkan.
- **Bila lapisan statistik tidak menambah nilai terukur**: halaman menampilkan hasil itu apa adanya, dan sistem dikirim sebagai aturan-saja. Ini hasil yang sah, bukan kegagalan.
- **Bila kasus baru dibuat dan belum ada disposisi**: riwayat audit hanya berisi kejadian pembuatan dan penyaringan. Riwayat tidak pernah kosong sama sekali.

### 3.3 Navigasi Masuk dari Modul Lain

- Dari modul `04`, lewat tab Audit di dalam layar Detail Kasus.
- Dari modul `03`, lewat penanda versi di deretan metrik.

---

## 4. Alur Bisnis

### 4.1 Alur Penelaahan Riwayat (Happy Path)

```
┌──────────────────┐     ┌────────────────────────┐
│ Peninjau senior  │────▶│ Buka kasus dari        │
│                  │     │ antrean                │
└──────────────────┘     └───────────┬────────────┘
                                     │
                                     ▼
                         ┌────────────────────────┐
                         │ Pindah ke tab Audit    │
                         └───────────┬────────────┘
                                     │
                                     ▼
                         ┌────────────────────────┐
                         │ Baca linimasa kejadian │
                         │ dari awal              │
                         └───────────┬────────────┘
                                     │
                                     ▼
                         ┌────────────────────────┐
                         │ Buka satu kejadian →   │
                         │ pelaku, alasan, bukti, │
                         │ versi aturan           │
                         └───────────┬────────────┘
                                     │
                                     ▼
                         ┌────────────────────────┐
                         │ Telusuri rujukan bukti │
                         │ sampai sumber aslinya  │
                         └────────────────────────┘
```

**Penjelasan singkat:** Peninjau dapat merekonstruksi mengapa sebuah keputusan diambil, berdasarkan apa yang terlihat oleh petugas **pada saat itu** — bukan berdasarkan versi aturan yang berlaku hari ini.

### 4.2 Alur Menjalankan Evaluasi

1. Kumpulan data, model, dan pembagian data dibekukan.
2. Satu perintah dijalankan dari lingkungan bersih.
3. Sistem menghasilkan berkas metrik yang terbaca mesin, tabel, dan grafik — semuanya dari sumber nilai yang sama.
4. Manifes jalannya evaluasi mencatat sidik data, versi generator, versi model, ambang batas, dan sidik lingkungan.
5. Halaman evaluasi membaca artefak tersebut. **Tidak ada** angka yang diketik manual di antarmuka.
6. Menjalankan ulang dari lingkungan bersih harus menghasilkan sidik artefak yang sama.

### 4.3 Alur Edge Case — Koreksi atas Disposisi yang Sudah Tercatat

```
┌────────────────────────────────────────────┐
│ Disposisi sudah tercatat, kemudian         │
│ diketahui keliru                           │
└──────────────────┬─────────────────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ Peninjau berwenang buka  │
        │ kembali kasus            │
        └──────────┬───────────────┘
                   │
                   ▼
        ┌──────────────────────────┐
        │ Buat disposisi BARU      │
        │ + alasan koreksi         │
        └──────────┬───────────────┘
                   │
                   ▼
┌───────────────────────────────────────────────────────┐
│ Kejadian lama TETAP ADA di riwayat.                   │
│ Kejadian baru ditandai sebagai PENGGANTI.             │
│ Keduanya tampil berurutan, hubungannya jelas.         │
│ TIDAK ADA penimpaan. TIDAK ADA penghapusan.           │
└───────────────────────────────────────────────────────┘
```

**Penjelasan:** Riwayat yang bisa disunting bukan riwayat. Kemampuan menyunting tidak disembunyikan di balik peran tertentu — kemampuan itu memang tidak dibangun.

### 4.4 Alur Edge Case — Evaluasi Menunjukkan Hibrida Tidak Menambah Nilai

1. Evaluasi dijalankan pada kumpulan uji yang dibekukan.
2. Hasilnya: hibrida tidak lebih baik daripada aturan-saja pada ketepatan di kapasitas review, keterpanggilan, maupun pengendalian positif palsu.
3. Halaman evaluasi **menampilkan hasil itu apa adanya**.
4. Tim membuang lapisan statistik dan mengirim sistem sebagai aturan-saja.
5. Proposal melaporkan keputusan ini sebagai bukti disiplin metodologis.

> Ini bukan pembatalan produk. Kriteria pembatalan di `docs/canonical/01_product_decision.md` menyatakan hal ini secara eksplisit: pertahankan TilikKlaim, buang lapisan pembelajarannya.

---

## 5. Data yang Dikelola Modul

### 5.1 Entity Bisnis Utama

**Kejadian Audit**

| Informasi | Deskripsi |
|-----------|-----------|
| Pengenal kejadian | Penanda unik, hanya bisa ditambah |
| Kaitan ke kasus | Kasus yang bersangkutan |
| Jenis kejadian | Pembuatan / penyaringan / disposisi / penyaringan ulang / penggantian |
| Pelaku | Peran yang melakukan |
| Waktu | Cap waktu |
| Muatan | Rincian sesuai jenis kejadian |
| Rujukan bukti | Bukti yang menjadi dasar |
| Versi aturan dan model | Versi yang berlaku saat kejadian |
| Kaitan ke kejadian yang digantikan | Diisi hanya pada kejadian pengganti |

**Jalannya Evaluasi**

| Informasi | Deskripsi |
|-----------|-----------|
| Pengenal jalannya evaluasi | Penanda unik |
| Sidik kumpulan data | Penanda kumpulan data yang dipakai |
| Versi generator dan adapter | Versi pembuat data |
| Manifes pembagian data | Pembagian latih, validasi, dan uji |
| Versi bahan pertimbangan, aturan, dan model | Versi seluruh komponen |
| Logika ambang batas | Cara ambang dipilih |
| Sidik commit kode | Penanda kode yang menghasilkan |
| Sidik lingkungan | Penanda lingkungan eksekusi |
| Sidik artefak hasil | Penanda berkas keluaran |
| Metrik | Nilai terbaca mesin per baseline dan per mode |

### 5.2 Catatan untuk Tim Downstream

- Kejadian audit **hanya bisa ditambah**. Larangan ini ditegakkan di tingkat penyimpanan, bukan hanya di antarmuka.
- Riwayat audit hanya dapat dibaca peran yang berwenang.
- Halaman evaluasi membaca artefak yang sudah jadi. **Dilarang** menghitung metrik secara langsung di antarmuka — nilai di layar dan nilai di berkas artefak wajib identik.
- Lima kasus contoh demo **tidak boleh** ikut dalam perhitungan metrik apa pun. Harus ada pengujian yang membuktikan pemisahan ini.

---

## 6. Kebutuhan Data Eksternal

**Tidak ada.**

---

## 7. Stack Agent Modul

**Tidak ada agent.** Evaluasi berjalan sebagai proses luring yang dijalankan manusia lewat satu perintah, menghasilkan artefak berversi. Tidak ada penyetelan otomatis, tidak ada pembelajaran berkelanjutan, tidak ada penyesuaian ambang batas dari umpan balik disposisi.

Umpan balik disposisi dicatat untuk **kualitas label di masa depan** — bukan untuk mengubah ambang batas secara otomatis. Perubahan aturan atau model wajib melalui validasi ulang, bukan terjadi diam-diam.

---

## 8. Konfigurasi Alert

Modul ini tidak mengirim notifikasi keluar.

| Kondisi | Tampilan |
|---------|----------|
| Belum ada evaluasi dijalankan | Keterangan jelas berikut perintah yang harus dijalankan — bukan angka nol |
| Nilai grafik tidak cocok dengan tabel | Ditandai sebagai cacat integritas artefak |
| Kasus contoh demo terdeteksi masuk kumpulan evaluasi | Ditandai sebagai cacat pemisahan data |
| Riwayat audit tidak dapat dibaca | Galat jujur; **tidak pernah** menampilkan riwayat kosong yang menyesatkan |

---

## 9. Standar Layanan yang Diharapkan

### 9.1 Kecepatan Tampil Data

Sedang. Halaman evaluasi jarang dibuka dan membaca artefak yang sudah jadi; kecepatannya bukan jalur kritis.

### 9.2 Frekuensi Pembaruan Data

Riwayat audit: langsung setiap kali kejadian tercatat. Halaman evaluasi: hanya berubah ketika evaluasi dijalankan ulang secara sengaja.

### 9.3 Ketersediaan Layanan

Berfungsi penuh tanpa jaringan eksternal. Artefak evaluasi tersimpan lokal.

### 9.4 Standar Tata Kelola

- Riwayat audit hanya bisa ditambah, ditegakkan di tingkat penyimpanan.
- Akses riwayat dibatasi peran berwenang.
- Setiap angka yang dikutip proposal wajib dapat ditelusuri ke artefak yang dihasilkan mesin.
- Kartu keterbatasan wajib menyertai setiap penyajian metrik — tanpa kecuali, termasuk saat waktu menipis.

---

## 10. Use Case Scenarios

### 10.1 Skenario Happy Path — Menelaah Keputusan Kemarin

Peninjau senior membuka kasus yang kemarin dikonfirmasi sebagai anomali oleh seorang petugas. Tab Audit menampilkan empat kejadian berurutan: kasus dibuat, kasus disaring pada versi aturan tertentu, petugas mengambil kasus, petugas mengonfirmasi anomali dengan alasan dan rujukan bukti yang tercatat. Peninjau membuka kejadian terakhir dan menelusuri rujukan buktinya sampai ke sumber daya asli. Ia dapat menilai kembali keputusan itu berdasarkan apa yang terlihat oleh petugas saat itu — bukan berdasarkan versi aturan yang berlaku hari ini.

### 10.2 Skenario Edge Case — Koreksi Disposisi

Sebuah kasus ternyata ditolak sinyalnya secara keliru; belakangan diketahui buktinya sebenarnya ada tetapi tercatat di kunjungan lain. Peninjau berwenang membuka kembali kasus tersebut dan membuat disposisi baru disertai alasan koreksi. Riwayat kini memuat lima kejadian: kejadian penolakan yang lama **tetap ada**, ditandai telah digantikan, dan kejadian baru menyusul di bawahnya. Tidak ada yang hilang. Siapa pun yang membaca riwayat ini di kemudian hari dapat melihat bahwa koreksi terjadi, kapan, oleh siapa, dan atas dasar apa.

### 10.3 Skenario — Juri Memeriksa Bukti Kinerja

Seorang juri bertanya apakah lapisan statistik benar-benar diperlukan. Tim membuka halaman evaluasi. Di sana tampak empat baris baseline dengan metrik masing-masing, pecahan per mode risiko, grafik positif palsu per 100 klaim bersih, dan penanda versi data serta model. Di bawahnya, kartu keterbatasan menyatakan terbuka bahwa angka-angka ini membuktikan perangkat lunaknya menemukan kembali pola yang disuntikkan — dan **tidak** membuktikan ketepatan di dunia nyata. Jawaban ini lebih kuat daripada klaim akurasi tinggi tanpa konteks, karena ia dapat diperiksa.

---

## 11. Referensi Implementasi

Baseline, metrik utama, protokol eksperimen, dan daftar artefak bukti yang wajib ada di `docs/canonical/06_evaluation_plan.md`. Kontrol tata kelola dan akuntabilitas manusia ada di `docs/canonical/07_privacy_threat_model.md`. Pemetaan setiap artefak ke slide proposal ada di `docs/canonical/09_proposal_evidence_map.md`.

---

*Bagian dari Dokumentasi Implementasi TilikKlaim · Versi 1.0.0 · 2026-08-30*
