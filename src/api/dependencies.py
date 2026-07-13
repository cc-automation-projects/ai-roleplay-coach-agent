"""FastAPI dependency injection wiring.

Wires in-memory repositories + rule-based or LLM-powered agent
implementations based on LLM_PROVIDER env var.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

import structlog
import yaml
from fastapi import Depends, Header, HTTPException, status
from pydantic import ValidationError

from agents.analyst.fairness_service import FairnessService
from agents.analyst.service import AnalystService
from agents.coach.adapter import LLMCoachAdapter
from agents.coach.agent import CoachAgent
from agents.coach.llm_agent import LLMCoachAgent
from agents.curator.agent import CuratorAgentImpl
from agents.gamification.engine import GamificationEngine
from agents.simulator.agent import SimulatorAgent as SimulatorAgentImpl
from agents.simulator_llm.adapter import LLMSimulatorAdapter
from agents.simulator_llm.agent import LLMSimulatorAgent
from core.dto.pagination import PageParams as _PageParams
from core.entities.fairness import FairnessConfig
from core.entities.user import UserRole
from core.exceptions import AuthorizationError
from core.services.auth_service import AuthService
from core.services.circuit_breaker import CircuitBreakerRegistry
from core.services.evaluation_service import EvaluationService
from core.services.session_service import SessionService
from infrastructure.llm.factory import create_llm_provider
from infrastructure.memory.repositories import (
    InMemoryBadgeRepository,
    InMemoryEvaluationRepository,
    InMemoryScenarioRepository,
    InMemorySessionRepository,
    InMemoryUserRepository,
    InMemoryXPTransactionRepository,
)
from infrastructure.redis.token_store import InMemoryTokenStore, RedisTokenStore

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from core.entities.user import User
    from core.interfaces.agents import CoachAgent as CoachAgentProtocol
    from core.interfaces.agents import SimulatorAgent

logger = structlog.get_logger(__name__)


async def get_page_params(
    page: int = 1,
    size: int = 20,
) -> _PageParams:
    """FastAPI dependency that yields validated pagination parameters."""
    try:
        return _PageParams(page=page, size=size)
    except ValidationError:
        raise HTTPException(
            status_code=422, detail={"detail": "Invalid pagination parameters"}
        ) from None


@lru_cache
def get_session_repo() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@lru_cache
def get_scenario_repo() -> InMemoryScenarioRepository:
    return InMemoryScenarioRepository()


@lru_cache
def get_user_repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@lru_cache
def get_eval_repo() -> InMemoryEvaluationRepository:
    return InMemoryEvaluationRepository()


@lru_cache
def get_badge_repo() -> InMemoryBadgeRepository:
    return InMemoryBadgeRepository()


@lru_cache
def get_xp_repo() -> InMemoryXPTransactionRepository:
    return InMemoryXPTransactionRepository()


# ── Agent singletons ─────────────────────────────────────────────────


@lru_cache
def get_llm_provider() -> Any:
    """Return the LLM provider instance (cached)."""
    return create_llm_provider()


@lru_cache
def get_simulator() -> SimulatorAgent:
    """Return SimulatorAgent — rule-based or LLM-powered based on LLM_PROVIDER.

    LLM_PROVIDER=mock       → rule-based SimulatorAgent
    LLM_PROVIDER=ollama|openai_compat → LLMSimulatorAgent + adapter
    """
    provider_name = os.getenv("LLM_PROVIDER", "mock").lower().strip()
    if provider_name in ("ollama", "openai_compat"):
        llm = create_llm_provider()
        llm_agent = LLMSimulatorAgent(llm)
        logger.info("Using LLM-powered SimulatorAgent (%s)", provider_name)
        return LLMSimulatorAdapter(llm_agent)  # type: ignore[no-any-return]
    logger.info("Using rule-based SimulatorAgent")
    return SimulatorAgentImpl()  # type: ignore[no-any-return]


@lru_cache
def get_coach() -> CoachAgentProtocol:
    """Return CoachAgent — rule-based or LLM-powered based on LLM_PROVIDER.

    LLM_PROVIDER=mock       → rule-based CoachAgent
    LLM_PROVIDER=ollama|openai_compat → LLMCoachAgent + adapter with CircuitBreaker
    """
    provider_name = os.getenv("LLM_PROVIDER", "mock").lower().strip()
    if provider_name in ("ollama", "openai_compat"):
        llm = create_llm_provider()
        llm_agent = LLMCoachAgent(llm=llm, rule_based=CoachAgent())
        cb_registry = get_circuit_breaker_registry()
        logger.info("Using LLM-powered CoachAgent (%s)", provider_name)
        return LLMCoachAdapter(llm_agent, CoachAgent(), cb_registry)  # type: ignore[no-any-return]
    logger.info("Using rule-based CoachAgent")
    return CoachAgent()  # type: ignore[no-any-return]


@lru_cache
def get_curator() -> CuratorAgentImpl:
    """Return a rule-based CuratorAgentImpl singleton."""
    return CuratorAgentImpl()


@lru_cache
def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Return a singleton CircuitBreakerRegistry."""
    return CircuitBreakerRegistry()


@lru_cache
def get_gamification_engine() -> GamificationEngine:
    """Wire GamificationEngine with in-memory repos."""
    return GamificationEngine(
        user_repo=get_user_repo(),
        xp_repo=get_xp_repo(),
        badge_repo=get_badge_repo(),
    )


# ── Services ──────────────────────────────────────────────────────────


@lru_cache
def get_session_service() -> SessionService:
    """Wire SessionService with in-memory repos + agents."""
    return SessionService(
        session_repo=get_session_repo(),
        scenario_repo=get_scenario_repo(),
        simulator=get_simulator(),
        coach=get_coach(),
        user_repo=get_user_repo(),
        eval_repo=get_eval_repo(),
    )


@lru_cache
def get_evaluation_service() -> EvaluationService:
    """Wire EvaluationService with in-memory repos and gamification engine."""
    return EvaluationService(
        eval_repo=get_eval_repo(),
        user_repo=get_user_repo(),
        xp_repo=get_xp_repo(),
        gamification_engine=get_gamification_engine(),
    )


@lru_cache
def get_analyst_service() -> AnalystService:
    """Wire AnalystService with in-memory repos."""
    return AnalystService(
        eval_repo=get_eval_repo(),
        session_repo=get_session_repo(),
        user_repo=get_user_repo(),
    )


@lru_cache
def get_fairness_service() -> FairnessService:
    """Wire FairnessService singleton with in-memory repos + YAML config."""
    raw = yaml.safe_load(Path("fairness_config.yaml").read_text(encoding="utf-8"))
    cfg = FairnessConfig.from_dict(raw)
    return FairnessService(
        user_repo=get_user_repo(),
        eval_repo=get_eval_repo(),
        config=cfg,
    )


@lru_cache
def get_token_store() -> InMemoryTokenStore | RedisTokenStore:
    """Return RedisTokenStore when REDIS_URL is set, else InMemoryTokenStore."""
    redis_url = os.getenv("REDIS_URL", "").strip()
    if redis_url:
        return RedisTokenStore(redis_url)
    return InMemoryTokenStore()


@lru_cache
def get_auth_service() -> AuthService:
    """Wire AuthService with user repo and token store."""
    return AuthService(user_repo=get_user_repo(), token_store=get_token_store())


async def get_current_user(
    authorization: str | None = Header(alias="authorization", default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """Extract and validate user from Bearer token."""
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")
    try:
        return await auth_service.get_current_user(token)
    except AuthorizationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


async def _require_role(current_user: User, roles: tuple[UserRole, ...]) -> User:
    """Validate that current_user has one of the given roles.

    ADMIN is granted a universal bypass — an admin user passes
    regardless of the required roles.
    """
    if current_user.role is UserRole.ADMIN:
        return current_user
    if current_user.role not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{current_user.role.value}' not in {[r.value for r in roles]}",
        )
    return current_user




def require_role(*roles: UserRole) -> Callable[[User], Coroutine[Any, Any, User]]:
    """FastAPI dependency factory: require current user to have one of the given roles.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            current_user: User = Depends(require_role(UserRole.ADMIN)),
        ):
            ...
    """
    async def _dependency(current_user: User = Depends(get_current_user)) -> User:
        return await _require_role(current_user, roles)

    return _dependency
