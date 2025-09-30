"""
Trajectory Evaluator - Layer 2 AgentOps evaluation
Tracks ReAct loops: Reason → Act → Observe sequences
"""

import contextlib
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class StepPhase(Enum):
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"


class TrajectoryStatus(Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class Step:
    """Individual step in ReAct trajectory"""

    step_index: int
    phase: StepPhase
    timestamp: str
    latency_ms: int
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    output_snippet: Optional[str] = None
    error: Optional[str] = None
    tokens_in: Optional[int] = None  # TODO: Hook into Claude client
    tokens_out: Optional[int] = None  # TODO: Hook into Claude client
    rationale_summary: Optional[str] = None
    evidence_refs: Optional[List[Dict[str, str]]] = None

    def to_dict(self):
        data = asdict(self)
        data["phase"] = self.phase.value
        return data


@dataclass
class Trajectory:
    """Complete ReAct trajectory for a request"""

    request_id: str
    started_at: str
    ended_at: Optional[str] = None
    status: TrajectoryStatus = TrajectoryStatus.IN_PROGRESS
    model: str = "claude-3-5-sonnet"
    tags: List[str] = None
    total_steps: int = 0
    total_latency_ms: int = 0
    react_cycles: int = 0
    tools_used: Dict[str, int] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.tools_used is None:
            self.tools_used = {}

    def to_dict(self):
        data = asdict(self)
        data["status"] = self.status.value
        return data


class TrajectoryEvaluator:
    """Manages trajectory tracking and evaluation"""

    def __init__(self, db_path: str = "termnet_trajectories.db"):
        self.db_path = db_path
        self._persistent_conn = None  # For in-memory databases
        self._init_schema()  # Always call schema init unconditionally
        self.active_trajectories: Dict[str, List[Step]] = {}

    def _init_schema(self):
        """Initialize SQLite tables with correct schema"""
        # For in-memory databases, keep persistent connection
        if self.db_path == ":memory:":
            self._persistent_conn = sqlite3.connect(self.db_path)
            conn = self._persistent_conn
            need_close = False
        else:
            # Use context manager for file databases
            with sqlite3.connect(self.db_path) as conn:
                self._init_schema_tables(conn)
            return

        try:
            self._init_schema_tables(conn)
        finally:
            if need_close:
                conn.close()

    def _init_schema_tables(self, conn):
        """Initialize database tables (extracted for reuse with context managers)"""
        # Enable WAL mode for better performance (skip for in-memory)
        if self.db_path != ":memory:":
            conn.execute("PRAGMA journal_mode=WAL")

        # Main trajectories table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trajectories (
                request_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                tags_json TEXT,
                react_cycles INTEGER DEFAULT 0,
                total_latency_ms INTEGER DEFAULT 0
            )
        """
        )

        # Trajectory steps table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS trajectory_steps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                step_index INTEGER NOT NULL,
                phase TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                latency_ms INTEGER NOT NULL,
                tool_name TEXT,
                tool_args_json TEXT,
                output_snippet TEXT,
                error TEXT,
                tokens_in INTEGER DEFAULT 0,
                tokens_out INTEGER DEFAULT 0,
                rationale_summary TEXT,
                evidence_refs_json TEXT,
                FOREIGN KEY (request_id) REFERENCES trajectories(request_id)
            )
        """
        )

        # Golden trajectories table
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS golden_trajectories (
                label TEXT NOT NULL,
                step_index INTEGER NOT NULL,
                phase TEXT NOT NULL,
                tool_name TEXT,
                expected_latency_ms INTEGER NOT NULL,
                PRIMARY KEY (label, step_index)
            )
        """
        )

        # Create indexes
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_steps_request ON trajectory_steps(request_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_trajectories_status ON trajectories(status)"
        )
        conn.commit()

    @contextlib.contextmanager
    def _get_connection(self):
        """Get database connection with proper resource management"""
        if self._persistent_conn:
            # For in-memory databases, use persistent connection without closing
            yield self._persistent_conn
        else:
            # For file databases, use context manager
            with sqlite3.connect(self.db_path) as conn:
                yield conn

    def close(self):
        """Close persistent database connection if exists"""
        if self._persistent_conn:
            self._persistent_conn.close()
            self._persistent_conn = None

    def __del__(self):
        """Cleanup persistent connections on object destruction"""
        self.close()

    def start_trajectory(self, request_id: str, tags: List[str] = None) -> Trajectory:
        """Start tracking a new trajectory"""
        trajectory = Trajectory(
            request_id=request_id,
            started_at=datetime.now().isoformat(),
            tags=tags or [],
        )

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO trajectories
                (request_id, started_at, status, tags_json)
                VALUES (?, ?, ?, ?)
            """,
                (
                    trajectory.request_id,
                    trajectory.started_at,
                    trajectory.status.value,
                    json.dumps(trajectory.tags),
                ),
            )
            conn.commit()

        self.active_trajectories[request_id] = []
        return trajectory

    def record_step(self, request_id: str, step: Step) -> None:
        """Record a step in the trajectory"""
        if request_id not in self.active_trajectories:
            self.active_trajectories[request_id] = []

        self.active_trajectories[request_id].append(step)

        # Insert step with correct JSON serialization
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO trajectory_steps
                (request_id, step_index, phase, timestamp, latency_ms,
                 tool_name, tool_args_json, output_snippet, error,
                 tokens_in, tokens_out, rationale_summary, evidence_refs_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    request_id,
                    step.step_index,
                    step.phase.value,
                    step.timestamp,
                    step.latency_ms,  # Persist latency verbatim (requirement B)
                    step.tool_name,
                    json.dumps(step.tool_args) if step.tool_args else None,
                    step.output_snippet,
                    step.error,
                    step.tokens_in or 0,
                    step.tokens_out or 0,
                    step.rationale_summary,
                    json.dumps(step.evidence_refs) if step.evidence_refs else None,
                ),
            )
            conn.commit()

    def _compute_react_cycles(self, request_id: str) -> int:
        """Count complete ReAct cycles, preferring OBSERVE count as fallback floor(num_steps/3)"""
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT phase FROM trajectory_steps
                WHERE request_id = ? ORDER BY step_index
            """,
                (request_id,),
            )
            phases = [row[0] for row in cursor.fetchall()]

            # Prefer count of OBSERVE phases as cycle count
            observe_count = sum(1 for phase in phases if phase == "observe")
            if observe_count > 0:
                return observe_count

            # Fallback: floor(num_steps/3) for incomplete cycles
            return len(phases) // 3

    def finish_trajectory(self, request_id: str, status: TrajectoryStatus) -> None:
        """Mark trajectory as complete"""
        finished_at = datetime.now().isoformat()

        # Compute total latency from recorded steps
        with self._get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT SUM(latency_ms) FROM trajectory_steps
                WHERE request_id = ?
            """,
                (request_id,),
            )
            total_latency = cursor.fetchone()[0] or 0

            # Compute ReAct cycles
            react_cycles = self._compute_react_cycles(request_id)

            conn.execute(
                """
                UPDATE trajectories
                SET finished_at = ?, status = ?, total_latency_ms = ?, react_cycles = ?
                WHERE request_id = ?
            """,
                (finished_at, status.value, total_latency, react_cycles, request_id),
            )
            conn.commit()

        # Clean up active tracking
        if request_id in self.active_trajectories:
            del self.active_trajectories[request_id]

    def save_golden(self, request_id: str, label: str, description: str = None) -> None:
        """Save a trajectory as golden reference"""
        with self._get_connection() as conn:
            # Delete existing golden steps for this label
            conn.execute("DELETE FROM golden_trajectories WHERE label = ?", (label,))

            # Get all steps for this trajectory
            cursor = conn.execute(
                """
                SELECT step_index, phase, tool_name, latency_ms
                FROM trajectory_steps
                WHERE request_id = ?
                ORDER BY step_index
            """,
                (request_id,),
            )

            steps = cursor.fetchall()
            for step_index, phase, tool_name, latency_ms in steps:
                conn.execute(
                    """
                    INSERT INTO golden_trajectories
                    (label, step_index, phase, tool_name, expected_latency_ms)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (label, step_index, phase, tool_name, latency_ms),
                )

            conn.commit()

    def compare_to_golden(self, request_id: str, label: str) -> Dict[str, Any]:
        """Compare trajectory to golden reference"""
        with self._get_connection() as conn:
            # Get golden trajectory steps
            cursor = conn.execute(
                """
                SELECT step_index, phase, tool_name, expected_latency_ms
                FROM golden_trajectories
                WHERE label = ?
                ORDER BY step_index
            """,
                (label,),
            )
            golden_steps = cursor.fetchall()

            if not golden_steps:
                return {"error": f"Golden trajectory '{label}' not found"}

            # Get current trajectory steps
            cursor = conn.execute(
                """
                SELECT step_index, phase, tool_name, latency_ms
                FROM trajectory_steps
                WHERE request_id = ?
                ORDER BY step_index
            """,
                (request_id,),
            )
            current_steps = cursor.fetchall()

            if not current_steps:
                return {"error": f"Trajectory '{request_id}' not found"}

            # Compare sequences
            golden_seq = [
                (step[1], step[2]) for step in golden_steps
            ]  # (phase, tool_name)
            current_seq = [
                (step[1], step[2]) for step in current_steps
            ]  # (phase, tool_name)
            sequence_match = golden_seq == current_seq

            # Calculate latency ratios (no infinities - requirement D)
            ratios = []
            per_step_deltas = []
            for i in range(min(len(golden_steps), len(current_steps))):
                expected_latency_ms = golden_steps[i][3]  # expected_latency_ms
                actual_latency = current_steps[i][3]  # latency_ms
                baseline = max(
                    1, expected_latency_ms
                )  # Ensure baseline >= 1 to avoid infinities
                ratio = actual_latency / baseline
                ratios.append(ratio)
                per_step_deltas.append(
                    {
                        "step": i,
                        "expected": expected_latency_ms,
                        "actual": actual_latency,
                        "ratio": ratio,
                    }
                )

            avg_ratio = sum(ratios) / len(ratios) if ratios else 1.0
            max_ratio = max(ratios) if ratios else 1.0

            return {
                "golden_label": label,
                "sequence_match": sequence_match,
                "step_difference": len(current_steps) - len(golden_steps),
                "avg_ratio": round(avg_ratio, 3),
                "max_ratio": round(max_ratio, 3),
                "per_step_deltas": per_step_deltas,
                "current_steps": len(current_steps),
                "expected_steps": len(golden_steps),
                "verdict": "PASS" if sequence_match and max_ratio <= 1.2 else "FAIL",
            }

    def get_trajectory(self, request_id: str) -> Dict[str, Any]:
        """Get full trajectory with steps"""
        with self._get_connection() as conn:
            # Get trajectory
            cursor = conn.execute(
                """
                SELECT request_id, started_at, finished_at, status, tags_json,
                       react_cycles, total_latency_ms
                FROM trajectories WHERE request_id = ?
            """,
                (request_id,),
            )
            trajectory_row = cursor.fetchone()

            if not trajectory_row:
                return None

            # Get steps
            cursor = conn.execute(
                """
                SELECT step_index, phase, timestamp, latency_ms, tool_name, output_snippet, error
                FROM trajectory_steps
                WHERE request_id = ? ORDER BY step_index
            """,
                (request_id,),
            )
            steps = cursor.fetchall()

            return {"trajectory": trajectory_row, "steps": steps}

    def print_trajectory(self, request_id: str) -> None:
        """Print trajectory in compact table format"""
        data = self.get_trajectory(request_id)
        if not data:
            print(f"Trajectory {request_id} not found")
            return

        trajectory = data["trajectory"]
        steps = data["steps"]

        print(f"\n╭─ Trajectory: {request_id}")
        print(f"│  Status: {trajectory[3]}")
        print(f"│  React Cycles: {trajectory[5]}")
        print(f"│  Total Latency: {trajectory[6]}ms")
        print(f"╰─ Steps: {len(steps)}")

        if steps:
            print(
                "\n┌─────┬────────┬──────────┬────────────┬────────────────────────────┐"
            )
            print(
                "│ Idx │ Phase  │ Latency  │ Tool       │ Output/Error               │"
            )
            print(
                "├─────┼────────┼──────────┼────────────┼────────────────────────────┤"
            )

            for step in steps:
                idx = step[0]  # step_index
                phase = step[1]  # phase
                latency = f"{step[3]}ms"  # latency_ms
                tool = step[4] or "-"  # tool_name
                output = (step[5] or step[6] or "-")[:26]  # output_snippet or error

                print(
                    f"│ {idx:3} │ {phase:6} │ {latency:8} │ {tool:10} │ {output:26} │"
                )

            print(
                "└─────┴────────┴──────────┴────────────┴────────────────────────────┘"
            )

        print()


def main():
    """CLI interface for trajectory evaluator"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="TermNet Trajectory Evaluator")
    parser.add_argument(
        "--show", metavar="REQUEST_ID", help="Show trajectory for request"
    )
    parser.add_argument(
        "--compare",
        nargs=2,
        metavar=("REQUEST_ID", "LABEL"),
        help="Compare trajectory to golden",
    )
    parser.add_argument(
        "--init", action="store_true", help="Initialize schema and exit"
    )
    parser.add_argument(
        "--reset-test-db",
        action="store_true",
        help="Reset test database (only if path contains 'test')",
    )

    args = parser.parse_args()
    db_path = "termnet_trajectories.db"

    # Handle special flags first
    if args.init:
        evaluator = TrajectoryEvaluator(db_path)
        print(f"Schema initialized in {db_path}")
        sys.exit(0)

    if args.reset_test_db:
        if "test" not in db_path.lower():
            print("ERROR: --reset-test-db only works with test databases")
            sys.exit(1)

        import os

        if os.path.exists(db_path):
            os.unlink(db_path)
        evaluator = TrajectoryEvaluator(db_path)
        print(f"Test database {db_path} reset")
        sys.exit(0)

    evaluator = TrajectoryEvaluator(db_path)

    if args.show:
        evaluator.print_trajectory(args.show)
    elif args.compare:
        result = evaluator.compare_to_golden(args.compare[0], args.compare[1])
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
