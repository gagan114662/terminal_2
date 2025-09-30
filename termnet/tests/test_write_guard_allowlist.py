"""Test write guard allowlist enforcement."""

import json
import os
from pathlib import Path


def load_config():
    """Load configuration from config.json."""
    config_path = Path(__file__).parent.parent / "config.json"
    with open(config_path) as f:
        return json.load(f)


def path_is_allowed(file_path: str) -> bool:
    """Check if a path is allowed for writing."""
    config = load_config()
    allowlist = config["write_guardrails"]["write_allowlist_paths"]
    blocklist = config["write_guardrails"]["write_blocklist_paths"]

    # Check blocklist first
    for pattern in blocklist:
        if pattern.endswith("/**"):
            base = pattern[:-3]
            if file_path.startswith(base):
                return False
        elif pattern.startswith("**/"):
            suffix = pattern[3:]
            if file_path.endswith(suffix):
                return False
        elif file_path == pattern:
            return False

    # Check allowlist
    for pattern in allowlist:
        if pattern.endswith("/**"):
            base = pattern[:-3]
            if file_path.startswith(base):
                return True
        elif pattern.startswith("*."):
            ext = pattern[1:]
            if file_path.endswith(ext):
                return True
        elif file_path == pattern:
            return True

    return False


def test_block_outside_allowlist():
    """Test that system paths are blocked."""
    assert not path_is_allowed("/etc/hosts")
    assert not path_is_allowed("/usr/bin/python")
    assert not path_is_allowed("~/.ssh/config")
    assert not path_is_allowed("/System/Library/test.py")


def test_allow_inside_repo():
    """Test that repo paths are allowed."""
    assert path_is_allowed("TermNet/termnet/agent.py")
    assert path_is_allowed("src/main.py")
    assert path_is_allowed("tests/test_example.py")
    assert path_is_allowed("config.json")


def test_block_secrets():
    """Test that secret files are blocked."""
    assert not path_is_allowed("secrets/api.key")
    assert not path_is_allowed("myproject/.aws/credentials")
    assert not path_is_allowed("cert.pem")
    assert not path_is_allowed("private.key")
