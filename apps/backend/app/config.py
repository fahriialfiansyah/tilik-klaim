"""Runtime configuration. Values come from the environment; nothing is hardcoded."""
from functools import lru_cache

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PLACEHOLDER_KEYS = frozenset({"dummy", "changeme", "eb-replace-with-your-key", "your-key-here"})
"""Key-shaped values that pass an eye check and become a 401 later. Refused at start-up."""

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

    # The bounded, read-only Case Briefing (ADR-0005), served by the internal vLLM gateway.
    #
    # **Off by default, and nothing below is required while it is off.** ADR-0002 says the MVP
    # does not require an LLM and § 22 *Demo reliability* says never to depend on a remote one,
    # so an unconfigured service starts perfectly well and answers with the template.
    #
    # The moment it is switched on, all three values must be present and well formed —
    # `docs/VLLM-SETUP.md` § 3: a secret with a default lets a service start healthy and fail at
    # the first call, which moves the failure from deploy hour to demo hour. The check below
    # runs at settings construction, i.e. at import, i.e. at start-up.
    #
    # **No default for the address or the key.** A gateway address is a deployment fact, not a
    # program constant, and neither it nor the key may appear in a committed file — they live in
    # `apps/backend/.env` (gitignored) and are documented in `docs/VLLM-SETUP.md`.
    briefing_enabled: bool = False
    llm_model_vllm: str = ""
    vllm_base_url: str = ""
    vllm_api_key: SecretStr = SecretStr("")
    # Ninety seconds, not twenty: a closed port on the gateway host DROPS packets rather than
    # refusing them, so a request hangs for the full timeout instead of failing fast, and a
    # healthy extraction on a larger model genuinely exceeds a shorter bound.
    briefing_timeout_seconds: float = 90.0
    briefing_max_tool_calls: int = 8
    # Room for the largest legal answer, plus the whitespace the model pads after closing the
    # object. That padding is harmless — the provider parses before it judges the finish reason
    # — but it is charged here, so this is deliberately generous. Measured: a real answer is
    # 450–900 tokens; anything above that is padding, and cutting the budget to fit the content
    # cut real objects open instead.
    briefing_max_output_tokens: int = 3000
    # **The single biggest lever measured on this gateway.** Qwen3.5 is a hybrid reasoning
    # model: left on, it spent ~3,500 hidden thinking tokens that vLLM strips from the content
    # but still charges against `max_tokens`, so a complete 2,300-character answer arrived
    # truncated after 43s. Off, the same case answered in 6.5s using 456 tokens. Summarising
    # already-gathered evidence under a schema is not a reasoning task.
    briefing_enable_thinking: bool = False
    briefing_temperature: float = 0.1
    # Zero, not the guide's two. **The template fallback is the retry.** With a 90-second
    # timeout, two retries put one call at four and a half minutes, and this panel is on-demand
    # in front of a reviewer — a briefing that arrives after the decision is worse than one that
    # never came. Observed: a run stalled past three minutes in validation because of this.
    briefing_max_retry: int = 0
    # Wall-clock budget for the whole run, reads included. Any single call is bounded by the
    # timeout above; without this, eight reads plus a submission are not bounded by anything.
    briefing_deadline_seconds: float = 120.0

    @field_validator("vllm_base_url")
    @classmethod
    def end_at_v1(cls, value: str) -> str:
        """`/v1` is not decoration.

        The OpenAI client appends `/chat/completions` to this string verbatim, so a base URL
        missing `/v1` produces a 404 that reads exactly like a model that does not exist —
        `docs/VLLM-SETUP.md` § 1. Trailing slashes are trimmed so the join never doubles one.
        """
        trimmed = value.strip().rstrip("/")
        if trimmed and not trimmed.endswith("/v1"):
            raise ValueError(f"VLLM_BASE_URL must end with /v1, got: {trimmed}")
        return trimmed

    @model_validator(mode="after")
    def gateway_is_complete_when_enabled(self) -> "Settings":
        """Everything the gateway needs, checked once, at start-up — and only when it is on."""
        if not self.briefing_enabled:
            return self

        missing = [
            name
            for name, value in (
                ("LLM_MODEL_VLLM", self.llm_model_vllm.strip()),
                ("VLLM_BASE_URL", self.vllm_base_url.strip()),
                ("VLLM_API_KEY", self.vllm_api_key.get_secret_value().strip()),
            )
            if not value
        ]
        if missing:
            raise ValueError(
                f"BRIEFING_ENABLED is true but {', '.join(missing)} is empty. "
                "Set them in apps/backend/.env, or set BRIEFING_ENABLED=false to run on the "
                "deterministic template."
            )
        # Never interpolate the key into the message: this text reaches logs and tracebacks.
        if self.vllm_api_key.get_secret_value().strip() in PLACEHOLDER_KEYS:
            raise ValueError(
                "VLLM_API_KEY is still a placeholder. The gateway answers 'Upstream "
                "unreachable.' for a missing credential — an error that reads like a dead server."
            )
        return self

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
