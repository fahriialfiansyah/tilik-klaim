"""vLLM gateway configuration — validated at start-up, and only when it is switched on.

Two rules meet here and neither gives way.

`docs/VLLM-SETUP.md` § 3: a secret with a default lets an app start healthy and fail at the
first call — demo hour rather than deploy hour. So configuration failure belongs at start-up.

`docs/canonical/decisions/ADR-0002` and § 22 *Demo reliability*: the MVP does not require an
LLM and the demo must never depend on a remote one. So an **unconfigured** service must start
perfectly well and answer with the deterministic template.

The reconciliation is the switch: with `BRIEFING_ENABLED=false` nothing is required and nothing
is checked; the moment it is `true`, all three vLLM values must be present and well formed, and
a bad one stops the process at import rather than at a reviewer's first click.
"""
from __future__ import annotations

import pytest
from pydantic import SecretStr, ValidationError

from app.config import Settings

GOOD = {
    "briefing_enabled": "true",
    "llm_model_vllm": "Qwen3.5-9B",
    "vllm_base_url": "http://gateway.invalid:9999/v1",
    "vllm_api_key": "a-real-looking-key",
}


def _settings(**overrides: str) -> Settings:
    return Settings(_env_file=None, **{**GOOD, **overrides})


# ---- off by default -----------------------------------------------------------------------


def test_the_briefing_is_off_and_needs_nothing_configured() -> None:
    """The canonical default. No key, no model, no gateway — and the service still starts."""
    settings = Settings(_env_file=None)
    assert settings.briefing_enabled is False
    assert settings.llm_model_vllm == ""
    assert settings.vllm_base_url == ""
    assert settings.vllm_api_key.get_secret_value() == ""


def test_no_gateway_address_is_baked_into_the_code() -> None:
    """§ 8: an infrastructure address is not a program constant.

    A default here means a deployment that forgot to configure one starts anyway and points at
    somebody else's host. It also means the address ships in the repository, which is exactly
    what this project was told not to do.
    """
    assert Settings(_env_file=None).vllm_base_url == ""


@pytest.mark.parametrize("field", ["llm_model_vllm", "vllm_base_url", "vllm_api_key"])
def test_enabling_the_briefing_without_all_three_values_refuses_to_start(field: str) -> None:
    with pytest.raises(ValidationError) as refused:
        _settings(**{field: ""})
    assert "BRIEFING_ENABLED" in str(refused.value)


# ---- the base URL -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "given,expected",
    [
        ("http://gateway.invalid:9999/v1", "http://gateway.invalid:9999/v1"),
        ("http://gateway.invalid:9999/v1/", "http://gateway.invalid:9999/v1"),
        ("http://gateway.invalid:9999/v1///", "http://gateway.invalid:9999/v1"),
    ],
)
def test_a_trailing_slash_is_trimmed_rather_than_doubled(given: str, expected: str) -> None:
    assert _settings(vllm_base_url=given).vllm_base_url == expected


def test_a_base_url_without_v1_is_refused_with_the_reason(pytestconfig) -> None:
    """§ 1: the client appends `/chat/completions` verbatim, so a missing `/v1` is a 404 that
    reads like a missing model — an hour lost to the wrong hypothesis."""
    with pytest.raises(ValidationError) as refused:
        _settings(vllm_base_url="http://gateway.invalid:9999")
    assert "/v1" in str(refused.value)


# ---- the key ------------------------------------------------------------------------------


@pytest.mark.parametrize("placeholder", ["dummy", "changeme", "eb-replace-with-your-key", "  "])
def test_a_placeholder_key_is_refused(placeholder: str) -> None:
    """A key-shaped placeholder passes an eye check and becomes a 401 in production."""
    with pytest.raises(ValidationError):
        _settings(vllm_api_key=placeholder)


def test_the_key_never_appears_in_repr_or_in_a_validation_error() -> None:
    """`SecretStr`, so the key stays out of logs, tracebacks and error reporting."""
    settings = _settings(vllm_api_key="super-secret-value")
    assert "super-secret-value" not in repr(settings)
    assert "super-secret-value" not in str(settings.model_dump())
    assert settings.vllm_api_key.get_secret_value() == "super-secret-value"

    with pytest.raises(ValidationError) as refused:
        _settings(vllm_api_key="super-secret-value", vllm_base_url="http://no-v1.invalid")
    assert "super-secret-value" not in str(refused.value)


def test_the_key_is_a_secret_str_not_a_plain_string() -> None:
    assert isinstance(_settings().vllm_api_key, SecretStr)


# ---- the committed contract ---------------------------------------------------------------


def test_no_committed_file_carries_a_gateway_address_or_a_key() -> None:
    """The owner's instruction, asserted rather than remembered.

    `.env.example` is committed, so it documents the *names* and leaves both the address and the
    key empty. `docs/VLLM-SETUP.md` holds the real address and is gitignored.
    """
    import pathlib
    import re

    example = pathlib.Path(__file__).resolve().parents[1] / ".env.example"
    text = example.read_text(encoding="utf-8")

    assert "VLLM_BASE_URL=\n" in text or text.rstrip().endswith("VLLM_BASE_URL=")
    assert re.search(r"^VLLM_API_KEY=\s*$", text, re.MULTILINE), "the key must be left empty"
    assert not re.search(r"VLLM_BASE_URL=\S", text), "no address may be committed"
    assert not re.search(r"\b\d{1,3}(\.\d{1,3}){3}\b", text), "no gateway IP may be committed"
