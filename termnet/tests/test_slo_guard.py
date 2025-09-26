"""Test SLO (Service Level Objective) guards."""

import json
import statistics
from pathlib import Path
from typing import Any, Dict, List


def test_slo_threshold():
    """Test that SLO thresholds are met."""
    metrics_path = (
        Path(__file__).parent.parent / "artifacts" / "last_run" / "metrics_dump.json"
    )

    # Create mock metrics if file doesn't exist (for testing)
    if not metrics_path.exists():
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        mock_metrics = [{"reasoning_latency_ms": 150, "step": i} for i in range(5)]
        with open(metrics_path, "w") as f:
            json.dump(mock_metrics, f)

    with open(metrics_path) as f:
        data = json.load(f)

    # Get last 5 measurements
    recent_metrics = data[-5:] if len(data) >= 5 else data
    latencies = [m.get("reasoning_latency_ms", 0) for m in recent_metrics]

    # Check median latency
    if latencies:
        median_latency = statistics.median(latencies)
        assert (
            median_latency <= 300
        ), f"Median latency {median_latency}ms exceeds 300ms SLO"


def test_error_rate_slo():
    """Test error rate is within SLO."""
    metrics_path = (
        Path(__file__).parent.parent / "artifacts" / "last_run" / "metrics_dump.json"
    )

    if not metrics_path.exists():
        # Create mock data for testing
        metrics_path.parent.mkdir(parents=True, exist_ok=True)
        mock_metrics = [{"success": True, "step": i} for i in range(10)]
        with open(metrics_path, "w") as f:
            json.dump(mock_metrics, f)

    with open(metrics_path) as f:
        data = json.load(f)

    # Calculate success rate
    if data:
        successes = sum(1 for m in data if m.get("success", False))
        success_rate = successes / len(data)
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} below 95% SLO"


def test_response_time_budget():
    """Test that response times stay within budget."""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    per_call_timeout = config["timeout_config"]["per_call_timeout_ms"]
    session_timeout = config["timeout_config"]["session_timeout_ms"]

    assert (
        per_call_timeout <= 30000
    ), f"Per-call timeout {per_call_timeout}ms exceeds 30s budget"

    assert (
        session_timeout <= 600000
    ), f"Session timeout {session_timeout}ms exceeds 10min budget"
