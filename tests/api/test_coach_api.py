"""API integration tests for /api/v1/coach endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    import httpx


class TestCoachAPI:
    """Coach agent endpoint: evaluate."""

    async def test_evaluate_session(
        self,
        async_client: httpx.AsyncClient,
        operator_user: dict,
        seeded_scenario: dict,
        auth_header: dict[str, str],
    ) -> None:
        """POST /api/v1/coach/evaluate → 200 with evaluation."""
        # Create → turn → finish a session first
        session_resp = await async_client.post(
            "/api/v1/sessions",
            json={"scenario_id": seeded_scenario["id"]},
            headers=auth_header,
        )
        assert session_resp.status_code == 201
        session_id = session_resp.json()["id"]

        # Add a turn
        await async_client.post(
            f"/api/v1/sessions/{session_id}/turns",
            json={
                "user_id": operator_user["id"],
                "message": "Hello, I can help you today.",
            },
            headers=auth_header,
        )

        # Finish
        await async_client.post(
            f"/api/v1/sessions/{session_id}/finish",
            headers=auth_header,
        )

        # Evaluate via coach
        response = await async_client.post(
            "/api/v1/coach/evaluate",
            json={"session_id": session_id},
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "overall_score" in data
        assert data["overall_score"] > 0
        assert "praise_text" in data
        assert "growth_text" in data

    async def test_evaluate_not_found(
        self,
        async_client: httpx.AsyncClient,
        auth_header: dict[str, str],
    ) -> None:
        """Evaluate non-existent session → 404."""
        response = await async_client.post(
            "/api/v1/coach/evaluate",
            json={"session_id": str(uuid4())},
            headers=auth_header,
        )
        assert response.status_code == 404
