"""Tests for Request ID middleware."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import httpx


class TestRequestIDMiddleware:
    """X-Request-ID header behaviour."""

    async def test_generates_request_id(self, async_client: httpx.AsyncClient) -> None:
        """Without header, middleware generates a UUID."""
        response = await async_client.get("/health")
        assert "x-request-id" in response.headers
        rid = response.headers["x-request-id"]
        # Ensure it's a valid hex string (UUID4)
        assert len(rid) == 32
        int(rid, 16)

    async def test_uses_provided_request_id(self, async_client: httpx.AsyncClient) -> None:
        """With header, the provided ID is used."""
        custom_id = uuid.uuid4().hex
        response = await async_client.get(
            "/health",
            headers={"X-Request-ID": custom_id},
        )
        assert response.headers.get("x-request-id") == custom_id

    async def test_request_id_in_response_header(self, async_client: httpx.AsyncClient) -> None:
        """Request ID is always present in response headers."""
        response = await async_client.get("/health")
        assert "x-request-id" in response.headers
