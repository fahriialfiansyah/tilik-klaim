# Konteks build adalah ROOT REPO, bukan apps/backend: API mengimpor `tilik_domain` dari
# packages/domain/, jadi konteks yang berakar di apps/backend tidak bisa melihat
# dependensinya sendiri. Di Railway: Root Directory = "/" dan Dockerfile Path =
# "apps/backend/Dockerfile".
FROM python:3.11-slim

# uv disalin dari image resminya, bukan dipasang lewat pip: resolver yang sama dengan yang
# dipakai tim di lokal, dan tidak meninggalkan toolchain build di dalam layer runtime.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH

WORKDIR /srv
RUN uv venv "$VIRTUAL_ENV"

# `tilik-domain` belum tercatat sebagai dependensi di apps/backend/pyproject.toml, jadi
# keduanya dipasang eksplisit di sini. Urutannya penting: domain lebih dulu, API menyusul.
COPY packages/domain packages/domain
COPY apps/backend apps/backend
RUN uv pip install --no-cache ./packages/domain ./apps/backend

WORKDIR /srv/apps/backend

# Railway menyuntikkan PORT sendiri; nilai bawaan ini menjaga `docker run -p 8000:8000`
# tetap bekerja di laptop.
ENV PORT=8000
EXPOSE 8000

CMD ["./scripts/start.sh"]
