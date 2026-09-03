"""The single bounded LLM call in this codebase.

One `httpx` POST to an OpenAI-compatible `/chat/completions` — OpenRouter by default, or any
self-hosted gateway. No SDK, no streaming from the provider, one attempt. Nothing in the risk
path imports this module; `tests/test_briefing_isolation.py` asserts that.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Protocol

import httpx
from pydantic import Field

from app.dto.common import Dto

logger = logging.getLogger(__name__)


class LlmUnavailable(RuntimeError):
    """Transport, timeout, or an answer that is not a chat completion."""


class ToolCall(Dto):
    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class AssistantTurn(Dto):
    content: str | None
    tool_calls: tuple[ToolCall, ...] = ()


class ChatProvider(Protocol):
    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AssistantTurn: ...


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float,
        max_output_tokens: int,
    ) -> None:
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        self._model = model
        self._timeout = timeout_seconds
        self._max_output_tokens = max_output_tokens

    def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AssistantTurn:
        body = {
            "model": self._model,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0,
            "max_tokens": self._max_output_tokens,
        }
        try:
            response = httpx.post(self._url, json=body, headers=self._headers, timeout=self._timeout)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as failure:
            # Logged without the request body: the messages carry the case's own evidence text.
            logger.warning("briefing provider unavailable: %s", type(failure).__name__)
            raise LlmUnavailable(f"provider unavailable: {type(failure).__name__}") from failure
        return _parse_turn(payload)


def _parse_turn(payload: dict[str, Any]) -> AssistantTurn:
    try:
        message = payload["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as malformed:
        raise LlmUnavailable("provider answer was not a chat completion") from malformed
    calls = []
    for raw in message.get("tool_calls") or ():
        function = raw.get("function") or {}
        arguments = function.get("arguments") or "{}"
        try:
            parsed = json.loads(arguments) if isinstance(arguments, str) else dict(arguments)
        except (ValueError, TypeError):
            parsed = {}
        calls.append(ToolCall(id=str(raw.get("id", "")), name=str(function.get("name", "")), arguments=parsed))
    return AssistantTurn(content=message.get("content"), tool_calls=tuple(calls))
