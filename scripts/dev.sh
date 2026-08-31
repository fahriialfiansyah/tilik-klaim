#!/usr/bin/env bash
#
# Menjalankan API (FastAPI) dan Web (Rsbuild) berdampingan dalam satu terminal.
# Ctrl-C menghentikan keduanya sekaligus — tidak ada proses yatim yang menahan port.
#
#   ./scripts/dev.sh              API + Web
#   ./scripts/dev.sh --db         Postgres (Docker) + migrasi, lalu API + Web
#   ./scripts/dev.sh --help       Semua opsi
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"
WITH_DB=0
SKIP_INSTALL=0

# Warna hanya bila stdout adalah terminal, supaya `./scripts/dev.sh > log.txt` tetap bersih.
if [ -t 1 ]; then
  C_API=$'\033[36m'; C_WEB=$'\033[35m'; C_RUN=$'\033[32m'; C_ERR=$'\033[31m'; C_OFF=$'\033[0m'
else
  C_API=''; C_WEB=''; C_RUN=''; C_ERR=''; C_OFF=''
fi

usage() {
  cat <<'USAGE'
Penggunaan: ./scripts/dev.sh [opsi]

  --db              Nyalakan Postgres via Docker Compose lalu jalankan `alembic upgrade head`
                    sebelum kedua layanan hidup. Tanpa ini backend memakai penyimpanan in-memory.
  --skip-install    Jangan jalankan `npm install` walau node_modules belum ada.
  --api-port PORT   Port API (bawaan 8000, atau env API_PORT).
  --web-port PORT   Port Web (bawaan 3000, atau env WEB_PORT).
  -h, --help        Tampilkan bantuan ini.
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --db) WITH_DB=1; shift ;;
    --skip-install) SKIP_INSTALL=1; shift ;;
    --api-port) API_PORT="${2:?--api-port butuh nilai}"; shift 2 ;;
    --web-port) WEB_PORT="${2:?--web-port butuh nilai}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) printf '%sOpsi tidak dikenal: %s%s\n\n' "$C_ERR" "$1" "$C_OFF" >&2; usage >&2; exit 2 ;;
  esac
done

log()  { printf '%s[dev]%s %s\n' "$C_RUN" "$C_OFF" "$1"; }
fail() { printf '%s[dev]%s %s\n' "$C_ERR" "$C_OFF" "$1" >&2; exit 1; }

# --- Prasyarat -------------------------------------------------------------

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "\`$1\` tidak ditemukan. $2"
}
require_cmd uv  "Pasang dengan: curl -LsSf https://astral.sh/uv/install.sh | sh"
require_cmd npm "Pasang Node.js 20+: https://nodejs.org"

port_owner() { lsof -nP -iTCP:"$1" -sTCP:LISTEN -t 2>/dev/null | head -1; }

# Kedua port diperiksa sekaligus, lalu dilaporkan bersama. Berhenti pada konflik pertama
# memaksa menebak satu per satu — dan pesan yang menyebut port lain mudah disangka
# "semua port dipakai", padahal yang bentrok cuma satu.
CONFLICTS=""
check_port() {
  local port=$1 label=$2 pid owner
  pid="$(port_owner "$port")" || true
  [ -z "$pid" ] && return 0
  owner="$(ps -p "$pid" -o comm= 2>/dev/null | sed 's|.*/||' || true)"
  [ -z "$owner" ] && owner="proses tak dikenal"
  CONFLICTS="${CONFLICTS}  • port ${port} — dipakai ${label} lain: PID ${pid} (${owner})
    lepaskan: kill ${pid}   ·   atau pakai port lain: --${label}-port <PORT>
"
}
check_port "$API_PORT" api
check_port "$WEB_PORT" web

if [ -n "$CONFLICTS" ]; then
  printf '%s[dev]%s Tidak bisa mulai — port berikut sudah terpakai:\n%s' "$C_ERR" "$C_OFF" "$CONFLICTS" >&2
  printf '%s[dev]%s Port lain sudah dicek dan bebas; hanya yang tercantum di atas yang bentrok.\n' "$C_ERR" "$C_OFF" >&2
  printf '%s[dev]%s Biang keroknya biasanya server dev dari terminal lama yang sudah ditutup.\n' "$C_ERR" "$C_OFF" >&2
  exit 1
fi

# --- Persiapan opsional ----------------------------------------------------

if [ "$WITH_DB" -eq 1 ]; then
  require_cmd docker "Pasang Docker Desktop: https://docker.com"
  log "Menyalakan Postgres…"
  ( cd "$ROOT" && docker compose up -d --wait db )
  log "Menerapkan migrasi Alembic…"
  ( cd "$ROOT/apps/backend" && uv run alembic upgrade head )
fi

if [ "$SKIP_INSTALL" -eq 0 ] && [ ! -d "$ROOT/apps/web/node_modules" ]; then
  log "node_modules belum ada — menjalankan npm install…"
  ( cd "$ROOT/apps/web" && npm install )
fi

# --- Menjalankan kedua layanan ---------------------------------------------

# `set -m` membuat tiap job latar mendapat process group sendiri, sehingga satu `kill`
# pada PGID menjangkau seluruh anaknya (uvicorn --reload dan Rsbuild sama-sama fork).
set -m

run_service() {
  local name=$1 color=$2 dir=$3; shift 3
  set +m  # anak-anak di dalam subshell ini tetap satu process group dengan subshell-nya
  cd "$dir"
  "$@" 2>&1 | while IFS= read -r line; do
    printf '%s[%s]%s %s\n' "$color" "$name" "$C_OFF" "$line"
  done
}

run_service api "$C_API" "$ROOT/apps/backend" \
  uv run uvicorn app.main:app --reload --port "$API_PORT" &
API_PGID=$!

run_service web "$C_WEB" "$ROOT/apps/web" \
  npm run dev -- --port "$WEB_PORT" &
WEB_PGID=$!

set +m

SHUTTING_DOWN=0
shutdown() {
  [ "$SHUTTING_DOWN" -eq 1 ] && return 0
  SHUTTING_DOWN=1
  trap - INT TERM EXIT

  # Bash mengumumkan kematian job ke stderr-nya sendiri ("Terminated: 15"), asinkron dan
  # tak bisa ditekan lewat trap. Bungkam stderr shell selama pembunuhan, lalu pulihkan.
  exec 3>&2 2>/dev/null

  printf '\n'
  log "Menghentikan kedua layanan…"
  for pgid in "$API_PGID" "$WEB_PGID"; do
    kill -TERM -- "-$pgid" 2>/dev/null || true
  done
  # Beri waktu shutdown rapi, lalu paksa apa pun yang masih bertahan.
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    kill -0 -- "-$API_PGID" 2>/dev/null || kill -0 -- "-$WEB_PGID" 2>/dev/null || break
    sleep 0.5
  done
  for pgid in "$API_PGID" "$WEB_PGID"; do
    kill -KILL -- "-$pgid" 2>/dev/null || true
  done

  exec 2>&3 3>&-
  log "Selesai."
}

# Ctrl-C dan SIGTERM adalah penghentian yang disengaja: matikan layanan lalu keluar bersih,
# tanpa jatuh kembali ke loop pengawas yang akan salah melaporkannya sebagai crash.
on_signal() { shutdown; exit 0; }
trap on_signal INT TERM
trap shutdown EXIT

log "API  → http://localhost:$API_PORT  (dokumen: http://localhost:$API_PORT/docs)"
log "Web  → http://localhost:$WEB_PORT"
log "Ctrl-C untuk menghentikan keduanya."

# Bila salah satu layanan mati, hentikan yang lain — separuh stack lebih membingungkan
# daripada stack yang mati seluruhnya. `wait -n` tidak dipakai: tidak ada di bash 3.2 (macOS).
while true; do
  api_dead=0; web_dead=0
  kill -0 "$API_PGID" 2>/dev/null || api_dead=1
  kill -0 "$WEB_PGID" 2>/dev/null || web_dead=1
  if [ "$api_dead" -eq 1 ] || [ "$web_dead" -eq 1 ]; then
    # Laporkan yang benar-benar mati; keduanya bisa jatuh dalam siklus yang sama.
    if [ "$api_dead" -eq 1 ]; then
      printf '%s[dev]%s API berhenti tak terduga — cek log [api] di atas.\n' "$C_ERR" "$C_OFF" >&2
    fi
    if [ "$web_dead" -eq 1 ]; then
      printf '%s[dev]%s Web berhenti tak terduga — cek log [web] di atas.\n' "$C_ERR" "$C_OFF" >&2
    fi
    exit 1
  fi
  sleep 1
done
