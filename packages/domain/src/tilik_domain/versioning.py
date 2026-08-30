"""Version identity carried by every derived artifact.

`docs/canonical/03_architecture.md` requires that a result can always be traced back to the
exact schema, rules, and model that produced it. Historical results keep the version that was
in force when they were produced — they are never re-interpreted under a newer ruleset.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "0.1.0"
RULESET_VERSION = "0.1.0"
ENGINE_VERSION = "0.1.0"


class EngineIdentity(BaseModel):
    """Stamped onto every case, reason, edge, and audit event."""

    model_config = ConfigDict(frozen=True)

    schema_version: str = Field(default=SCHEMA_VERSION)
    ruleset_version: str = Field(default=RULESET_VERSION)
    engine_version: str = Field(default=ENGINE_VERSION)
    dataset_version: str = Field(default="unset")

    def as_label(self) -> str:
        """Compact form for UI version badges."""
        return (
            f"schema {self.schema_version} · rules {self.ruleset_version} "
            f"· engine {self.engine_version} · data {self.dataset_version}"
        )
