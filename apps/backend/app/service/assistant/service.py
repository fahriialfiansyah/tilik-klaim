"""Public surface: answer one question, or stream the reading that leads to the answer.

Off by default and template-first. Order is fixed: the deterministic reader runs first and a
refused question never reaches the model, whatever the switch says (ADR-0007 § 4.1). With the
switch off, no key, or no model, the template is the answer — not an error.
"""
from __future__ import annotations

import logging
import queue
import threading
from collections.abc import Iterator
from functools import lru_cache

from app.config import Settings
from app.dto.assistant import (
    AnswerDoneEvent,
    AssistantAnswer,
    AssistantEvent,
    AssistantQuestion,
    BriefingPhase,
    ErrorEvent,
    StatusEvent,
)
from app.dto.cases import CaseDetailResponse
from app.service.assistant.context import AssistantContext
from app.service.assistant.intents import classify
from app.service.assistant.runner import Emit, run_answer
from app.service.assistant.template import template_answer
from app.service.llm_provider import ChatProvider, VllmProvider

logger = logging.getLogger(__name__)

_END = object()

BUSY = "model capacity in use; answered from the template"

_SLOTS: dict[int, threading.BoundedSemaphore] = {}
_SLOTS_LOCK = threading.Lock()


def _slots(capacity: int) -> threading.BoundedSemaphore:
    """One process-wide semaphore per configured capacity — the bound on concurrent model calls."""
    with _SLOTS_LOCK:
        if capacity not in _SLOTS:
            _SLOTS[capacity] = threading.BoundedSemaphore(max(1, capacity))
        return _SLOTS[capacity]


@lru_cache(maxsize=4)
def _provider_for(
    base_url: str,
    api_key: str,
    model: str,
    timeout_seconds: float,
    max_output_tokens: int,
    temperature: float,
    max_retries: int,
    enable_thinking: bool,
) -> ChatProvider:
    """One client per configuration — a client per request is a new TCP handshake every time."""
    return VllmProvider(
        base_url=base_url,
        api_key=api_key,
        model=model,
        timeout_seconds=timeout_seconds,
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        max_retries=max_retries,
        enable_thinking=enable_thinking,
    )


def _make_provider(settings: Settings) -> ChatProvider:
    """Replaced in tests. The one place this feature reaches for a network client."""
    return _provider_for(
        settings.vllm_base_url,
        settings.vllm_api_key.get_secret_value(),
        settings.llm_model_vllm,
        settings.assistant_timeout_seconds,
        settings.assistant_max_output_tokens,
        settings.briefing_temperature,
        settings.briefing_max_retry,
        settings.briefing_enable_thinking,
    )


def is_assistant_model_configured(settings: Settings) -> bool:
    """A second, cheap reading of what `Settings` already enforces at start-up."""
    return bool(
        settings.assistant_enabled
        and settings.vllm_api_key.get_secret_value()
        and settings.llm_model_vllm
        and settings.vllm_base_url
    )


def answer_question(
    request: AssistantQuestion,
    ctx: AssistantContext,
    settings: Settings,
    scoped: CaseDetailResponse | None = None,
    emit: Emit | None = None,
) -> AssistantAnswer:
    """`scoped` is the case a CASE scope names, already loaded by the router."""
    send: Emit = emit or (lambda _event: None)
    reading = classify(request.question, request.scope.kind)

    if reading.refusal_topic is not None or not is_assistant_model_configured(settings):
        answer = template_answer(request, reading, ctx, scoped)
        send(StatusEvent(phase=BriefingPhase.STARTED, detail="template"))
        send(StatusEvent(phase=BriefingPhase.DONE, detail=answer.generated_by))
        send(AnswerDoneEvent(answer=answer))
        return answer

    slots = _slots(settings.assistant_max_concurrent)
    if not slots.acquire(blocking=False):
        answer = template_answer(request, reading, ctx, scoped).model_copy(
            update={"validation_rejected": True, "rejection_reason": BUSY}
        )
        send(StatusEvent(phase=BriefingPhase.STARTED, detail="template"))
        send(StatusEvent(phase=BriefingPhase.DONE, detail=answer.generated_by))
        send(AnswerDoneEvent(answer=answer))
        return answer
    try:
        return run_answer(
            request,
            reading,
            ctx,
            scoped,
            _make_provider(settings),
            model_id=settings.llm_model_vllm,
            emit=send,
        )
    finally:
        slots.release()


def stream_answer(
    request: AssistantQuestion,
    ctx: AssistantContext,
    settings: Settings,
    scoped: CaseDetailResponse | None = None,
) -> Iterator[AssistantEvent]:
    """Yield events as they happen. The run itself is synchronous, so it runs on a thread."""
    events: queue.Queue = queue.Queue()

    def work() -> None:
        try:
            answer_question(request, ctx, settings, scoped, emit=events.put)
        except Exception as failure:
            logger.exception("assistant answer failed")
            events.put(ErrorEvent(code="ASSISTANT_UNAVAILABLE", detail=type(failure).__name__))
        finally:
            events.put(_END)

    threading.Thread(target=work, name="assistant", daemon=True).start()
    while True:
        item = events.get()
        if item is _END:
            return
        yield item
