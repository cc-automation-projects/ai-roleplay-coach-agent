"""Request ID middleware — ensures every request has a traceable ID."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog
from starlette.datastructures import MutableHeaders

if TYPE_CHECKING:
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

_MAX_REQUEST_ID_LENGTH = 128


class RequestIDMiddleware:
    """Middleware that reads or generates a ``X-Request-ID`` header.

    - If the client sends ``X-Request-ID``, it is forwarded as-is.
    - Otherwise a new ``UUID4`` is generated.
    - The ID is set on the response header **and** pushed to structlog
      context vars so every log line emitted during the request carries it.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = MutableHeaders(scope=scope)  # type: ignore[arg-type]
        request_id = headers.get("x-request-id", uuid.uuid4().hex)

        # Guard against excessively long client-supplied IDs
        request_id = request_id[:_MAX_REQUEST_ID_LENGTH]

        # Push into structlog context for this request
        structlog.contextvars.bind_contextvars(request_id=request_id)

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            structlog.contextvars.unbind_contextvars("request_id")
