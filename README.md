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

Dua layanan berjalan berdampingan:

| Layanan | Folder | Alamat |
|---------|--------|--------|
| API (FastAPI) | `apps/backend/` | http://localhost:8000 |
| Web (React + Rsbuild) | `apps/web/` | http://localhost:3000 |

Semua langkah di bawah berjalan di **macOS, Linux, dan Windows**. Perintah dasarnya sama;
bila ada perbedaan antar sistem operasi, perbedaannya ditulis eksplisit.

### 0. Prasyarat

| Alat | Versi minimum | macOS / Linux | Windows |
|------|---------------|---------------|---------|
| Node.js | 20.x | `brew install node` · `nvm install 20` | `winget install OpenJS.NodeJS.LTS` · [nodejs.org](https://nodejs.org) |
| [uv](https://docs.astral.sh/uv/) | 0.11+ | `curl -LsSf https://astral.sh/uv/install.sh \| sh` · `brew install uv` | `winget install astral-sh.uv` · `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| Docker | opsional — lihat langkah 3 | Docker Desktop / Docker Engine | Docker Desktop |

Python tidak perlu dipasang manual: `uv` yang mengunduh dan mengelola Python 3.11.

Verifikasi prasyarat:

```
node -v
npm -v
uv --version
```

### 1. Siapkan variabel lingkungan

Dari root repo:

| Shell | Perintah |
|-------|----------|
| bash / zsh (macOS, Linux) | `cp apps/backend/.env.example apps/backend/.env` |
| PowerShell (Windows) | `Copy-Item apps\backend\.env.example apps\backend\.env` |
| Command Prompt (Windows) | `copy apps\backend\.env.example apps\backend\.env` |

Nilai bawaannya sudah cukup untuk berjalan lokal. `.env` tidak pernah di-commit.

### 2. Pasang dependensi (sekali saja)

**API** — dari root repo:

```
cd apps/backend
uv venv --python 3.11
uv pip install -e ".[dev]"
```

**Web** — dari root repo:

```
cd apps/web
npm install
```

> Di Windows gunakan `cd apps\backend` dan `cd apps\web`.
> Virtual environment tidak perlu diaktifkan manual — `uv run` sudah menanganinya.

### 3. Basis data (opsional — API tetap jalan tanpanya)

Backend memakai Postgres bila tersedia, dan **otomatis jatuh ke penyimpanan in-memory bila
tidak**. Fallback ini disengaja: demo harus bisa berjalan tanpa jaringan luar, dan tim frontend
bekerja tanpa Docker sama sekali. Tanpa basis data, 12 test integrasi akan `skip` — bukan gagal.

Nyalakan bila sedang mengerjakan lapisan persistensi, atau ingin menjalankan test integrasi:

```
docker compose up -d db          # Postgres 16 di localhost:5432
docker compose ps                # tunggu status "healthy"

cd apps/backend
uv run alembic upgrade head      # buat tabel ingestions & evidence_edges
```

> Port 5432 sering sudah dipakai instance Postgres lokal lain. Kalau `docker compose ps`
> menunjukkan container sehat tetapi koneksi ditolak dengan *password authentication failed*,
> yang menjawab adalah instance lain — hentikan instance itu, atau ubah pemetaan port di
> `docker-compose.yml` beserta `DATABASE_URL`.

Perintah Alembic yang sering dipakai, semuanya dari `apps/backend`:

| Keperluan | Perintah |
|-----------|----------|
| Terapkan semua migrasi | `uv run alembic upgrade head` |
| Lihat revisi terpasang | `uv run alembic current` |
| Buat migrasi dari perubahan tabel | `uv run alembic revision --autogenerate -m "pesan"` |
| Mundur satu revisi | `uv run alembic downgrade -1` |

URL basis data dibaca dari `app.config`, bukan dari `alembic.ini` — jadi layanan dan migrasinya
tidak mungkin menunjuk basis data yang berbeda. Jangan mengisi `sqlalchemy.url` di `alembic.ini`.

### 4. Jalankan kedua layanan

Pilih salah satu cara. **Cara A** adalah cara baku dan berjalan di semua sistem operasi.

#### Cara A — dua terminal (semua OS, tanpa alat tambahan)

Buka dua jendela/tab terminal. Keduanya dimulai dari root repo.

Terminal 1 — API:

```
cd apps/backend
uv run uvicorn app.main:app --reload --port 8000
```

Terminal 2 — Web:

```
cd apps/web
npm run dev
```

Biarkan kedua terminal terbuka selama pengembangan. Log tampil langsung di masing-masing
terminal, dan hot reload aktif di kedua layanan.

#### Cara B — satu sesi tmux (opsional; macOS, Linux, atau Windows via WSL)

Berguna bila ingin kedua proses tetap hidup setelah terminal ditutup. Membutuhkan
`tmux` (`brew install tmux` / `apt install tmux`).

```bash
ROOT=$(pwd)

tmux new-session -d -s tilik-klaim -n api -c "$ROOT/apps/backend"
tmux send-keys -t tilik-klaim:api 'uv run uvicorn app.main:app --reload --port 8000' C-m

tmux new-window -t tilik-klaim -n web -c "$ROOT/apps/web"
tmux send-keys -t tilik-klaim:web 'npm run dev' C-m
```

Mengoperasikan sesi:

```bash
tmux attach -t tilik-klaim                # masuk ke sesi
tmux capture-pane -p -t tilik-klaim:api   # baca log tanpa attach
tmux kill-session -t tilik-klaim          # hentikan kedua layanan
```

Di dalam sesi, prefix bawaan `Ctrl-b`: `0`/`1` pindah window, `d` detach,
`[` mode scroll log (`q` untuk keluar).

### 5. Verifikasi

Buka http://localhost:3000 dan http://localhost:8000/docs di peramban, atau dari terminal:

| Shell | Perintah |
|-------|----------|
| bash / zsh / PowerShell 6+ | `curl http://localhost:8000/healthz` |
| Windows PowerShell 5.1 | `Invoke-RestMethod http://localhost:8000/healthz` |

Balasan yang diharapkan:

```json
{"status":"ok","engine_version":"0.1.0","ruleset_version":"0.1.0","dataset_version":"unset","data_class":"synthetic"}
```

| Alamat | Isi |
|--------|-----|
| http://localhost:3000 | Antarmuka web — Antrean Review, Ingest/Demo, Audit & Evaluasi |
| http://localhost:8000/docs | OpenAPI (Swagger UI) |
| http://localhost:8000/healthz | Probe kesehatan + identitas engine/ruleset |

Catatan: pada sprint ini web belum memanggil API — keduanya masih berjalan mandiri.

### 6. Menghentikan

| Cara | Perintah |
|------|----------|
| Dua terminal | `Ctrl-C` di masing-masing terminal |
| tmux | `tmux kill-session -t tilik-klaim` |
| Basis data (jika dinyalakan) | `docker compose down` |

## Pengujian

Dari root repo:

```
cd apps/backend
uv run pytest        # unit + integrasi
```

```
cd apps/web
npm run typecheck    # pemeriksaan tipe
```

## Pemecahan masalah

| Gejala | Penyebab & solusi |
|--------|-------------------|
| `Address already in use` / `EADDRINUSE` di port 8000 atau 3000 | Proses lama masih hidup. macOS/Linux: `lsof -ti:8000 \| xargs kill`. Windows: `netstat -ano \| findstr :8000` lalu `taskkill /PID <pid> /F` |
| `uv: command not found` / `npm: command not found` | Terminal dibuka sebelum alat terpasang — tutup dan buka ulang terminal agar PATH termuat |
| `uv run` gagal dengan error impor | Dependensi belum terpasang atau terminal berada di folder yang salah — ulangi langkah 2 dari `apps/backend` |
| Peramban menampilkan halaman kosong di :3000 | Proses web belum selesai build — tunggu baris `ready built in ...` muncul di terminal |
| `docker compose up` gagal | Docker belum berjalan — nyalakan Docker Desktop (`open -a Docker`), atau lewati: API tetap jalan dengan penyimpanan in-memory |
| Test integrasi ter-`skip` | Tidak ada Postgres yang terjangkau. Jalankan `docker compose up -d db` lalu `uv run alembic upgrade head` |
| `password authentication failed for user "tilik"` | Ada Postgres lain di port 5432. Hentikan instance itu, atau ubah pemetaan port di `docker-compose.yml` dan `DATABASE_URL` |
| PowerShell menolak menjalankan skrip pemasangan | Jalankan sekali: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` |
| `error connecting to /tmp/tmux-*/default` | Hanya muncul pada Cara B saat belum ada server tmux — normal, `tmux new-session` akan menyalakannya |

## Mulai dari mana

Baca [`brief/00_OVERVIEW.md`](brief/00_OVERVIEW.md), lalu
[`sprint/01-sprint-planning.md`](sprint/01-sprint-planning.md) untuk sprint yang aktif.
