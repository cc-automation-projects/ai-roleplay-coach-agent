"""Simulator agent standalone API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.dependencies import get_current_user, get_scenario_repo, get_session_service, get_simulator
from core.entities import Psychotype
from core.entities.user import User
from core.exceptions import NotFoundError
from core.interfaces.agents import SimulatorAgent
from core.interfaces.repositories import ScenarioRepository
from core.services.session_service import SessionService

router = APIRouter(prefix="/api/v1/simulator", tags=["simulator"])


class StartDialogueRequest(BaseModel):
    scenario_id: UUID


class StartDialogueResponse(BaseModel):
    greeting: str
    psychotype: Psychotype


class RespondRequest(BaseModel):
    session_id: UUID


class RespondResponse(BaseModel):
    client_message: str


@router.post("/start")
async def start_dialogue(
    body: StartDialogueRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
    sim: Annotated[SimulatorAgent, Depends(get_simulator)],
    scenario_repo: Annotated[ScenarioRepository, Depends(get_scenario_repo)],
) -> StartDialogueResponse:
    """Start a new simulator dialogue (standalone)."""
    scenario = await scenario_repo.get_by_id(body.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    greeting, psychotype = await sim.start_dialogue(scenario)
    return StartDialogueResponse(greeting=greeting, psychotype=psychotype)


@router.post("/respond")
async def generate_response(
    body: RespondRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
    sim: Annotated[SimulatorAgent, Depends(get_simulator)],
    svc: Annotated[SessionService, Depends(get_session_service)],
) -> RespondResponse:
    """Generate a client response for a session."""
    try:
        session = await svc.get_session(body.session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    client_msg = await sim.generate_response(session)
    return RespondResponse(client_message=client_msg)


@router.post("/should-end/{session_id}")
async def should_end(
    session_id: UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    sim: Annotated[SimulatorAgent, Depends(get_simulator)],
    svc: Annotated[SessionService, Depends(get_session_service)],
) -> dict[str, bool]:
    """Check if the dialogue should end."""
    try:
        session = await svc.get_session(session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    result = await sim.should_end(session)
    return {"should_end": result}
