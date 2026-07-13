"""API-specific fixtures — RBAC users with direct repo creation.

Shared fixtures (``app``, ``async_client``, ``auth_header``, repos, etc.)
live in ``tests/conftest.py`` and are inherited automatically.
"""

import pytest

from core.entities import UserCreate, UserRole
from core.services.auth_service import _create_access_token
from infrastructure.memory.repositories import InMemoryUserRepository

_FAKE_HASH = "$2b$12$dummyhashfordevelopmenttestingonlyabc"


@pytest.fixture
async def rbac_admin_user(
    user_repo: InMemoryUserRepository,
) -> dict:
    """Create an ADMIN user directly in repo (bypasses auth register)."""
    user = await user_repo.create(
        UserCreate(
            username="rbac_direct_admin",
            hashed_password=_FAKE_HASH,
            email="direct_admin@test.com",
            name="Direct Admin",
            role=UserRole.ADMIN,
        ),
    )
    token = _create_access_token(user)
    return {"id": str(user.id), "token": token}


@pytest.fixture
def rbac_admin_header(rbac_admin_user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {rbac_admin_user['token']}"}


@pytest.fixture
async def rbac_trainer_user(
    user_repo: InMemoryUserRepository,
) -> dict:
    """Create a TRAINER user directly in repo (bypasses auth register)."""
    user = await user_repo.create(
        UserCreate(
            username="rbac_direct_trainer",
            hashed_password=_FAKE_HASH,
            email="direct_trainer@test.com",
            name="Direct Trainer",
            role=UserRole.TRAINER,
        ),
    )
    token = _create_access_token(user)
    return {"id": str(user.id), "token": token}


@pytest.fixture
def rbac_trainer_header(rbac_trainer_user: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {rbac_trainer_user['token']}"}
