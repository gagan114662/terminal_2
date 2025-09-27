from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Literal

SCHEMA_VERSION = "1.0.0"


def _artifacts_dir() -> str:
    base = os.getenv("TERMNET_ARTIFACTS_DIR") or os.path.join("artifacts", "last_run")
    os.makedirs(base, exist_ok=True)
    return base


def _traj_path() -> str:
    return os.path.join(_artifacts_dir(), "trajectory.jsonl")


def now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")


Phase = Literal["reason", "act", "observe"]


@dataclass
class TrajectoryStep:
    run_id: str
    trace_id: str
    step_index: int
    phase: Phase
    timestamp: str
    latency_ms: int
    tool_name: str | None = None
    tool_args_redacted: dict[str, Any] | None = None
    schema_version: str = SCHEMA_VERSION


def log_step(step: TrajectoryStep) -> None:
    path = _traj_path()
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(step), ensure_ascii=False) + "\n")
