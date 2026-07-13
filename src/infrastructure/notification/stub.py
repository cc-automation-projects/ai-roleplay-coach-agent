"""Notification service protocol and stub implementation.

MVP: StubNotificationService logs alerts via structlog.
In production, replace with email/Telegram/Slack integration.
"""

from __future__ import annotations

from typing import Protocol

import structlog

logger = structlog.get_logger(__name__)


class NotificationService(Protocol):
    """Protocol for sending fairness alerts."""

    def send_alert(
        self,
        metric: str,
        group: str,
        value: float,
        threshold: float,
    ) -> None:
        """Send an alert about a threshold breach."""
        ...


class StubNotificationService:
    """Stub that logs alerts via structlog.warning.

    Used in MVP when ``alerting.enabled`` is set. Replace with a real
    provider (email / Telegram / Slack) once the notification channel is
    specified.
    """

    def send_alert(
        self,
        metric: str,
        group: str,
        value: float,
        threshold: float,
    ) -> None:
        """Log a warning-level alert for a fairness threshold breach."""
        logger.warning(
            "Fairness threshold breached",
            metric=metric,
            group=group,
            value=value,
            threshold=threshold,
        )
