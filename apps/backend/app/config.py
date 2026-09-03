"""Runtime configuration. Values come from the environment; nothing is hardcoded."""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PSYCOPG_SCHEME = "postgresql+psycopg://"
"""SQLAlchemy memilih driver dari skema URL, dan psycopg3 yang dipasang proyek ini."""

_UNNAMED_DRIVER_SCHEMES = ("postgresql://", "postgres://")
"""Bentuk URL yang dibagikan penyedia terkelola — tanpa nama driver di dalamnya."""


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://tilik:tilik@localhost:5432/tilik_klaim"

    # Peramban menolak jawaban lintas-origin yang tidak disebut namanya oleh API. Web dan API
    # berjalan di host berbeda saat di-deploy, jadi daftar ini adalah konfigurasi — bukan `*`,
    # yang akan mengizinkan situs mana pun memanggil API ini atas nama peninjau.
    cors_allow_origins: str = "http://localhost:3000"
    # Vercel memberi URL baru untuk setiap preview deployment, sehingga daftar tetap di atas
    # tidak pernah cukup untuk preview. Kosong secara bawaan: pola longgar yang tidak sengaja
    # tertinggal lebih berbahaya daripada preview yang harus didaftarkan manual.
    cors_allow_origin_regex: str = ""

    # Engine identity. Every case and audit event records these, so a result can always
    # be traced back to the exact rules and model that produced it.
    engine_version: str = "0.1.0"
    ruleset_version: str = "0.1.0"
    dataset_version: str = "unset"

    # Ingestion limits (docs/canonical/03_architecture.md § Security and observability).
    max_bundle_bytes: int = 8 * 1024 * 1024
    max_json_depth: int = 32

    # Where the offline evaluation runner writes its artifacts. The API only ever reads them —
    # a metric is produced by `evaluation/runner`, deliberately by an engineer, never by a
    # request. Relative paths resolve against the repository root.
    evaluation_artifacts_dir: str = "evaluation/artifacts"

    # The bounded, read-only Case Briefing (ADR-0005). **Off by default**: the demo runbook
    # forbids depending on a remote LLM, and with this off — or with no key or model — the
    # endpoint answers with the deterministic template, which is not an error. Any
    # OpenAI-compatible chat-completions gateway works; OpenRouter is the default host.
    briefing_enabled: bool = False
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = ""
    openrouter_api_key: str = ""
    briefing_timeout_seconds: float = 20.0
    briefing_max_tool_calls: int = 8
    briefing_max_output_tokens: int = 900

    @field_validator("database_url")
    @classmethod
    def name_the_driver(cls, value: str) -> str:
        """Menyebut driver secara eksplisit pada URL yang tidak menyebutkannya.

        Penyedia Postgres terkelola (Railway, Render, Supabase) membagikan `postgresql://`
        atau `postgres://`, dan SQLAlchemy membaca keduanya sebagai psycopg2 — paket yang
        tidak dipasang proyek ini, sehingga koneksi gagal dengan galat yang menunjuk ke
        arah yang salah. Penulisan ulang terjadi di sini, mengembalikan string baru dan
        tidak pernah mengubah nilai asal, supaya URL yang dirotasi platform tetap dipakai
        apa adanya tanpa salinan hasil suntingan tangan yang bisa basi.
        """
        for scheme in _UNNAMED_DRIVER_SCHEMES:
            if value.startswith(scheme):
                return PSYCOPG_SCHEME + value[len(scheme) :]
        return value

    @property
    def cors_origins(self) -> tuple[str, ...]:
        """`CORS_ALLOW_ORIGINS` dipecah menjadi origin-origin tepat.

        Dibaca sebagai satu string yang dipisah koma, bukan `list[str]`: pydantic-settings
        menuntut JSON untuk tipe daftar, dan sebuah kotak isian variabel lingkungan di
        dasbor Railway adalah tempat paling mudah untuk salah menulis JSON.
        """
        return tuple(origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
