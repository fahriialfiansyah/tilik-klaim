#!/bin/sh
#
# Entrypoint kontainer. Menerapkan migrasi lebih dulu bila ada basis data, lalu menyerahkan
# PID 1 ke uvicorn supaya sinyal berhenti dari platform sampai ke server, bukan ke shell.
set -eu

# Kuncinya variabel lingkungan, bukan `settings.database_url` — nilai bawaan setting menunjuk
# localhost, yang di dalam kontainer selalu ada tetapi tidak pernah menjawab. Membedakan
# keduanya di sini yang membuat "tanpa basis data" menjadi mode sah, bukan crash saat start.
if [ -n "${DATABASE_URL:-}" ]; then
  echo "[start] DATABASE_URL terpasang — menerapkan migrasi Alembic…"
  # Tanpa `set -e` yang menggigit di sini, migrasi gagal akan lolos diam-diam dan API
  # menyajikan skema yang salah. Lebih baik deploy ditolak.
  alembic upgrade head
  echo "[start] Migrasi selesai."
else
  echo "[start] DATABASE_URL kosong — API berjalan dengan penyimpanan in-memory."
  echo "[start] Data hilang setiap kali kontainer di-restart. Ini normal untuk demo tanpa DB."
fi

echo "[start] uvicorn mendengarkan di 0.0.0.0:${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
