#!/usr/bin/env python3
"""
Create a test trajectory for TermNet trajectory evaluator
Demonstrates a complete ReAct cycle with multiple tools
"""

import time
import uuid
from datetime import datetime

from termnet.trajectory_evaluator import (Step, StepPhase, TrajectoryEvaluator,
                                          TrajectoryStatus)


def create_test_trajectory():
    """Create a sample trajectory with multiple ReAct cycles"""

    evaluator = TrajectoryEvaluator("test_trajectory.db")

    # Generate a unique request ID
    request_id = f"test_{uuid.uuid4().hex[:8]}"

    print(f"Creating test trajectory: {request_id}")

    # Start the trajectory
    trajectory = evaluator.start_trajectory(
        request_id=request_id, tags=["test", "demo", "multi-tool"]
    )

    # Simulate ReAct Cycle 1: File Search
    print("\nReAct Cycle 1: File Search")

    # THINK phase
    step1 = Step(
        step_index=0,
        phase=StepPhase.THINK,
        timestamp=datetime.now().isoformat(),
        latency_ms=150,
        rationale_summary="Need to search for configuration files in the project",
        evidence_refs=[{"type": "user_request", "content": "Find all config files"}],
    )
    evaluator.record_step(request_id, step1)
    time.sleep(0.1)

    # ACT phase
    step2 = Step(
        step_index=1,
        phase=StepPhase.ACT,
        timestamp=datetime.now().isoformat(),
        latency_ms=250,
        tool_name="grep",
        tool_args={"pattern": "*.config.json", "path": "./"},
        output_snippet="Found 3 config files",
    )
    evaluator.record_step(request_id, step2)
    time.sleep(0.1)

    # OBSERVE phase
    step3 = Step(
        step_index=2,
        phase=StepPhase.OBSERVE,
        timestamp=datetime.now().isoformat(),
        latency_ms=100,
        output_snippet="./termnet/config.json\n./test/config.json\n./backup/config.json",
    )
    evaluator.record_step(request_id, step3)
    time.sleep(0.2)

    # Simulate ReAct Cycle 2: Terminal Execution
    print("ReAct Cycle 2: Terminal Execution")

    # THINK phase
    step4 = Step(
        step_index=3,
        phase=StepPhase.THINK,
        timestamp=datetime.now().isoformat(),
        latency_ms=180,
        rationale_summary="Need to check Python version and installed packages",
        evidence_refs=[{"type": "context", "content": "Verifying environment setup"}],
    )
    evaluator.record_step(request_id, step4)
    time.sleep(0.1)

    # ACT phase
    step5 = Step(
        step_index=4,
        phase=StepPhase.ACT,
        timestamp=datetime.now().isoformat(),
        latency_ms=320,
        tool_name="terminal",
        tool_args={"command": "python --version && pip list | head -5"},
        output_snippet="Python 3.11.5",
    )
    evaluator.record_step(request_id, step5)
    time.sleep(0.1)

    # OBSERVE phase
    step6 = Step(
        step_index=5,
        phase=StepPhase.OBSERVE,
        timestamp=datetime.now().isoformat(),
        latency_ms=150,
        output_snippet="Python 3.11.5\nPackage list retrieved successfully",
    )
    evaluator.record_step(request_id, step6)
    time.sleep(0.15)

    # Simulate ReAct Cycle 3: Web Search
    print("ReAct Cycle 3: Web Search")

    # THINK phase
    step7 = Step(
        step_index=6,
        phase=StepPhase.THINK,
        timestamp=datetime.now().isoformat(),
        latency_ms=200,
        rationale_summary="Need to search for latest security vulnerabilities",
        tokens_in=150,
        tokens_out=50,
    )
    evaluator.record_step(request_id, step7)
    time.sleep(0.1)

    # ACT phase
    step8 = Step(
        step_index=7,
        phase=StepPhase.ACT,
        timestamp=datetime.now().isoformat(),
        latency_ms=850,
        tool_name="browsersearch",
        tool_args={"query": "CVE 2024 critical vulnerabilities", "max_results": 5},
        output_snippet="Retrieved 5 recent CVE entries",
    )
    evaluator.record_step(request_id, step8)
    time.sleep(0.1)

    # OBSERVE phase with error
    step9 = Step(
        step_index=8,
        phase=StepPhase.OBSERVE,
        timestamp=datetime.now().isoformat(),
        latency_ms=200,
        error="Rate limit exceeded for API",
        output_snippet=None,
    )
    evaluator.record_step(request_id, step9)
    time.sleep(0.1)

    # Simulate ReAct Cycle 4: Recovery and Alternative Approach
    print("ReAct Cycle 4: Recovery")

    # THINK phase
    step10 = Step(
        step_index=9,
        phase=StepPhase.THINK,
        timestamp=datetime.now().isoformat(),
        latency_ms=170,
        rationale_summary="API rate limited, switching to local cache",
        evidence_refs=[{"type": "error", "content": "Rate limit exceeded"}],
    )
    evaluator.record_step(request_id, step10)
    time.sleep(0.1)

    # ACT phase
    step11 = Step(
        step_index=10,
        phase=StepPhase.ACT,
        timestamp=datetime.now().isoformat(),
        latency_ms=280,
        tool_name="scratchpad",
        tool_args={"action": "read", "file": "cache_vulnerabilities.txt"},
        output_snippet="Reading cached vulnerability data",
    )
    evaluator.record_step(request_id, step11)
    time.sleep(0.1)

    # OBSERVE phase
    step12 = Step(
        step_index=11,
        phase=StepPhase.OBSERVE,
        timestamp=datetime.now().isoformat(),
        latency_ms=120,
        output_snippet="Successfully retrieved 10 cached CVE entries",
    )
    evaluator.record_step(request_id, step12)

    # Finish the trajectory
    evaluator.finish_trajectory(request_id, TrajectoryStatus.COMPLETED)

    print(f"\n✓ Test trajectory created successfully!")
    print(f"  Request ID: {request_id}")
    print(f"  Total steps: 12")
    print(f"  ReAct cycles: 4")

    # Save as golden trajectory
    evaluator.save_golden(
        request_id=request_id,
        label="test_multi_tool_flow",
        description="Test trajectory with multiple tools and error recovery",
    )
    print(f"\n✓ Saved as golden trajectory: 'test_multi_tool_flow'")

    # Display the trajectory
    print("\n" + "=" * 60)
    evaluator.print_trajectory(request_id)

    return request_id


def test_comparison():
    """Test trajectory comparison functionality"""
    print("\n" + "=" * 60)
    print("Testing Trajectory Comparison")
    print("=" * 60)

    evaluator = TrajectoryEvaluator("test_trajectory.db")

    # Create a second trajectory that's similar but slightly different
    request_id2 = f"test_{uuid.uuid4().hex[:8]}"
    print(f"\nCreating comparison trajectory: {request_id2}")

    trajectory = evaluator.start_trajectory(
        request_id=request_id2, tags=["test", "comparison"]
    )

    # Similar but faster execution
    steps = [
        Step(0, StepPhase.THINK, datetime.now().isoformat(), 100),
        Step(1, StepPhase.ACT, datetime.now().isoformat(), 200, tool_name="grep"),
        Step(2, StepPhase.OBSERVE, datetime.now().isoformat(), 80),
        Step(3, StepPhase.THINK, datetime.now().isoformat(), 150),
        Step(4, StepPhase.ACT, datetime.now().isoformat(), 280, tool_name="terminal"),
        Step(5, StepPhase.OBSERVE, datetime.now().isoformat(), 100),
    ]

    for step in steps:
        evaluator.record_step(request_id2, step)
        time.sleep(0.05)

    evaluator.finish_trajectory(request_id2, TrajectoryStatus.COMPLETED)

    # Compare to golden
    print("\nComparing to golden trajectory 'test_multi_tool_flow':")
    comparison = evaluator.compare_to_golden(request_id2, "test_multi_tool_flow")

    for key, value in comparison.items():
        print(f"  {key}: {value}")

    print("\n✓ Comparison test completed!")

    return request_id2


def test_analytics():
    """Test trajectory analytics queries"""
    print("\n" + "=" * 60)
    print("Testing Trajectory Analytics")
    print("=" * 60)

    import sqlite3

    with sqlite3.connect("test_trajectory.db") as conn:
        # Query 1: Tool usage statistics
        print("\n📊 Tool Usage Statistics:")
        cursor = conn.execute(
            """
            SELECT
                tool_name,
                COUNT(*) as usage_count,
                AVG(latency_ms) as avg_latency,
                MIN(latency_ms) as min_latency,
                MAX(latency_ms) as max_latency
            FROM trajectory_steps
            WHERE tool_name IS NOT NULL
            GROUP BY tool_name
            ORDER BY usage_count DESC
        """
        )

        for row in cursor.fetchall():
            print(
                f"  {row[0]}: {row[1]} calls, avg={row[2]:.0f}ms, range=[{row[3]}-{row[4]}ms]"
            )

        # Query 2: Phase distribution
        print("\n📊 Phase Distribution:")
        cursor = conn.execute(
            """
            SELECT
                phase,
                COUNT(*) as count,
                AVG(latency_ms) as avg_latency
            FROM trajectory_steps
            GROUP BY phase
            ORDER BY phase
        """
        )

        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} steps, avg={row[2]:.0f}ms")

        # Query 3: Error analysis
        print("\n📊 Error Analysis:")
        cursor = conn.execute(
            """
            SELECT
                tool_name,
                error,
                COUNT(*) as error_count
            FROM trajectory_steps
            WHERE error IS NOT NULL
            GROUP BY tool_name, error
        """
        )

        errors = cursor.fetchall()
        if errors:
            for row in errors:
                print(f"  {row[0] or 'N/A'}: {row[1]} (count: {row[2]})")
        else:
            print("  No errors found")

        # Query 4: Trajectory summary
        print("\n📊 Trajectory Summary:")
        cursor = conn.execute(
            """
            SELECT
                status,
                COUNT(*) as count,
                AVG(total_steps) as avg_steps,
                AVG(total_latency_ms) as avg_latency,
                AVG(react_cycles) as avg_cycles
            FROM trajectories
            GROUP BY status
        """
        )

        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} trajectories")
            print(
                f"    Avg steps: {row[2]:.1f}, Avg latency: {row[3]:.0f}ms, Avg cycles: {row[4]:.1f}"
            )

    print("\n✓ Analytics test completed!")


if __name__ == "__main__":
    print("=" * 60)
    print("TermNet Trajectory Evaluator - Test Suite")
    print("=" * 60)

    # Run all tests
    request_id1 = create_test_trajectory()
    request_id2 = test_comparison()
    test_analytics()

    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print(f"\nCreated trajectories:")
    print(f"  - {request_id1} (golden: test_multi_tool_flow)")
    print(f"  - {request_id2} (comparison test)")
    print(f"\nDatabase: test_trajectory.db")
    print("=" * 60)
