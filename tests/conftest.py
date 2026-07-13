"""Shared fixtures for all test suites — API, integration, e2e.

Provides: repo fixtures, test app with dependency overrides, async HTTP
client, seeded data, and rate-limit isolation.
"""

from collections.abc import AsyncIterator

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport

from core.entities import (
    DifficultyLevel,
    Psychotype,
    ScenarioCreate,
    UserCreate,
    UserRole,
)
from core.services.auth_service import AuthService
from infrastructure.memory.repositories import (
    InMemoryBadgeRepository,
    InMemoryEvaluationRepository,
    InMemoryScenarioRepository,
    InMemorySessionRepository,
    InMemoryUserRepository,
    InMemoryXPTransactionRepository,
)
from infrastructure.redis.token_store import InMemoryTokenStore

# ── Repo fixtures ──────────────────────────────────────────────────


@pytest.fixture
def session_repo() -> InMemorySessionRepository:
    return InMemorySessionRepository()


@pytest.fixture
def scenario_repo() -> InMemoryScenarioRepository:
    return InMemoryScenarioRepository()


@pytest.fixture
def user_repo() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def eval_repo() -> InMemoryEvaluationRepository:
    return InMemoryEvaluationRepository()


@pytest.fixture
def xp_repo() -> InMemoryXPTransactionRepository:
    return InMemoryXPTransactionRepository()


@pytest.fixture
def badge_repo() -> InMemoryBadgeRepository:
    return InMemoryBadgeRepository()


# ── App fixture ────────────────────────────────────────────────────


@pytest.fixture
def app(
    session_repo: InMemorySessionRepository,
    scenario_repo: InMemoryScenarioRepository,
    user_repo: InMemoryUserRepository,
    eval_repo: InMemoryEvaluationRepository,
    xp_repo: InMemoryXPTransactionRepository,
    badge_repo: InMemoryBadgeRepository,
) -> FastAPI:
    """Build a FastAPI app with test dependency overrides."""
    from agents.analyst.service import AnalystService
    from agents.coach.agent import CoachAgent
    from agents.curator.agent import CuratorAgentImpl
    from agents.gamification.engine import GamificationEngine
    from agents.simulator.agent import SimulatorAgent
    from api.dependencies import (
        get_analyst_service,
        get_auth_service,
        get_badge_repo,
        get_coach,
        get_curator,
        get_eval_repo,
        get_evaluation_service,
        get_gamification_engine,
        get_scenario_repo,
        get_session_repo,
        get_session_service,
        get_simulator,
        get_user_repo,
        get_xp_repo,
    )
    from core.services.evaluation_service import EvaluationService
    from core.services.session_service import SessionService
    from main import app as _app

    sim = SimulatorAgent()
    ch = CoachAgent()
    cur = CuratorAgentImpl()

    gengine = GamificationEngine(
        user_repo=user_repo,
        xp_repo=xp_repo,
        badge_repo=badge_repo,
    )

    svc = SessionService(
        session_repo=session_repo,
        scenario_repo=scenario_repo,
        simulator=sim,
        coach=ch,
        user_repo=user_repo,
    )
    eval_svc = EvaluationService(
        eval_repo=eval_repo,
        user_repo=user_repo,
        xp_repo=xp_repo,
    )

    analyst_svc = AnalystService(
        eval_repo=eval_repo,
        session_repo=session_repo,
        user_repo=user_repo,
    )

    auth_svc = AuthService(user_repo=user_repo, token_store=InMemoryTokenStore())

    overrides = {
        get_session_repo: lambda: session_repo,
        get_scenario_repo: lambda: scenario_repo,
        get_user_repo: lambda: user_repo,
        get_eval_repo: lambda: eval_repo,
        get_xp_repo: lambda: xp_repo,
        get_badge_repo: lambda: badge_repo,
        get_simulator: lambda: sim,
        get_coach: lambda: ch,
        get_curator: lambda: cur,
        get_session_service: lambda: svc,
        get_evaluation_service: lambda: eval_svc,
        get_gamification_engine: lambda: gengine,
        get_analyst_service: lambda: analyst_svc,
        get_auth_service: lambda: auth_svc,
    }

    for dep, impl in overrides.items():
        _app.dependency_overrides[dep] = impl

    return _app


# ── Async HTTP client ──────────────────────────────────────────────


@pytest.fixture
async def async_client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    """Provide an async HTTP client connected to the test app."""
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ── Rate-limit isolation ───────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_rate_limit_store() -> None:
    """Reset the global rate-limit store before every test.

    Prevents cross-test pollution: without this, tests that make many
    requests through the middleware (e.g. auth registration/login) can
    fill the sliding window and cause 429 failures in later tests.
    """
    from api.auth_rate_limit_middleware import _AUTH_STORE
    from api.rate_limit import _store as _global_store
    # Clear sliding window store
    _global_store._buckets.clear()
    _global_store._request_count = 0
    # Clear auth rate-limit store
    _AUTH_STORE.clear()


# ── Seeded data fixtures ───────────────────────────────────────────


_FAKE_HASH = "$2b$12$dummyhashfordevelopmenttestingonlyabc"


# ── Auth fixtures (register via API) ───────────────────────────────


async def _register_user(
    async_client: httpx.AsyncClient,
    username: str,
    pw: str,
) -> dict:
    """Register a user through the auth API."""
    import os

    pw = os.environ.get("TEST_PW", pw)
    resp = await async_client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": pw},
    )
    assert resp.status_code == 201, f"Register failed: {resp.text}"
    data = resp.json()
    return {
        "id": data["user_id"],
        "username": data["username"],
        "role": data["role"],
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


@pytest.fixture
async def operator_user(async_client: httpx.AsyncClient) -> dict:
    return await _register_user(async_client, "rbac_op", "tmpPw99!!")


@pytest.fixture
async def trainer_user(async_client: httpx.AsyncClient) -> dict:
    return await _register_user(async_client, "rbac_tr", "tmpPw99!!")


@pytest.fixture
async def admin_user(async_client: httpx.AsyncClient) -> dict:
    return await _register_user(async_client, "rbac_ad", "tmpPw99!!")


@pytest.fixture
def auth_header(operator_user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {operator_user['access_token']}"}


@pytest.fixture
def admin_auth_header(admin_user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_user['access_token']}"}


@pytest.fixture
def trainer_auth_header(trainer_user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {trainer_user['access_token']}"}


# ── Seeded data fixtures ───────────────────────────────────────────


@pytest.fixture
async def seeded_user(user_repo: InMemoryUserRepository) -> dict:
    """Create and return a test user."""
    user = await user_repo.create(
        UserCreate(
            username="operator",
            hashed_password=_FAKE_HASH,
            email="op@test.com",
            name="Test Operator",
            role=UserRole.OPERATOR,
        ),
    )
    return {"id": str(user.id), "email": user.email}


@pytest.fixture
async def seeded_scenario(scenario_repo: InMemoryScenarioRepository) -> dict:
    """Create and return a test scenario."""
    sc = await scenario_repo.create(
        ScenarioCreate(
            name="Test Scenario",
            description="A test scenario",
            difficulty=DifficultyLevel.BEGINNER,
            psychotype=Psychotype.NEUTRAL,
            script_ref="TEST-001",
            script_text="Greet. Identify. Solve.",
            tags=["test"],
        ),
    )
    return {"id": str(sc.id), "name": sc.name}
