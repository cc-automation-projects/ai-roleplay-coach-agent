"""Main API router — aggregates all sub-routers."""

from fastapi import APIRouter

from api.analyst import router as analyst_router
from api.auth import router as auth_router
from api.coach import router as coach_router
from api.curator import router as curator_router
from api.gamification import router as gamification_router
from api.sessions import router as sessions_router
from api.simulator import router as simulator_router

api_router = APIRouter()
api_router.include_router(sessions_router)
api_router.include_router(simulator_router)
api_router.include_router(coach_router)
api_router.include_router(curator_router)
api_router.include_router(gamification_router)
api_router.include_router(analyst_router)
api_router.include_router(auth_router)
