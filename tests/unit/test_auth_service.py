"""Unit tests for AuthService."""

from __future__ import annotations

from unittest.mock import patch
from uuid import UUID

import pytest
from jose import jwt

from core.config import settings
from core.exceptions import AuthorizationError, DuplicateError
from core.services.auth_service import AuthService, _create_access_token
from infrastructure.memory.repositories import InMemoryUserRepository
from infrastructure.redis.token_store import InMemoryTokenStore


@pytest.fixture
def svc() -> AuthService:
    return AuthService(
        user_repo=InMemoryUserRepository(),
        token_store=InMemoryTokenStore(),
    )


class TestRegister:

    async def test_register_success(self, svc: AuthService) -> None:
        result = await svc.register("fresh_user", "zD3k9mQx")
        assert "user_id" in result
        assert result["username"] == "fresh_user"
        assert result["role"] == "operator"
        assert "access_token" in result
        assert "refresh_token" in result
        assert UUID(result["user_id"])

    async def test_register_duplicate(self, svc: AuthService) -> None:
        await svc.register("dup_user", "zD3k9mQx")
        with pytest.raises(DuplicateError):
            await svc.register("dup_user", "zD3k9mQx")

    async def test_register_invalid_username_short(
        self, svc: AuthService,
    ) -> None:
        with pytest.raises(ValueError, match="Username must be 3-32"):
            await svc.register("ab", "zD3k9mQx")

    async def test_register_invalid_username_chars(
        self, svc: AuthService,
    ) -> None:
        with pytest.raises(ValueError, match="Username must be 3-32"):
            await svc.register("user name!", "zD3k9mQx")

    async def test_register_short_pwd(self, svc: AuthService) -> None:
        with pytest.raises(ValueError, match="at least 8 characters"):
            await svc.register("valid_user", "short")

    async def test_register_no_uppercase(self, svc: AuthService) -> None:
        with pytest.raises(ValueError, match="uppercase letter"):
            await svc.register("valid_user", "lowercase1")

    async def test_register_no_digit(self, svc: AuthService) -> None:
        with pytest.raises(ValueError, match="at least one digit"):
            await svc.register("valid_user", "NoDigitsHere")

    async def test_register_common_password(self, svc: AuthService) -> None:
        with pytest.raises(ValueError, match="too common"):
            await svc.register("valid_user", "Password1")


class TestLogin:

    async def test_login_success(self, svc: AuthService) -> None:
        await svc.register("login_user", "zD3k9mQx")
        tokens = await svc.login("login_user", "zD3k9mQx")
        assert tokens.access_token
        assert tokens.refresh_token
        assert tokens.token_type == "bearer"

    async def test_login_wrong_pwd(self, svc: AuthService) -> None:
        await svc.register("login_user2", "zD3k9mQx")
        with pytest.raises(AuthorizationError, match="Invalid username or"):
            await svc.login("login_user2", "y" * 8)

    async def test_login_nonexistent(self, svc: AuthService) -> None:
        with pytest.raises(AuthorizationError, match="Invalid username or"):
            await svc.login("nobody", "zD3k9mQx")

    async def test_login_inactive_user(self, svc: AuthService) -> None:
        await svc.register("deact_user", "zD3k9mQx")
        user = await svc._user_repo.get_by_username("deact_user")
        assert user is not None
        user.is_active = False
        await svc._user_repo.update(user)
        with pytest.raises(AuthorizationError, match="Account is inactive"):
            await svc.login("deact_user", "zD3k9mQx")


class TestRefresh:

    async def test_refresh_success(self, svc: AuthService) -> None:
        await svc.register("refresh_user", "zD3k9mQx")
        login_tokens = await svc.login("refresh_user", "zD3k9mQx")
        new_tokens = await svc.refresh_token(login_tokens.refresh_token)
        assert new_tokens.access_token
        assert new_tokens.refresh_token
        # new token pair is valid for the same user
        user = await svc.get_current_user(new_tokens.access_token)
        assert user.username == "refresh_user"

    async def test_refresh_invalid_token(self, svc: AuthService) -> None:
        with pytest.raises(AuthorizationError, match="Invalid or revoked"):
            await svc.refresh_token("bogusstr")

    async def test_refresh_revoked_token(self, svc: AuthService) -> None:
        await svc.register("refresh_user2", "zD3k9mQx")
        login_tokens = await svc.login("refresh_user2", "zD3k9mQx")
        rt = login_tokens.refresh_token
        await svc.logout(rt)
        with pytest.raises(AuthorizationError, match="Invalid or revoked"):
            await svc.refresh_token(rt)


class TestLogout:

    async def test_logout_revokes_token(self, svc: AuthService) -> None:
        await svc.register("logout_user", "zD3k9mQx")
        login_tokens = await svc.login("logout_user", "zD3k9mQx")
        await svc.logout(login_tokens.refresh_token)
        with pytest.raises(AuthorizationError, match="Invalid or revoked"):
            await svc.refresh_token(login_tokens.refresh_token)


class TestGetCurrentUser:

    async def test_get_current_user_success(self, svc: AuthService) -> None:
        await svc.register("me_user", "zD3k9mQx")
        login_tokens = await svc.login("me_user", "zD3k9mQx")
        user = await svc.get_current_user(login_tokens.access_token)
        assert user is not None
        assert user.username == "me_user"
        assert user.is_active is True

    async def test_get_current_user_invalid_token(
        self, svc: AuthService,
    ) -> None:
        with pytest.raises(AuthorizationError, match="Invalid or expired"):
            await svc.get_current_user("bogusstr")

    async def test_get_current_user_expired_token(
        self, svc: AuthService,
    ) -> None:
        await svc.register("expire_user", "zD3k9mQx")
        target = await svc._user_repo.get_by_username("expire_user")
        assert target is not None
        cfg = settings
        with patch.object(cfg, "JWT_ACCESS_EXPIRE_MINUTES", -1):
            code = _create_access_token(target)
            with pytest.raises(AuthorizationError, match="Invalid or expired"):
                await svc.get_current_user(code)

    async def test_get_current_user_token_payload(
        self, svc: AuthService,
    ) -> None:
        await svc.register("payload_user", "zD3k9mQx")
        login_tokens = await svc.login("payload_user", "zD3k9mQx")
        raw = jwt.decode(
            login_tokens.access_token,
            settings.JWT_SIGNING_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        assert raw["username"] == "payload_user"
        assert raw["role"] == "operator"
        assert UUID(raw["sub"])

