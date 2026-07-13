"""Integration tests for security: headers, input validation, auth hardening."""

import pytest

_PW = "tmpPw99!!"

@pytest.mark.asyncio
async def test_security_headers_present(async_client):
    """All 5 security headers are present in response."""
    resp = await async_client.get("/health")
    expected = [
        "x-content-type-options",
        "x-frame-options",
        "x-xss-protection",
        "strict-transport-security",
        "content-security-policy",
    ]
    for h in expected:
        assert h in resp.headers, f"Missing header: {h}"


@pytest.mark.asyncio
async def test_auth_cache_control(async_client):
    """Auth endpoints have Cache-Control: no-store."""
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "test", "password": _PW},
    )
    assert resp.headers.get("cache-control") == "no-store"


@pytest.mark.asyncio
async def test_register_short_password(async_client):
    """Register with short password -> 422."""
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={"username": "short_pwd", "password": "123"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_session_empty_scenario(async_client, auth_header):
    """Create session with empty scenario_id -> 422."""
    resp = await async_client.post(
        "/api/v1/sessions",
        json={"scenario_id": ""},
        headers=auth_header,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_auth_hardening_6_register_attempts(async_client):
    """6 register attempts -> 429."""
    for i in range(5):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"username": f"hard_{i}", "password": _PW},
        )
        assert resp.status_code in (201, 409)
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={"username": "hard_6", "password": _PW},
    )
    assert resp.status_code == 429
