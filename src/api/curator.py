"""Curator agent API endpoints — learning plans, quizzes, LMS sync."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from agents.curator.agent import CuratorAgentImpl
from api.dependencies import (
    get_curator,
    get_current_user,
    get_eval_repo,
    get_scenario_repo,
    require_role,
)
from core.entities import Evaluation, LearningPlan, MicroQuiz
from core.entities.user import User, UserRole
from core.exceptions import CuratorError
from core.interfaces.repositories import EvaluationRepository, ScenarioRepository

router = APIRouter(prefix="/api/v1/curator", tags=["curator"])


class LearningPlanRequest(BaseModel):
    scenario_id: UUID


class QuizRequest(BaseModel):
    scenario_id: UUID
    question_count: int = 5


class QuizResponse(BaseModel):
    quiz: MicroQuiz


class SyncLMSRequest(BaseModel):
    plan_id: UUID


@router.post("/learning-plan")
async def generate_learning_plan(
    body: LearningPlanRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    curator: Annotated[CuratorAgentImpl, Depends(get_curator)],
    scenario_repo: Annotated[ScenarioRepository, Depends(get_scenario_repo)],
    eval_repo: Annotated[EvaluationRepository, Depends(get_eval_repo)],
) -> LearningPlan:
    """Generate a learning plan based on evaluation history."""
    scenario = await scenario_repo.get_by_id(body.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Load user's evaluations for plan generation
    evaluations: list[Evaluation] = await eval_repo.list_by_user(current_user.id)

    try:
        return await curator.generate_learning_plan(
            user_id=current_user.id,
            evaluations=evaluations,
            scenario=scenario,
        )
    except CuratorError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/quiz")
async def generate_quiz(
    body: QuizRequest,
    _current_user: Annotated[User, Depends(require_role(UserRole.TRAINER, UserRole.ADMIN))],
    curator: Annotated[CuratorAgentImpl, Depends(get_curator)],
    scenario_repo: Annotated[ScenarioRepository, Depends(get_scenario_repo)],
) -> QuizResponse:
    """Generate a micro-quiz for a scenario (trainer+)."""
    scenario = await scenario_repo.get_by_id(body.scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    quiz = await curator.generate_quiz(scenario, question_count=body.question_count)
    return QuizResponse(quiz=quiz)


@router.post("/sync-lms")
async def sync_to_lms(
    body: SyncLMSRequest,
    _current_user: Annotated[User, Depends(require_role(UserRole.ADMIN))],
) -> dict:
    """Stub: sync a learning plan to LMS (admin only)."""
    plan_id_str = str(body.plan_id)
    course_id = f"COACH-{hash(plan_id_str) % 100000:05d}"
    lms_url = f"https://lms.example.com/api/v1/courses/{course_id}"
    return {
        "status": "synced",
        "lms_course_id": course_id,
        "lms_url": lms_url,
        "plan_id": plan_id_str,
    }
