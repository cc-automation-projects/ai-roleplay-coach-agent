"""Integration tests for API hardening: pagination, rate limiting, CORS, ProblemDetail."""

import uuid

import pytest

_PW = "tmpPw99!!"

_MISSING_UUID = str(uuid.UUID(int=0))  # 00000000-0000-0000-0000-000000000000


@pytest.mark.asyncio
async def test_pagination_25_sessions(async_client, auth_header, seeded_scenario):
    """25 sessions -> page 1 returns 20, page 2 returns 5."""
    for _i in range(25):
        resp = await async_client.post(
            "/api/v1/sessions",
            json={"scenario_id": seeded_scenario["id"]},
            headers=auth_header,
        )
        assert resp.status_code == 201

    resp = await async_client.get("/api/v1/sessions?page=1&size=20", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 20
    assert data["total"] >= 25
    assert data["page"] == 1
    assert data["size"] == 20

    resp = await async_client.get("/api/v1/sessions?page=2&size=20", headers=auth_header)
    assert resp.status_code == 200
    data2 = resp.json()
    assert len(data2["items"]) == 5


@pytest.mark.asyncio
async def test_pagination_invalid_params(async_client, auth_header):
    """Invalid pagination params -> 422 ProblemDetail."""
    resp = await async_client.get("/api/v1/sessions?page=0&size=20", headers=auth_header)
    assert resp.status_code == 422
    data = resp.json()
    assert "detail" in data
    assert isinstance(data.get("detail"), (list, dict, str))


@pytest.mark.asyncio
async def test_rate_limiting_110_requests(async_client):
    """110 requests -> last one returns 429."""
    for _i in range(100):
        resp = await async_client.get("/api/v1/gamification/leaderboard")
        if resp.status_code == 429:
            break
    else:
        for _i in range(20):
            resp = await async_client.get("/api/v1/gamification/leaderboard")
            if resp.status_code == 429:
                break
        else:
            pytest.fail("Rate limit not triggered after 120 requests")

@pytest.mark.asyncio
async def test_cors_headers(async_client):
    """OPTIONS preflight returns CORS headers."""
    resp = await async_client.options(
        "/api/v1/auth/login",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    ao = resp.headers.get("access-control-allow-origin")
    assert ao is not None
    assert "access-control-allow-methods" in resp.headers


@pytest.mark.asyncio
async def test_problem_detail_404(async_client, auth_header):
    """GET /nonexistent returns 404 with ProblemDetail JSON."""
    resp = await async_client.get(f"/api/v1/sessions/{_MISSING_UUID}", headers=auth_header)
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_problem_detail_422(async_client, auth_header):
    """Invalid input returns 422 with errors."""
    resp = await async_client.post(
        "/api/v1/sessions",
        json={"scenario_id": "not-a-uuid"},
        headers=auth_header,
    )
    assert resp.status_code == 422
    data = resp.json()
    assert "detail" in data

@pytest.mark.asyncio
async def test_auth_rate_limit_11_requests(async_client):
    """10 auth requests -> last one 429 (register + 9 logins = 10, limit=10)."""
    await async_client.post(
        "/api/v1/auth/register",
        json={"username": "auth_rl_user", "password": _PW},
    )
    for _i in range(9):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "auth_rl_user", "password": _PW},
        )
        assert resp.status_code == 200
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "auth_rl_user", "password": _PW},
    )
    assert resp.status_code == 429
