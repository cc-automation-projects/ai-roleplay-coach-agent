"""API integration tests for /api/v1/sessions endpoint.

Tests session lifecycle: start → turn → finish → evaluate → get.
Uses httpx.AsyncClient with clean in-memory repos per test class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    import httpx


class TestSessionsAPI:
    """Session lifecycle via HTTP."""

    async def _start_session(
        self,
        client: httpx.AsyncClient,
        scenario_id: str,
        auth_header: dict[str, str],
    ) -> str:
        """Helper: POST /api/v1/sessions and return session ID."""
        resp = await client.post(
            "/api/v1/sessions",
            json={"scenario_id": scenario_id},
            headers=auth_header,
        )
        assert resp.status_code == 201, f"Create failed: {resp.text}"
        return resp.json()["id"]

    async def test_create_session(
        self,
        async_client: httpx.AsyncClient,
        operator_user: dict,
        seeded_scenario: dict,
        auth_header: dict[str, str],
    ) -> None:
        """POST /api/v1/sessions → 201 with session data."""
        response = await async_client.post(
            "/api/v1/sessions",
            json={"scenario_id": seeded_scenario["id"]},
            headers=auth_header,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == operator_user["id"]
        assert data["scenario_id"] == seeded_scenario["id"]
        assert data["status"] == "in_progress"
        assert len(data.get("transcript", [])) >= 1  # simulator greeting

    async def test_create_session_scenario_not_found(
        self,
        async_client: httpx.AsyncClient,
        auth_header: dict[str, str],
    ) -> None:
        """POST with non-existent scenario → 404."""
        fake_id = str(uuid4())
        response = await async_client.post(
            "/api/v1/sessions",
            json={"scenario_id": fake_id},
            headers=auth_header,
        )
        assert response.status_code == 404

    async def test_create_session_no_auth(
        self,
        async_client: httpx.AsyncClient,
        seeded_scenario: dict,
    ) -> None:
        """POST /sessions without auth → 401."""
        response = await async_client.post(
            "/api/v1/sessions",
            json={"scenario_id": seeded_scenario["id"]},
        )
        assert response.status_code == 401

    async def test_session_lifecycle(
        self,
        async_client: httpx.AsyncClient,
        operator_user: dict,
        seeded_scenario: dict,
        auth_header: dict[str, str],
        rbac_admin_header: dict[str, str],
    ) -> None:
        """Full lifecycle: start → turn → finish → evaluate → get."""
        session_id = await self._start_session(
            async_client,
            seeded_scenario["id"],
            auth_header,
        )

        # Turn 1
        resp = await async_client.post(
            f"/api/v1/sessions/{session_id}/turns",
            json={"user_id": operator_user["id"], "message": "Hello, how can I help?"},
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["transcript"]) >= 2

        # Turn 2
        resp = await async_client.post(
            f"/api/v1/sessions/{session_id}/turns",
            json={
                "user_id": operator_user["id"],
                "message": "I understand your issue.",
            },
            headers=auth_header,
        )
        assert resp.status_code == 200

        # Finish
        resp = await async_client.post(
            f"/api/v1/sessions/{session_id}/finish",
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

        # Evaluate (requires TRAINER/ADMIN)
        resp = await async_client.post(
            f"/api/v1/sessions/{session_id}/evaluate",
            headers=rbac_admin_header,
        )
        assert resp.status_code == 200
        eval_data = resp.json()
        assert "evaluation" in eval_data
        assert eval_data["evaluation"]["overall_score"] > 0

        # Get
        resp = await async_client.get(
            f"/api/v1/sessions/{session_id}",
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == session_id

    async def test_session_turn_not_found(
        self,
        async_client: httpx.AsyncClient,
        auth_header: dict[str, str],
    ) -> None:
        """Turn on non-existent session → 400."""
        response = await async_client.post(
            f"/api/v1/sessions/{uuid4()}/turns",
            json={"user_id": str(uuid4()), "message": "Hello"},
            headers=auth_header,
        )
        assert response.status_code == 400

    async def test_finish_not_found(
        self,
        async_client: httpx.AsyncClient,
        auth_header: dict[str, str],
    ) -> None:
        """Finish non-existent session → 400."""
        response = await async_client.post(
            f"/api/v1/sessions/{uuid4()}/finish",
            headers=auth_header,
        )
        assert response.status_code == 400

    async def test_evaluate_not_found(
        self,
        async_client: httpx.AsyncClient,
        rbac_admin_header: dict[str, str],
    ) -> None:
        """Evaluate non-existent session → 400."""
        response = await async_client.post(
            f"/api/v1/sessions/{uuid4()}/evaluate",
            headers=rbac_admin_header,
        )
        assert response.status_code == 400

    async def test_get_session_not_found(
        self,
        async_client: httpx.AsyncClient,
        auth_header: dict[str, str],
    ) -> None:
        """GET non-existent session → 404."""
        response = await async_client.get(
            f"/api/v1/sessions/{uuid4()}",
            headers=auth_header,
        )
        assert response.status_code == 404
