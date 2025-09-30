"""
Shared fixtures for TermNet tests
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_terminal():
    """Mock terminal that returns predictable results for testing"""

    class _MockTerminal:
        def run(self, cmd: str, timeout: int | None = None):
            """Mock terminal run method"""
            if "error" in cmd.lower():
                return {"stdout": "", "stderr": "simulated error", "exit_code": 1}
            elif "timeout" in cmd.lower():
                return {"stdout": "", "stderr": "command timed out", "exit_code": 124}
            elif "echo" in cmd.lower():
                # Extract text after echo
                parts = cmd.split("echo", 1)
                if len(parts) > 1:
                    text = parts[1].strip().strip("'\"")
                    return {"stdout": f"{text}\n", "stderr": "", "exit_code": 0}
            elif "python" in cmd.lower() and "print" in cmd.lower():
                # Mock python print statements
                return {"stdout": "test output\n", "stderr": "", "exit_code": 0}

            # Default successful command
            return {"stdout": "command executed\n", "stderr": "", "exit_code": 0}

    return _MockTerminal()


@pytest.fixture
def tmp_db():
    """Temporary database file for testing"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def temp_dir():
    """Temporary directory for file-based testing"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_agent():
    """Mock agent for testing agent interactions"""
    agent = MagicMock()
    agent.name = "test_agent"
    agent.execute_tool.return_value = {"status": "success", "output": "mock result"}
    agent.chat.return_value = "mock response"
    return agent


@pytest.fixture
def sample_trajectory_data():
    """Sample trajectory data for testing"""
    return {
        "request_id": "test-req-123",
        "steps": [
            {
                "step_index": 0,
                "phase": "think",
                "timestamp": "2024-01-01T12:00:00",
                "latency_ms": 50,
            },
            {
                "step_index": 1,
                "phase": "act",
                "timestamp": "2024-01-01T12:00:01",
                "latency_ms": 120,
                "tool_name": "terminal_execute",
                "tool_args": {"cmd": "echo test"},
            },
            {
                "step_index": 2,
                "phase": "observe",
                "timestamp": "2024-01-01T12:00:02",
                "latency_ms": 80,
            },
        ],
    }


@pytest.fixture
def mock_tool_registry():
    """Mock tool registry data for testing"""
    return [
        {
            "name": "terminal_execute",
            "type": "function",
            "enabled": True,
            "description": "Execute terminal commands",
        },
        {
            "name": "browser_search",
            "type": "function",
            "enabled": True,
            "description": "Search the web",
        },
        {
            "name": "disabled_tool",
            "type": "function",
            "enabled": False,
            "description": "This tool is disabled",
        },
        {
            "name": "non_function_tool",
            "type": "other",
            "enabled": True,
            "description": "This is not a function type",
        },
    ]


@pytest.fixture(autouse=True)
def cleanup_sqlite_connections():
    """Auto-cleanup fixture to prevent ResourceWarnings from SQLite connections"""
    yield
    # Force garbage collection to close any lingering connections
    import gc

    gc.collect()


@pytest.fixture
def no_warnings():
    """Fixture to suppress ResourceWarnings during tests"""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ResourceWarning)
        yield
