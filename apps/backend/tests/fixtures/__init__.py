"""Gold fixture loading for tests."""
from __future__ import annotations

import json
import pathlib

from pydantic import BaseModel, ConfigDict

from tilik_domain.canonical import CanonicalBundle, DemoMetadata
from tilik_domain.reasons import ReasonCode

GOLD_DIR = pathlib.Path(__file__).parent / "gold"
SCENARIOS = ("clean", "phantom", "repeat", "clone", "unbundled")


class GoldFixture(BaseModel):
    """A curated scenario plus its answer key.

    `demo` and `expected_reason_codes` sit here, outside `CanonicalBundle`, so nothing the
    detector reads can reach them.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    scenario: str
    demo: DemoMetadata
    history: tuple[CanonicalBundle, ...]
    bundle: CanonicalBundle
    expected_reason_codes: tuple[ReasonCode, ...]
    expected_evidence_complete: bool


def load(scenario: str) -> GoldFixture:
    path = GOLD_DIR / f"{scenario}.json"
    return GoldFixture.model_validate(json.loads(path.read_text(encoding="utf-8")))


def load_all() -> tuple[GoldFixture, ...]:
    return tuple(load(name) for name in SCENARIOS)
