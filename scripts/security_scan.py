#!/usr/bin/env python3
"""Security scan script for CI/CD.

Runs:
- pip-audit for dependency vulnerabilities
- ruff check for SAST
- regex scan for hardcoded secrets

Outputs JSON report to stdout.
"""

import json
import logging
import re
import shutil
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def run_pip_audit() -> dict:
    """Run pip-audit and return JSON report."""
    pip_audit = shutil.which("pip-audit")
    if pip_audit is None:
        return {"tool": "pip-audit", "status": "skipped", "reason": "pip-audit not found"}
    try:
        result = subprocess.run(  # noqa: S603
            [pip_audit, "--format", "json", "--no-deps"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return {"tool": "pip-audit", "status": "skipped", "reason": "pip-audit not installed"}
    else:
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "tool": "pip-audit",
                "status": "ok",
                "vulnerabilities": data.get("vulnerabilities", []),
            }
        return {"tool": "pip-audit", "status": "error", "stderr": result.stderr}


def run_ruff_check() -> dict:
    """Run ruff check and return JSON report."""
    ruff = shutil.which("ruff")
    if ruff is None:
        return {"tool": "ruff", "status": "skipped", "reason": "ruff not found"}
    try:
        result = subprocess.run(  # noqa: S603
            [ruff, "check", "src/", "tests/", "--output-format", "json"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return {"tool": "ruff", "status": "skipped", "reason": "ruff not installed"}
    else:
        if result.returncode == 0:
            return {"tool": "ruff", "status": "ok", "issues": []}
        try:
            issues = json.loads(result.stdout)
        except json.JSONDecodeError:
            issues = []
        return {"tool": "ruff", "status": "error", "issues": issues}


def scan_hardcoded_secrets() -> dict:
    """Scan Python files for hardcoded secret patterns."""
    patterns = [
        (r"(?i)secret['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Generic secret"),
        (r"password['\"]?\s*[:=]\s*['\"][^'\"]{4,}['\"]", "Password"),
        (r"api_key['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]", "API key"),
        (r"token['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Token"),
    ]
    findings = []
    for py_file in Path().rglob("*.py"):
        if any(part.startswith(".") or part in ("venv", "env", ".git") for part in py_file.parts):
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
            for line_no, line in enumerate(content.splitlines(), 1):
                for pattern, desc in patterns:
                    if re.search(pattern, line):
                        findings.append({
                            "file": str(py_file),
                            "line": line_no,
                            "description": desc,
                            "match": line.strip(),
                        })
        except OSError as exc:
            logger.debug("Skipping %s: %s", py_file, exc)
    status = "ok" if not findings else "warning"
    return {"tool": "hardcoded-secrets", "status": status, "findings": findings}


def main() -> None:
    """Run all security scans and print JSON report."""
    results = [
        run_pip_audit(),
        run_ruff_check(),
        scan_hardcoded_secrets(),
    ]
    overall = "pass"
    for r in results:
        if r.get("status") in ("error", "warning"):
            overall = "fail"
            break
    report = {"overall": overall, "results": results}
    print(json.dumps(report, indent=2))  # noqa: T201
    sys.exit(0 if overall == "pass" else 1)


if __name__ == "__main__":
    main()
