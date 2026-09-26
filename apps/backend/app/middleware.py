"""Two small ASGI layers that guard every route, so no router has to remember to.

`BodyLimitMiddleware` refuses an oversized request body before anything reads it into memory.
`SecurityHeadersMiddleware` adds the headers a browser needs to treat a JSON API as one.

Both are written against the raw ASGI interface rather than `BaseHTTPMiddleware`: the latter
buffers streaming responses, and the briefing endpoint streams server-sent events.
"""
from __future__ import annotations

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.errors import ErrorCode, ErrorResponse

BODYLESS_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})

UNGUARDED_PREFIXES = ("/v1/bundles",)
"""Ingestion enforces its own, larger limit and answers with its own stable code.

Two layers answering the same failure with different codes would be worse than one, so the
bundle routes are left to `BUNDLE_TOO_LARGE`.
"""

DOCUMENTATION_PREFIXES = ("/docs", "/redoc")
"""Swagger UI and ReDoc load scripts from a CDN and run inline; a locked-down policy blanks them."""

API_CONTENT_SECURITY_POLICY = "default-src 'none'; frame-ancestors 'none'"


class _BodyTooLarge(Exception):
    def __init__(self, size: int) -> None:
        self.size = size


class BodyLimitMiddleware:
    """Reject a request body over `max_bytes`, whether or not it declares its length."""

    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] != "http"
            or scope["method"] in BODYLESS_METHODS
            or scope["path"].startswith(UNGUARDED_PREFIXES)
        ):
            await self.app(scope, receive, send)
            return

        declared = _declared_length(scope)
        if declared is not None and declared > self.max_bytes:
            await self._refuse(send, declared)
            return

        received = 0
        overflow: int | None = None
        answered = False

        async def counting_receive() -> Message:
            nonlocal received, overflow
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    overflow = received
                    raise _BodyTooLarge(received)
            return message

        async def guarded_send(message: Message) -> None:
            nonlocal answered
            if overflow is None:
                await send(message)
                return
            # FastAPI turns *any* failure while reading a body into a generic 400. The caller
            # is owed the real reason, so once the limit has been crossed whatever the app says
            # is replaced by one accurate answer.
            if not answered:
                answered = True
                await self._refuse(send, overflow)

        try:
            await self.app(scope, counting_receive, guarded_send)
        except _BodyTooLarge:
            pass
        if overflow is not None and not answered:
            await self._refuse(send, overflow)

    async def _refuse(self, send: Send, size: int) -> None:
        envelope = ErrorResponse(
            code=ErrorCode.REQUEST_TOO_LARGE,
            detail=f"Request body is at least {size} bytes; the limit is {self.max_bytes}",
        )
        body = envelope.model_dump_json().encode()
        await send(
            {
                "type": "http.response.start",
                "status": envelope.http_status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode()),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


def _declared_length(scope: Scope) -> int | None:
    for name, value in scope["headers"]:
        if name == b"content-length":
            try:
                return int(value)
            except ValueError:
                return None
    return None


class SecurityHeadersMiddleware:
    """Baseline response headers. Never overrides one a route chose for itself."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers.setdefault("x-content-type-options", "nosniff")
                headers.setdefault("x-frame-options", "DENY")
                headers.setdefault("referrer-policy", "no-referrer")
                if not path.startswith(DOCUMENTATION_PREFIXES):
                    headers.setdefault("content-security-policy", API_CONTENT_SECURITY_POLICY)
                if path.startswith("/v1/"):
                    # Case data is per-reviewer. A shared cache or a back-button must not replay it.
                    # The briefing stream sets its own `no-cache`, which is left alone.
                    headers.setdefault("cache-control", "no-store")
            await send(message)

        await self.app(scope, receive, send_with_headers)
