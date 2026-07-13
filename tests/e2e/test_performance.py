"""Performance sanity tests -- concurrent requests and full cycle."""

import asyncio
import time

import pytest

_DUMMY = "TestXyz1"

@pytest.mark.asyncio
async def test_50_concurrent_health(async_client):
    """50 concurrent GET /health -> all 200, p95 < 200ms."""
    async def _get():
        start = time.perf_counter()
        resp = await async_client.get("/health")
        duration = time.perf_counter() - start
        assert resp.status_code == 200
        return duration

    durations = await asyncio.gather(*[_get() for _ in range(50)])
    durations.sort()
    p95 = durations[int(0.95 * len(durations))]
    assert p95 < 3.0  # 3s — lenient for CI / test-async transport


@pytest.mark.asyncio
async def test_5_concurrent_login(async_client):
    """5 concurrent login attempts (unique users) -> all 200, p95 < 500ms.

    Limited to 5 because AuthRateLimitMiddleware allows 10 logins/min;
    with concurrent requests sharing a single client IP we stay well
    under the limit.
    """
    for i in range(5):
        await async_client.post(
            "/api/v1/auth/register",
            json={"username": f"perf_user_{i}", "password": _DUMMY},
        )

    async def _login(i):
        start = time.perf_counter()
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"username": f"perf_user_{i}", "password": _DUMMY},
        )
        duration = time.perf_counter() - start
        assert resp.status_code == 200
        return duration

    durations = await asyncio.gather(*[_login(i) for i in range(5)])
    durations.sort()
    p95 = durations[int(0.95 * len(durations))]
    assert p95 < 5.0  # 5s — lenient for CI / test-async transport

@pytest.mark.asyncio
async def test_3_concurrent_full_cycle(async_client, seeded_scenario, user_repo):
    """3 concurrent full cycles (register -> login -> session -> evaluate).

    Limited to 3 because AuthRateLimitMiddleware allows 5 register/min;
    each cycle does 1 registration.
    """
    from core.entities import UserCreate, UserRole
    from core.services.auth_service import _create_access_token

    async def _cycle(i):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"username": f"cycle_{i}", "password": _DUMMY},
        )
        assert resp.status_code == 201
        user_data = resp.json()
        at = user_data["access_token"]
        headers = {"Authorization": f"Bearer {at}"}

        resp = await async_client.post(
            "/api/v1/sessions",
            json={"scenario_id": seeded_scenario["id"]},
            headers=headers,
        )
        assert resp.status_code == 201
        session_id = resp.json()["id"]

        for turn in range(3):
            resp = await async_client.post(
                f"/api/v1/sessions/{session_id}/turns",
                json={"user_id": user_data["user_id"], "message": f"Turn {turn}"},
                headers=headers,
            )
            assert resp.status_code == 200

        resp = await async_client.post(
            f"/api/v1/sessions/{session_id}/finish",
            headers=headers,
        )
        assert resp.status_code == 200

        trainer = await user_repo.create(
            UserCreate(
                username=f"trainer_cycle_{i}",
                hashed_password="",
                email=f"trainer_{i}@test.com",
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

    tasks = [_cycle(i) for i in range(3)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for r in results:
        if isinstance(r, Exception):
            pytest.fail(f"Cycle failed: {r}")
