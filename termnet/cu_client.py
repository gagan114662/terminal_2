"""Computer-Use client for claim verification."""

import os
import subprocess
from typing import Dict


def verify_claim(name: str, cmd: str, use_computer: bool = False) -> Dict:
    """
    Run a verification command either locally or via Computer-Use HTTP.
    Returns: {'name','cmd','exit','stdout','stderr', 'provider': <str>}
    """
    # Safety check: block dangerous commands unless explicitly allowed
    DANGEROUS = ["rm -rf /", ":(){ :|:& };:", "shutdown -h now"]
    if not os.getenv("TERMNET_ALLOW_DANGEROUS") and any(
        bad in cmd for bad in DANGEROUS  # noqa: E501
    ):
        return {
            "name": name,
            "cmd": cmd,
            "exit": 123,
            "stdout": "",
            "stderr": "blocked dangerous cmd",
            "provider": "local",
        }

    if not use_computer:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return {
            "name": name,
            "cmd": cmd,
            "exit": p.returncode,
            "stdout": p.stdout,
            "stderr": p.stderr,
            "provider": "local",
        }

    # CU path (Qwen VL Computer Use proxy)
    import requests

    cu_url = os.getenv("CU_URL", "http://localhost:5055").rstrip("/")
    url = f"{cu_url}/run"
    try:
        r = requests.post(url, json={"cmd": cmd}, timeout=60)
        out = (
            r.json()
            if r.headers.get("content-type", "").startswith("application/json")
            else {}
        )
        return {
            "name": name,
            "cmd": cmd,
            "exit": int(out.get("exit", -1)),
            "stdout": out.get("stdout", ""),
            "stderr": out.get("stderr", ""),
            "provider": "qwen-vl-cu",
            "http_status": r.status_code,
        }
    except Exception as e:
        return {
            "name": name,
            "cmd": cmd,
            "exit": -1,
            "stdout": "",
            "stderr": str(e),
            "provider": "qwen-vl-cu",
        }
