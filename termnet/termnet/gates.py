"""Gate runner for lint and test checks."""

import subprocess
from typing import Dict


def _run(cmd: str) -> int:
    """Run a shell command, return exit code only (no raise)."""
    return subprocess.run(cmd, shell=True, capture_output=True).returncode


def run_gates() -> Dict[str, int]:
    """Run flake8 and pytest -q. Return exit codes as {'flake8': int, 'pytest': int}."""
    return {"flake8": _run("flake8"), "pytest": _run("pytest -q")}