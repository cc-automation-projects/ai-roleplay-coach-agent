"""API integration tests for /api/v1/simulator endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    import httpx


class TestSimulatorAPI:
    """Simulator agent endpoints: start_dialogue, respond, should-end."""

    async def test_start_dialogue(
        self,
        async_client: httpx.AsyncClient,
        seeded_scenario: dict,
        auth_header: dict[str, str],
    ) -> None:
        """POST /api/v1/simulator/start → 200 with greeting + psychotype."""
        response = await async_client.post(
            "/api/v1/simulator/start",
            json={"scenario_id": seeded_scenario["id"]},
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "greeting" in data
        assert len(data["greeting"]) > 0
        assert "psychotype" in data

    async def test_start_dialogue_not_found(
        self,
        async_client: httpx.AsyncClient,
        auth_header: dict[str, str],
    ) -> None:
        """POST with non-existent scenario → 404."""
        response = await async_client.post(
            "/api/v1/simulator/start",
            json={"scenario_id": str(uuid4())},
            headers=auth_header,
        )
        assert response.status_code == 404

    async def test_respond(
        self,
        async_client: httpx.AsyncClient,
        seeded_scenario: dict,
        auth_header: dict[str, str],
    ) -> None:
        """POST /api/v1/simulator/respond → 200 with client message."""
        # First: create a session (needs auth)
        session_resp = await async_client.post(
            "/api/v1/sessions",
            json={"scenario_id": seeded_scenario["id"]},
            headers=auth_header,
        )
        assert session_resp.status_code == 201
        session_id = session_resp.json()["id"]

        response = await async_client.post(
            "/api/v1/simulator/respond",
            json={"session_id": session_id},
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "client_message" in data
        assert len(data["client_message"]) > 0

    async def test_respond_not_found(
        self,
        async_client: httpx.AsyncClient,
        auth_header: dict[str, str],
    ) -> None:
        """POST /respond with non-existent session → 404."""
        response = await async_client.post(
            "/api/v1/simulator/respond",
            json={"session_id": str(uuid4())},
            headers=auth_header,
        )
        assert response.status_code == 404

    async def test_should_end(
        self,
        async_client: httpx.AsyncClient,
        seeded_scenario: dict,
        auth_header: dict[str, str],
    ) -> None:
        """POST /api/v1/simulator/should-end/{id} → 200 with bool."""
        session_resp = await async_client.post(
            "/api/v1/sessions",
            json={"scenario_id": seeded_scenario["id"]},
            headers=auth_header,
        )
        assert session_resp.status_code == 201
        session_id = session_resp.json()["id"]

        response = await async_client.post(
            f"/api/v1/simulator/should-end/{session_id}",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert "should_end" in data
        assert isinstance(data["should_end"], bool)

    async def test_should_end_not_found(
        self,
        async_client: httpx.AsyncClient,
        auth_header: dict[str, str],
    ) -> None:
        """POST /should-end with non-existent session → 404."""
        response = await async_client.post(
            f"/api/v1/simulator/should-end/{uuid4()}",
            headers=auth_header,
        )
        assert response.status_code == 404
