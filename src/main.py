"""FastAPI application entry point for AI Roleplay Coach Hub."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from starlette.requests import Request

import structlog
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from api.dependencies import (
    get_scenario_repo,
    get_user_repo,
)
from api.middleware import RequestIDMiddleware
from api.router import api_router
from core.config import settings
from core.dto.problem_detail import ProblemDetail
from core.entities import DifficultyLevel, Psychotype, ScenarioCreate, UserCreate, UserRole

logger = structlog.get_logger(__name__)

_SEED_USER_COUNT = 3


async def _seed_data() -> None:
    """Pre-populate in-memory stores with sample data."""
    user_repo = get_user_repo()
    scenario_repo = get_scenario_repo()

    for i in range(1, _SEED_USER_COUNT + 1):
        existing = await user_repo.get_by_email(f"operator{i}@example.com")
        if existing is None:
            await user_repo.create(
                UserCreate(
                    username=f"operator{i}",
                    hashed_password="",  # no auth in dev seed
                    email=f"operator{i}@example.com",
                    name=f"Operator {i}",
                    role=UserRole.TRAINER if i == _SEED_USER_COUNT else UserRole.OPERATOR,
                ),
            )

    samples: list[ScenarioCreate] = [
        ScenarioCreate(
            name="Tech Support Call",
            description="Customer with internet outage — diagnose and resolve",
            difficulty=DifficultyLevel.BEGINNER,
            psychotype=Psychotype.NEUTRAL,
            script_ref="TS-001",
            script_text=(
                "Greet the customer warmly. Identify their account details. "
                "Diagnose the issue step by step. Offer a solution. "
                "Confirm the fix worked. Close the call professionally. "
                "Follow up within 24 hours."
            ),
            tags=["support", "internet"],
        ),
        ScenarioCreate(
            name="Billing Complaint",
            description="Upset customer about incorrect charge — de-escalate",
            difficulty=DifficultyLevel.INTERMEDIATE,
            psychotype=Psychotype.AGGRESSIVE,
            script_ref="BILL-002",
            script_text=(
                "Listen to the complaint without interrupting. "
                "Apologize for the inconvenience. "
                "Explain the charge clearly. "
                "Offer a resolution or credit. "
                "Confirm the customer is satisfied."
            ),
            tags=["billing", "complaint"],
        ),
        ScenarioCreate(
            name="New Product Inquiry",
            description="Customer asking about product features — upsell",
            difficulty=DifficultyLevel.BEGINNER,
            psychotype=Psychotype.CONFUSED,
            script_ref="SALES-003",
            script_text=(
                "Greet and engage the customer. "
                "Identify their needs by asking open-ended questions. "
                "Recommend the most suitable product. "
                "Explain key features and benefits. "
                "Close with a call to action."
            ),
            tags=["sales", "product"],
        ),
    ]

    for s in samples:
        all_scenarios = await scenario_repo.list_all()
        if not any(sc.name == s.name for sc in all_scenarios):
            await scenario_repo.create(s)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: C901, PLR0915
    """Application lifespan — setup/teardown."""
    # Configure structured logging
    from infrastructure.logging import configure_logging  # noqa: PLC0415

    configure_logging(fmt=settings.LOG_FORMAT, level=settings.LOG_LEVEL)

    # Validate configuration (can raise)
    try:
        settings.validate()
    except ValueError as e:
        logger.critical("Configuration validation failed: %s", e)
        msg = f"Configuration validation failed: {e}"
        raise RuntimeError(msg) from e

    _ = app
    logger.info("Application starting — seeding data", log_format=settings.LOG_FORMAT)
    await _seed_data()
    logger.info("Seed data loaded (3 users, 3 scenarios)")

    # ── Periodic fairness audit (non-blocking) ──────────────────────
    fairness_task: asyncio.Task[None] | None = None
    if settings.FAIRNESS_ENABLED and Path(settings.FAIRNESS_CONFIG_PATH).exists():  # noqa: ASYNC240
        import yaml  # noqa: PLC0415

        from agents.analyst.fairness_service import FairnessService  # noqa: PLC0415
        from api.dependencies import get_eval_repo, get_user_repo  # noqa: PLC0415
        from core.entities.fairness import FairnessConfig  # noqa: PLC0415
        from infrastructure.notification.stub import StubNotificationService  # noqa: PLC0415

        raw = yaml.safe_load(Path(settings.FAIRNESS_CONFIG_PATH).read_text(encoding="utf-8"))  # noqa: ASYNC240
        fairness_cfg = FairnessConfig.from_dict(raw)
        fairness_svc = FairnessService(
            user_repo=get_user_repo(),
            eval_repo=get_eval_repo(),
            config=fairness_cfg,
        )
        notifier = StubNotificationService()
        interval = max(1, settings.FAIRNESS_AUDIT_INTERVAL_HOURS) * 3600

        async def _periodic_fairness_audit() -> None:
            """Run fairness audit periodically (default: once per week)."""
            try:
                # First run after 1 hour to let data accumulate
                await asyncio.sleep(3600)
                while True:
                    logger.info("Running periodic fairness audit")
                    try:
                        report = await fairness_svc.generate_report(
                            user_ids=None, scenario_ids=None,
                        )
                        for m in report.metrics:
                            if not m.passed and fairness_cfg.alerting.enabled:
                                logger.warning(
                                    "FAIRNESS_ALERT: periodic audit",
                                    metric=m.metric_name.value,
                                    group=m.group,
                                    value=m.value,
                                    threshold=m.threshold,
                                )
                                if fairness_cfg.alerting.threshold_breach_action == "log":
                                    notifier.send_alert(
                                        metric=m.metric_name.value,
                                        group=m.group,
                                        value=m.value,
                                        threshold=m.threshold,
                                    )
                    except Exception:
                        logger.exception("Fairness audit iteration failed")
                    await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger.info("Periodic fairness audit cancelled")
                raise

        fairness_task = asyncio.create_task(_periodic_fairness_audit())
        logger.info(
            "Periodic fairness audit scheduled",
            interval_hours=settings.FAIRNESS_AUDIT_INTERVAL_HOURS,
            first_run_delay_minutes=60,
        )
    else:
        logger.info(
            "Periodic fairness audit disabled (FAIRNESS_ENABLED=%s)",
            settings.FAIRNESS_ENABLED,
        )

    try:
        yield
    finally:
        logger.info("Application shutting down — cleaning up resources")

        # Cancel periodic fairness audit if running
        if fairness_task is not None and not fairness_task.done():
            fairness_task.cancel()

        # Close database connections
        try:
            from infrastructure.postgres.database import Database  # noqa: PLC0415
            db = Database()
            await db.close()
        except Exception:
            logger.exception("Error closing database")

        # Close LLM provider (if any)
        try:
            from api.dependencies import get_llm_provider  # noqa: PLC0415
            provider = get_llm_provider()
            if hasattr(provider, "aclose"):
                await provider.aclose()
        except Exception:
            logger.exception("Error closing LLM provider")

        # Close Qdrant client if any
        try:
            from infrastructure.qdrant.client import QdrantStore  # noqa: PLC0415
            store = QdrantStore()
            await store.close()
        except Exception:
            logger.exception("Error closing Qdrant client")

        # Allow background tasks to finish (with timeout)
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if tasks:
            logger.info("Waiting for %d background tasks to finish...", len(tasks))
            _done, pending = await asyncio.wait(tasks, timeout=5.0)
            if pending:
                logger.warning("Cancelling %d pending tasks", len(pending))
                for t in pending:
                    t.cancel()
        logger.info("Shutdown complete")


app = FastAPI(
    title="AI Roleplay Coach Hub",
    version="0.1.0",
    lifespan=lifespan,
)

if settings.CORS_ORIGINS == ["*"]:
    logger.warning(
        'CORS_ORIGINS is set to ["*"] — wide open. '
        'Restrict to specific origins in production (e.g. ["https://app.example.com"]).'
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)

from api.metrics import MetricsMiddleware  # noqa: E402

app.add_middleware(MetricsMiddleware)

from api.rate_limit import RateLimitMiddleware  # noqa: E402

app.add_middleware(
    RateLimitMiddleware,
    default_limit=settings.RATE_LIMIT_DEFAULT,
    default_window=settings.RATE_LIMIT_WINDOW,
    auth_limit=settings.RATE_LIMIT_AUTH,
    auth_window=settings.RATE_LIMIT_WINDOW,
)

from api.security_headers import SecurityHeadersMiddleware  # noqa: E402

app.add_middleware(SecurityHeadersMiddleware)

from api.auth_rate_limit_middleware import AuthRateLimitMiddleware  # noqa: E402

app.add_middleware(AuthRateLimitMiddleware)

# ── RFC 9457 Problem Details handlers ──────────────────────────────


def _problem_response(status: int, title: str, detail: str | None = None,
                      instance: str | None = None, **extra: object) -> JSONResponse:
    """Build an RFC 9457 JSON response."""
    body = ProblemDetail(
        type="about:blank",
        title=title,
        status=status,
        detail=detail,
        instance=instance,
        **extra,
    ).model_dump(exclude_none=True)
    return JSONResponse(status_code=status, content=body)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException,
) -> JSONResponse:
    return _problem_response(
        status=exc.status_code,
        title=HTTPStatus(exc.status_code).phrase,
        detail=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
        instance=str(request.url),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError,
) -> JSONResponse:
    return _problem_response(
        status=422,
        title="Validation Error",
        detail="Request validation failed",
        instance=str(request.url),
        errors=exc.errors(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception,
) -> JSONResponse:
    logger.error("Unhandled exception", exc_info=exc, path=str(request.url))
    return _problem_response(
        status=500,
        title="Internal Server Error",
        detail="An unexpected error occurred",
        instance=str(request.url),
    )


app.include_router(api_router)

from api.metrics import metrics_router  # noqa: E402

app.include_router(metrics_router)


import time as _time  # noqa: E402

_start_time: float = _time.time()


@app.get("/health")
async def health() -> dict[str, object]:
    """Health check endpoint — liveness probe."""
    return {
        "status": "ok",
        "version": "0.1.0",
        "uptime_seconds": round(_time.time() - _start_time),
    }


@app.get("/ready")
async def ready() -> dict[str, object]:
    """Readiness probe — all components are available."""
    # In-memory mode is always ready; production DB/CB checks
    # can be added when the relevant infrastructure is wired.
    return {
        "status": "ok",
        "version": "0.1.0",
        "uptime_seconds": round(_time.time() - _start_time),
        "components": {
            "auth": "ok",
            "simulator": "ok",
            "coach": "ok",
            "curator": "ok",
            "gamification": "ok",
            "analyst": "ok",
        },
    }
