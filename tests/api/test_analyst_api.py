"""Integration tests for the Analyst API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

from core.entities import EvaluationCreate, SessionCreate, SessionStatus

if TYPE_CHECKING:
    import httpx

    from infrastructure.memory.repositories import (
        InMemoryEvaluationRepository,
        InMemorySessionRepository,
    )


@pytest.mark.asyncio
async def test_get_global_stats_empty(
    async_client: httpx.AsyncClient,
    rbac_admin_header: dict[str, str],
) -> None:
    """GET /analyst/stats should return global stats (auth user exists)."""
    resp = await async_client.get("/api/v1/analyst/stats", headers=rbac_admin_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_users"] >= 1  # auth user exists
    assert data["total_sessions"] == 0
    assert data["avg_score"] == 0.0


@pytest.mark.asyncio
async def test_get_global_stats_no_auth(
    async_client: httpx.AsyncClient,
) -> None:
    """GET /analyst/stats without auth → 401."""
    resp = await async_client.get("/api/v1/analyst/stats")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_global_stats_operator_forbidden(
    async_client: httpx.AsyncClient,
    auth_header: dict[str, str],
) -> None:
    """GET /analyst/stats as operator → 403 (trainer+ required)."""
    resp = await async_client.get("/api/v1/analyst/stats", headers=auth_header)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_user_stats_empty(
    async_client: httpx.AsyncClient,
    auth_header: dict[str, str],
) -> None:
    """GET /analyst/stats/{uid} for non-existent user should return zeros."""
    resp = await async_client.get(f"/api/v1/analyst/stats/{uuid4()}", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_sessions"] == 0


@pytest.mark.asyncio
async def test_get_user_stats_with_data(
    async_client: httpx.AsyncClient,
    eval_repo: InMemoryEvaluationRepository,
    session_repo: InMemorySessionRepository,
    auth_header: dict[str, str],
) -> None:
    """GET /analyst/stats/{uid} should return populated stats after seeding."""
    uid = uuid4()
    sid = uuid4()
    session = await session_repo.create(
        SessionCreate(user_id=uid, scenario_id=sid, status=SessionStatus.COMPLETED)
    )
    await eval_repo.create(
        EvaluationCreate(
            session_id=session.id,
            user_id=uid,
            overall_score=85,
            script_adherence=80,
            tone_score=75,
            empathy_score=70,
            objection_handling=85,
            completeness_score=90,
        )
    )
    resp = await async_client.get(f"/api/v1/analyst/stats/{uid}", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_sessions"] == 1
    assert data["completed_sessions"] == 1
    assert data["avg_overall_score"] == 85.0


@pytest.mark.asyncio
async def test_get_score_distribution(
    async_client: httpx.AsyncClient,
    eval_repo: InMemoryEvaluationRepository,
    session_repo: InMemorySessionRepository,
    auth_header: dict[str, str],
) -> None:
    """GET /analyst/distribution/{uid} should return 6 dimensions."""
    uid = uuid4()
    sid = uuid4()
    session = await session_repo.create(
        SessionCreate(user_id=uid, scenario_id=sid, status=SessionStatus.COMPLETED)
    )
    await eval_repo.create(
        EvaluationCreate(
            session_id=session.id, user_id=uid, overall_score=85,
            script_adherence=80, tone_score=75, empathy_score=70,
            objection_handling=85, completeness_score=90,
        )
    )
    resp = await async_client.get(f"/api/v1/analyst/distribution/{uid}", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 6
    assert data[0]["dimension"] == "overall_score"
    assert "bins" in data[0]


@pytest.mark.asyncio
async def test_get_progress(
    async_client: httpx.AsyncClient,
    eval_repo: InMemoryEvaluationRepository,
    session_repo: InMemorySessionRepository,
    auth_header: dict[str, str],
) -> None:
    """GET /analyst/progress/{uid} should return progress points."""
    uid = uuid4()
    sid = uuid4()
    session = await session_repo.create(
        SessionCreate(user_id=uid, scenario_id=sid, status=SessionStatus.COMPLETED)
    )
    await eval_repo.create(
        EvaluationCreate(
            session_id=session.id, user_id=uid, overall_score=92,
            script_adherence=85, tone_score=88, empathy_score=80,
            objection_handling=90, completeness_score=85,
        )
    )
    resp = await async_client.get(f"/api/v1/analyst/progress/{uid}", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["overall_score"] == 92.0


@pytest.mark.asyncio
async def test_get_progress_with_limit(
    async_client: httpx.AsyncClient,
    eval_repo: InMemoryEvaluationRepository,
    session_repo: InMemorySessionRepository,
    auth_header: dict[str, str],
) -> None:
    """GET /analyst/progress/{uid}?limit=5 should respect the limit parameter."""
    uid = uuid4()
    sid = uuid4()
    for score in [70, 80, 90]:
        session = await session_repo.create(
            SessionCreate(
                user_id=uid, scenario_id=sid, status=SessionStatus.COMPLETED
            )
        )
        await eval_repo.create(
            EvaluationCreate(
                session_id=session.id, user_id=uid, overall_score=score,
                script_adherence=score - 5, tone_score=score - 10,
                empathy_score=score - 15, objection_handling=score - 5,
                completeness_score=score - 10,
            )
        )
    resp = await async_client.get(f"/api/v1/analyst/progress/{uid}?limit=2", headers=auth_header)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_router_mounted(
    async_client: httpx.AsyncClient,
    rbac_admin_header: dict[str, str],
) -> None:
    """Verify the analyst router is included in the main app."""
    resp = await async_client.get("/api/v1/analyst/stats", headers=rbac_admin_header)
    assert resp.status_code == 200, "Analyst router should be mounted"


@pytest.mark.asyncio
async def test_invalid_uuid_returns_422(
    async_client: httpx.AsyncClient,
    auth_header: dict[str, str],
) -> None:
    """GET with invalid UUID should return 422."""
    resp = await async_client.get("/api/v1/analyst/stats/not-a-uuid", headers=auth_header)
    assert resp.status_code == 422
