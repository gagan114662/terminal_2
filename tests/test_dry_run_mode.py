"""Test dry run mode configuration."""

import json
import os
from pathlib import Path


def test_dry_run_default_true():
    """Test that dry_run is set to true by default."""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    assert (
        config["write_guardrails"]["dry_run"] is True
    ), "dry_run should be True by default for safety"


def test_safe_mode_enabled():
    """Test that safe mode is required."""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    assert (
        config["write_guardrails"]["require_safe_mode"] is True
    ), "require_safe_mode should be True for safety"


def test_conservative_limits():
    """Test that conservative limits are set."""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path) as f:
        config = json.load(f)

    assert (
        config["retry_limits"]["concurrency_limit"] == 1
    ), "concurrency_limit should be 1 for controlled execution"

    assert (
        config["retry_limits"]["global_qps_limit"] == 2
    ), "global_qps_limit should be 2 for rate limiting"

    assert (
        config["model_config"]["temperature"] == 0.3
    ), "temperature should be 0.3 for deterministic outputs"
