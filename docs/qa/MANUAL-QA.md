# Manual QA — apa yang perlu diperiksa sendiri

Berkas ini untuk **verifikasi manual oleh pemilik proyek**, bukan pengganti tes otomatis.
Tes otomatis membuktikan perilaku; halaman ini untuk hal-hal yang hanya bisa dinilai mata:
apakah kalimatnya terbaca benar, apakah warnanya berarti hal yang benar, apakah layarnya
terasa seperti daftar kerja.

Setiap sesi yang menambah layar **wajib menambahkan bagian baru di sini** berikut tangkapan
layar tiap keadaan, lalu menyebutkannya di `changelog/web.md`.

---

## Cara menyalakan

```bash
cd /Users/fahrialfiansyah121gmail.com/Documents/HEALTHKATHON-2026/tilik-klaim
./scripts/dev.sh --db          # Postgres + migrasi + API + Web, Ctrl-C menghentikan semuanya
# lalu, sekali saja, isi data contoh:
(cd apps/backend && uv run python scripts/seed_dev.py)
```

Buka <http://localhost:3000>. Lima kasus contoh akan tampil.

> **Jebakan:** `uv run pytest` **mengosongkan basis data pengembangan**. Kalau layar tiba-tiba
> kosong setelah menjalankan tes, itu bukan kerusakan — jalankan `seed_dev.py` lagi.

---

## 1. Antrean Review (`/`) — ✅ selesai 1 Sep 2026

Tangkapan layar: [`2026-09-01-antrean-review/`](./2026-09-01-antrean-review/)

| Berkas | Keadaan |
|--------|---------|
| `01-populated-dark.png` | Terisi, tema gelap |
| `02-populated-light.png` | Terisi, tema terang |
| `03-empty-from-filters.png` | Kosong **karena saringan** |
| `04-service-failure.png` | Layanan mati |
| `05-no-cases-at-all.png` | Belum ada kasus sama sekali |

### Langkah pemeriksaan

1. **Buka `/`.** Dalam 5 detik, apakah terbaca sebagai *daftar kerja yang terurut*? Kalau yang
   pertama tertangkap mata adalah skor, nama model, atau grafik — rancangannya gagal, sebagus
   apa pun mesinnya. (Uji keterpahaman `design/DESIGN.md`.)
2. **Baca kolom pertama.** Harus kalimat alasan berbahasa kerja, bukan angka. Contoh yang benar:
   *"Baris tindakan ini tidak punya catatan tindakan yang selesai."*
3. **Hitung kartu metrik.** Harus **tepat lima** (empat angka + kartu versi). Tidak boleh ada
   grafik agregat, peringkat fasilitas, angka "fraud dicegah", atau rupiah "diselamatkan".
4. **Tekan kartu "Konflik deterministik".** Tabel menyaring ke 3 kasus, dan muncul keping
   saringan yang bisa dilepas satu per satu.
5. **Tekan judul kolom NOMINAL.** Urutan berubah; tekan lagi, arahnya membalik. Panah mengikuti.
6. **Tekan judul kolom PITA PRIORITAS.** Urutan **tidak** membalik walau ditekan dua kali —
   ini disengaja, lihat § 3 di bawah.
7. **Ketik pengenal kasus di kotak pencarian.** Hanya kasus itu yang tersisa. Pencarian hanya
   menerima pengenal pseudonim — memang tidak ada bidang nama atau NIK di sistem ini.
8. **Masuk ke satu kasus lalu tekan tombol kembali peramban.** Saringan dan urutan harus
   **tetap sama** seperti sebelum masuk.
9. **Ganti tema** lewat sakelar di kanan atas. Kedua tema harus sama-sama terbaca; tidak ada
   tema yang terasa versi "rusak" dari yang lain.
10. **Bandingkan kolom BUKTI dengan halaman detail** untuk kasus yang sama. Angkanya harus
    identik (mis. `1/2 baris didukung` di antrean = `1/2` di detail). Ini pernah salah dan
    tidak ketahuan dari tampilan — lihat § 3.

### Empat keadaan kosong — pastikan terlihat **berbeda**

Bandingkan `03`, `04`, dan `05`. Ketiganya menampilkan tabel tanpa isi, tetapi penyebabnya
berbeda dan tindak lanjutnya berbeda. `brief/03_ANTREAN_REVIEW.md` § 4.3 menyebut penyamaan
ketiganya sebagai cacat antarmuka yang paling merusak kepercayaan saat demo.

| Keadaan | Yang harus terbaca | Tombol yang ditawarkan |
|---------|--------------------|------------------------|
| Kosong karena saringan | Menyebut **saringan mana** yang menyaring habis, dan bahwa datanya tetap ada | Bersihkan saringan |
| Layanan mati | "Ini bukan berarti tidak ada kasus" | Coba lagi |
| Belum ada kasus | Mengajak ke layar Ingest | Masukkan bundel |

Cara memunculkannya sendiri:
- **kosong karena saringan** → pilih mode *Dokumentasi salinan* + pita *Konflik deterministik*
- **layanan mati** → hentikan API (`Ctrl-C` pada `[api]`), muat ulang halaman
- **belum ada kasus** → `(cd apps/backend && uv run pytest)` lalu muat ulang; **ingat menyemai
  ulang** setelahnya

---

## 1b. Detail Kasus (`/cases/:id`) — ✅ selesai 1 Sep 2026

Tangkapan layar: [`2026-09-01-detail-kasus/`](./2026-09-01-detail-kasus/)

| Berkas | Keadaan |
|--------|---------|
| `01-populated-atas.png` | Terisi — kepala kasus, kartu alasan, panel disposisi |
| `02-populated-bawah.png` | Terisi — jalur bukti dan linimasa episode |
| `03-dasar-keyakinan.png` | Panel "dasar keyakinan" terbuka |
| `04-panel-sumber-asli.png` | Panel sumber asli (widget 16) |
| `05-penegasan-bukan-fraud.png` | Kotak penegasan konfirmasi anomali (widget 26) |
| `06-tab-riwayat-audit.png` | Tab riwayat audit setelah disposisi tersimpan (widget 25) |
| `07-peringatan-templat.png` | Peringatan templat pada kasus dokumentasi salinan (widget 24) |
| `08-laci-perbandingan.png` | Laci perbandingan, bidang cocok vs berbeda (widget 23) |
| `09-versi-kasus-tidak-cocok.png` | **Versi kasus berubah** — simpan ditolak, isian utuh (widget 27) |
| `10-tidak-ada-risiko-teramati.png` | Kasus tanpa sinyal apa pun |
| `11-gagal-simpan-isian-utuh.png` | Layanan mati saat menyimpan — isian utuh, tombol coba lagi |
| `12-layanan-tidak-merespons.png` | Layanan mati saat memuat halaman |
| `13-kasus-tidak-ditemukan.png` | Pengenal kasus tidak ada |
| `14-memuat.png` | Sedang memuat (rangka tiga kolom) |
| `15-tema-gelap.png` | Terisi, tema gelap |
| `16-teks-panjang-terpenggal.png` | Catatan audit panjang — terpenggal empat baris dengan tautan buka penuh |

### Langkah pemeriksaan

Semua langkah dijalankan pada kasus **tagihan tanpa bukti** kecuali disebutkan lain. Ambil
pengenalnya dari antrean; pengenal berubah setiap kali `seed_dev.py` dijalankan.

1. **Buka satu baris antrean.** Yang pertama terbaca harus **kalimat alasan**, bukan pita dan
   bukan angka. Pita dan tombol "dasar keyakinan" berada di *bawahnya*. Kalau urutannya
   terbalik, aturan tampil no. 1 dilanggar.
2. **Periksa kepala kasus tanpa menggulir.** Harus terlihat sekaligus: pengenal pseudonim,
   nominal, rentang kunjungan, status, badge `DATA SINTETIK`, dan **keempat tombol tindakan**.
3. **Tekan "Dasar keyakinan".** Terbuka penjelasan pita berikut komponen skornya — bukan sekadar
   angka lain. Kalimatnya wajib memuat "*bukan menolak klaim dan bukan menyatakan fraud*".
4. **Lihat kolom kiri.** Baris `88.71` sudah tersorot otomatis karena itulah baris penyebab
   alasan utama. Keadaan dukungannya tertulis **dan** berwarna — jangan warna saja.
5. **Baca "Bukti tandingan" tanpa membuka apa pun.** Kalimatnya harus sudah terbaca pada kartu
   alasan yang tertutup sekalipun. Tutup kartu alasan (tekan judulnya) dan pastikan bukti
   tandingan **tetap terlihat**. Ini aturan tampil no. 2 dan yang paling mudah rusak diam-diam.
6. **Tekan tiap rujukan bukti.** Semuanya harus membuka panel sumber asli. Panel menyebutkan
   salah satu dari empat keadaan: *ada di bundel ini*, *milik bundel pembanding*, *dirujuk lewat
   identitas*, atau *tidak dapat dibuka*. Yang terakhir ditandai merah sebagai **cacat integritas
   bukti** — pada data contoh tidak boleh ada satu pun.
7. **Lihat "Jalur bukti".** Harus satu garis lurus: Klaim → Baris tagihan → Kunjungan → Bukti
   klinis. Kalau mulai bercabang seperti jaring, rancangannya salah (aturan tampil no. 3).
8. **Buka kasus dokumentasi salinan.** Peringatan templat harus terbaca **di atas** tombol
   tindakan, bukan hanya di dalam laci. Buka "Bandingkan pasangan kandidat": bidang yang cocok
   dan berbeda ditandai *dan* diberi label kata. Pastikan **tidak ada** pengenal peserta lain
   di dalam laci — hanya jenis dokumen, waktu, panjang teks, dan sidik teks.
9. **Coba menyimpan tanpa memilih apa pun.** Tombol simpan mati, dan di bawahnya tertulis bidang
   mana yang kurang. Pilih tindakan saja — masih mati, keterangannya berubah jadi soal alasan.
10. **Pilih "Konfirmasi anomali" lalu simpan.** Kotak penegasan wajib muncul lebih dulu, memuat
    empat kalimat penyangkalan (klaim tidak ditolak, pembayaran tidak dihentikan, tidak ada
    sanksi, tidak ada kode diubah). Tekan **Batal** — panel harus kembali persis seperti semula.
11. **Simpan sungguhan,** lalu buka kembali kasus itu dan pindah ke tab **Riwayat audit**.
    Disposisi Anda tercatat lengkap dengan pelaku, alasan, catatan, dan versi mesin.
12. **Pilih "Minta bukti tambahan".** Daftar centang muncul dengan sumber daya yang kurang
    **sudah tercentang**; hilangkan satu centang dan tambahkan yang lain — keduanya harus bisa.
13. **Ganti tema.** Kedua tema harus sama-sama terbaca, termasuk penyorotan bidang di laci
    perbandingan.

### Edge case yang wajib dicoba dengan tangan

| Keadaan | Cara memunculkan | Yang harus terjadi |
|---------|------------------|--------------------|
| **Versi kasus berubah** | Isi disposisi tapi jangan simpan. Di terminal lain: `curl -X POST localhost:8000/v1/cases/<id>/dispositions -H 'content-type: application/json' -H 'X-Actor-Role: senior_reviewer' -d '{"action":"REQUEST_EVIDENCE","structured_reason":"Berkas pendukung belum lengkap","expected_case_version":1}'` lalu tekan simpan | Banner menyebut **apa** yang berubah, **siapa** yang mengubah, versi lama → baru, menawarkan muat ulang — dan **isian Anda tetap utuh** |
| **Layanan mati saat menyimpan** | Isi disposisi, hentikan API, tekan simpan | Galat jujur, tombol coba lagi, isian utuh, dan **tidak ada** kejadian audit yang tertulis sebagian |
| **Kasus tanpa sinyal** | Buka kasus dengan pita *Tidak ada risiko teramati* | Berbunyi "tidak ada risiko teramati", **tidak pernah** "bersih" atau "aman". Jalur bukti tidak boleh menuduh apa pun hilang |
| **Pengenal tidak ada** | Buka `/cases/case_tautan_usang` | "Kasus ini tidak ditemukan" — berbeda tegas dari "layanan tidak merespons" |
| **Alasan lebih dari satu** | Kasus *episode terpecah* | Semua kartu alasan terdaftar, terurut kekuatan bukti, yang terkuat sudah terbuka |
| **Teks sangat panjang** | Simpan disposisi dengan catatan ratusan karakter, lalu buka tab riwayat audit | Catatan terpenggal empat baris dengan tautan "Tampilkan selengkapnya (n karakter)". Tata letak tidak melar, dan **tidak ada** teks yang hilang — hanya disembunyikan sampai dibuka |

### Seluruh alur wajib bisa diselesaikan dengan papan ketik

Uji tanpa menyentuh tetikus sama sekali:

1. `Tab` sampai ke panel disposisi, `Space` untuk memilih tindakan, panah untuk berpindah pilihan.
2. `Tab` ke daftar alasan, pilih dengan papan ketik, `Tab` ke catatan, ketik.
3. `Tab` ke salah satu rujukan bukti, `Enter` membuka panel, `Esc` menutupnya — **fokus harus
   kembali ke rujukan yang tadi dibuka**, bukan ke atas halaman. Ini pernah rusak: Radix
   mengembalikan fokus ke `DialogTrigger` yang tidak dipakai aplikasi ini, jadi fokus jatuh ke
   `<body>` dan `Tab` berikutnya mulai lagi dari kepala halaman.
4. Cincin fokus harus terlihat di **setiap** kontrol, termasuk radio tindakan dan centang bukti.


---

## 1c. Ingest / Demo (`/ingest`) — ✅ selesai 1 Sep 2026

Tangkapan layar: [`2026-09-01-ingest/`](./2026-09-01-ingest/)

| Berkas | Keadaan |
|--------|---------|
| `01-belum-ada-berkas.png` | Kosong — batas berkas sudah terbaca sebelum unggah |
| `02-sah.png` | **Sah** — cacah sumber daya, sidik digital, satu tombol |
| `03-sah-dengan-catatan.png` | **Sah dengan catatan** — banner kelengkapan, tombol tetap aktif |
| `04-tidak-sah-rujukan-menggantung.png` | **Tidak sah** (200) — tombol nonaktif, tabel galat menyebut sumber dayanya |
| `05-tidak-sah-berkas-rusak.png` | **Tidak sah** (4xx) — berkas ditolak sebelum diurai |
| `06-berkas-terlalu-besar.png` | Ditolak di peramban, **tanpa dikirim** |
| `07-berkas-identik-dan-konteks-kasus.png` | Pemberitahuan berkas identik + konteks dari "minta bukti tambahan" |
| `08-layanan-tidak-merespons.png` | Layanan mati — galat jujur, tombol coba lagi, tanpa pemuat menggantung |
| `09-tema-gelap.png` | Terisi, tema gelap |

### Langkah pemeriksaan

1. **Buka `/ingest`.** Sebelum menyentuh apa pun, batas berkas harus sudah terbaca: ukuran
   maksimum **8 MB**, tipe **.json**, kedalaman **32**. Kalau angka itu baru muncul setelah
   unggah gagal, `brief/01` § 2.1 dilanggar.
2. **Hitung tombol aksi setelah validasi berhasil.** Harus **tepat satu**: "Saring klaim". Tidak
   boleh ada pilihan detektor, ambang batas, mode, atau apa pun yang bisa disetel. Kalau ada,
   seorang penyaji bisa menyetel jalannya menuju hasil yang diinginkan dan demonya tidak
   membuktikan apa-apa.
3. **Pilih kasus contoh "Tagihan tanpa bukti tindakan".** Status **Sah**, cacah sumber daya
   terisi, sidik digital tampil dan bisa disalin. Tekan "Saring klaim" — layar berpindah ke
   detail kasus dengan alasan utama yang sesuai.
4. **Perhatikan tiga kasus contoh yang menyebut "+ 1 klaim riwayat".** Tagihan berulang,
   dokumentasi salinan, dan episode terpecah hanya terlihat **antar** klaim, jadi ketiganya
   memasukkan satu klaim terdahulu lebih dulu. Baris itu wajib menyebutkannya — memasukkan dua
   bundel sambil tampak memasukkan satu adalah salah gambaran tentang cara detektornya bekerja.
5. **Kembali ke `/ingest` lalu pilih kasus contoh yang sama.** Muncul pemberitahuan sidik digital
   identik dengan tautan ke kasus yang sudah ada. Menekan tombol dua kali **tidak** boleh
   menghasilkan dua kasus kembar di antrean.
6. **Bandingkan ketiga status validasi.** Ketiganya harus terbaca berbeda, dan yang tengah
   adalah yang paling mudah salah dibaca:

| Status | Warna | Tombol saring | Yang harus terbaca |
|--------|-------|---------------|--------------------|
| Sah | Netral | Aktif | Bentuk berkas lolos dan seluruh rujukan terselesaikan |
| Sah dengan catatan | Kuning | **Aktif** | Berkas memang tidak lengkap; ketiadaannya menurunkan keyakinan dan mengarah ke *minta bukti*, **bukan** menaikkan sinyal risiko |
| Tidak sah | Merah | Nonaktif, disertai alasan | Perbaiki sumber daya yang disebut lalu kirim ulang; tidak ada penyaringan sebagian |

> **Yang paling penting di halaman ini:** "Sah dengan catatan" **tetap bisa disaring**. Rekam
> medis tipis bukan berkas yang ditolak. Kalau tombolnya mati di status itu, pembeda etis yang
> jadi alasan seluruh modul ini ada sudah runtuh.

7. **Buka tabel galat pada berkas tidak sah.** Empat kolom: kode stabil, jenis sumber daya,
   pengenal, dan penjelasan. Kalau yang terbaca hanya "berkas tidak valid", operator tidak punya
   apa pun untuk diperbaiki.
8. **Coba unggah berkas > 8 MB.** Ditolak di peramban, pesan menyebut **kedua** angka, dan tidak
   ada permintaan yang terkirim (periksa di tab Network — harus kosong).
9. **Ganti tema.** Kedua tema harus sama-sama terbaca, termasuk badge status dan tabel galat.

### Edge case yang wajib dicoba dengan tangan

| Keadaan | Cara memunculkan | Yang harus terjadi |
|---------|------------------|--------------------|
| **Berkas rusak** | Unggah berkas JSON yang terpotong di tengah | Status **Tidak sah** dengan kode `BUNDLE_MALFORMED_JSON`. Ini datang sebagai galat 4xx, bukan laporan 200 — layar tetap harus menyebutnya "tidak sah", bukan "layanan gagal" |
| **Rujukan menggantung** | Unggah bundel yang `supporting_refs`-nya menunjuk pengenal yang tidak ikut terkirim | Status **Tidak sah** dengan kode `BUNDLE_DANGLING_REFERENCE` dan pengenal sumber dayanya disebut |
| **Layanan mati** | Hentikan API, lalu pilih satu kasus contoh | Galat jujur + tombol coba lagi. **Tidak boleh** ada pemuat yang berputar selamanya, dan panel laporan harus tetap berkata "belum diperiksa" — bukan menampilkan laporan lama |
| **Datang dari kasus** | Buka `/ingest?case=<id>` | Banner menyebut bahwa Anda datang dari kasus yang menunggu bukti, dengan tautan kembali |


---

## 2. Aturan bahasa risiko — periksa di **setiap** layar baru

Empat aturan ini yang paling mungkin ditangkap juri, dan paling mahal kalau salah. Semuanya
sudah dikunci di `docs/canonical/` dan diuji, tetapi tes tidak bisa menilai kalimat baru yang
ditulis sesi berikutnya.

| # | Aturan | Cara memeriksa dengan mata |
|---|--------|----------------------------|
| 1 | **Merah hanya untuk konflik deterministik.** Merah menandai konflik pasti, **bukan** pihak yang bersalah | Cari warna merah di layar. Kalau merah dipakai untuk tombol hapus, galat biasa, atau penekanan — itu salah |
| 2 | **Hijau hanya untuk aksi selesai & tervalidasi.** Hijau **tidak pernah** berarti klaim aman | Kalau ada hijau di dekat baris tagihan, nominal, atau pita prioritas — itu salah |
| 3 | **Kasus tanpa sinyal berbunyi "tidak ada risiko teramati"** — tidak pernah "bersih", "aman", atau "lolos" | Baris terakhir antrean. Pita netral abu-abu, bukan hijau |
| 4 | **Berkas belum lengkap ≠ bukti tidak ada.** Rekam medis tipis menurunkan keyakinan dan mengarah ke *minta bukti*, tidak pernah ke *konfirmasi anomali* | Kolom BUKTI: "Berkas belum lengkap" harus terbaca berbeda dari "0/2 baris didukung" |

Dua lagi yang berlaku di Detail Kasus (layar itu sudah jadi — periksa langsung):

| # | Aturan | Cara memeriksa |
|---|--------|----------------|
| 5 | **"Konfirmasi anomali" wajib memunculkan penegasan bahwa ini bukan temuan fraud** sebelum tersimpan | Pilih tindakan itu, tekan simpan — kotak penegasan harus muncul lebih dulu |
| 6 | **Bukti tandingan sederajat dengan bukti pendukung** — tidak boleh disembunyikan di panel tertutup | Buka kasus *dokumentasi salinan*; bukti tandingan harus terlihat tanpa membuka apa pun |

Kata yang **tidak boleh** muncul sebagai temuan sistem di mana pun: *fraud*, *kecurangan*,
*penipuan*, *tolak klaim*, *sanksi*, *bersih*, *aman*.
(Kata "fraud" boleh muncul **hanya** dalam kalimat yang menyangkalnya, mis. "ini bukan temuan
fraud" — itu justru pengamannya.)

---

## 3. Yang pernah salah dan tidak terlihat dari tampilan

Dicatat karena keduanya lolos dari mata dan dari compiler, dan hanya ketahuan saat diukur.

| Cacat | Kenapa tidak terlihat | Cara memastikan tidak kambuh |
|-------|------------------------|------------------------------|
| Antrean dan detail berbeda soal kelengkapan bukti | Antrean menulis "Tidak ada baris tertagih" untuk klaim yang sebenarnya punya 2 baris yang didukung penuh. Tampilannya wajar; hanya salah | Langkah 10 di atas — bandingkan angkanya |
| Setiap tombol kehilangan warna teksnya | `tailwind-merge` membuang `text-brand-on` karena mengira bentrok dengan ukuran huruf. Tombol jadi teks gelap di atas teal gelap, **2.5:1** | Lihat tombol "Masukkan bundel baru" — teksnya harus putih dan terbaca jelas |
| `--t-3` gagal AA di dua permukaan | Diukur hanya di atas kartu putih; di atas `--s-page` hanya 4.07:1 | Semua teks abu-abu kecil di tema terang harus tetap terbaca nyaman |

Tambahan dari sesi Detail Kasus (1 Sep). Semuanya lolos compiler dan lolos tes, dan semuanya
ketahuan hanya karena layarnya dibuka:

| Cacat | Kenapa tidak terlihat | Cara memastikan tidak kambuh |
|-------|------------------------|------------------------------|
| `seed_dev.py` mengosongkan bundel tapi **tidak** mengosongkan kasus | Kasus lama tertinggal menunjuk `ingestion_id` yang sudah dihapus, jadi `GET /v1/cases/{id}` menjawab `lines: []` dan `timeline: []`. Layarnya tampil rapi — hanya tanpa satu pun baris tagihan, dari data yang tampak sudah disemai | Langkah 4 di § 1b: kasus tagihan-tanpa-bukti harus punya **dua** baris tagihan |
| Kalimat bukti tandingan dibuang di lapisan DTO | Aturan sudah menulis kalimatnya ("*tidak ditemukannya catatan di sini bukan bukti bahwa layanan tidak diberikan*"), tetapi wire hanya membawa rujukannya. Widget 13 tampil sebagai satu pengenal sumber daya di bawah judul "bukti tandingan" — terlihat berfungsi, tanpa argumen apa pun | Langkah 5 di § 1b: yang terbaca harus **kalimat**, bukan pengenal |
| Laci perbandingan membandingkan angka dengan dirinya sendiri | `fields` diisi dari komponen skor alasan dengan kiri = kanan dan `matches` selalu `true`. Sebuah perbandingan yang mustahil menemukan perbedaan | Langkah 8 di § 1b: harus ada minimal satu baris berlabel **berbeda** dengan dua nilai yang memang berbeda |
| "Bukti yang diharapkan" memakai bidang yang salah | Katalog punya dua daftar: apa yang dibutuhkan **alasan** agar sah, dan apa yang seharusnya menopang **baris tagihan**. Yang pertama dipakai, sehingga kasus phantom melaporkan semua bukti "ditemukan" — pada kasus yang seluruh temuannya justru ketiadaan | Langkah 5 & 6: pada kasus tagihan-tanpa-bukti, "Tindakan" harus tertulis **tidak ditemukan** |
| Fokus tidak kembali setelah laci ditutup | Radix mengembalikan fokus ke `DialogTrigger`; aplikasi ini membuka laci dari tombol biasa, jadi ref itu `null`, Radix membatalkan pemulihan bawaan, dan fokus jatuh ke `<body>`. Dengan tetikus tidak terasa sama sekali | Uji papan ketik no. 3 di § 1b |
| Jalur bukti menuduh pada kasus tanpa alasan | Rantai selalu ditutup dengan simpul "bukti klinis tidak ditemukan", termasuk saat tidak ada alasan yang menyala dan semua baris didukung penuh | Buka kasus *tidak ada risiko teramati*: rantai berhenti di baris tagihan, tanpa simpul merah/kuning |
| Berkas yang **ditolak** dilaporkan sebagai **layanan gagal** | API menolak bundel lewat dua jalur: galat `4xx` untuk apa pun yang tertangkap sebelum diurai, dan laporan `200` berstatus `INVALID` untuk yang tertangkap setelahnya. `catch` biasa menampilkan yang pertama sebagai "permintaan gagal" berikut tombol coba lagi — pada berkas yang akan ditolak persis sama setiap kali — sambil menyembunyikan kode stabil yang justru dibutuhkan operator | Unggah berkas JSON terpotong: status harus **Tidak sah** dengan kode `BUNDLE_MALFORMED_JSON`, bukan banner "layanan gagal" |

---

## § 1d — Audit & Evaluasi (`/evaluation`)

Tangkapan layar: [`2026-09-01-evaluation/`](./2026-09-01-evaluation/) — 4 berkas.

**Prasyarat.** Halaman ini membaca artefak, bukan basis data. Jalankan dulu evaluasinya:

```bash
(cd packages/data && uv run python -m tilik_data.pipeline --out build)   # sekali, setelah regenerasi disetujui
(cd evaluation && uv run python -m runner.run --build ../packages/data/build)
```

Tanpa itu halaman menampilkan keadaan **belum ada evaluasi**, dan itu memang benar.

### Klik-tayang

1. Buka <http://localhost:3000/evaluation>. Judul **Audit & Evaluasi** muncul, disusul spanduk
   **DATA SINTETIK** berlatar krem. Spanduk ini tidak pernah bersyarat — kalau hilang, itu cacat.
2. **Penanda versi.** Sepuluh baris: run, waktu selesai, sidik kumpulan data, dan versi generator,
   aturan, mesin, fitur, model, commit kode, sidik lingkungan. Commit kode harus berakhiran
   **`-dirty`** bila pohon kerja sedang kotor — kalau tidak, penanda itu menyebut keadaan kode yang
   bukan keadaan yang berjalan.
3. **Perbandingan baseline.** Empat baris, selalu keempatnya: Acak · Aturan saja · Statistik saja ·
   TilikKlaim (hibrida). Bandingkan kolom *Ketepatan pada kapasitas review*: hibrida **1.0000** di
   atas aturan-saja **0.9565**. Kolom *Positif palsu per 100 klaim bersih*: hibrida **52.5000**
   sedikit **lebih buruk** dari aturan-saja **51.8750**. Keduanya harus tampil apa adanya; angka yang
   memburuk tidak boleh disembunyikan.
4. **Metrik per mode risiko.** Empat mode, dan kolom *Jumlah kasus* berisi **bilangan bulat**
   (`7`, `24`, `15`, `23`) — bukan `7.0000`. Hitungan kasus bukan pengukuran berdesimal.
5. **Dua grafik batang.** Nilai di samping tiap batang harus **sama persis** dengan sel tabel di
   atasnya. Ini aturan tampil no. 2 dan ketidakcocokan di sini adalah cacat integritas, bukan beda
   pembulatan. Bandingkan `52.5000` pada grafik positif palsu dengan sel hibrida di langkah 3.
6. **Waktu pemrosesan.** p50 dan p95 dalam milidetik penuh, disertai catatan bahwa nilainya
   dibulatkan. Bila keduanya tampak sama, itu efek pembulatan, bukan kerusakan — angka penuhnya ada
   di `latency.json`.
7. **Kartu keterbatasan.** Selalu ada bila ada angka. Kalimat wajib tampil dalam bahasa Indonesia
   dengan aslinya (bahasa Inggris) di bawahnya dalam huruf miring — kanonis menuntut kalimat itu
   apa adanya. Dua kolom: *Yang ditunjukkan* dan *Yang tidak ditunjukkan*. Kolom kanan harus memuat
   catatan khas run ini: jumlah berkas uji, berkas latih yang ditahan, dan porsi penandaan hibrida
   **tanpa alasan aturan**. Tekan **Salin** — teks masuk ke papan klip dan tombol berubah menjadi
   *Tersalin*.
8. **Tidak ada kendali apa pun.** Tidak ada penggeser ambang batas, tidak ada masukan what-if,
   tidak ada tombol "jalankan". Satu-satunya tombol di halaman ini adalah **Salin**. Kalau ada yang
   lain, itu pelanggaran aturan tampil no. 1 — halaman yang bisa menyetel ambang batas berarti
   halaman yang bisa menyetel terhadap partisi uji yang sedang ditampilkannya sendiri.
9. **Belum ada evaluasi.** Hentikan sementara artefaknya (`mv evaluation/artifacts/run-* /tmp/`) lalu
   muat ulang. Yang muncul: judul *Belum ada evaluasi yang dijalankan*, penjelasan, dan **perintah**
   yang harus dijalankan. Tidak ada satu pun angka nol. Ini aturan tampil no. 4 — nol berarti
   "sudah diukur dan hasilnya kosong", yang justru kebalikan dari keadaan sebenarnya.
10. **Layanan gagal ≠ belum ada evaluasi.** Matikan API (`pkill -f "uvicorn app.main:app"`) lalu
    muat ulang: yang muncul *Hasil evaluasi tidak dapat dimuat* dengan tombol **Coba lagi** — bukan
    keadaan langkah 9. Keduanya menghasilkan halaman kosong dan artinya berlawanan.

### Cacat yang ketahuan hanya karena halamannya dibuka (1 Sep)

Ketiganya lolos compiler, lolos 104 tes unit, dan lolos ulasan kode.

| Cacat | Kenapa tidak terlihat | Cara memastikan tidak kambuh |
|-------|------------------------|------------------------------|
| Jumlah kasus tampil `7.0000` | Semua sel lewat satu pemformat metrik. Untuk ketepatan dan F1 itu benar; untuk **hitungan kasus** hasilnya angka yang mengaku punya empat desimal presisi | Langkah 4 — kolom *Jumlah kasus* harus bilangan bulat |
| Kartu keterbatasan tampil **berbahasa Inggris** | Baris kanonis memang berbahasa Inggris di `06_evaluation_plan.md`, dan artefak `LIMITATIONS.md` menyalinnya apa adanya. Yang keliru bukan artefaknya melainkan menampilkannya mentah di layar berbahasa Indonesia | Langkah 7 — teks utama Indonesia, aslinya di bawahnya |
| `threshold_logic` dari manifes tercetak mentah di kartu versi | Bidang manifes adalah catatan teknis berbahasa Inggris, sama seperti data card dan model card. Menyalinnya ke layar operator membawa serta bahasanya | Langkah 2 — baris penutup kartu versi harus berbahasa Indonesia dan menunjuk ke `manifest.json` |

Satu temuan lagi, dari sisi runner dan bukan dari layar: pemeriksaan keabsahan rujukan bukti mula-mula
melaporkan **39 dari 140** rujukan tidak dapat diselesaikan. Semuanya alasan *dokumentasi salinan* yang
menunjuk catatan **peserta lain** di fasilitas yang sama — persis ke mana alasan kloning memang harus
menunjuk. Yang salah adalah pemeriksanya, yang hanya mencari di dalam bundel dan riwayatnya. Kalau
angka itu dibiarkan, tanggapan yang wajar adalah "memperbaiki" detektor yang sebenarnya sudah benar.

---

*Diperbarui 1 September 2026 — setelah Antrean Review, Detail Kasus, Ingest, dan Audit & Evaluasi
selesai.*

---

## § 1e — Evidence Workspace di `/cases/:id` — ✅ selesai 3 Sep 2026

Tangkapan layar: [`2026-09-03-evidence-workspace/`](./2026-09-03-evidence-workspace/) · Keputusan: ADR-0004

| Berkas | Keadaan |
|--------|---------|
| `01-workspace-phantom-light.png` | Seluruh workspace, kasus phantom, tema terang |
| `02-workspace-phantom-dark.png` | Sama, tema gelap |
| `03-matrix-phantom.png` | Matriks bukti: `tidak ditemukan` pada 88.71/Tindakan; `—` (tidak diharapkan) pada 89.7 |
| `04-swimlane-empty-procedure-lane.png` | Swimlane: jalur Obat kosong dan berlabel; celah di 17.00 pada jalur Tindakan tepat di atas tagihan 88.71 |
| `05-map-reason-focused.png` | Peta bukti: satu batang, dua simpul ujung, cabang tandingan putus-putus |
| `06-drawer-source-from-matrix.png` | Laci sumber dibuka dari sel matriks |
| `07-drawer-comparison-clone.png` | Laci perbandingan (kasus salinan) — hanya satu laci pada satu waktu |
| `08-matrix-claim-level-row-repeat.png` | Kasus tagihan berulang: kolom Klaim, dua rujukan klaim, salah satunya `bundel pembanding` |
| `09-workspace-no-observed-risk.png` | Kasus tanpa sinyal: matriks tanpa kolom, peta tanpa alasan, swimlane tetap terisi |
| `10-loading.png` | Memuat |
| `11-service-failure.png` | Galat layanan |
| `12-stale-version-workspace-kept.png` | Versi usang — workspace tetap tampil, isian dipertahankan |
| `13-dispositioned-case-still-readable.png` | Kasus yang sudah didisposisi tetap dapat dibaca |

### Klik-tayang

1. Buka kasus phantom. **Kartu alasan tetap yang pertama** di kolom tengah; matriks, peta, dan
   swimlane ada di bawahnya. Tidak ada angka skor di ketiganya.
2. Pada matriks, baris `Layanan 89.7` menampilkan `—` di semua sel, dan `0 alasan`. Arahkan
   kursor: tooltip berbunyi *tidak diharapkan … kosong bukan berarti tidak ada*. Ini keadaan
   keempat dan **tidak boleh** tampak seperti `tidak ditemukan`.
3. Klik `Kunjungan ENC-PH-1` di sel matriks → laci sumber terbuka. Tekan **Escape** → fokus
   kembali ke tautan yang sama di sel. Ulangi dari simpul peta dan dari chip swimlane.
4. Di swimlane, jalur **Penagihan** memuat `Layanan 89.7 · LN-P1` sebagai teks (bukan tautan,
   bukan cacat) dan `Layanan 88.71` dengan tautan `Baris tagihan LN-P2`. Baris yang tidak
   dirujuk alasan **tidak boleh** berwarna merah.
5. Tutup kartu alasan (tombol `−`). Peta berbunyi *Belum ada alasan yang ditelusuri* dan
   **tidak** menyebut *tidak ditemukan*. Bukti tandingan di kartu tetap terbaca.
6. Buka kasus salinan. Klik satu rujukan → laci sumber; Escape; klik *Bandingkan pasangan
   kandidat* → laci perbandingan. Tidak pernah dua laci sekaligus.
7. Isi disposisi setengah jalan, lalu buka-tutup beberapa laci dan pindah alasan: isian tidak
   berubah.

### Cacat yang ketahuan hanya karena halamannya dibuka (3 Sep)

- Jalur Penagihan menandai baris 89.7 sebagai *cacat integritas bukti* — karena API hanya
  mengindeks sumber untuk sumber daya yang **dirujuk alasan**. Baris yang tidak dirujuk kini
  tampil sebagai teks tanpa rujukan. Lihat `changelog/web.md` 3 Sep.

---

## § 1f — Ringkasan bukti di `/cases/:id` — ✅ selesai 3 Sep 2026

Tangkapan layar: [`2026-09-03-case-briefing/`](./2026-09-03-case-briefing/) · Keputusan: ADR-0005

| Berkas | Keadaan |
|--------|---------|
| `01-collapsed-light.png` | Terlipat — hanya judul dan penafian; **tidak ada permintaan jaringan** |
| `02-open-idle-light.png` | Dibuka, belum diminta — tombol *Susun ringkasan* |
| `03-template-briefing-light.png` | Templat deterministik: pengamatan ber-rujukan → pertanyaan → ketidakpastian → cara disusun |
| `04-template-briefing-dark.png` | Sama, tema gelap |
| `05-failed-service.png` | Layanan gagal — kalimat galat, bukti di atas tetap utuh |
| `06-model-briefing-vllm.png` | **Ringkasan dari model sungguhan** (Qwen3.5-9B lewat gerbang vLLM), 4 Sep 2026 |

### Klik-tayang

1. Panel ada di **paling bawah** kolom tengah, di bawah linimasa, terlipat. Buka tab jaringan:
   tidak ada panggilan `/briefing` sampai Anda menekan *Susun ringkasan*.
2. Tekan *Susun ringkasan*. Log kemajuan (`role=status`) menyebut fase; pada jalur templat
   hampir instan. Pengamatan muncul dengan chip jenis (*Celah bukti*, *Bukti tandingan*, …),
   kata keyakinan (*tercatat langsung* / *disimpulkan*), dan rujukan yang **dapat dibuka** ke
   laci sumber yang sama. Escape mengembalikan fokus ke rujukan.
3. Bagian **CARA DISUSUN** berbunyi *Templat deterministik — tanpa model bahasa*. Ini keadaan
   bawaan dan keadaan demo luring. Kalau tertulis *dimuat tanpa aliran*, proxy memutus SSE dan
   cadangan `?stream=false` yang menjawab — bukan cacat, tetapi catat.
4. Tidak ada tombol tindakan, radio, atau centang di dalam panel. Isi disposisi setengah jalan,
   susun ringkasan: isian tidak berubah.
5. Bahasa: tidak ada *fraud*, *curang*, *palsu*, *tolak*, *sanksi*, *terbukti*, *pasti*,
   *bersih*, *aman*, *bayar*, *denda* — validator menolak keluaran model yang memuatnya, dan
   templat lolos validator yang sama pada kelima skenario.
6. **Sudah diuji dengan model sungguhan (4 Sep 2026).** Gerbang vLLM internal, `Qwen3.5-9B`.
   Terukur pada 15 kali jalan atas lima skenario emas: jalur model menjawab **9 dari 15**,
   median **23 detik**, paling lama **87 detik**. Enam sisanya jatuh ke templat dan menyebutkan
   alasannya di panel — keenamnya karena objek terpotong di 3.000 token. **Ini perilaku yang
   dirancang, bukan kegagalan:** peninjau selalu mendapat ringkasan yang ber-rujukan.
   Yang diperiksa dengan mata: **CARA DISUSUN** berbunyi *Model bahasa, tervalidasi* dan
   menyebut nama model. Kalau namanya berbeda dari `LLM_MODEL_VLLM`, gerbang mengganti model
   diam-diam — tercatat apa adanya, ada peringatan di log, bukan cacat.

6b. **Kalau ingin menyalakannya sendiri:** `BRIEFING_ENABLED` masih `false`; jalur model hanya
   diuji terhadap gerbang tiruan. Menyalakannya adalah keputusan pemilik, lewat gerbang vLLM
   internal (bukan penyedia pihak ketiga) — urutannya:

   ```bash
   # 1. Isi apps/backend/.env — alamat & kunci ada di docs/VLLM-SETUP.md, tidak di repo.
   #    BRIEFING_ENABLED=true · LLM_MODEL_VLLM=… · VLLM_BASE_URL=…/v1 · VLLM_API_KEY=…
   # 2. Nilai salah = API MENOLAK START. Itu disengaja; baca pesannya.
   # 3. Gerbang menjawab dan modelnya ada?
   curl -s localhost:8000/health/llm     # model_available harus true
   # 4. Baru buka satu kasus dan tekan "Susun ringkasan".
   ```

   Yang diperiksa dengan mata setelah itu: **CARA DISUSUN** berbunyi *Model bahasa, tervalidasi*
   dan menyebut nama model. Kalau namanya **berbeda** dari `LLM_MODEL_VLLM`, gerbang mengganti
   model diam-diam — itu tercatat apa adanya dan ada peringatan di log; bukan cacat, tetapi
   perlu diketahui. Kalau tetap berbunyi *Templat deterministik*, lihat `rejection_reason` di
   panel: validator menolak keluaran model, dan alasannya tertulis.

---

## § 2 — Masuk (`/login`) & Manajemen Pengguna (`/admin/users`) — ✅ selesai 4 Sep 2026

Tangkapan layar: [`2026-09-04-auth-roles/`](./2026-09-04-auth-roles/) · Keputusan: [ADR-0006](../canonical/decisions/ADR-0006-three-roles-and-simulated-login.md)

| Berkas | Keadaan |
|--------|---------|
| `01-login-light.png` | Halaman masuk, tema terang |
| `02-login-dark.png` | Halaman masuk, tema gelap |
| `03-login-admin-row-chosen.png` | Baris administrator dipilih — isian dan nama tombol ikut berubah |
| `04-login-wrong-passcode.png` | **Galat** — kode demo salah |
| `05-login-deactivated-account.png` | **Nonaktif** — akun dinonaktifkan, ditolak dengan menyebut tokennya |
| `06-queue-reviewer-light.png` | Antrean sebagai Peninjau; tiga entri menu |
| `07-admin-users-light.png` | Manajemen pengguna, tema terang |
| `08-admin-users-dark.png` | Manajemen pengguna, tema gelap |
| `09-admin-users-after-deactivate.png` | Setelah menonaktifkan Budi — riwayat bertambah |
| `10-profile-menu-light.png` | Menu profil, tema terang |
| `11-profile-menu-dark.png` | Menu profil, tema gelap |
| `12-logout-warns-unsaved-draft.png` | Keluar dengan draf disposisi belum tersimpan |
| `13-admin-redirected-from-queue.png` | Administrator mengetik `/` — dialihkan, bukan ditampilkan |
| `14-admin-users-service-failure.png` | **Galat** — daftar pengguna gagal dimuat |

### Klik-tayang

1. **Buka `/login`.** Dalam 5 detik, apakah terbaca sebagai *daftar siapa boleh apa*? Kalau yang
   pertama tertangkap mata adalah formulir biasa, gagasan halaman ini belum sampai.
2. **Baca baris Rina Hartati.** Harus **lima kolom `Tidak`** dan satu `Boleh` di kolom terakhir.
   Itulah pemisahan tugas, terbaca sebelum siapa pun masuk. Kalau administrator punya `Boleh` di
   kolom kasus mana pun, matriksnya salah — dan halaman pertama produk ini sedang berbohong.
3. **Gulir halaman.** Tidak boleh ada bilah gulir pada 1440×900 **maupun** 1280×800. Versi pertama
   halaman ini gagal di sini; sebuah spesifikasi Playwright sekarang mengukurnya.
4. **Tekan Tab dari atas.** Sakelar tema → radio baris pertama. Lalu **panah bawah** dua kali:
   pilihan berpindah ke Budi lalu Rina, kedua isian ikut terisi, dan **nama tombol berubah**
   menjadi *Masuk sebagai Administrator*. Peran yang salah harus terlihat sebelum ditekan.
5. **Sunting kolom email dengan tangan.** Harus bisa. Matriks hanya jalan pintas; isian adalah
   kontrol sebenarnya.
6. **Tekan `Salin kredensial`.** Tempel di tempat lain: harus `email · kode`. Kalau peramban
   menolak menyalin, tombol **tidak boleh** berbunyi *Tersalin*.
7. **Kosongkan kode demo.** Tombol masuk nonaktif, dan kalimat di bawahnya menyebutkan alasannya —
   bukan sekadar tombol abu tanpa penjelasan.
8. **Isi kode demo yang salah lalu masuk.** Kalimat galat muncul, **dan email yang sudah diketik
   tetap ada**. Penolakan tidak boleh memakan isian.
9. **Periksa latar.** Barisan klaim samar dengan beberapa segmen amber. Ia harus terbaca sebagai
   *tekstur*, bukan sebagai isi. Kalau ia bersaing dengan matriks, opasitasnya terlalu tinggi.
10. **Periksa kaki halaman.** Harus tertulis kategori lomba **dan** *bukan produk atau layanan
    resmi BPJS Kesehatan*. Kalimat itu bukan basa-basi — ia yang menjaga halaman ini tidak terbaca
    sebagai produk penyelenggara.
11. **Ganti tema.** Kedua tema harus sama-sama terbaca; tidak ada yang terasa versi "rusak".
12. **Masuk sebagai Peninjau.** Menu sisi punya **tiga** entri, tidak ada Manajemen Pengguna.
    Kaki menu menyebut peran yang masuk dan kata *bukan autentikasi*.
13. **Buka menu profil di kanan atas.** Nama, email, peran, token petugas, tombol **Keluar**.
    Tekan **Escape**: menu tertutup dan fokus **kembali ke pemicunya**, bukan ke `<body>`.
14. **Isi disposisi setengah jalan, lalu Keluar.** Peringatan muncul dan Anda **masih masuk**.
    Tekan sekali lagi untuk benar-benar keluar. `store.ts` menjaga draf supaya penyimpanan yang
    ditolak tidak memakan pekerjaan; keluar diam-diam akan membatalkan jaminan itu dari sisi lain.
15. **Masuk sebagai Administrator, lalu ketik `/` di bilah alamat.** Anda dialihkan ke Manajemen
    Pengguna — bukan halaman galat. Menu sisi hanya punya **satu** entri. Ini disengaja.
16. **Uji dengan `curl`, bukan hanya dengan mata:**
    ```bash
    curl -s -o /dev/null -w '%{http_code}\n' localhost:8000/v1/cases \
      -H 'X-Actor-Role: admin' -H 'X-Actor-Id: usr_rina_hartati'      # harus 403
    curl -s localhost:8000/v1/users -H 'X-Actor-Role: reviewer'       # USER_MANAGEMENT_FORBIDDEN
    ```
    Menyembunyikan tombol bukan kendali akses. Kalau salah satu menjawab 200, fitur ini tidak layak
    kirim apa pun kata tampilannya.
17. **Di `/admin/users`, ubah peran Sari.** Riwayat di bawah bertambah: *Peran diubah — Sari
    Wulandari · Peninjau → Peninjau Senior · oleh Rina Hartati*. Kembalikan lagi; riwayat bertambah
    **dua**, bukan berkurang. Ia tambah-saja.
18. **Coba ubah baris Rina sendiri.** Kedua kontrolnya nonaktif **dan** ada kalimat yang menyebut
    alasannya. Mengunci satu-satunya administrator keluar adalah cacat, bukan pilihan.
19. **Nonaktifkan Budi, lalu coba masuk sebagai Budi** di jendela penyamaran. Ditolak dengan
    kalimat yang menyebut **PTG-02** dan mengatakan akunnya dinonaktifkan — bukan "kode salah".
    Kredensialnya benar; menyebutnya salah akan mengirim orang mencari kesalahan ketik yang tidak ada.
20. **Jalankan `demo_reset.py`.** Ketiga akun aktif kembali. Gladi berikutnya tidak boleh dimulai
    dari daftar yang seseorang lupa kembalikan.

### Pemeriksaan cangkang aplikasi (ditambahkan setelah putaran perapian)

Tangkapan layar: `15-logout-confirmation-modal.png` · `16-shell-icons-light.png` · `17-shell-icons-dark.png`

21. **Lihat urutan di kanan atas.** Penanda versi → sakelar tema → **DATA SINTETIK** → profil.
    Profil paling kanan; badge tata kelola **tidak** boleh terdorong ke tepi tempat mata berhenti
    memindai.
22. **Sakelar tema.** Hanya ikon — matahari di tema terang, bulan di tema gelap, tanpa teks.
    Arahkan penunjuk: judulnya *Ganti tema*. Dengan pembaca layar, namanya harus menyebut keadaan
    **dan** tindakannya; kontrol yang maknanya hanya ada di gambar adalah kontrol yang tidak bisa
    dibacakan.
23. **Tiga ikon menu harus berbeda satu sama lain**, dan masing-masing harus menggambarkan isi
    halamannya: daftar kerja dengan rel prioritas · bundel masuk ke baki · tiga batang terukur di
    atas garis dasar. Kalau ketiganya terasa sama, ikonnya hiasan, bukan penunjuk.
24. **Tekan Keluar di menu profil.** Harus muncul **dialog konfirmasi**, bukan langsung keluar.
    Tekan **Batal**: dialog tertutup, Anda masih masuk. Tekan **Escape**: sama.
25. **Isi disposisi setengah jalan, lalu Keluar.** Dialognya berganti kalimat — menyebut draf yang
    belum tersimpan — dan tombolnya berbunyi *Keluar dan buang draf*. Kalau kalimatnya sama saja
    dengan keadaan tanpa draf, peringatannya tidak mengatakan apa-apa.
26. **Tutup dialog dengan Escape lalu tekan Tab.** Fokus harus kembali ke pemicu menu profil,
    bukan ke awal halaman. Ini jebakan yang sudah pernah dibayar sekali di laci kasus.

### Cacat yang ketahuan hanya karena halamannya dibuka

- **Rancangan pertama menggulir.** Panel merek kiri + formulir kanan dengan tiga kartu akun
  bertumpuk = ±1.240 px pada 1440×900. Tidak ada tes yang gagal; hanya mata. Diganti total oleh
  matriks peran, dan sekarang ada spesifikasi Playwright yang mengukur tinggi halaman.
- **Latar tekstur versi pertama terlalu kuat dan menyeberang ke pita navy**, membuat pitanya
  terlihat kotor. Diturunkan ke 24% dan dipotong di bawah pita.
- **`Pakai` memindahkan fokus ke tombol yang masih `disabled`**, jadi fokusnya tidak ke mana-mana.
  Terlihat benar di kode, gagal di papan ketik. (Kontrolnya kini matriks, tetapi pelajarannya
  tetap: pindahkan fokus setelah commit, bukan di dalam handler klik.)
- **Tanda TilikKlaim tak terlihat di atas permukaan terang** — stroke solidnya `--t-inv`, nyaris
  putih. Sekarang ada `onSurface` yang memakai `currentColor`.
