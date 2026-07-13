"""API tests for fairness audit endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

if TYPE_CHECKING:
    import httpx
    from fastapi import FastAPI

from api.dependencies import get_fairness_service
from core.entities import (
    FairnessMetric,
    FairnessMetricType,
    FairnessReport,
    ReportSummary,
)


@pytest.fixture(autouse=True)
def _override_fairness_service(
    app: FastAPI,
) -> None:
    """Replace FairnessService DI with a mock for all tests."""
    mock_service = MagicMock()

    # Mock protected attributes (used by /fairness/groups)
    mock_attr = MagicMock()
    mock_attr.name = "gender"
    mock_attr.values = ["male", "female"]
    mock_attr.description = "Gender identity"
    mock_service._config = MagicMock()
    mock_service._config.protected_attributes = [mock_attr]

    # Mock generate_report
    mock_service.generate_report = AsyncMock(  # type: ignore[method-assign]
        return_value=FairnessReport(
            metrics=[
                FairnessMetric(
                    metric_name=FairnessMetricType.DEMOGRAPHIC_PARITY,
                    value=1.0,
                    group="female",
                    attribute="gender",
                    threshold=0.8,
                    passed=True,
                ),
            ],
            summary=ReportSummary.PASS,
        ),
    )

    app.dependency_overrides[get_fairness_service] = lambda: mock_service


# ── GET /fairness/report ────────────────────────────────────────────


class TestFairnessReport:
    async def test_no_token_returns_401(
        self, async_client: httpx.AsyncClient
    ) -> None:
        """Missing auth → 401."""
        resp = await async_client.get("/api/v1/analyst/fairness/report")
        assert resp.status_code == 401

    async def test_operator_token_returns_403(
        self, async_client: httpx.AsyncClient, auth_header: dict[str, str]
    ) -> None:
        """Operator token → 403 (ADMIN only)."""
        resp = await async_client.get(
            "/api/v1/analyst/fairness/report",
            headers=auth_header,
        )
        assert resp.status_code == 403

    async def test_admin_token_returns_200(
        self,
        async_client: httpx.AsyncClient,
        rbac_admin_header: dict[str, str],
    ) -> None:
        """Admin token → 200 + valid structure."""
        resp = await async_client.get(
            "/api/v1/analyst/fairness/report",
            headers=rbac_admin_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "report_id" in data
        assert "summary" in data
        assert "metrics" in data
        assert data["summary"] == ReportSummary.PASS.value

    async def test_with_invalid_scenario_id(
        self,
        async_client: httpx.AsyncClient,
        rbac_admin_header: dict[str, str],
    ) -> None:
        """Invalid scenario_id → 422 (UUID validation)."""
        resp = await async_client.get(
            "/api/v1/analyst/fairness/report",
            params={"scenario_id": "not-a-uuid"},
            headers=rbac_admin_header,
        )
        assert resp.status_code == 422


# ── GET /fairness/groups ────────────────────────────────────────────


class TestFairnessGroups:
    async def test_groups_returns_200(
        self,
        async_client: httpx.AsyncClient,
        rbac_admin_header: dict[str, str],
    ) -> None:
        """Admin → 200 + list of attributes."""
        resp = await async_client.get(
            "/api/v1/analyst/fairness/groups",
            headers=rbac_admin_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == "gender"
        assert "values" in data[0]
        assert "description" in data[0]


# ── GET /fairness/history ───────────────────────────────────────────


class TestFairnessHistory:
    async def test_history_returns_200(
        self,
        async_client: httpx.AsyncClient,
        rbac_admin_header: dict[str, str],
    ) -> None:
        """Admin → 200 + empty list (no persisted reports)."""
        resp = await async_client.get(
            "/api/v1/analyst/fairness/history",
            headers=rbac_admin_header,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_content_type_json(
        self,
        async_client: httpx.AsyncClient,
        rbac_admin_header: dict[str, str],
    ) -> None:
        """Response Content-Type includes application/json."""
        resp = await async_client.get(
            "/api/v1/analyst/fairness/groups",
            headers=rbac_admin_header,
        )
        assert resp.status_code == 200
        assert "application/json" in resp.headers.get("content-type", "")
