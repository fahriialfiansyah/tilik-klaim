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

```bash
# Basis data lokal
docker compose up -d db

# API  → http://localhost:8000  (docs di /docs, probe di /healthz)
cd apps/backend && uv venv --python 3.11 && uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload

# Web  → http://localhost:3000
cd apps/web && npm install && npm run dev
```

## Pengujian

```bash
cd apps/backend && uv run pytest        # unit + integrasi
cd apps/web && npm run typecheck        # pemeriksaan tipe
```

## Mulai dari mana

Baca [`brief/00_OVERVIEW.md`](brief/00_OVERVIEW.md), lalu
[`sprint/01-sprint-planning.md`](sprint/01-sprint-planning.md) untuk sprint yang aktif.
