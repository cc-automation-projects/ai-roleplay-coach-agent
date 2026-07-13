#!/usr/bin/env python3
"""CLI script to generate a fairness report via FairnessService.

Usage::

    python scripts/generate_fairness_report.py \\
        --output report.json \\
        --user-ids u1,u2,... \\
        --scenario-ids s1,s2,...

Exit codes:
    0 -- PASS (all metrics within threshold)
    1 -- FAIL (any metric below threshold)
    2 -- PARTIAL (some metrics below threshold)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from uuid import UUID

import yaml

from agents.analyst.fairness_service import FairnessService
from core.entities import FairnessConfig, ReportSummary
from infrastructure.memory.repositories import (
    InMemoryEvaluationRepository,
    InMemoryUserRepository,
)


def _load_config(path: str = "fairness_config.yaml") -> FairnessConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return FairnessConfig.from_dict(data)


def _parse_uuids(raw: str | None) -> list[UUID] | None:
    if not raw:
        return None
    return [UUID(s.strip()) for s in raw.split(",")]


async def _build_report_async(
    user_ids: list[UUID] | None,
    scenario_ids: list[UUID] | None,
    config: FairnessConfig,
) -> dict:
    """Run the fairness service and return a JSON-serialisable report."""
    user_repo = InMemoryUserRepository()
    eval_repo = InMemoryEvaluationRepository()

    service = FairnessService(
        user_repo=user_repo,
        eval_repo=eval_repo,
        config=config,
    )

    report = await service.generate_report(user_ids, scenario_ids)

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
        description="Generate a fairness report for the coaching system.",
    )
    parser.add_argument(
        "--output",
        default="fairness_report.json",
        help="Path to write the JSON report (default: fairness_report.json)",
    )
    parser.add_argument(
        "--user-ids",
        default=None,
        help="Comma-separated list of user UUIDs (optional -- all if omitted)",
    )
    parser.add_argument(
        "--scenario-ids",
        default=None,
        help="Comma-separated list of scenario UUIDs (optional -- all if omitted)",
    )
    parser.add_argument(
        "--config",
        default="fairness_config.yaml",
        help="Path to fairness config YAML (default: fairness_config.yaml)",
    )
    args = parser.parse_args()

    config = _load_config(args.config)
    user_ids = _parse_uuids(args.user_ids)
    scenario_ids = _parse_uuids(args.scenario_ids)

    report_dict = asyncio.run(_build_report_async(user_ids, scenario_ids, config))

    Path(args.output).write_text(
        json.dumps(report_dict, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    summary = report_dict["summary"]
    if summary == ReportSummary.PASS.value:
        sys.stdout.write(f"Fairness report: PASS -- {args.output}\n")
        sys.exit(0)
    elif summary == ReportSummary.FAIL.value:
        sys.stdout.write(f"Fairness report: FAIL -- {args.output}\n")
        sys.exit(1)
    else:
        sys.stdout.write(f"Fairness report: PARTIAL -- {args.output}\n")
        sys.exit(2)


if __name__ == "__main__":
    main()
