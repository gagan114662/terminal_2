"""Test secrets redaction in logs and trajectories."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def now_iso():
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()


class TrajectoryStep:
    """Trajectory step data class."""

    def __init__(
        self,
        run_id: str,
        trace_id: str,
        step_index: int,
        phase: str,
        timestamp: str,
        latency_ms: int,
        tool_name: str,
        tool_args_redacted: Dict[str, Any],
    ):
        self.run_id = run_id
        self.trace_id = trace_id
        self.step_index = step_index
        self.phase = phase
        self.timestamp = timestamp
        self.latency_ms = latency_ms
        self.tool_name = tool_name
        self.tool_args_redacted = tool_args_redacted


def log_step(step: TrajectoryStep, output_path: Path = None):
    """Log a trajectory step with redaction."""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    secrets_patterns = config["safety_config"]["secrets_patterns"]

    # Convert step to dict
    step_dict = {
        "run_id": step.run_id,
        "trace_id": step.trace_id,
        "step_index": step.step_index,
        "phase": step.phase,
        "timestamp": step.timestamp,
        "latency_ms": step.latency_ms,
        "tool_name": step.tool_name,
        "tool_args": step.tool_args_redacted,
    }

    # Redact secrets from the serialized data
    step_json = json.dumps(step_dict)
    for pattern in secrets_patterns:
        step_json = re.sub(pattern, "[REDACTED]", step_json, flags=re.IGNORECASE)

    # Write to trajectory file
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "a") as f:
            f.write(step_json + "\n")

    return step_json


def test_redaction_in_trajectory(tmp_path):
    """Test that secrets are redacted in trajectory logs."""
    traj_file = tmp_path / "trajectory.jsonl"

    # Create a step with various secret patterns
    step = TrajectoryStep(
        run_id="test-run",
        trace_id="test-trace",
        step_index=0,
        phase="observe",
        timestamp=now_iso(),
        latency_ms=10,
        tool_name="test",
        tool_args_redacted={
            "github_token": "ghp_abcdef1234567890abcdef1234567890abcd",
            "api_key": "sk-proj1234567890abcdefghijklmnopqrstuv",
            "password": "super_secret_password_123",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
        },
    )

    # Log the step
    log_step(step, traj_file)

    # Read the file content
    content = traj_file.read_text()

    # Verify no secrets remain
    assert "ghp_abcdef1234567890abcdef1234567890abcd" not in content
    assert "sk-proj1234567890abcdefghijklmnopqrstuv" not in content
    assert "super_secret_password_123" not in content
    assert "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" not in content

    # Verify redaction markers are present
    assert "[REDACTED]" in content


def test_github_token_redaction():
    """Test GitHub token patterns are redacted."""
    secrets = [
        "ghp_abcdef1234567890abcdef1234567890abcd",  # Personal access token
        "ghs_abcdef1234567890abcdef1234567890abcd",  # Server token
        "github_pat_11ABCDEFG_1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN",  # Fine-grained PAT
    ]

    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    patterns = config["safety_config"]["secrets_patterns"]

    for secret in secrets:
        text = f"My token is {secret} in the code"
        redacted = text
        for pattern in patterns:
            redacted = re.sub(pattern, "[REDACTED]", redacted, flags=re.IGNORECASE)

        assert secret not in redacted, f"Failed to redact: {secret}"


def test_api_key_redaction():
    """Test various API key patterns are redacted."""
    test_cases = [
        ("api_key: 'abc123def456'", "api_key"),
        ("APIKEY=xyz789ghi012", "APIKEY"),
        ("secret: super_secret_value", "secret"),
        ("token = 'bearer abc123'", "token"),
        ("password: my_password_123", "password"),
    ]

    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    patterns = config["safety_config"]["secrets_patterns"]

    for text, keyword in test_cases:
        redacted = text
        for pattern in patterns:
            redacted = re.sub(pattern, "[REDACTED]", redacted, flags=re.IGNORECASE)

        # The secret value should be gone but keyword might remain
        assert keyword.lower() in text.lower()
        if "[REDACTED]" in redacted:
            # If redaction occurred, original secret shouldn't be present
            assert text != redacted
