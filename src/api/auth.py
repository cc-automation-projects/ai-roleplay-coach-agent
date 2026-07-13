"""Authentication API endpoints — register, login, refresh, logout, me."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.dependencies import (
    get_auth_service,
    get_current_user,
    get_page_params,
    get_user_repo,
    require_role,
)
from core.dto.pagination import Page, PageParams
from core.entities.user import User, UserRole
from core.exceptions import AuthorizationError, DuplicateError

if TYPE_CHECKING:
    from core.entities.user import User
    from core.interfaces.repositories import UserRepository
    from core.services.auth_service import AuthService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ── Request / Response models ──────────────────────────────────────────


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserInfo(BaseModel):
    user_id: str
    username: str
    role: str
    email: str
    is_active: bool


# ── Endpoints ──────────────────────────────────────────────────────────


@router.post("/register", status_code=201)
async def register(
    body: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Register a new user. Returns TokenPair + user info."""
    try:
        return await auth_service.register(body.username, body.password)
    except DuplicateError:
        raise HTTPException(status_code=409, detail="Username already exists") from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/login")
async def login(
    body: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Authenticate and return TokenPair."""
    try:
        tokens = await auth_service.login(body.username, body.password)
    except AuthorizationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return tokens.model_dump()


@router.post("/refresh")
async def refresh(
    body: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Exchange a refresh token for a new token pair."""
    try:
        tokens = await auth_service.refresh_token(body.refresh_token)
    except AuthorizationError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return tokens.model_dump()


@router.post("/logout")
async def logout(
    body: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Revoke a refresh token."""
    await auth_service.logout(body.refresh_token)
    return {"detail": "Logged out"}


@router.get("/me")
async def me(
    current_user: User = Depends(get_current_user),
) -> UserInfo:
    """Return current user info (requires valid Bearer token)."""
    return UserInfo(
        user_id=str(current_user.id),
        username=current_user.username,
        role=current_user.role.value,
        email=str(current_user.email),
        is_active=current_user.is_active,
    )


@router.get("/users")
async def list_users(
    page_params: PageParams = Depends(get_page_params),
    _admin: User = Depends(require_role(UserRole.ADMIN)),
    user_repo: UserRepository = Depends(get_user_repo),
) -> Page[UserInfo]:
    """Return paginated list of all users (admin only)."""
    users = await user_repo.list_all(skip=page_params.skip, limit=page_params.size)
    total = await user_repo.count()
    return Page(
        items=[
            UserInfo(
                user_id=str(u.id),
                username=u.username,
                role=u.role.value,
                email=str(u.email),
                is_active=u.is_active,
            )
            for u in users
        ],
        total=total,
        page=page_params.page,
        size=page_params.size,
    )
