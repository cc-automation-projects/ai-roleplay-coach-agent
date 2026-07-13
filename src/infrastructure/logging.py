"""structlog configuration — JSON for production, colored console for dev.

Usage:
    from infrastructure.logging import configure_logging
    configure_logging(format="json", level="INFO")

Or rely on Settings:
    configure_logging()
"""

from __future__ import annotations

import logging
import sys

import structlog


def configure_logging(
    fmt: str = "console",
    level: str = "INFO",
) -> None:
    """Configure structlog (and stdlib logging) globally.

    Args:
        fmt: ``"json"`` for JSON-structured output (production),
             ``"console"`` for colored human-readable output (dev).
        level: Log level name (``"DEBUG"``, ``"INFO"``, ``"WARNING"``, …).
    """
    # ── stdlib logging baseline ──────────────────────────────────────
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )

    # ── Shared processor list ────────────────────────────────────────
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if fmt == "json":
        shared_processors.append(structlog.processors.JSONRenderer())
    else:
        # Console: rich traceback + colored key-value pairs
        shared_processors.append(
            structlog.dev.ConsoleRenderer(
                colors=sys.stdout.isatty(),
                pad_level=True,
            ),
        )

    structlog.configure(
        processors=shared_processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
