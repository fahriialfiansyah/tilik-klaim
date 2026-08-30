"""Runtime configuration. Values come from the environment; nothing is hardcoded."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://tilik:tilik@localhost:5432/tilik_klaim"

    # Engine identity. Every case and audit event records these, so a result can always
    # be traced back to the exact rules and model that produced it.
    engine_version: str = "0.1.0"
    ruleset_version: str = "0.1.0"
    dataset_version: str = "unset"

    # Ingestion limits (docs/canonical/03_architecture.md § Security and observability).
    max_bundle_bytes: int = 8 * 1024 * 1024
    max_json_depth: int = 32


@lru_cache
def get_settings() -> Settings:
    return Settings()
