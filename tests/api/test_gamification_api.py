"""API tests for /api/v1/gamification endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

from core.entities import BadgeCreate, UserCreate, UserRole

if TYPE_CHECKING:
    import httpx

    from infrastructure.memory.repositories import (
        InMemoryBadgeRepository,
        InMemoryUserRepository,
    )


class TestGamificationAPI:
    """Gamification endpoints: XP, badges, leaderboard, streak."""

    async def test_get_xp_success(
        self,
        async_client: httpx.AsyncClient,
        operator_user: dict,
        auth_header: dict[str, str],
    ) -> None:
        """GET /gamification/xp/{uid} → 200 with XP + level."""
        resp = await async_client.get(
            f"/api/v1/gamification/xp/{operator_user['id']}",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "xp_total" in data
        assert "level" in data
        assert "badges" in data

    async def test_get_xp_not_found(
        self,
        async_client: httpx.AsyncClient,
        auth_header: dict[str, str],
    ) -> None:
        """GET /gamification/xp/{uid} for unknown user → 404."""
        resp = await async_client.get(
            f"/api/v1/gamification/xp/{uuid4()}",
            headers=auth_header,
        )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    async def test_get_xp_no_auth(
        self,
        async_client: httpx.AsyncClient,
    ) -> None:
        """GET /gamification/xp without auth → 401."""
        resp = await async_client.get(f"/api/v1/gamification/xp/{uuid4()}")
        assert resp.status_code == 401

    async def test_get_xp_history(
        self,
        async_client: httpx.AsyncClient,
        operator_user: dict,
        auth_header: dict[str, str],
    ) -> None:
        """GET /gamification/xp/{uid}/history → 200 with Page."""
        resp = await async_client.get(
            f"/api/v1/gamification/xp/{operator_user['id']}/history",
            params={"page": 1, "size": 20},
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert isinstance(data["items"], list)

    async def test_list_all_badges(
        self,
        async_client: httpx.AsyncClient,
        badge_repo: InMemoryBadgeRepository,
        auth_header: dict[str, str],
    ) -> None:
        """GET /gamification/badges → 200 with list of badges."""
        await badge_repo.create(
            BadgeCreate(name="Bronze", description="First badge", criteria="reach level 5"),
        )
        await badge_repo.create(
            BadgeCreate(name="Silver", description="Second badge", criteria="reach level 10"),
        )

        resp = await async_client.get("/api/v1/gamification/badges", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        names = [b["name"] for b in data]
        assert "Bronze" in names
        assert "Silver" in names

    async def test_get_user_badges_empty(
        self,
        async_client: httpx.AsyncClient,
        operator_user: dict,
        auth_header: dict[str, str],
    ) -> None:
        """GET /gamification/badges/{uid} for user with no badges → empty list."""
        resp = await async_client.get(
            f"/api/v1/gamification/badges/{operator_user['id']}",
            headers=auth_header,
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_get_user_badges_with_data(
        self,
        async_client: httpx.AsyncClient,
        operator_user: dict,
        badge_repo: InMemoryBadgeRepository,
        user_repo: InMemoryUserRepository,
        auth_header: dict[str, str],
    ) -> None:
        """GET /gamification/badges/{uid} → returns user's badges."""
        from uuid import UUID

        from core.entities import UserBadge

        user = await user_repo.get_by_id(UUID(operator_user["id"]))
        assert user is not None

        b = await badge_repo.create(
            BadgeCreate(name="Gold", description="Top performer", criteria="score 95+"),
        )
        await badge_repo.award_to_user(
            UserBadge(user_id=user.id, badge_id=b.id),
        )

        resp = await async_client.get(
            f"/api/v1/gamification/badges/{operator_user['id']}",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Gold"

    async def test_leaderboard_empty(
        self,
        async_client: httpx.AsyncClient,
        auth_header: dict[str, str],
    ) -> None:
        """GET /gamification/leaderboard → valid Page response."""
        resp = await async_client.get("/api/v1/gamification/leaderboard", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert isinstance(data["items"], list)

    async def test_leaderboard_with_data(
        self,
        async_client: httpx.AsyncClient,
        rbac_admin_header: dict[str, str],
        user_repo: InMemoryUserRepository,
    ) -> None:
        """GET /gamification/leaderboard → sorted by XP DESC."""
        u1 = await user_repo.create(
            UserCreate(
                username="alice", hashed_password="", email="a@t.com",
                name="Alice", role=UserRole.OPERATOR,
            ),
        )
        u2 = await user_repo.create(
            UserCreate(
                username="bob", hashed_password="", email="b@t.com",
                name="Bob", role=UserRole.OPERATOR,
            ),
        )
        u1.add_xp(500)
        u2.add_xp(300)
        await user_repo.update(u1)
        await user_repo.update(u2)

        url = "/api/v1/gamification/leaderboard"
        resp = await async_client.get(url, params={"page": 1, "size": 5}, headers=rbac_admin_header)
        assert resp.status_code == 200
        data = resp.json()
        items = data["items"]
        assert len(items) >= 2
        # Alice (500 XP) should be first, Bob (300 XP) second
        assert items[0]["name"] == "Alice"
        assert items[1]["name"] == "Bob"
        assert items[0]["rank"] == 1
        assert items[1]["rank"] == 2

    async def test_leaderboard_pagination(
        self,
        async_client: httpx.AsyncClient,
        auth_header: dict[str, str],
        user_repo: InMemoryUserRepository,
    ) -> None:
        """GET /gamification/leaderboard → respects page size."""
        for i in range(5):
            u = await user_repo.create(
                UserCreate(
                    username=f"user{i}",
                    hashed_password="",
                    email=f"user{i}@t.com",
                    name=f"User{i}",
                    role=UserRole.OPERATOR,
                ),
            )
            u.add_xp(100 * (5 - i))
            await user_repo.update(u)

        url = "/api/v1/gamification/leaderboard"
        resp = await async_client.get(url, params={"page": 1, "size": 3}, headers=auth_header)
        data = resp.json()
        assert len(data["items"]) == 3
        assert data["total"] >= 5  # may include seeded users
        assert data["page"] == 1
        assert data["size"] == 3

    async def test_get_streak(
        self,
        async_client: httpx.AsyncClient,
        operator_user: dict,
        auth_header: dict[str, str],
    ) -> None:
        """GET /gamification/streak/{uid} → 200 with streak count."""
        resp = await async_client.get(
            f"/api/v1/gamification/streak/{operator_user['id']}",
            headers=auth_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "streak" in data
        assert "user_id" in data

    async def test_router_included(
        self,
        async_client: httpx.AsyncClient,
        auth_header: dict[str, str],
    ) -> None:
        """Gamification router is mounted (any endpoint returns valid JSON)."""
        resp = await async_client.get("/api/v1/gamification/xp/not-a-uuid", headers=auth_header)
        assert resp.status_code == 422
