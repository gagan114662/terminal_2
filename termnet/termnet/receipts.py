"""Receipt management for Project Mode."""

import json
import time
from pathlib import Path
from typing import Any, Dict


def _receipts_dir() -> Path:
    """Ensure .termnet/receipts exists and return Path."""
    p = Path(".termnet/receipts")
    p.mkdir(parents=True, exist_ok=True)
    return p


def _slug(name: str) -> str:
    """Slugify a name for file paths."""
    return name.lower().replace(" ", "-").replace("_", "-")


def write_project_receipt(stage: str, payload: Dict[str, Any]) -> str:
    """
    Write a project receipt to .termnet/receipts/.

    Args:
        stage: Stage name (e.g., "roadmap", "start", "complete")
        payload: Data to write

    Returns:
        Path to written receipt file
    """
    receipt_path = _receipts_dir() / f"receipt_{int(time.time())}_{stage}.json"
    receipt_path.write_text(json.dumps(payload, indent=2))
    return str(receipt_path)


def write_task_receipt(task: str, payload: Dict[str, Any]) -> str:
    """
    Write a task receipt to .termnet/receipts/.

    Args:
        task: Task identifier (will be slugified)
        payload: Task execution data

    Returns:
        Path to written receipt file
    """
    task_slug = _slug(task)
    receipt_path = _receipts_dir() / f"receipt_{int(time.time())}_task_{task_slug}.json"
    receipt_path.write_text(json.dumps(payload, indent=2))
    return str(receipt_path)
