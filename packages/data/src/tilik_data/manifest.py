"""The generation manifest: what was produced, from what, and by which version.

Written beside every corpus so a result months later can be traced to the exact inputs that
produced it. `docs/canonical/03_architecture.md` requires that provenance; without it a reported
metric is a number with no way to check it.
"""
from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict

GENERATOR_VERSION = "0.1.0"


class Manifest(BaseModel):
    """Everything needed to reproduce and audit one generation run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    generator_version: str = GENERATOR_VERSION
    seed: int
    corpus_hash: str
    """Digest over the whole corpus. Re-running with this seed must reproduce it."""

    bundles: int
    participants: int
    providers: int

    injections: int
    injections_by_mode: dict[str, int]
    multi_label_ratio: float

    train: int
    validation: int
    test: int
    excluded_demo: int
    test_set_digest: str
    """Recorded when the test set was frozen, so a later change to it is detectable."""

    leakage_margin: float
    leakage_passed: bool

    generated_at: str = ""

    @classmethod
    def stamped(cls, **values: object) -> Manifest:
        """Build with a generation timestamp.

        The timestamp is metadata about the *run*, never an input to generation — nothing in the
        corpus depends on it, which is what keeps the output reproducible.
        """
        return cls(generated_at=datetime.now(UTC).isoformat(), **values)  # type: ignore[arg-type]
