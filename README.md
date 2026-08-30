# TilikKlaim

Lapisan integritas bukti klaim JKN — menyaring bundel klaim/RME berbentuk SATUSEHAT
sebelum pengiriman, menautkan item tagihan ke bukti klinis, dan menandai empat pola
risiko fasilitas kesehatan untuk ditinjau manusia.

> **Sistem ini tidak pernah menyatakan fraud.** Ia melaporkan "risiko atau anomali yang
> perlu ditinjau", menampilkan bukti berikut ketidakpastiannya, dan mewajibkan disposisi
> manusia yang tercatat. Seluruh data bersifat **sintetik**.

Healthkathon 2026 · kategori *Efisiensi Risiko pada Fasilitas Kesehatan* · batas kirim 19 September 2026.

## Struktur

| Folder | Isi |
|--------|-----|
| `docs/canonical/` | Referensi & batasan — read-only, hanya berubah lewat ADR |
| `brief/` | Blueprint produk (6 modul), bahasa bisnis-teknis |
| `sprint/` | App spec page-level + rencana sprint + task per stack |
| `design/` | Arah desain + alur layar (detail visual menunggu tim desain) |
| `apps/backend/` | API FastAPI — ingest, bukti, aturan, peringkat, disposisi, audit |
| `apps/web/` | Antarmuka React — antrean, detail kasus, ingest, evaluasi |
| `packages/` | `domain/` skema kanonik · `data/` generator & injektor · `model/` fitur & detektor |
| `evaluation/` | Runner evaluasi reproducible + artefak berversi |

## Menjalankan

Dua layanan berjalan berdampingan: **API** di `http://localhost:8000` dan **Web** di
`http://localhost:3000`. Panduan di bawah menjalankan keduanya di dalam satu sesi
[tmux](https://github.com/tmux/tmux) bernama `tilik-klaim`, satu window per layanan,
sehingga proses tetap hidup setelah terminal ditutup.

### 0. Prasyarat

| Alat | Versi diuji | Pemasangan (macOS) |
|------|-------------|--------------------|
| Node.js | 20.x | `brew install node` atau `fnm install 20` |
| [uv](https://docs.astral.sh/uv/) | 0.11+ | `brew install uv` |
| tmux | 3.x | `brew install tmux` |
| Docker | 29.x — **opsional**, lihat catatan Basis Data | Docker Desktop |

Verifikasi: `node -v && uv --version && tmux -V`.

### 1. Siapkan variabel lingkungan

```bash
cd <root-repo>
cp apps/backend/.env.example apps/backend/.env
```

Nilai bawaan sudah cukup untuk berjalan lokal; `.env` tidak pernah di-commit.

### 2. Pasang dependensi (sekali saja)

```bash
# API — membuat apps/backend/.venv dan memasang dependensi + tooling dev
cd apps/backend && uv venv --python 3.11 && uv pip install -e ".[dev]" && cd -

# Web
cd apps/web && npm install && cd -
```

### 3. Basis data (opsional pada tahap ini)

Sprint saat ini belum memakai Postgres — `apps/backend/app/store/` masih kosong dan API
berjalan tanpa koneksi basis data. Jalankan langkah ini hanya jika sedang mengerjakan
lapisan persistensi:

```bash
docker compose up -d db          # Postgres 16 di localhost:5432
docker compose ps                # tunggu status "healthy"
```

### 4. Buat sesi tmux dan jalankan kedua layanan

Salin blok berikut apa adanya dari root repo:

```bash
ROOT=$(pwd)

# Sesi baru (detached), window pertama = API
tmux new-session -d -s tilik-klaim -n api -c "$ROOT/apps/backend"
tmux send-keys -t tilik-klaim:api 'uv run uvicorn app.main:app --reload --port 8000' C-m

# Window kedua = Web
tmux new-window -t tilik-klaim -n web -c "$ROOT/apps/web"
tmux send-keys -t tilik-klaim:web 'npm run dev' C-m
```

> Jika sesi bernama sama sudah ada, hapus dulu: `tmux kill-session -t tilik-klaim`.

### 5. Verifikasi

```bash
curl -s http://localhost:8000/healthz     # {"status":"ok", ... ,"data_class":"synthetic"}
curl -sI http://localhost:3000            # HTTP/1.1 200 OK
```

| Alamat | Isi |
|--------|-----|
| http://localhost:3000 | Antarmuka web — Antrean Review, Ingest/Demo, Audit & Evaluasi |
| http://localhost:8000/docs | OpenAPI (Swagger UI) |
| http://localhost:8000/healthz | Probe kesehatan + identitas engine/ruleset |

Catatan: pada sprint ini web belum memanggil API — keduanya masih berjalan mandiri.

### 6. Mengoperasikan sesi tmux

```bash
tmux attach -t tilik-klaim                # masuk ke sesi
tmux ls                                   # daftar sesi
tmux list-windows -t tilik-klaim          # daftar window
tmux capture-pane -p -t tilik-klaim:api   # baca log API tanpa attach
tmux capture-pane -p -t tilik-klaim:web   # baca log Web tanpa attach
```

Di dalam sesi (prefix bawaan `Ctrl-b`):

| Tombol | Aksi |
|--------|------|
| `Ctrl-b` lalu `0` / `1` | Pindah ke window `api` / `web` |
| `Ctrl-b` lalu `n` / `p` | Window berikutnya / sebelumnya |
| `Ctrl-b` lalu `d` | Detach — proses tetap berjalan |
| `Ctrl-b` lalu `[` | Mode scroll log (`q` untuk keluar) |

### 7. Menghentikan

```bash
tmux kill-session -t tilik-klaim   # hentikan API + Web
docker compose down                # jika basis data dinyalakan
```

## Pengujian

```bash
cd apps/backend && uv run pytest        # unit + integrasi
cd apps/web && npm run typecheck        # pemeriksaan tipe
```

## Pemecahan masalah

| Gejala | Penyebab & solusi |
|--------|-------------------|
| `error connecting to /private/tmp/tmux-*/default` | Belum ada server tmux — normal; perintah `tmux new-session` akan menyalakannya |
| `Address already in use` di port 8000/3000 | Proses lama masih hidup: `lsof -ti:8000 \| xargs kill` (ganti 8000 → 3000 sesuai kebutuhan) |
| Window tmux langsung tertutup | Dependensi belum terpasang — ulangi langkah 2, lalu cek log dengan `tmux capture-pane -p -t tilik-klaim:api` |
| `uv: command not found` di dalam tmux | tmux memuat shell login yang berbeda; jalankan dengan path penuh, mis. `/opt/homebrew/bin/uv` |
| `docker compose up` gagal | Docker Desktop belum berjalan — nyalakan, atau lewati karena basis data masih opsional |

## Mulai dari mana

Baca [`brief/00_OVERVIEW.md`](brief/00_OVERVIEW.md), lalu
[`sprint/01-sprint-planning.md`](sprint/01-sprint-planning.md) untuk sprint yang aktif.
