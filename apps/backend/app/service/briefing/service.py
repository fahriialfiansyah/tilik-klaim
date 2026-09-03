"""Public surface: build a briefing, or stream its progress.

Off by default. With no key, no model, or `BRIEFING_ENABLED=false`, the template is the
answer — not an error. `08_demo_runbook.md`: "Never depend on a remote LLM."
"""
from __future__ import annotations

import queue
import threading
from collections.abc import Iterator

from tilik_domain.versioning import EngineIdentity

from app.config import Settings
from app.dto.briefing import (
    BriefingEvent,
    BriefingPhase,
    CaseBriefing,
    DoneEvent,
    ErrorEvent,
    ObservationEvent,
    StatusEvent,
)
from app.dto.cases import CaseDetailResponse
from app.service.briefing.runner import Emit, run_briefing
from app.service.briefing.template import template_briefing
from app.service.llm_provider import ChatProvider, VllmProvider

_END = object()


def _make_provider(settings: Settings) -> ChatProvider:
    """Replaced in tests. The one place a real network client is constructed."""
    return VllmProvider(
        base_url=settings.vllm_base_url,
        api_key=settings.vllm_api_key.get_secret_value(),
        model=settings.llm_model_vllm,
        timeout_seconds=settings.briefing_timeout_seconds,
        max_output_tokens=settings.briefing_max_output_tokens,
        temperature=settings.briefing_temperature,
        max_retries=settings.briefing_max_retry,
    )


def list_gateway_models(settings: Settings) -> frozenset[str]:
    """Model ids the gateway will serve. Used by `/health/llm`; costs no tokens."""
    return _make_provider(settings).available_models()


def is_llm_configured(settings: Settings) -> bool:
    """`Settings` already refuses to build if the switch is on and anything is missing, so this
    is a second, cheap reading of the same fact — and the one that keeps a half-set `.env` on a
    developer's machine answering with the template instead of raising."""
    return bool(
        settings.briefing_enabled
        and settings.vllm_api_key.get_secret_value()
        and settings.llm_model_vllm
        and settings.vllm_base_url
    )


def build_briefing(detail: CaseDetailResponse, settings: Settings, emit: Emit | None = None) -> CaseBriefing:
    identity = EngineIdentity()
    send: Emit = emit or (lambda _event: None)
    if not is_llm_configured(settings):
        briefing = template_briefing(detail, identity)
        send(StatusEvent(phase=BriefingPhase.STARTED, detail="template"))
        for observation in briefing.observations:
            send(ObservationEvent(observation=observation))
        send(StatusEvent(phase=BriefingPhase.DONE, detail="TEMPLATE"))
        send(DoneEvent(briefing=briefing))
        return briefing
    return run_briefing(
        detail,
        identity,
        _make_provider(settings),
        model_id=settings.llm_model_vllm,
        max_tool_calls=settings.briefing_max_tool_calls,
        emit=send,
    )


def stream_briefing(detail: CaseDetailResponse, settings: Settings) -> Iterator[BriefingEvent]:
    """Yield events as they happen. The run itself is synchronous, so it runs on a thread."""
    events: queue.Queue = queue.Queue()

    def work() -> None:
        try:
            build_briefing(detail, settings, emit=events.put)
        except Exception as failure:  # noqa: BLE001 - the stream must end with an event, not hang
            events.put(ErrorEvent(code="BRIEFING_UNAVAILABLE", detail=type(failure).__name__))
        finally:
            events.put(_END)

    threading.Thread(target=work, name="briefing", daemon=True).start()
    while True:
        item = events.get()
        if item is _END:
            return
        yield item
