"""Coach agent standalone API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from agents.coach.agent import CoachAgent
from api.dependencies import get_coach, get_current_user, get_scenario_repo, get_session_service
from core.entities import Evaluation
from core.entities.user import User
from core.exceptions import NotFoundError
from core.interfaces.repositories import ScenarioRepository
from core.services.session_service import SessionService

router = APIRouter(prefix="/api/v1/coach", tags=["coach"])


class EvaluateRequest(BaseModel):
    session_id: UUID


@router.post("/evaluate")
async def evaluate_session(
    body: EvaluateRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
    coach: Annotated[CoachAgent, Depends(get_coach)],
    svc: Annotated[SessionService, Depends(get_session_service)],
    scenario_repo: Annotated[ScenarioRepository, Depends(get_scenario_repo)],
) -> Evaluation:
    """Evaluate a session by ID (standalone, no persistence)."""
    try:
        session = await svc.get_session(body.session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    scenario = await scenario_repo.get_by_id(session.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    try:
        return await coach.evaluate_session(session, scenario)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
