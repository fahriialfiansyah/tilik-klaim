# Modul Detail Kasus & Disposisi

> **Kode modul:** `04_DETAIL_KASUS_DISPOSISI` · **Prioritas:** Tinggi · **Gate:** G5 (9 September)

## 1. Gambaran Umum

Di sinilah **keputusan terjadi**. Modul ini menampilkan satu kasus secara utuh — baris tagihan mana yang bermasalah, bukti apa yang seharusnya ada, bukti apa yang benar-benar ditemukan, apa yang justru melemahkan sinyal itu, dan bagaimana urutan kejadiannya di sepanjang episode layanan. Setelah memeriksa, petugas memilih satu dari empat tindakan dan **wajib menuliskan alasannya**. Keputusan itu langsung menjadi catatan permanen.

Tujuan layar ini bukan "menampilkan semua data tentang kasus". Tujuannya **memahami dan menuntaskan satu alasan**. Karena itu layar terbuka langsung pada alasan terkuat, bukan pada halaman profil umum. Grafik hubungan bukti dibuat kecil dan terarah — menampilkan jalur bukti, bukan jaring-jaring rumit yang mengesankan tetapi tidak bisa dibaca.

Empat tindakan yang tersedia sengaja dipilih agar tak satu pun bermakna vonis: **tolak sinyal**, **minta bukti tambahan**, **konfirmasi anomali**, dan **eskalasi**. Perhatikan bahwa "konfirmasi anomali" berarti petugas membenarkan adanya ketidaksesuaian — **bukan** menyatakan fraud, dan bukan pula temuan hukum.

### 1.1 Tujuan Modul

| Tujuan | Deskripsi |
|--------|-----------|
| Menuntaskan satu alasan, bukan menjelajah data | Layar terbuka pada alasan terkuat dan mengarahkan ke keputusan. |
| Menampilkan bukti dan bukti tandingan berdampingan | Hal yang melemahkan sinyal muncul di layar yang sama, bukan di tempat terpisah. |
| Mewajibkan alasan pada setiap keputusan | Tidak ada disposisi tanpa alasan tertulis. |
| Mencegah keputusan atas data usang | Perubahan yang dibuat di atas versi kasus yang sudah berubah ditolak, disertai penjelasan. |
| Menjaga bahasa tetap berhati-hati | "Konfirmasi anomali" wajib disertai penegasan bahwa ini bukan temuan fraud. |
| Menghasilkan jejak yang bisa dipertanggungjawabkan | Setiap keputusan menghasilkan catatan permanen berisi pelaku, waktu, alasan, bukti, dan versi. |

### 1.2 Target Pengguna

| Pengguna | Kebutuhan |
|----------|-----------|
| Petugas casemix / anti-fraud rumah sakit | Memahami satu sinyal sampai cukup yakin, lalu mencatat keputusan yang bisa ia pertahankan bila ditanya. |
| Peninjau senior | Menelaah kembali keputusan yang sudah dibuat berikut dasarnya. |
| Anggota tim proposal | Menangkap layar yang membuktikan bahwa keputusan akhir memang ada di tangan manusia. |

---

## 2. Fitur Utama

### 2.1 Kepala Kasus

**Deskripsi**: Bagian teratas layar — identitas kasus, status, dan empat tombol tindakan. Semuanya terlihat tanpa perlu menggulir.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Pengenal kasus pseudonim | Teks penanda | Penanda kasus tanpa identitas peserta | Saat dimuat |
| Status kasus | Indikator status warna | Posisi kasus dalam alur kerja | Saat berubah |
| Nominal klaim | Angka dengan digit sejajar | Nominal sintetik dan ilustratif | Saat dimuat |
| Rentang waktu kunjungan | Teks rentang tanggal | Awal dan akhir episode layanan | Saat dimuat |
| Alasan utama | Teks menonjol | Kalimat alasan terkuat dalam bahasa kerja | Saat dimuat |
| Dasar keyakinan | Teks pendek yang bisa dibuka | Menjawab "kenapa pita ini?" berikut komponen penyusunnya | Saat dibuka |
| Empat tombol tindakan | Deretan tombol | Tolak sinyal · Minta bukti tambahan · Konfirmasi anomali · Eskalasi | Selalu tampil |
| Badge data sintetik | Indikator status | Penanda permanen | Selalu tampil |

**Interaksi**:

- Petugas membaca alasan utama lebih dulu; skor dan pita berada di bawahnya, bukan di atasnya.
- Menekan "dasar keyakinan" membuka penjelasan komponen — bukan sekadar menampilkan angka lain.
- Keempat tombol selalu terlihat, sehingga petugas tahu sejak awal keputusan apa saja yang mungkin.

### 2.2 Daftar Baris Tagihan

**Deskripsi**: Kolom kiri. Seluruh baris tagihan dalam klaim ini berikut keadaan dukungan buktinya masing-masing.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Baris tagihan | Tabel daftar ringkas | Kode layanan, keterangan, jumlah, nominal, waktu layanan | Saat dimuat |
| Keadaan dukungan | Indikator status warna per baris | Didukung · Tidak didukung · Dukungan sebagian · Tidak dapat dinilai | Saat dimuat |
| Penanda baris terpilih | Sorotan visual | Baris yang sedang ditelaah | Saat dipilih |

**Interaksi**:

- Menekan satu baris memuat jejak buktinya di kolom tengah.
- Baris yang menjadi penyebab alasan utama tersorot otomatis saat layar terbuka.
- "Tidak dapat dinilai" dibedakan tegas dari "tidak didukung" — yang pertama berarti berkasnya kurang, yang kedua berarti buktinya memang tidak ada.

### 2.3 Jejak Bukti dan Linimasa

**Deskripsi**: Kolom tengah. Bagian yang paling menentukan — apa yang seharusnya ada, apa yang ditemukan, apa yang bertentangan, dan bagaimana urutan waktunya.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Kartu alasan | Kartu yang bisa dibuka-tutup | Satu kartu per alasan, terurut kekuatan bukti | Saat dimuat |
| Bukti yang diharapkan | Daftar ringkas | Jenis sumber daya yang seharusnya mendukung baris ini | Saat baris dipilih |
| Bukti yang ditemukan | Daftar ringkas dengan tautan | Sumber daya yang benar-benar ada, dapat dibuka sampai ke aslinya | Saat baris dipilih |
| Bukti tandingan | Kartu terpisah dengan penanda berbeda | Hal yang melemahkan alasan ini | Saat dimuat |
| Linimasa episode | Diagram waktu ringkas | Urutan kunjungan, tindakan, dan penagihan sepanjang episode | Saat dimuat |
| Jalur bukti | Diagram hubungan kecil dan terarah | Rantai dari klaim ke baris ke kunjungan ke bukti klinis | Saat alasan dipilih |
| Sumber asli | Panel tertutup yang bisa dibuka | Isi sumber daya apa adanya, versi aturan dan model | Saat dibuka |

**Interaksi**:

- Kartu alasan terkuat sudah terbuka saat layar dimuat; sisanya tertutup.
- Menekan satu rujukan bukti membuka sumber daya aslinya. **Rujukan yang tidak dapat dibuka adalah cacat, bukan tampilan kosong yang wajar.**
- Bukti tandingan **selalu** ditampilkan bila ada, dengan penanda visual yang berbeda dari bukti pendukung.
- Diagram hubungan dijaga kecil dan mengikuti satu jalur. Bila ia mulai menyerupai jaring rumit, rancangannya salah.

### 2.4 Laci Perbandingan

**Deskripsi**: Untuk mode tagihan berulang dan dokumentasi salinan, dua kandidat ditampilkan berdampingan.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Panel kiri dan kanan | Tampilan berdampingan | Dua klaim atau dua dokumen kandidat | Saat dibuka |
| Penanda bidang yang cocok | Sorotan visual | Bidang yang sama antar keduanya | Saat dibuka |
| Penanda bidang yang berbeda | Sorotan visual berbeda | Bidang yang tidak sama | Saat dibuka |
| Rentang tumpang tindih | Diagram waktu ringkas | Bagian waktu yang beririsan | Saat dibuka |
| Komponen kemiripan | Daftar ringkas | Unsur penyusun nilai kemiripan | Saat dibuka |
| Peringatan templat | Kotak catatan | Pengingat bahwa dokumentasi berbasis templat yang sah dapat terlihat serupa | Selalu tampil pada mode salinan |

**Interaksi**:

- Laci dibuka dari kartu alasan, dan menutup kembali ke posisi baca semula.
- Penyorotan potongan yang cocok **tidak boleh** memunculkan identitas peserta lain. Yang ditampilkan hanya potongan yang relevan.
- Peringatan templat wajib terbaca **sebelum** petugas menekan tombol tindakan.

### 2.5 Panel Disposisi

**Deskripsi**: Kolom kanan. Tempat keputusan dicatat.

**Komponen Visual**:

| Komponen | Tipe | Data | Update |
|----------|------|------|--------|
| Pilihan tindakan | Deretan pilihan tunggal | Empat tindakan yang tersedia | Saat dipilih |
| Alasan terstruktur | Daftar pilihan alasan | Alasan baku sesuai tindakan yang dipilih | Saat dipilih |
| Catatan bebas | Kotak teks | Penjelasan tambahan dari petugas | Saat diketik |
| Bukti yang diminta | Daftar centang | Untuk "minta bukti": jenis sumber daya yang kurang, sudah tercentang otomatis namun dapat diubah | Saat dipilih |
| Penanda versi kasus | Teks pendek | Versi kasus yang sedang dilihat | Saat dimuat |
| Tombol simpan | Tombol utama | Nonaktif sampai tindakan dan alasan terisi | Saat isian lengkap |

**Interaksi**:

- Tombol simpan tetap nonaktif sampai tindakan **dan** alasan terisi. Tidak ada jalan pintas.
- "Konfirmasi anomali" memunculkan kotak penegasan yang menjelaskan bahwa ini **bukan temuan fraud**, melainkan pembenaran adanya ketidaksesuaian yang perlu ditindaklanjuti.
- "Minta bukti tambahan" mencentang otomatis sumber daya yang kurang, tetapi petugas tetap bisa menambah atau mengurangi.
- Bila versi kasus sudah berubah sejak layar dibuka, penyimpanan ditolak disertai penjelasan dan tawaran memuat ulang.

---

## 3. Navigasi & Interaksi

### 3.1 Peta Navigasi

| Dari Layar / Komponen | User Klik / Aksi | Menuju Ke | Context yang Dibawa |
|----------------------|------------------|-----------|---------------------|
| Detail — baris tagihan | Menekan baris | Kolom tengah memuat jejak bukti baris itu | Pengenal baris, rujukan bukti |
| Detail — kartu alasan | Menekan kartu | Kartu terbuka, jalur bukti tampil | Kode alasan, versi aturan |
| Detail — tombol "Bandingkan" | Menekan tombol | Laci perbandingan terbuka | Pasangan kandidat |
| Detail — rujukan bukti | Menekan rujukan | Panel sumber asli terbuka | Pengenal sumber daya |
| Detail — simpan disposisi | Menekan simpan | Kembali ke Antrean (modul `03`) | Saringan dan urutan sebelumnya dipertahankan |
| Detail — "Minta bukti tambahan" | Menekan simpan | Layar Ingest (modul `01`) dengan konteks kasus | Pengenal kasus, daftar bukti yang diminta |
| Detail — tab Audit | Menekan tab | Riwayat kasus (modul `05`) | Pengenal kasus |

### 3.2 Decision Branch

- **Konfirmasi anomali** → kotak penegasan wajib muncul lebih dulu. Batal berarti kembali ke panel disposisi tanpa perubahan apa pun.
- **Minta bukti tambahan** → kasus berpindah ke status menunggu bukti, dan petugas diarahkan ke layar Ingest membawa konteks kasus.
- **Eskalasi** → kasus ditandai untuk penelusuran berwenang. **Tidak ada** sanksi otomatis, tidak ada tindakan pembayaran, tidak ada pemberitahuan keluar sistem.
- **Tolak sinyal** → kasus ditutup dengan alasan. Peninjau berwenang masih dapat membukanya kembali di kemudian hari.
- **Versi kasus tidak cocok** → penyimpanan ditolak, perubahan petugas tetap dipertahankan di layar, ditawarkan memuat ulang lalu mengirim ulang.

### 3.3 Navigasi Masuk dari Modul Lain

- Dari modul `03`, menekan satu baris antrean.
- Dari modul `01`, setelah menekan "Saring klaim" — kasus baru langsung terbuka pada alasan terkuat.
- Dari modul `05`, dari sebuah entri riwayat audit menuju kasus yang bersangkutan.

---

## 4. Alur Bisnis

### 4.1 Alur Disposisi (Happy Path)

```
┌──────────────────┐     ┌─────────────────────────┐
│ Petugas buka     │────▶│ Baca alasan utama       │
│ kasus            │     │ (sebelum skor apa pun)  │
└──────────────────┘     └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │ Periksa baris tagihan   │
                         │ yang tersorot           │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │ Telusuri bukti yang     │
                         │ diharapkan vs ditemukan │
                         │ + bukti tandingan       │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │ Pilih satu tindakan     │
                         │ + tulis alasan (wajib)  │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │ Sistem periksa versi    │
                         │ kasus masih sama        │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │ Tulis kejadian audit    │
                         │ permanen + ubah status  │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │ Kembali ke antrean      │
                         └─────────────────────────┘
```

**Penjelasan singkat:** Perjalanan ini adalah inti demo. Dari membuka kasus sampai kejadian audit tercatat harus dapat diselesaikan dalam waktu yang wajar untuk ditunjukkan langsung di depan juri.

### 4.2 Alur Minta Bukti Tambahan

1. Petugas menilai buktinya belum cukup untuk memutuskan.
2. Ia memilih "minta bukti tambahan"; sistem sudah mencentang jenis sumber daya yang kurang.
3. Ia menyesuaikan centang bila perlu dan menuliskan alasan.
4. Kasus berpindah ke status menunggu bukti; kejadian audit tercatat.
5. Ketika berkas versi baru masuk lewat modul `01`, kasus disaring ulang dan kembali ke status tersaring.
6. Riwayat alasan lama **tetap tersimpan** — kasus punya sejarah, bukan hanya keadaan terkini.

### 4.3 Alur Edge Case — Kasus Sudah Berubah di Tangan Orang Lain

```
┌────────────────────────┐         ┌────────────────────────┐
│ Petugas A buka kasus   │         │ Petugas B buka kasus   │
│ (versi 3)              │         │ yang sama (versi 3)    │
└───────────┬────────────┘         └───────────┬────────────┘
            │                                  │
            │                                  ▼
            │                      ┌────────────────────────┐
            │                      │ B simpan disposisi     │
            │                      │ → kasus jadi versi 4   │
            │                      └───────────┬────────────┘
            ▼                                  │
┌────────────────────────┐                     │
│ A simpan disposisi     │◀────────────────────┘
│ (masih mengira versi 3)│
└───────────┬────────────┘
            │
            ▼
┌──────────────────────────────────────────────────────────┐
│ DITOLAK — versi tidak cocok.                             │
│ • Isian A TIDAK hilang, tetap di layar                   │
│ • Ditampilkan apa yang berubah dan siapa yang mengubah   │
│ • Ditawarkan muat ulang lalu kirim ulang                 │
│ • TIDAK ADA penimpaan diam-diam                          │
└──────────────────────────────────────────────────────────┘
```

**Penjelasan:** Menimpa keputusan orang lain tanpa sepengetahuannya adalah kegagalan akuntabilitas, bukan sekadar bug konkurensi. Pengaman versi ini wajib, dan wajib diuji.

### 4.4 Alur Edge Case — Layanan Gagal saat Menyimpan

1. Petugas menekan simpan; permintaan gagal karena layanan tidak merespons.
2. Sistem menampilkan galat yang jujur. **Isian petugas dipertahankan utuh di layar.**
3. Tersedia tombol coba lagi.
4. **Tidak ada** kejadian audit yang tertulis sebagian. Kejadian audit ditulis utuh atau tidak sama sekali.

---

## 5. Data yang Dikelola Modul

### 5.1 Entity Bisnis Utama

**Kejadian Disposisi**

| Informasi | Deskripsi |
|-----------|-----------|
| Pengenal kejadian | Penanda unik, hanya bisa ditambah |
| Kaitan ke kasus | Kasus yang didisposisi |
| Pelaku | Peran yang mengambil keputusan |
| Tindakan | Tolak sinyal / minta bukti / konfirmasi anomali / eskalasi |
| Alasan terstruktur | Alasan baku yang dipilih |
| Catatan bebas | Penjelasan tambahan petugas |
| Rujukan bukti | Bukti yang menjadi dasar keputusan |
| Versi aturan dan model | Versi mesin yang berlaku saat keputusan diambil |
| Versi kasus sebelum dan sesudah | Untuk pengunci optimistik |
| Waktu | Cap waktu |
| Bukti yang diminta | Khusus tindakan minta bukti |

### 5.2 Catatan untuk Tim Downstream

- Kejadian disposisi **hanya bisa ditambah**. Koreksi dilakukan dengan menambah kejadian baru yang menggantikan — riwayat lama tidak pernah ditimpa.
- Alasan bersifat wajib di tingkat penyimpanan, bukan hanya di tingkat tampilan. Antarmuka bisa dilewati; penyimpanan tidak boleh.
- Pengunci optimistik memakai versi kasus. Ini pengaman akuntabilitas, bukan penyempurnaan opsional.
- Tidak ada satu pun tindakan yang boleh memicu penolakan klaim, penghentian pembayaran, sanksi, atau perubahan kode — baik di dalam sistem maupun ke sistem lain.

---

## 6. Kebutuhan Data Eksternal

**Tidak ada.**

---

## 7. Stack Agent Modul

**Tidak ada agent.** Keputusan sepenuhnya diambil manusia. Sistem hanya boleh menyarankan alasan terstruktur sebagai pilihan — tidak pernah memilihkannya, dan tidak pernah mengisi otomatis lalu menyimpan.

---

## 8. Konfigurasi Alert

Modul ini tidak mengirim notifikasi keluar.

| Kondisi | Tampilan |
|---------|----------|
| Konfirmasi anomali dipilih | Kotak penegasan yang menjelaskan bahwa ini bukan temuan fraud |
| Alasan belum terisi | Tombol simpan nonaktif disertai keterangan bidang mana yang kurang |
| Versi kasus tidak cocok | Galat yang menjelaskan apa yang berubah, isian dipertahankan |
| Rujukan bukti tidak dapat dibuka | Ditandai sebagai cacat integritas bukti, bukan sekadar tampilan kosong |
| Layanan gagal saat menyimpan | Galat jujur, isian dipertahankan, tombol coba lagi |

---

## 9. Standar Layanan yang Diharapkan

### 9.1 Kecepatan Tampil Data

Cepat. Membuka kasus dan menyimpan disposisi harus terasa langsung — layar ini adalah puncak demo.

### 9.2 Frekuensi Pembaruan Data

Saat dimuat. Tidak ada pembaruan otomatis yang menggeser isi layar saat petugas sedang membaca bukti.

### 9.3 Ketersediaan Layanan

Berfungsi penuh tanpa jaringan eksternal.

### 9.4 Standar Aksesibilitas

- Seluruh alur — memilih baris, membuka kartu, memilih tindakan, mengetik alasan, menyimpan — dapat diselesaikan dengan papan ketik.
- Fokus selalu terlihat; membuka dan menutup laci perbandingan mengembalikan fokus ke tempat yang masuk akal.
- Status tidak pernah disampaikan lewat warna saja.
- Kontras memenuhi tingkat AA, termasuk pada penyorotan bidang yang cocok dan berbeda.

---

## 10. Use Case Scenarios

### 10.1 Skenario Happy Path — Menuntaskan Tagihan Tanpa Bukti

Petugas membuka kasus dari antrean. Alasan utama terbaca langsung: baris tindakan ini tidak punya catatan tindakan yang selesai. Baris tagihan yang dimaksud sudah tersorot di kolom kiri. Di kolom tengah ia melihat jenis bukti yang diharapkan, daftar sumber daya yang sudah dicari sistem, dan keterangan bahwa berkasnya lengkap — jadi ketiadaan bukti memang bermakna. Tidak ada bukti tandingan. Ia memilih "konfirmasi anomali", membaca kotak penegasan yang mengingatkan bahwa ini bukan temuan fraud, memilih alasan baku, menambahkan satu kalimat catatan, lalu menyimpan. Kejadian audit tercatat dan ia kembali ke antrean dengan saringan yang sama seperti sebelumnya.

### 10.2 Skenario Edge Case — Bukti Tandingan Mengubah Keputusan

Sebuah kasus tagihan berulang muncul dengan pita prioritas tinggi. Namun pada kartu alasan yang sama, petugas melihat bukti tandingan: rentang kunjungan kedua klaim tidak bertumpang tindih, dan ada catatan hubungan tindak lanjut yang terdokumentasi. Ia membuka laci perbandingan, memastikan bidang mana yang benar-benar berbeda, lalu memilih "tolak sinyal" dengan alasan tindak lanjut yang sah. Kasus ditutup. Yang penting: bukti tandingan itu **tidak perlu ia cari** — sistem sudah menampilkannya berdampingan dengan sinyalnya.

### 10.3 Skenario — Bukti Tidak Cukup untuk Memutuskan

Petugas membuka kasus dengan pita "perlu konteks". Sistem menandai bahwa berkas pendukungnya tidak lengkap dan menyarankan meminta kelengkapan. Ia setuju, memilih "minta bukti tambahan", memeriksa daftar sumber daya yang sudah tercentang otomatis, menambahkan satu jenis lagi, menulis alasan, lalu menyimpan. Kasus berpindah ke status menunggu bukti. Ia **tidak** dipaksa memilih antara mengonfirmasi atau menolak — menunda dengan alasan yang tercatat adalah keputusan yang sah, dan sistem memperlakukannya begitu.

---

## 11. Referensi Implementasi

Model status fungsional dan tabel batas kewenangan sistem ada di `docs/HEALTHKATHON_2026_WINNING_MASTER_PLAN.docx` §10. Kontrak disposisi, pengunci optimistik, dan kewajiban alasan ada di `docs/canonical/03_architecture.md`. Skenario ancaman terkait tuduhan keliru dan penyangkaran pada skor merah ada di `docs/canonical/07_privacy_threat_model.md`.

---

*Bagian dari Dokumentasi Implementasi TilikKlaim · Versi 1.0.0 · 2026-08-30*
