#!/usr/bin/env python3
"""cu_shim.py — minimal Computer-Use shim for TermNet"""
from flask import Flask, request, jsonify
import subprocess
import shlex
import os

app = Flask(__name__)

SAFE = {
    "git status",
    "ls",
    "pwd",
    "cat README.md",
    "echo ok > /dev/null",
    "python3 -m pytest -q",
    "flake8 termnet/termnet/ tests/ scripts/",
    "git status --porcelain",
}


def run(cmd, cwd=None, timeout=30):
    """Execute a shell command safely."""
    try:
        # For simple commands in SAFE set, use shell=False with split
        if cmd in SAFE or cmd.startswith("echo ") or cmd.startswith("cat "):
            p = subprocess.run(
                shlex.split(cmd) if cmd in SAFE else cmd,
                cwd=cwd or os.getcwd(),
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False if cmd in SAFE else True,
            )
            return p.returncode, p.stdout, p.stderr
        else:
            return 123, "", "blocked by allowlist"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as e:
        return 125, "", str(e)


@app.post("/execute")
def execute():
    """Execute a command with allowlist guardrails."""
    data = request.get_json(force=True) or {}
    cmd = (data.get("command") or "").strip()

    # Guardrails: allowlist style
    if (
        cmd not in SAFE
        and not cmd.startswith("echo ")
        and not cmd.startswith("cat ")
    ):
        return (
            jsonify(
                {"ok": False, "error": "blocked by allowlist", "code": 123}
            ),
            200,
        )

    code, out, err = run(cmd, cwd=os.getcwd())
    return jsonify({"ok": code == 0, "code": code, "stdout": out, "stderr": err})


@app.get("/healthz")
def healthz():
    """Health check endpoint."""
    return jsonify({"ok": True, "service": "cu_shim", "version": "1.0"})


if __name__ == "__main__":
    print("🚀 CU Shim starting on http://0.0.0.0:5055")
    print("📋 Allowlist:", SAFE)
    # Default 0.0.0.0 so you can port-forward
    app.run(host="0.0.0.0", port=5055)