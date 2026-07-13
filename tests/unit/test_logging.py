"""Tests for the structlog logging configuration."""

from __future__ import annotations

import structlog

from infrastructure.logging import configure_logging


class TestLoggingConfig:
    """Verify structlog is properly configured."""

    def test_json_formatter(self) -> None:
        """JSON formatter produces valid JSON output."""
        configure_logging(fmt="json", level="INFO")

        log = structlog.get_logger("test_json")
        log.info("hello", extra="world")

        # Cannot easily capture structlog stdout in test context,
        # but we can verify the JSON renderer is registered.
        processors = structlog.get_config().get("processors", [])
        has_json = any(
            p.__class__.__name__ == "JSONRenderer"
            for p in processors
        )
        assert has_json, "JSONRenderer should be registered when fmt=json"

    def test_console_formatter(self) -> None:
        """Console formatter produces coloured human-readable output."""
        configure_logging(fmt="console", level="DEBUG")

        processors = structlog.get_config().get("processors", [])
        has_console = any(
            p.__class__.__name__ == "ConsoleRenderer"
            for p in processors
        )
        assert has_console, "ConsoleRenderer should be registered when fmt=console"

    def test_logger_name(self) -> None:
        """Logger created with structlog.get_logger carries the correct name."""
        log = structlog.get_logger("my.custom.logger")
        assert log.name == "my.custom.logger"  # type: ignore[attr-defined]

    def test_configure_logging_idempotent(self) -> None:
        """Calling configure_logging twice does not crash."""
        configure_logging(fmt="json", level="INFO")
        configure_logging(fmt="console", level="WARNING")
        # Should not raise
        log = structlog.get_logger("idempotent_test")
        log.warning("still works")
