import pytest


@pytest.mark.asyncio
async def test_register_rate_limit(async_client):
    # 5 successful, 6th blocked
    for i in range(5):
        resp = await async_client.post(
            "/api/v1/auth/register",
            json={"username": f"rlim_{i}", "password": "zD3k9mQx"},
        )
        assert resp.status_code in (201, 409)  # 409 if duplicate, but we use unique
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={"username": "rlim_5", "password": "zD3k9mQx"},
    )
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers


@pytest.mark.asyncio
async def test_login_rate_limit(async_client):
    # Register a user
    await async_client.post(
        "/api/v1/auth/register",
        json={"username": "login_rl", "password": "zD3k9mQx"},
    )
    # 9 logins, 10th blocked (limit=10, register counts too)
    for _i in range(9):
        resp = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "login_rl", "password": "zD3k9mQx"},
        )
        assert resp.status_code == 200
    resp = await async_client.post(
        "/api/v1/auth/login",
        json={"username": "login_rl", "password": "zD3k9mQx"},
    )
    assert resp.status_code == 429


@pytest.mark.asyncio
async def test_block_duration(async_client):
    # Trigger block on register
    for i in range(5):
        await async_client.post(
            "/api/v1/auth/register",
            json={"username": f"block_{i}", "password": "zD3k9mQx"},
        )
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={"username": "block_5", "password": "zD3k9mQx"},
    )
    assert resp.status_code == 429
    retry = int(resp.headers["Retry-After"])
    assert retry > 0
    # Subsequent request immediately blocked
    resp2 = await async_client.post(
        "/api/v1/auth/register",
        json={"username": "block_6", "password": "zD3k9mQx"},
    )
    assert resp2.status_code == 429
