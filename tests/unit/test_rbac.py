"""Unit tests for RBAC require_role() dependency and UserRole enum."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.entities.user import User, UserRole


class TestUserRoleEnum:
    """UserRole string enum sanity."""

    def test_roles_exist(self) -> None:
        assert UserRole.OPERATOR.value == "operator"
        assert UserRole.TRAINER.value == "trainer"
        assert UserRole.ADMIN.value == "admin"

    def test_role_order(self) -> None:
        """Roles are in order: operator < trainer < admin."""
        roles = list(UserRole)
        assert roles == [UserRole.OPERATOR, UserRole.TRAINER, UserRole.ADMIN]


class TestRequireRoleUnit:
    """Unit tests for the _require_role validation logic."""

    @pytest.fixture
    def operator_user(self) -> User:
        return User(
            id=uuid4(),
            username="op_user",
            hashed_password="",
            email="op@test.com",
            name="Operator",
            role=UserRole.OPERATOR,
        )

    @pytest.fixture
    def admin_user(self) -> User:
        return User(
            id=uuid4(),
            username="ad_user",
            hashed_password="",
            email="ad@test.com",
            name="Admin",
            role=UserRole.ADMIN,
        )

    async def test_operator_allowed_for_operator_role(
        self,
        operator_user: User,
    ) -> None:
        """Operator should pass when OPERATOR is in allowed roles."""
        from api.dependencies import _require_role

        result = await _require_role(operator_user, (UserRole.OPERATOR,))
        assert result == operator_user

    async def test_operator_allowed_for_operator_trainer_admin(
        self,
        operator_user: User,
    ) -> None:
        """Operator should pass when OPERATOR/TRAINER/ADMIN are allowed."""
        from api.dependencies import _require_role

        result = await _require_role(
            operator_user, (UserRole.OPERATOR, UserRole.TRAINER, UserRole.ADMIN),
        )
        assert result == operator_user

    async def test_operator_blocked_from_admin_only(
        self,
        operator_user: User,
    ) -> None:
        """Operator should be denied when only ADMIN is allowed."""
        from fastapi import HTTPException

        from api.dependencies import _require_role

        with pytest.raises(HTTPException) as exc_info:
            await _require_role(operator_user, (UserRole.ADMIN,))
        assert exc_info.value.status_code == 403

    async def test_operator_blocked_from_trainer_only(
        self,
        operator_user: User,
    ) -> None:
        """Operator should be denied when only TRAINER is allowed."""
        from fastapi import HTTPException

        from api.dependencies import _require_role

        with pytest.raises(HTTPException) as exc_info:
            await _require_role(operator_user, (UserRole.TRAINER,))
        assert exc_info.value.status_code == 403

    async def test_admin_allowed_for_admin_only(
        self,
        admin_user: User,
    ) -> None:
        """Admin should pass when only ADMIN is allowed."""
        from api.dependencies import _require_role

        result = await _require_role(admin_user, (UserRole.ADMIN,))
        assert result == admin_user

    async def test_admin_allowed_for_any_role(
        self,
        admin_user: User,
    ) -> None:
        """Admin should pass when any role is allowed."""
        from api.dependencies import _require_role

        result = await _require_role(admin_user, (UserRole.OPERATOR,))
        assert result == admin_user
