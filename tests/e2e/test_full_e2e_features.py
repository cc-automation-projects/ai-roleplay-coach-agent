"""Full E2E scenario covering all core features (sessions, evaluate, metrics)."""

import pytest
from prometheus_client import REGISTRY

from core.entities import UserCreate, UserRole
from core.services.auth_service import _create_access_token

_DUMMY = "TestXyz1"

@pytest.mark.asyncio
async def test_full_e2e_with_all_features(async_client, seeded_scenario, user_repo):
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={"username": "e2e_full", "password": _DUMMY},
    )
    assert resp.status_code == 201
    user_data = resp.json()
    user_id = user_data["user_id"]
    at = user_data["access_token"]
    headers = {"Authorization": f"Bearer {at}"}
    register_rid = resp.headers.get("x-request-id")
    assert register_rid is not None

    resp = await async_client.post(
        "/api/v1/sessions",
        json={"scenario_id": seeded_scenario["id"]},
        headers=headers,
    )
    assert resp.status_code == 201
    session_id = resp.json()["id"]
    session_rid = resp.headers.get("x-request-id")
    assert session_rid is not None

    for i in range(4):
        resp = await async_client.post(
            f"/api/v1/sessions/{session_id}/turns",
            json={"user_id": user_id, "message": f"Turn {i}"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert "x-request-id" in resp.headers

    resp = await async_client.post(
        f"/api/v1/sessions/{session_id}/finish",
        headers=headers,
    )
    assert resp.status_code == 200
    finish_rid = resp.headers.get("x-request-id")
    assert finish_rid is not None

    trainer = await user_repo.create(
        UserCreate(
            username="e2e_trainer",
            hashed_password="",
            email="e2e_trainer@test.com",
            name="Trainer",
            role=UserRole.TRAINER,
        )
    )
    trainer_at = _create_access_token(trainer)
    trainer_headers = {"Authorization": f"Bearer {trainer_at}"}
    resp = await async_client.post(
        f"/api/v1/sessions/{session_id}/evaluate",
        headers=trainer_headers,
    )
    assert resp.status_code == 200
    eval_data = resp.json()
    assert "evaluation" in eval_data
    assert eval_data["evaluation"]["overall_score"] > 0

    sample = REGISTRY.get_sample_value("http_requests_total", {"method": "POST", "path": "/api/v1/sessions", "status": "201"})
    assert sample is not None
    assert sample > 0

    resp = await async_client.get("/health")
    assert "x-content-type-options" in resp.headers
    assert "x-frame-options" in resp.headers
    assert "strict-transport-security" in resp.headers

    resp = await async_client.get("/health")
    assert resp.json()["version"] == "0.1.0"

    resp = await async_client.get("/api/v1/sessions?page=1&size=10", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["size"] == 10
    assert len(data["items"]) >= 1
    assert "total" in data
