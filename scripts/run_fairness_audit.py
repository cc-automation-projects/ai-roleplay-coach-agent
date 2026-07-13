#!/usr/bin/env python3
"""CLI script to run a fairness audit on all users and completed sessions.

Usage::

    python scripts/run_fairness_audit.py [--output report.json] [--config fairness_config.yaml]

Compared to ``generate_fairness_report.py``, this script:
- Loads ALL users and ALL completed sessions (no manual UUIDs needed)
- Logs ALERT for every metric below threshold
- Calls NotificationStub if ``alerting.enabled`` in config
- Same exit codes: 0=PASS, 1=FAIL, 2=PARTIAL

Exit codes:
    0 — PASS (all metrics within threshold)
    1 — FAIL (any metric below threshold)
    2 — PARTIAL (some metrics below threshold)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import structlog
import yaml

from agents.analyst.fairness_service import FairnessService
from core.entities import FairnessConfig, ReportSummary
from infrastructure.memory.repositories import (
    InMemoryEvaluationRepository,
    InMemoryUserRepository,
)
from infrastructure.notification.stub import StubNotificationService

logger = structlog.get_logger(__name__)


def _load_config(path: str = "fairness_config.yaml") -> FairnessConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return FairnessConfig.from_dict(data)


def _emit_alerts(
    metrics: list[dict],
    config: FairnessConfig,
    notifier: StubNotificationService,
) -> None:
    """Log ALERT + call notifier for every failed metric."""
    if not config.alerting.enabled:
        return
    for m in metrics:
        if not m["passed"]:
            logger.warning(
                "FAIRNESS_ALERT: metric below threshold",
                metric=m["metric_name"],
                group=m["group"],
                value=m["value"],
                threshold=m["threshold"],
            )
            if config.alerting.threshold_breach_action == "log":
                notifier.send_alert(
                    metric=m["metric_name"],
                    group=m["group"],
                    value=m["value"],
                    threshold=m["threshold"],
                )


async def _run_audit_async(config: FairnessConfig) -> dict:
    """Run the fairness audit and return a JSON-serialisable report."""
    user_repo = InMemoryUserRepository()
    eval_repo = InMemoryEvaluationRepository()

    service = FairnessService(
        user_repo=user_repo,
        eval_repo=eval_repo,
        config=config,
    )

    # Load ALL users (no user_ids filter) and ALL completed sessions
    report = await service.generate_report(user_ids=None, scenario_ids=None)

    return {
        "report_id": str(report.report_id),
        "generated_at": report.generated_at.isoformat(),
        "summary": report.summary.value,
        "config_version": report.config_version,
        "metrics": [
            {
                "metric_name": m.metric_name.value,
                "value": m.value,
                "group": m.group,
                "attribute": m.attribute,
                "threshold": m.threshold,
                "passed": m.passed,
            }
            for m in report.metrics
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a fairness audit on all users and completed sessions.",
    )
    parser.add_argument(
        "--output",
        default="fairness_report_latest.json",
        help="Path to write the JSON report (default: fairness_report_latest.json)",
    )
    parser.add_argument(
        "--config",
        default="fairness_config.yaml",
        help="Path to fairness config YAML (default: fairness_config.yaml)",
    )
    args = parser.parse_args()

    config = _load_config(args.config)
    notifier = StubNotificationService()

    report_dict = asyncio.run(_run_audit_async(config))

    # Emit alerts for failed metrics
    _emit_alerts(report_dict["metrics"], config, notifier)

    Path(args.output).write_text(
        json.dumps(report_dict, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    summary = report_dict["summary"]
    if summary == ReportSummary.PASS.value:
        logger.info("Fairness audit complete", result="PASS", output=args.output)
        sys.exit(0)
    elif summary == ReportSummary.FAIL.value:
        logger.info("Fairness audit complete", result="FAIL", output=args.output)
        sys.exit(1)
    else:
        logger.info("Fairness audit complete", result="PARTIAL", output=args.output)
        sys.exit(2)


if __name__ == "__main__":
    main()
