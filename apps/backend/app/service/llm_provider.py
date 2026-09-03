"""The single bounded LLM call in this codebase, against the internal vLLM gateway.

The gateway speaks the OpenAI protocol, so the official `openai` package is the whole client —
no private wheel, no internal index. `docs/VLLM-SETUP.md` is the setup guide; this module is
where its rules are enforced.

Nothing in the risk path imports this module; `tests/test_briefing_isolation.py` asserts it in
both directions.

**Sync, not async, deliberately.** The guide uses `AsyncOpenAI` because its host application is
async throughout. The briefing runs synchronously on a worker thread so the SSE endpoint can
stream it, so the sync client is the one that fits — same package, same typed errors, same
guided decoding.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Protocol

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAI,
    RateLimitError,
)
from pydantic import Field

from app.dto.common import Dto

logger = logging.getLogger(__name__)


class LlmUnavailable(RuntimeError):
    """The gateway could not answer. The message names which of the four fixes applies."""


class ToolCallsUnsupported(LlmUnavailable):
    """The gateway served the request but refuses tool calling.

    vLLM only offers tools when started with `--enable-auto-tool-choice`, and many gateway
    deployments are not. This is a *capability* answer rather than an outage, so the caller can
    retry the same case through guided decoding instead of giving up.
    """


class ToolCall(Dto):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class AssistantTurn(Dto):
    content: str | None
    tool_calls: tuple[ToolCall, ...] = ()
    served_model: str | None = None
    """The model that actually answered.

    Recorded rather than the requested name because **the gateway substitutes models silently**
    (`docs/VLLM-SETUP.md` § 8: asking for `Qwen2.5-7B` was answered by `Qwen3.5-9B`, unwarned).
    An audit trail that reports configuration reports something that did not happen.
    """


class ChatProvider(Protocol):
    def available_models(self) -> frozenset[str]: ...

    def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> AssistantTurn: ...

    def complete_structured(
        self, messages: list[dict[str, Any]], schema_name: str, schema: dict[str, Any]
    ) -> tuple[dict[str, Any], str | None]: ...


def _fail(cause: Exception, timeout_seconds: float, model: str) -> LlmUnavailable:
    """One exception class per fix. `except Exception` flattens three different repairs into one."""
    if isinstance(cause, NotFoundError):
        return LlmUnavailable(
            f"model {model!r} is not on the gateway roster — check LLM_MODEL_VLLM"
        )
    if isinstance(cause, AuthenticationError):
        return LlmUnavailable("the gateway rejected VLLM_API_KEY")
    if isinstance(cause, RateLimitError):
        return LlmUnavailable("the gateway is rate limiting this key")
    if isinstance(cause, (APITimeoutError, APIConnectionError)):
        # A closed port on the gateway host drops packets rather than refusing them, so this is
        # a full-timeout hang rather than a fast failure. Say so, or it reads as a slow model.
        return LlmUnavailable(
            f"the vLLM gateway did not answer within {timeout_seconds:g}s — check VLLM_BASE_URL "
            "and that the host is reachable"
        )
    return LlmUnavailable(f"gateway call failed: {type(cause).__name__}")


class VllmProvider:
    """One client for the process. Per-request clients mean a new TCP handshake every time."""

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_output_tokens: int,
        temperature: float,
        max_retries: int,
    ) -> None:
        self._model = model
        self._timeout = timeout_seconds
        self._max_output_tokens = max_output_tokens
        self._temperature = temperature
        self._client = OpenAI(
            base_url=base_url,
            api_key=api_key,
            # Mandatory. Without it a dead gateway hangs until the SDK's ten-minute default and
            # the worker is exhausted long before the request is.
            timeout=timeout_seconds,
            max_retries=max_retries,
        )

    def _note_substitution(self, served: str | None) -> None:
        if served and served != self._model:
            logger.warning(
                "vLLM gateway substituted the model: requested=%s served=%s", self._model, served
            )

    def available_models(self) -> frozenset[str]:
        """The gateway roster. Tests the network and the credential without spending a token."""
        try:
            return frozenset(model.id for model in self._client.models.list().data)
        except Exception as failure:
            raise _fail(failure, self._timeout, self._model) from failure

    def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]
    ) -> AssistantTurn:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=self._temperature,
                max_tokens=self._max_output_tokens,
            )
        except BadRequestError as refused:
            # A gateway started without `--enable-auto-tool-choice` refuses the *request shape*,
            # not the content. Distinguished so the caller can fall back to guided decoding
            # rather than reporting an outage that is not one.
            if _mentions_tools(refused):
                raise ToolCallsUnsupported(
                    "the gateway does not serve tool calling; falling back to guided decoding"
                ) from refused
            raise _fail(refused, self._timeout, self._model) from refused
        except Exception as failure:
            raise _fail(failure, self._timeout, self._model) from failure

        self._note_substitution(response.model)
        return _parse_turn(response)

    def complete_structured(
        self, messages: list[dict[str, Any]], schema_name: str, schema: dict[str, Any]
    ) -> tuple[dict[str, Any], str | None]:
        """One call, shape enforced by the server.

        Guided decoding rather than "please answer in JSON" plus a regex: the gateway holds the
        model to the schema, so a malformed answer is impossible rather than merely unlikely.
        """
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=0,
                max_tokens=self._max_output_tokens,
                response_format={
                    "type": "json_schema",
                    "json_schema": {"name": schema_name, "schema": schema, "strict": True},
                },
            )
        except Exception as failure:
            raise _fail(failure, self._timeout, self._model) from failure

        self._note_substitution(response.model)
        choice = response.choices[0]
        content = choice.message.content
        if not content:
            raise LlmUnavailable(
                f"the gateway returned no object (finish_reason={choice.finish_reason})"
            )
        try:
            parsed = json.loads(content)
        except ValueError as malformed:
            raise LlmUnavailable("the gateway returned content that is not JSON") from malformed
        if not isinstance(parsed, dict):
            raise LlmUnavailable("the gateway returned JSON that is not an object")
        return parsed, response.model


def _mentions_tools(error: BadRequestError) -> bool:
    text = str(error).lower()
    return "tool" in text or "function" in text


def _parse_turn(response: Any) -> AssistantTurn:
    message = response.choices[0].message
    calls = []
    for raw in message.tool_calls or ():
        function = getattr(raw, "function", None)
        arguments = getattr(function, "arguments", None) or "{}"
        try:
            parsed = json.loads(arguments) if isinstance(arguments, str) else dict(arguments)
        except (ValueError, TypeError):
            # A model that emits unparseable arguments has not called the tool; an empty dict
            # reaches the registry, which reports the argument error back to it.
            parsed = {}
        calls.append(
            ToolCall(id=str(raw.id or ""), name=str(getattr(function, "name", "")), arguments=parsed)
        )
    return AssistantTurn(
        content=message.content, tool_calls=tuple(calls), served_model=response.model
    )
