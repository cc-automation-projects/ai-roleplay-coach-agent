"""Analyst API — metrics and dashboard endpoints."""

from collections import deque
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Query

from agents.analyst.fairness_service import FairnessService
from agents.analyst.service import AnalystService
from api.dependencies import (
    get_analyst_service,
    get_current_user,
    get_fairness_service,
    require_role,
)
from core.entities.user import User, UserRole

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/analyst", tags=["analyst"])

# In-memory ring buffer for report history (max 100 entries).
_REPORT_HISTORY: deque[dict] = deque(maxlen=100)


@router.get("/stats")
async def get_global_stats(
    _current_user: Annotated[User, Depends(require_role(UserRole.TRAINER, UserRole.ADMIN))],
    analyst: Annotated[AnalystService, Depends(get_analyst_service)],
) -> dict:
    """Return global platform-wide statistics (trainer+)."""
    stats = await analyst.get_global_stats()
    return stats.model_dump()  # type: ignore[no-any-return]


@router.get("/stats/{user_id}")
async def get_user_stats(
    user_id: UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    analyst: Annotated[AnalystService, Depends(get_analyst_service)],
) -> dict:
    """Return aggregated session stats for a specific user."""
    stats = await analyst.get_session_stats(user_id)
    return stats.model_dump()  # type: ignore[no-any-return]


@router.get("/distribution/{user_id}")
async def get_score_distribution(
    user_id: UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    analyst: Annotated[AnalystService, Depends(get_analyst_service)],
) -> list[dict]:
    """Return histogram bins for each evaluation dimension for a user."""
    dist = await analyst.get_score_distribution(user_id)
    return [d.model_dump() for d in dist]


@router.get("/progress/{user_id}")
async def get_progress(
    user_id: UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    analyst: Annotated[AnalystService, Depends(get_analyst_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[dict]:
    """Return time-series of overall scores for a user."""
    points = await analyst.get_progress_over_time(user_id, limit=limit)
    return [p.model_dump() for p in points]


# ── Fairness endpoints (ADMIN only) ──────────────────────────────────


@router.get("/fairness/report")
async def get_fairness_report(
    _current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    fairness: Annotated[FairnessService, Depends(get_fairness_service)],
    scenario_id: UUID | None = Query(default=None),
) -> dict:
    """Generate a fairness report, optionally filtered by scenario."""
    user_ids: list[UUID] | None = None
    scenario_ids: list[UUID] | None = [scenario_id] if scenario_id else None
    report = await fairness.generate_report(
        user_ids=user_ids,
        scenario_ids=scenario_ids,
    )
    payload = {
        "report_id": str(report.report_id),
        "generated_at": report.generated_at.isoformat(),
        "summary": report.summary.value,
        "config_version": report.config_version,
        "metrics": [
            {
                "metric_name": m.metric_name.value,
                "value": m.value,
                "group": m.group,
                "attribute": m.attribute,
                "threshold": m.threshold,
                "passed": m.passed,
            }
            for m in report.metrics
        ],
    }
    _REPORT_HISTORY.append(payload)
    return payload


@router.get("/fairness/groups")
async def get_fairness_groups(
    _current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    fairness: Annotated[FairnessService, Depends(get_fairness_service)],
) -> list[dict]:
    """Return the list of protected attributes from the fairness config."""
    return [
        {"name": a.name, "values": a.values, "description": a.description}
        for a in fairness._config.protected_attributes  # noqa: SLF001
    ]


@router.get("/fairness/history")
async def get_fairness_history(
    _current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
) -> list[dict]:
    """Return paginated history of previously generated reports."""
    all_reports = list(_REPORT_HISTORY)
    return all_reports[skip : skip + limit]
