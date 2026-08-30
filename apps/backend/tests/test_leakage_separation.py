"""The demo scenario label must be structurally unreachable from detector features.

WS-001 acceptance: *injector-only fields absent from features*. The strongest form of that
guarantee is not a filter someone must remember to apply — it is a model in which the answer
key was never reachable in the first place.
"""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError
from tilik_domain.canonical import CanonicalBundle

from tests.fixtures import GOLD_DIR, SCENARIOS, load, load_all

LEAKY_TERMS = ("scenario", "label", "expected", "injection", "injector", "difficulty")


def _field_names(schema: dict) -> set[str]:
    """Every property name in a JSON schema, including nested `$defs`."""
    names: set[str] = set()
    for definition in (schema, *schema.get("$defs", {}).values()):
        names.update(definition.get("properties", {}).keys())
    return names


def test_canonical_bundle_has_no_scenario_or_label_field() -> None:
    """The bundle type carries no answer-key *field*, at any nesting depth.

    Checks property names only. Matching against the whole serialized schema would also
    match prose in the docstrings that explain this very rule.
    """
    names = _field_names(CanonicalBundle.model_json_schema())
    leaky = {name for name in names if any(term in name.lower() for term in LEAKY_TERMS)}
    assert not leaky, f"CanonicalBundle exposes leaky field(s): {sorted(leaky)}"
    assert "bundle_id" in names, "sanity check: field names were actually collected"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_bundle_payload_contains_no_answer_key(scenario: str) -> None:
    """The serialized bundle — what a detector actually reads — carries no answer key."""
    raw = json.loads((GOLD_DIR / f"{scenario}.json").read_text(encoding="utf-8"))
    bundle_text = json.dumps(raw["bundle"]).lower()
    for term in LEAKY_TERMS:
        assert term not in bundle_text, f"{scenario} bundle payload leaks {term!r}"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_answer_key_lives_outside_the_bundle(scenario: str) -> None:
    """Present in the fixture wrapper, absent from the bundle. Both halves matter."""
    raw = json.loads((GOLD_DIR / f"{scenario}.json").read_text(encoding="utf-8"))
    assert "demo" in raw and "expected_reason_codes" in raw
    assert "demo" not in raw["bundle"]
    assert "expected_reason_codes" not in raw["bundle"]


def test_bundle_rejects_injected_extra_fields() -> None:
    """`extra="forbid"` means a leaky field cannot be smuggled in at runtime either."""
    fixture = load("phantom")
    payload = json.loads(fixture.bundle.model_dump_json())
    payload["scenario_label"] = "Tagihan tanpa bukti tindakan"
    with pytest.raises(ValidationError):
        CanonicalBundle.model_validate(payload)


def test_demo_metadata_is_not_a_bundle_member() -> None:
    """DemoMetadata is a sibling of the bundle, never a field on it."""
    assert "demo" not in CanonicalBundle.model_fields
    assert "scenario_label" not in CanonicalBundle.model_fields
    for fixture in load_all():
        assert fixture.demo.bundle_id == fixture.bundle.bundle_id
