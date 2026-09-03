"""The vLLM client: which failure maps to which fix, and what gets recorded.

No network. Every gateway answer is constructed, because the point of these tests is the
translation layer — a 404 and a 401 need different repairs, and `except Exception` would flatten
them into one unactionable support ticket (`docs/VLLM-SETUP.md` § 4).
"""
from __future__ import annotations

import httpx
import pytest
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    RateLimitError,
)

from app.service.llm_provider import (
    LlmUnavailable,
    ToolCallsUnsupported,
    VllmProvider,
)

MODEL = "Qwen3.5-9B"
TIMEOUT = 90.0


def _provider() -> VllmProvider:
    return VllmProvider(
        base_url="http://gateway.invalid:9999/v1",
        api_key="a-real-looking-key",
        model=MODEL,
        timeout_seconds=TIMEOUT,
        max_output_tokens=900,
        temperature=0.1,
        max_retries=0,
    )


def _api_error(cls, status: int, message: str):
    request = httpx.Request("POST", "http://gateway.invalid:9999/v1/chat/completions")
    response = httpx.Response(status, request=request, json={"error": {"message": message}})
    return cls(message, response=response, body=None)


class _Message:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls


class _Choice:
    def __init__(self, message, finish_reason="stop"):
        self.message = message
        self.finish_reason = finish_reason


class _Response:
    def __init__(self, model, choices):
        self.model = model
        self.choices = choices


def _raises(provider, error, *, structured=False):
    def explode(**_kwargs):
        raise error

    provider._client.chat.completions.create = explode
    if structured:
        return provider.complete_structured([], "S", {"type": "object"})
    return provider.complete([], [])


# ---- one exception class per fix ----------------------------------------------------------


def test_a_missing_model_names_the_setting_to_change() -> None:
    with pytest.raises(LlmUnavailable) as failure:
        _raises(_provider(), _api_error(NotFoundError, 404, "Model 'X' not found."))
    assert "LLM_MODEL_VLLM" in str(failure.value)
    assert MODEL in str(failure.value)


def test_a_rejected_key_names_the_key_and_never_prints_it() -> None:
    with pytest.raises(LlmUnavailable) as failure:
        _raises(_provider(), _api_error(AuthenticationError, 401, "Invalid API key."))
    assert "VLLM_API_KEY" in str(failure.value)
    assert "a-real-looking-key" not in str(failure.value)


def test_rate_limiting_is_reported_as_itself() -> None:
    with pytest.raises(LlmUnavailable) as failure:
        _raises(_provider(), _api_error(RateLimitError, 429, "Too many requests."))
    assert "rate limit" in str(failure.value).lower()


@pytest.mark.parametrize("cls", [APITimeoutError, APIConnectionError])
def test_an_unreachable_gateway_names_the_timeout_and_the_address_setting(cls) -> None:
    """A closed port on the gateway host hangs rather than refusing, so the message has to say
    'did not answer within N seconds' — otherwise it reads as a slow model."""
    request = httpx.Request("POST", "http://gateway.invalid:9999/v1/chat/completions")
    with pytest.raises(LlmUnavailable) as failure:
        _raises(_provider(), cls(request=request))
    assert "90" in str(failure.value)
    assert "VLLM_BASE_URL" in str(failure.value)


# ---- tool calling is a capability, not an outage ------------------------------------------


def test_a_gateway_without_tool_calling_is_told_apart_from_a_broken_one() -> None:
    """vLLM serves tools only with `--enable-auto-tool-choice`. A gateway started without it
    refuses the request *shape*, which is a different thing from being down — and the caller
    answers it by reading deterministically instead of giving up."""
    with pytest.raises(ToolCallsUnsupported):
        _raises(
            _provider(),
            _api_error(BadRequestError, 400, "tool calling is not supported by this server"),
        )


def test_an_unrelated_bad_request_is_not_mistaken_for_a_missing_capability() -> None:
    with pytest.raises(LlmUnavailable) as failure:
        _raises(_provider(), _api_error(BadRequestError, 400, "context length exceeded"))
    assert not isinstance(failure.value, ToolCallsUnsupported)


# ---- what gets recorded --------------------------------------------------------------------


def test_the_model_that_answered_is_recorded_not_the_one_requested(caplog) -> None:
    """§ 8: the gateway substitutes models silently. An audit that reads configuration records
    something that did not happen."""
    provider = _provider()
    provider._client.chat.completions.create = lambda **_k: _Response(
        "Qwen3.6-27B", [_Choice(_Message(content="ok"))]
    )
    turn = provider.complete([], [])
    assert turn.served_model == "Qwen3.6-27B"
    assert "substituted" in caplog.text
    assert "Qwen3.6-27B" in caplog.text


def test_no_warning_when_the_gateway_served_what_was_asked(caplog) -> None:
    provider = _provider()
    provider._client.chat.completions.create = lambda **_k: _Response(
        MODEL, [_Choice(_Message(content="ok"))]
    )
    assert provider.complete([], []).served_model == MODEL
    assert "substituted" not in caplog.text


def test_unparseable_tool_arguments_become_an_empty_dict_not_a_crash() -> None:
    """The registry reports the argument error back to the model, which can correct itself."""

    class _Fn:
        name = "get_timeline"
        arguments = "{not json"

    class _Call:
        id = "1"
        function = _Fn()

    provider = _provider()
    provider._client.chat.completions.create = lambda **_k: _Response(
        MODEL, [_Choice(_Message(tool_calls=[_Call()]))]
    )
    turn = provider.complete([], [])
    assert turn.tool_calls[0].arguments == {}
    assert turn.tool_calls[0].name == "get_timeline"


# ---- guided decoding -----------------------------------------------------------------------


def test_structured_output_returns_the_object_and_the_served_model() -> None:
    provider = _provider()
    provider._client.chat.completions.create = lambda **_k: _Response(
        MODEL, [_Choice(_Message(content='{"observations": []}'))]
    )
    payload, served = provider.complete_structured([], "DraftBriefing", {"type": "object"})
    assert payload == {"observations": []}
    assert served == MODEL


def test_a_truncated_structured_answer_says_why() -> None:
    provider = _provider()
    provider._client.chat.completions.create = lambda **_k: _Response(
        MODEL, [_Choice(_Message(content=None), finish_reason="length")]
    )
    with pytest.raises(LlmUnavailable) as failure:
        provider.complete_structured([], "DraftBriefing", {"type": "object"})
    assert "length" in str(failure.value)


def test_structured_output_that_is_not_an_object_is_refused() -> None:
    provider = _provider()
    provider._client.chat.completions.create = lambda **_k: _Response(
        MODEL, [_Choice(_Message(content="[1, 2]"))]
    )
    with pytest.raises(LlmUnavailable):
        provider.complete_structured([], "DraftBriefing", {"type": "object"})


def test_the_client_is_built_once_and_carries_the_timeout() -> None:
    provider = _provider()
    assert provider._client.timeout == TIMEOUT
    assert provider._client is provider._client


def test_thinking_is_off_by_default_and_travels_on_every_request() -> None:
    """The single biggest lever measured on this gateway.

    Qwen3.5 is a hybrid reasoning model: left on, it spent ~3,500 hidden thinking tokens that
    vLLM strips from the content but still charges against `max_tokens`, so a complete answer
    arrived truncated after 43s. Off, the same case answered in 6.5s.
    """
    seen: dict = {}

    provider = _provider()
    provider._client.chat.completions.create = lambda **kw: (
        seen.update(kw) or _Response(MODEL, [_Choice(_Message(content='{"a": 1}'))])
    )

    provider.complete([], [])
    assert seen["extra_body"]["chat_template_kwargs"]["enable_thinking"] is False

    seen.clear()
    provider.complete_structured([], "S", {"type": "object"})
    assert seen["extra_body"]["chat_template_kwargs"]["enable_thinking"] is False


def test_thinking_can_be_switched_back_on() -> None:
    seen: dict = {}
    provider = VllmProvider(
        base_url="http://gateway.invalid:9999/v1", api_key="k", model=MODEL,
        timeout_seconds=TIMEOUT, max_output_tokens=900, temperature=0.1, max_retries=0,
        enable_thinking=True,
    )
    provider._client.chat.completions.create = lambda **kw: (
        seen.update(kw) or _Response(MODEL, [_Choice(_Message(content="ok"))])
    )
    provider.complete([], [])
    assert seen["extra_body"]["chat_template_kwargs"]["enable_thinking"] is True


def test_a_truncated_answer_points_at_both_of_its_causes() -> None:
    provider = _provider()
    provider._client.chat.completions.create = lambda **_k: _Response(
        MODEL, [_Choice(_Message(content='{"partial":'), finish_reason="length")]
    )
    with pytest.raises(LlmUnavailable) as failure:
        provider.complete_structured([], "S", {"type": "object"})
    assert "BRIEFING_MAX_OUTPUT_TOKENS" in str(failure.value)
    assert "THINKING" in str(failure.value)


class TestAPaddedAnswerIsNotATruncatedOne:
    """A JSON grammar permits unlimited trailing whitespace, and this gateway's model closes the
    object and then pads with tabs until the cap.

    Measured: treating `finish_reason == "length"` as truncation discarded four complete
    briefings out of ten and pointed the diagnosis at the token budget. The object decides.
    """

    def test_a_complete_object_followed_by_padding_is_accepted(self) -> None:
        provider = _provider()
        provider._client.chat.completions.create = lambda **_k: _Response(
            MODEL,
            [_Choice(_Message(content='{"observations": []}' + "	" * 2000), finish_reason="length")],
        )
        payload, served = provider.complete_structured([], "S", {"type": "object"})
        assert payload == {"observations": []}
        assert served == MODEL

    def test_an_object_actually_cut_open_still_reports_truncation(self) -> None:
        provider = _provider()
        provider._client.chat.completions.create = lambda **_k: _Response(
            MODEL, [_Choice(_Message(content='{"observations": [{"stat'), finish_reason="length")]
        )
        with pytest.raises(LlmUnavailable) as failure:
            provider.complete_structured([], "S", {"type": "object"})
        assert "still open" in str(failure.value)
        assert "BRIEFING_MAX_OUTPUT_TOKENS" in str(failure.value)
