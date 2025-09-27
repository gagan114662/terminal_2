# termnet/bmad_trajectory_bridge.py
from __future__ import annotations

import time
import uuid
from typing import Any

from termnet.trajectory_logger import TrajectoryStep, log_step, now_iso

DEFAULT_PHASE_MAP = {
    # common BMAD/METHOD event tags → trajectory phases
    "plan": "reason",
    "thought": "reason",
    "reason": "reason",
    "tool_call": "action",
    "action": "action",
    "act": "action",
    "tool": "action",  # Claude Code CLI uses "TOOL" tag
    "observation": "observe",
    "observe": "observe",
    "result": "observe",
    "final": "observe",
    "content": "observe",  # Claude Code CLI uses "CONTENT" tag
}


class BMADTrajectoryBridge:
    """
    Adapter to capture BMAD/METHOD stream events and write TermNet trajectory.jsonl entries.
    Use .from_stream(tag, payload) for stream-style integration, or .on_event(...) for callback hubs.
    """

    def __init__(
        self,
        run_id: str | None = None,
        trace_id: str | None = None,
        phase_map: dict[str, str] | None = None,
        redact_fn=None,
    ) -> None:
        self.run_id = run_id or f"req-{uuid.uuid4().hex[:12]}"
        self.trace_id = trace_id or f"tr-{uuid.uuid4().hex[:12]}"
        self.step_index = 0
        self.phase_map = {**DEFAULT_PHASE_MAP, **(phase_map or {})}
        self._t_last = time.perf_counter()
        self._redact = redact_fn or (lambda d: {})  # never log raw args by default

    def _latency_ms(self) -> int:
        now = time.perf_counter()
        dt = int((now - self._t_last) * 1000)
        self._t_last = now
        return dt

    def _phase_for(self, tag: str) -> str | None:
        return self.phase_map.get(tag.lower())

    def from_stream(self, tag: str, payload: dict[str, Any] | Any) -> None:
        """Call this for each (tag, payload) produced by BMAD streams."""
        phase = self._phase_for(tag)
        if not phase:
            return  # ignore non-cognitive events

        tool_name = None
        redacted = None

        # Heuristics for tool call events coming from BMAD/METHOD
        if phase == "action":
            if isinstance(payload, dict):
                tool_name = payload.get("tool") or payload.get("name")
                redacted = self._redact(payload)

        log_step(
            TrajectoryStep(
                run_id=self.run_id,
                trace_id=self.trace_id,
                step_index=self.step_index,
                phase=phase,  # "reason" | "action" | "observe"
                timestamp=now_iso(),
                latency_ms=self._latency_ms(),
                tool_name=tool_name,
                tool_args_redacted=redacted,
            )
        )
        self.step_index += 1

    # Optional callback-style API, if your BMAD core emits events via hooks
    def on_event(self, event: dict[str, Any]) -> None:
        tag = event.get("tag") or event.get("type") or ""
        self.from_stream(tag, event)


PHASE_MAP = {
    "think": "reason",
    "plan": "reason",
    "act": "act",
    "tool": "act",
    "observe": "observe",
    "reflect": "observe",
}


def map_event_to_step(event: dict[str, Any]) -> TrajectoryStep:
    """
    Minimal adapter that tests expect:
    input: {"run_id","trace_id","index","phase","latency_ms","tool","args"}
    """
    phase = PHASE_MAP.get(str(event.get("phase", "")).lower(), "observe")
    return TrajectoryStep(
        run_id=event.get("run_id", "unknown-run"),
        trace_id=event.get("trace_id", "unknown-trace"),
        step_index=int(event.get("index", 0)),
        phase=phase,
        timestamp=event.get("timestamp") or now_iso(),
        latency_ms=int(event.get("latency_ms") or 0),
        tool_name=event.get("tool"),
        tool_args_redacted=(
            event.get("args_redacted")
            or ({"__redacted__": True} if event.get("args") else None)
        ),
    )


__all__ = ["BMADTrajectoryBridge", "map_event_to_step"]
