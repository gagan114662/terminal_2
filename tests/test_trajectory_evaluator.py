"""
Tests for Trajectory Evaluator (Layer 2 AgentOps)
"""

import os
import tempfile
import time
from datetime import datetime

import pytest

from termnet.trajectory_evaluator import (
    Step,
    StepPhase,
    TrajectoryEvaluator,
    TrajectoryStatus,
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    evaluator = TrajectoryEvaluator(db_path)
    yield evaluator

    # Cleanup
    os.unlink(db_path)


def test_trajectory_creation(temp_db):
    """Test trajectory creation and database persistence"""
    evaluator = temp_db

    trajectory = evaluator.start_trajectory("test-001", tags=["unit-test"])

    assert trajectory.request_id == "test-001"
    assert "unit-test" in trajectory.tags
    assert trajectory.status == TrajectoryStatus.IN_PROGRESS

    # Verify database persistence
    data = evaluator.get_trajectory("test-001")
    assert data is not None
    assert data["trajectory"][0] == "test-001"  # request_id


def test_step_recording(temp_db):
    """Test step recording and latency tracking"""
    evaluator = temp_db

    evaluator.start_trajectory("test-002")

    # Record THINK step
    think_step = Step(
        step_index=0,
        phase=StepPhase.THINK,
        timestamp=datetime.now().isoformat(),
        latency_ms=100,
        rationale_summary="Need to check file status",
    )
    evaluator.record_step("test-002", think_step)

    # Record ACT step
    act_step = Step(
        step_index=1,
        phase=StepPhase.ACT,
        timestamp=datetime.now().isoformat(),
        latency_ms=250,
        tool_name="terminal_execute",
        tool_args={"command": "ls -la"},
        output_snippet="total 42\ndrwxr-xr-x ...",
    )
    evaluator.record_step("test-002", act_step)

    # Record OBSERVE step
    observe_step = Step(
        step_index=2,
        phase=StepPhase.OBSERVE,
        timestamp=datetime.now().isoformat(),
        latency_ms=50,
        tool_name="terminal_execute",
        output_snippet="Files found: 5 items",
        evidence_refs=[
            {
                "source_id": "fs:current_dir",
                "checksum": "sha256:abc123",
                "excerpt_hash": "def456",
            }
        ],
    )
    evaluator.record_step("test-002", observe_step)

    # Complete the trajectory to compute totals
    evaluator.finish_trajectory("test-002", TrajectoryStatus.COMPLETED)

    # Verify trajectory stats
    data = evaluator.get_trajectory("test-002")
    trajectory = data["trajectory"]
    steps = data["steps"]

    assert len(steps) == 3
    assert trajectory[6] == 400  # total_latency_ms (100+250+50)
    assert trajectory[5] == 1  # react_cycles (1 complete cycle)


def test_react_cycle_counting(temp_db):
    """Test ReAct cycle detection"""
    evaluator = temp_db

    evaluator.start_trajectory("test-003")

    # First complete ReAct cycle
    for i, phase in enumerate([StepPhase.THINK, StepPhase.ACT, StepPhase.OBSERVE]):
        step = Step(
            step_index=i,
            phase=phase,
            timestamp=datetime.now().isoformat(),
            latency_ms=100,
        )
        evaluator.record_step("test-003", step)

    # Second complete ReAct cycle
    for i, phase in enumerate(
        [StepPhase.THINK, StepPhase.ACT, StepPhase.OBSERVE], start=3
    ):
        step = Step(
            step_index=i,
            phase=phase,
            timestamp=datetime.now().isoformat(),
            latency_ms=100,
        )
        evaluator.record_step("test-003", step)

    # Incomplete cycle (just THINK)
    step = Step(
        step_index=6,
        phase=StepPhase.THINK,
        timestamp=datetime.now().isoformat(),
        latency_ms=100,
    )
    evaluator.record_step("test-003", step)

    # Finish trajectory to compute cycles
    evaluator.finish_trajectory("test-003", TrajectoryStatus.COMPLETED)

    data = evaluator.get_trajectory("test-003")
    trajectory = data["trajectory"]

    assert trajectory[5] == 2  # react_cycles should be 2 (only complete cycles)


def test_golden_trajectory(temp_db):
    """Test golden trajectory saving and comparison"""
    evaluator = temp_db

    # Create and complete a trajectory
    evaluator.start_trajectory("golden-001")

    for i in range(3):
        step = Step(
            step_index=i,
            phase=(
                StepPhase.THINK
                if i % 3 == 0
                else StepPhase.ACT
                if i % 3 == 1
                else StepPhase.OBSERVE
            ),
            timestamp=datetime.now().isoformat(),
            latency_ms=100,
        )
        evaluator.record_step("golden-001", step)

    evaluator.finish_trajectory("golden-001", TrajectoryStatus.COMPLETED)

    # Save as golden
    evaluator.save_golden(
        "golden-001", "quick-command", "Fast command execution pattern"
    )

    # Create similar trajectory
    evaluator.start_trajectory("test-004")

    for i in range(3):
        step = Step(
            step_index=i,
            phase=(
                StepPhase.THINK
                if i % 3 == 0
                else StepPhase.ACT
                if i % 3 == 1
                else StepPhase.OBSERVE
            ),
            timestamp=datetime.now().isoformat(),
            latency_ms=120,  # Slightly slower
        )
        evaluator.record_step("test-004", step)

    evaluator.finish_trajectory("test-004", TrajectoryStatus.COMPLETED)

    # Compare to golden
    comparison = evaluator.compare_to_golden("test-004", "quick-command")

    assert comparison["sequence_match"] is True
    assert comparison["step_difference"] == 0
    assert comparison["avg_ratio"] == 1.2
    assert comparison["max_ratio"] == 1.2
    assert comparison["verdict"] == "PASS"  # Within 20% latency tolerance


def test_trajectory_completion(temp_db):
    """Test trajectory completion and status tracking"""
    evaluator = temp_db

    evaluator.start_trajectory("test-005")

    # Add some steps
    step = Step(
        step_index=0,
        phase=StepPhase.THINK,
        timestamp=datetime.now().isoformat(),
        latency_ms=100,
    )
    evaluator.record_step("test-005", step)

    # Complete trajectory
    evaluator.finish_trajectory("test-005", TrajectoryStatus.COMPLETED)

    data = evaluator.get_trajectory("test-005")
    trajectory = data["trajectory"]

    assert trajectory[3] == "completed"  # status
    assert trajectory[2] is not None  # finished_at is set


def test_tools_used_tracking(temp_db):
    """Test tool usage counting"""
    evaluator = temp_db

    evaluator.start_trajectory("test-006")

    # Use terminal tool twice
    for i in range(2):
        step = Step(
            step_index=i,
            phase=StepPhase.ACT,
            timestamp=datetime.now().isoformat(),
            latency_ms=200,
            tool_name="terminal_execute",
        )
        evaluator.record_step("test-006", step)

    # Use browser search once
    step = Step(
        step_index=2,
        phase=StepPhase.ACT,
        timestamp=datetime.now().isoformat(),
        latency_ms=500,
        tool_name="browser_search",
    )
    evaluator.record_step("test-006", step)

    # Verify steps were recorded correctly
    data = evaluator.get_trajectory("test-006")
    steps = data["steps"]

    # Count tool usage in steps
    terminal_count = sum(
        1 for step in steps if len(step) > 4 and step[4] == "terminal_execute"
    )
    browser_count = sum(
        1 for step in steps if len(step) > 4 and step[4] == "browser_search"
    )

    assert terminal_count == 2
    assert browser_count == 1


def test_error_handling(temp_db):
    """Test error step recording"""
    evaluator = temp_db

    evaluator.start_trajectory("test-007")

    # Record step with error
    error_step = Step(
        step_index=0,
        phase=StepPhase.ACT,
        timestamp=datetime.now().isoformat(),
        latency_ms=50,
        tool_name="terminal_execute",
        error="Command not found: nonexistent_cmd",
        output_snippet="❌ Tool execution error: Command not found",
    )
    evaluator.record_step("test-007", error_step)

    data = evaluator.get_trajectory("test-007")
    steps = data["steps"]

    assert len(steps) == 1
    assert steps[0][6] is not None  # error field populated (index 6 in new schema)


def test_cli_display(temp_db, capsys):
    """Test CLI trajectory display"""
    evaluator = temp_db

    evaluator.start_trajectory("test-008", tags=["cli-test"])

    step = Step(
        step_index=0,
        phase=StepPhase.ACT,
        timestamp=datetime.now().isoformat(),
        latency_ms=150,
        tool_name="terminal_execute",
        output_snippet="Hello, World!",
    )
    evaluator.record_step("test-008", step)

    evaluator.finish_trajectory("test-008", TrajectoryStatus.COMPLETED)

    # Test CLI display
    evaluator.print_trajectory("test-008")

    captured = capsys.readouterr()
    assert "test-008" in captured.out
    assert "completed" in captured.out
    assert "150ms" in captured.out
    assert "terminal_execute" in captured.out


def test_nonexistent_trajectory(temp_db):
    """Test handling of nonexistent trajectories"""
    evaluator = temp_db

    data = evaluator.get_trajectory("nonexistent")
    assert data is None

    comparison = evaluator.compare_to_golden("nonexistent", "fake-golden")
    assert "error" in comparison


def test_performance_thresholds():
    """Test performance under load (deterministic)"""
    # Create in-memory DB for speed
    evaluator = TrajectoryEvaluator(":memory:")

    start_time = time.time()

    # Create 100 trajectories with 10 steps each
    for traj_id in range(100):
        request_id = f"perf-{traj_id:03d}"
        evaluator.start_trajectory(request_id)

        for step_id in range(10):
            step = Step(
                step_index=step_id,
                phase=StepPhase.THINK,
                timestamp=datetime.now().isoformat(),
                latency_ms=50,
            )
            evaluator.record_step(request_id, step)

        evaluator.finish_trajectory(request_id, TrajectoryStatus.COMPLETED)

    elapsed = time.time() - start_time

    # Should handle 1000 operations in under 2 seconds
    assert elapsed < 2.0, f"Performance test took {elapsed:.2f}s, expected < 2.0s"
