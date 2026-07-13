"""Gamification REST API endpoints.

Exposes XP, badges, leaderboard, and streak data
via the existing GamificationEngine.
"""

from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException

from agents.gamification.engine import GamificationEngine
from api.dependencies import (
    get_badge_repo,
    get_current_user,
    get_gamification_engine,
    get_page_params,
    get_user_repo,
    get_xp_repo,
)
from core.dto.pagination import Page, PageParams
from core.entities.user import User
from core.interfaces.repositories import BadgeRepository, UserRepository, XPTransactionRepository

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/gamification", tags=["gamification"])


# ── XP endpoints ─────────────────────────────────────────────────────────


@router.get("/xp/{user_id}")
async def get_xp_balance(
    user_id: UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[GamificationEngine, Depends(get_gamification_engine)],
) -> dict:
    """Return XP balance + level for a user."""
    stats = await engine.get_user_stats(user_id)
    if not stats:
        raise HTTPException(status_code=404, detail="User not found")
    return stats


@router.get("/xp/{user_id}/history")
async def get_xp_history(
    user_id: UUID,
    page_params: Annotated[PageParams, Depends(get_page_params)],
    _current_user: Annotated[User, Depends(get_current_user)],
    xp_repo: Annotated[XPTransactionRepository, Depends(get_xp_repo)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> Page[dict]:
    """Return paginated XP transaction history."""
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    txns = await xp_repo.list_by_user(
        user_id, skip=page_params.skip, limit=page_params.size
    )
    total = await xp_repo.count_by_user(user_id)
    items = [
        {
            "id": str(t.id),
            "amount": t.amount,
            "reason": t.reason.value,
            "reference_id": str(t.reference_id) if t.reference_id else None,
            "created_at": t.created_at.isoformat(),
        }
        for t in txns
    ]
    return Page(items=items, total=total, page=page_params.page, size=page_params.size)


# ── Badge endpoints ──────────────────────────────────────────────────────


@router.get("/badges")
async def list_all_badges(
    _current_user: Annotated[User, Depends(get_current_user)],
    badge_repo: Annotated[BadgeRepository, Depends(get_badge_repo)],
) -> list[dict]:
    """Return all available badges."""
    badges = await badge_repo.list_all()
    return [
        {
            "id": str(b.id),
            "name": b.name,
            "description": b.description,
        }
        for b in badges
    ]


@router.get("/badges/{user_id}")
async def get_user_badges(
    user_id: UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    badge_repo: Annotated[BadgeRepository, Depends(get_badge_repo)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> list[dict]:
    """Return badges earned by a user."""
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    badges = await badge_repo.get_user_badges(user_id)
    return [
        {
            "id": str(b.id),
            "name": b.name,
            "description": b.description,
        }
        for b in badges
    ]


# ── Leaderboard endpoint ─────────────────────────────────────────────────


@router.get("/leaderboard")
async def get_leaderboard(
    page_params: Annotated[PageParams, Depends(get_page_params)],
    _current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[GamificationEngine, Depends(get_gamification_engine)],
) -> Page[dict]:
    """Return top users by XP."""
    items = await engine.get_leaderboard(
        limit=page_params.size, skip=page_params.skip
    )
    total = await engine.get_leaderboard_count()
    return Page(
        items=items, total=total, page=page_params.page, size=page_params.size
    )


# ── Streak endpoint ──────────────────────────────────────────────────────


@router.get("/streak/{user_id}")
async def get_streak(
    user_id: UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    engine: Annotated[GamificationEngine, Depends(get_gamification_engine)],
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
) -> dict:
    """Return current streak for a user."""
    user = await user_repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    streak = await engine.get_streak(user_id)
    return {"user_id": str(user_id), "streak": streak}
