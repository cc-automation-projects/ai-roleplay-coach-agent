"""Session lifecycle API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.dependencies import (
    get_current_user,
    get_evaluation_service,
    get_page_params,
    get_session_repo,
    get_session_service,
    require_role,
)
from core.dto.pagination import Page, PageParams
from core.entities import Evaluation, Session
from core.entities.user import User, UserRole
from core.exceptions import BusinessRuleViolationError, NotFoundError
from core.interfaces.repositories import SessionRepository
from core.services.evaluation_service import EvaluationService
from core.services.session_service import SessionService

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


# ── Request/Response DTOs ─────────────────────────────────────────────


class StartSessionRequest(BaseModel):
    """Request to start a new session (user_id comes from JWT)."""
    scenario_id: UUID


class TurnRequest(BaseModel):
    user_id: UUID
    message: str


class EvaluateResponse(BaseModel):
    session: Session
    evaluation: Evaluation


@router.get("")
async def list_sessions(
    page_params: Annotated[PageParams, Depends(get_page_params)],
    current_user: Annotated[User, Depends(get_current_user)],
    session_repo: Annotated[SessionRepository, Depends(get_session_repo)],
) -> Page[Session]:
    """Return paginated list of sessions for the current user."""
    items = await session_repo.list_by_user(
        current_user.id,
        skip=page_params.skip,
        limit=page_params.size,
    )
    total = await session_repo.count_by_user(current_user.id)
    return Page(items=items, total=total, page=page_params.page, size=page_params.size)


@router.post("", status_code=status.HTTP_201_CREATED)
async def start_session(
    body: StartSessionRequest,
    current_user: Annotated[
        User,
        Depends(require_role(UserRole.OPERATOR, UserRole.TRAINER, UserRole.ADMIN)),
    ],
    svc: Annotated[SessionService, Depends(get_session_service)],
) -> Session:
    """Start a new simulation session for the authenticated user."""
    try:
        return await svc.start_session(
            user_id=current_user.id,
            scenario_id=body.scenario_id,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{session_id}/turns")
async def process_turn(
    session_id: UUID,
    body: TurnRequest,
    _current_user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[SessionService, Depends(get_session_service)],
) -> Session:
    """Process an operator turn and get client response."""
    try:
        await svc.process_turn(
            session_id=session_id,
            operator_text=body.message,
        )
    except (NotFoundError, BusinessRuleViolationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    session = await svc.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/{session_id}/finish")
async def finish_session(
    session_id: UUID,
    _current_user: Annotated[User, Depends(
        require_role(UserRole.OPERATOR, UserRole.TRAINER, UserRole.ADMIN),
    )],
    svc: Annotated[SessionService, Depends(get_session_service)],
) -> Session:
    """Mark a session as completed."""
    try:
        return await svc.finish_session(session_id)
    except (NotFoundError, BusinessRuleViolationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{session_id}/evaluate")
async def evaluate_session(
    session_id: UUID,
    _current_user: Annotated[User, Depends(require_role(UserRole.TRAINER, UserRole.ADMIN))],
    svc: Annotated[SessionService, Depends(get_session_service)],
    eval_svc: Annotated[EvaluationService, Depends(get_evaluation_service)],
) -> EvaluateResponse:
    """Evaluate a completed session and persist the evaluation."""
    try:
        evaluation = await svc.evaluate_session(session_id)
        if evaluation:
            await eval_svc.save_evaluation(evaluation)
        session = await svc.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return EvaluateResponse(session=session, evaluation=evaluation)
    except (NotFoundError, BusinessRuleViolationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{session_id}")
async def get_session(
    session_id: UUID,
    _current_user: Annotated[User, Depends(get_current_user)],
    svc: Annotated[SessionService, Depends(get_session_service)],
) -> Session:
    """Get session details by ID."""
    try:
        return await svc.get_session(session_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
