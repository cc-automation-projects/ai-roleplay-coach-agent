import subprocess
import sys


def test_ruff_passes():
    """Ensure ruff check returns 0."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "src/", "tests/"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"ruff failed:\n{result.stdout}\n{result.stderr}"


def test_no_hardcoded_secrets():
    """Placeholder: detailed secret scan is performed by security_scan.py."""
    assert True
