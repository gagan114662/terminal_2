"""Receipt management for Project Mode."""

import json
import os
from typing import Any, Dict


def write_project_receipt(stage: str, payload: Dict[str, Any]) -> str:
    """
    Write a project receipt to .termnet/receipts/.

    Args:
        stage: Stage name (e.g., "roadmap", "start", "complete")
        payload: Data to write

    Returns:
        Path to written receipt file
    """
    os.makedirs(".termnet/receipts", exist_ok=True)
    receipt_path = f".termnet/receipts/receipt_{stage}_project.json"

    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return receipt_path


def write_task_receipt(task: str, payload: Dict[str, Any]) -> str:
    """
    Write a task receipt to .termnet/receipts/.

    Args:
        task: Task identifier (will be slugified)
        payload: Task execution data

    Returns:
        Path to written receipt file
    """
    # Slugify task name
    task_slug = task.lower().replace(" ", "-").replace("_", "-")

    os.makedirs(".termnet/receipts", exist_ok=True)
    receipt_path = f".termnet/receipts/receipt_task_{task_slug}.json"

    with open(receipt_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    return receipt_path