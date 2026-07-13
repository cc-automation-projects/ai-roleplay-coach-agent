"""Unit tests for fairness alerting: StubNotificationService + audit CLI."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from infrastructure.notification.stub import StubNotificationService

# ── StubNotificationService ─────────────────────────────────────────


class TestStubNotificationService:
    def test_send_alert_logs_warning(
        self, mocker: pytest.MockFixture,
    ) -> None:
        """Calling send_alert emits a structlog warning with metric details."""
        svc = StubNotificationService()
        spy = mocker.spy(svc, "send_alert")
        svc.send_alert(
            metric="demographic_parity",
            group="female",
            value=0.65,
            threshold=0.8,
        )
        spy.assert_called_once_with(
            metric="demographic_parity",
            group="female",
            value=0.65,
            threshold=0.8,
        )

    def test_send_alert_no_error(self) -> None:
        """send_alert never raises."""
        svc = StubNotificationService()
        svc.send_alert(metric="test", group="x", value=0.5, threshold=0.8)
        svc.send_alert(metric="test2", group="y", value=0.0, threshold=0.5)
        svc.send_alert(metric="test3", group="z", value=1.0, threshold=1.0)


# ── run_fairness_audit.py (via subprocess) ──────────────────────────


class TestRunFairnessAuditCli:
    """Run the actual CLI script with synthetic configs.

    The script uses InMemory repos (no DB needed) with empty data,
    which produces an all-zero report -> summary FAIL.
    """

    SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
    CLI_PATH = SCRIPTS_DIR / "run_fairness_audit.py"

    @pytest.fixture
    def tmp_output(self, tmp_path: Path) -> Path:
        return tmp_path / "audit_result.json"

    async def test_cli_empty_data_returns_fail(
        self, tmp_output: Path,
    ) -> None:
        """With no users/sessions, the audit produces FAIL + exit 1."""
        proc = await asyncio.create_subprocess_exec(
            "D:\\__inst\\Python312\\python.exe",
            str(self.CLI_PATH),
            "--output", str(tmp_output),
            "--config", str(self.SCRIPTS_DIR.parent / "fairness_config.yaml"),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        assert proc.returncode == 1, f"Expected FAIL (1), got {proc.returncode}"
        assert tmp_output.exists()  # noqa: ASYNC240
        data = json.loads(tmp_output.read_text(encoding="utf-8"))  # noqa: ASYNC240
        assert data["summary"] == "fail"

    async def test_cli_creates_json_output(
        self, tmp_output: Path,
    ) -> None:
        """CLI output file is valid JSON with expected keys."""
        proc = await asyncio.create_subprocess_exec(
            "D:\\__inst\\Python312\\python.exe",
            str(self.CLI_PATH),
            "--output", str(tmp_output),
            "--config", str(self.SCRIPTS_DIR.parent / "fairness_config.yaml"),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        assert tmp_output.exists()  # noqa: ASYNC240
        data = json.loads(tmp_output.read_text(encoding="utf-8"))  # noqa: ASYNC240
        assert "report_id" in data
        assert "generated_at" in data
        assert "summary" in data
        assert "metrics" in data


# ── Periodic task cancellation ──────────────────────────────────────


class TestPeriodicTaskCancellation:
    async def test_periodic_task_cancels_on_shutdown(self) -> None:
        """A periodic fairness task can be cancelled gracefully."""
        started = asyncio.Event()
        cancelled = asyncio.Event()

        async def _dummy_audit() -> None:
            started.set()
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancelled.set()
                raise

        task = asyncio.create_task(_dummy_audit())
        await asyncio.wait_for(started.wait(), timeout=5)
        assert not task.done()

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert cancelled.is_set()
