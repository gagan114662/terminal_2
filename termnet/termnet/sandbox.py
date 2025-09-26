"""
Sandboxing & Security - Safe command execution with resource limits
Phase 3 of TermNet validation system: Container isolation and security
"""

import asyncio
import json
import os
import resource
import signal
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import psutil

from termnet.claims_engine import EvidenceCollector


class SandboxType(Enum):
    NONE = "none"
    PROCESS = "process"  # Process-level isolation
    CONTAINER = "container"  # Docker container
    CHROOT = "chroot"  # Chroot jail
    VM = "vm"  # Virtual machine


class SecurityLevel(Enum):
    TRUSTED = "trusted"  # Full access
    LIMITED = "limited"  # Some restrictions
    RESTRICTED = "restricted"  # Heavy restrictions
    ISOLATED = "isolated"  # Maximum isolation


@dataclass
class ResourceLimits:
    """Resource limits for sandboxed execution"""

    cpu_percent: int = 50  # Max CPU usage percentage
    memory_mb: int = 512  # Max memory in MB
    disk_mb: int = 1024  # Max disk usage in MB
    network: bool = False  # Network access allowed
    processes: int = 10  # Max number of processes
    time_limit: int = 300  # Max execution time in seconds
    file_descriptors: int = 100  # Max open file descriptors


@dataclass
class SandboxResult:
    """Result of sandboxed command execution"""

    success: bool
    exit_code: int
    output: str
    error: str
    duration: float
    resources_used: Dict[str, Any]
    violations: List[str]
    evidence_paths: List[str]
    sandbox_type: SandboxType


class SecurityPolicy:
    """Security policy for command execution"""

    def __init__(self):
        self.blocked_patterns = [
            # Destructive operations
            r"rm -rf /",
            r"sudo rm",
            r"mkfs\.",
            r"fdisk",
            r"dd if=.*of=/dev/",
            # System modifications
            r"chmod 777",
            r"chown.*root",
            r"/etc/passwd",
            r"/etc/shadow",
            r">/etc/",
            # Network security risks
            r"curl.*\|.*bash",
            r"wget.*\|.*sh",
            r"nc -l",
            r"netcat -l",
            # Process manipulation
            r"kill -9 1",
            r"killall -9",
            r"pkill -f",
            # File system risks
            r"mount.*/",
            r"umount",
            r"losetup",
            # Privilege escalation
            r"sudo su",
            r"su -",
            r"setuid",
        ]

        self.allowed_commands = [
            # Safe file operations
            r"^ls\b",
            r"^pwd\b",
            r"^echo\b",
            r"^cat\b",
            r"^grep\b",
            r"^find\b",
            r"^sort\b",
            r"^uniq\b",
            r"^wc\b",
            # Development tools
            r"^git\s+(status|log|diff|show)",
            r"^python\s+",
            r"^node\s+",
            r"^npm\s+(install|ci|test|run\s+build)",
            r"^pip\s+install\s+",
            r"^pytest\b",
            # Build tools
            r"^make\s+",
            r"^cmake\s+",
            r"^cargo\s+(build|test)",
            r"^mvn\s+(compile|test|package)",
            # Container tools (limited)
            r"^docker\s+(build|run\s+.*--rm)",
        ]

        self.security_levels = {
            SecurityLevel.TRUSTED: ResourceLimits(
                cpu_percent=100, memory_mb=2048, network=True, time_limit=1800
            ),
            SecurityLevel.LIMITED: ResourceLimits(
                cpu_percent=80, memory_mb=1024, network=True, time_limit=600
            ),
            SecurityLevel.RESTRICTED: ResourceLimits(
                cpu_percent=50, memory_mb=512, network=False, time_limit=300
            ),
            SecurityLevel.ISOLATED: ResourceLimits(
                cpu_percent=25, memory_mb=256, network=False, time_limit=120
            ),
        }

    def assess_command_security(self, command: str) -> Tuple[SecurityLevel, List[str]]:
        """Assess command security level and return violations"""
        violations = []

        # Check for blocked patterns
        import re

        for pattern in self.blocked_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                violations.append(f"Blocked pattern: {pattern}")

        # If violations found, require isolation
        if violations:
            return SecurityLevel.ISOLATED, violations

        # Check if command is explicitly allowed
        for pattern in self.allowed_commands:
            if re.match(pattern, command, re.IGNORECASE):
                return SecurityLevel.LIMITED, []

        # Unknown commands get restricted access
        return SecurityLevel.RESTRICTED, ["Unknown command - restricted access"]


class ProcessSandbox:
    """Process-level sandboxing with resource limits"""

    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.evidence_collector = EvidenceCollector()

    async def execute(self, command: str, working_dir: str = ".") -> SandboxResult:
        """Execute command with process-level sandboxing"""
        start_time = time.time()
        violations = []
        evidence_paths = []

        try:
            # Set resource limits
            self._set_resource_limits()

            # Create isolated environment
            env = self._create_isolated_env()

            # Create monitoring coroutine
            monitor_task = asyncio.create_task(self._monitor_resources(violations))

            # Execute command with timeout
            try:
                process = await asyncio.create_subprocess_shell(
                    command,
                    cwd=working_dir,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    preexec_fn=self._setup_process_limits,
                )

                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self.limits.time_limit
                )

                exit_code = process.returncode or 0
                output = stdout.decode("utf-8", errors="replace") if stdout else ""
                error = stderr.decode("utf-8", errors="replace") if stderr else ""

            except asyncio.TimeoutError:
                violations.append(f"Execution timeout ({self.limits.time_limit}s)")
                try:
                    process.terminate()
                    await asyncio.sleep(1)
                    if process.returncode is None:
                        process.kill()
                except:
                    pass
                exit_code = 124  # Timeout exit code
                output = ""
                error = "Process terminated due to timeout"

            finally:
                monitor_task.cancel()

            # Collect execution evidence
            evidence_path = await self._collect_execution_evidence(
                command, output, error, exit_code, violations
            )
            evidence_paths.append(evidence_path)

            # Get resource usage
            resources_used = self._get_resource_usage()

            duration = time.time() - start_time

            return SandboxResult(
                success=(exit_code == 0 and not violations),
                exit_code=exit_code,
                output=output,
                error=error,
                duration=duration,
                resources_used=resources_used,
                violations=violations,
                evidence_paths=evidence_paths,
                sandbox_type=SandboxType.PROCESS,
            )

        except Exception as e:
            return SandboxResult(
                success=False,
                exit_code=1,
                output="",
                error=f"Sandbox error: {str(e)}",
                duration=time.time() - start_time,
                resources_used={},
                violations=[f"Sandbox exception: {str(e)}"],
                evidence_paths=evidence_paths,
                sandbox_type=SandboxType.PROCESS,
            )

    def _set_resource_limits(self):
        """Set process resource limits"""
        try:
            # Memory limit
            if self.limits.memory_mb:
                memory_bytes = self.limits.memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))

            # Process limit
            if self.limits.processes:
                resource.setrlimit(
                    resource.RLIMIT_NPROC,
                    (self.limits.processes, self.limits.processes),
                )

            # File descriptor limit
            if self.limits.file_descriptors:
                resource.setrlimit(
                    resource.RLIMIT_NOFILE,
                    (self.limits.file_descriptors, self.limits.file_descriptors),
                )

            # CPU time limit (soft limit)
            if self.limits.time_limit:
                resource.setrlimit(
                    resource.RLIMIT_CPU,
                    (self.limits.time_limit, self.limits.time_limit + 10),
                )

        except Exception as e:
            print(f"⚠️ Failed to set resource limits: {e}")

    def _create_isolated_env(self) -> Dict[str, str]:
        """Create isolated environment variables"""
        # Start with minimal safe environment
        safe_env = {
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "HOME": tempfile.gettempdir(),
            "SHELL": "/bin/sh",
            "LANG": "en_US.UTF-8",
        }

        # Add specific variables if needed
        if self.limits.network:
            # Keep network-related variables
            for key in ["HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY"]:
                if key in os.environ:
                    safe_env[key] = os.environ[key]

        # Add Python/Node paths if needed
        for key in ["PYTHON_PATH", "NODE_PATH", "NPM_CONFIG_PREFIX"]:
            if key in os.environ:
                safe_env[key] = os.environ[key]

        return safe_env

    def _setup_process_limits(self):
        """Setup process limits (called in child process)"""
        try:
            # Create new process group
            os.setpgrp()

            # Set nice value to lower priority
            os.nice(10)

        except Exception as e:
            print(f"⚠️ Failed to setup process limits: {e}")

    async def _monitor_resources(self, violations: List[str]):
        """Monitor resource usage during execution"""
        try:
            while True:
                await asyncio.sleep(1)  # Check every second

                # Monitor CPU usage
                current_process = psutil.Process()
                cpu_percent = current_process.cpu_percent()

                if cpu_percent > self.limits.cpu_percent:
                    violations.append(
                        f"CPU limit exceeded: {cpu_percent}% > {self.limits.cpu_percent}%"
                    )

                # Monitor memory usage
                memory_info = current_process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)

                if memory_mb > self.limits.memory_mb:
                    violations.append(
                        f"Memory limit exceeded: {memory_mb:.1f}MB > {self.limits.memory_mb}MB"
                    )

        except asyncio.CancelledError:
            pass
        except Exception as e:
            violations.append(f"Monitoring error: {str(e)}")

    def _get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics"""
        try:
            current_process = psutil.Process()

            return {
                "cpu_percent": current_process.cpu_percent(),
                "memory_mb": current_process.memory_info().rss / (1024 * 1024),
                "num_threads": current_process.num_threads(),
                "num_fds": current_process.num_fds()
                if hasattr(current_process, "num_fds")
                else 0,
                "create_time": current_process.create_time(),
            }
        except Exception as e:
            return {"error": str(e)}

    async def _collect_execution_evidence(
        self,
        command: str,
        output: str,
        error: str,
        exit_code: int,
        violations: List[str],
    ) -> str:
        """Collect evidence of sandboxed execution"""
        timestamp = int(time.time())
        evidence_file = (
            self.evidence_collector.base_path / "logs" / f"{timestamp}_sandbox.json"
        )

        evidence_data = {
            "command": command,
            "exit_code": exit_code,
            "output": output,
            "error": error,
            "violations": violations,
            "sandbox_type": "process",
            "resource_limits": {
                "cpu_percent": self.limits.cpu_percent,
                "memory_mb": self.limits.memory_mb,
                "time_limit": self.limits.time_limit,
                "network": self.limits.network,
            },
            "timestamp": time.time(),
        }

        with open(evidence_file, "w") as f:
            json.dump(evidence_data, f, indent=2)

        return str(evidence_file)


class ContainerSandbox:
    """Docker container-based sandboxing"""

    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.evidence_collector = EvidenceCollector()

    async def execute(self, command: str, working_dir: str = ".") -> SandboxResult:
        """Execute command in Docker container"""
        start_time = time.time()
        violations = []
        evidence_paths = []

        try:
            # Check if Docker is available
            if not await self._docker_available():
                violations.append("Docker not available")
                return self._create_error_result(
                    "Docker not available", violations, evidence_paths
                )

            # Create container configuration
            container_config = self._create_container_config(command, working_dir)

            # Run container
            container_id = await self._run_container(container_config, violations)

            if not container_id:
                return self._create_error_result(
                    "Failed to start container", violations, evidence_paths
                )

            try:
                # Wait for container completion
                exit_code, output, error = await self._wait_for_container(
                    container_id, self.limits.time_limit, violations
                )

                # Collect container logs as evidence
                evidence_path = await self._collect_container_evidence(
                    container_id, command, output, error, exit_code
                )
                evidence_paths.append(evidence_path)

                # Get resource usage from container stats
                resources_used = await self._get_container_stats(container_id)

            finally:
                # Clean up container
                await self._cleanup_container(container_id)

            duration = time.time() - start_time

            return SandboxResult(
                success=(exit_code == 0 and not violations),
                exit_code=exit_code,
                output=output,
                error=error,
                duration=duration,
                resources_used=resources_used,
                violations=violations,
                evidence_paths=evidence_paths,
                sandbox_type=SandboxType.CONTAINER,
            )

        except Exception as e:
            return self._create_error_result(
                f"Container error: {str(e)}", violations, evidence_paths
            )

    async def _docker_available(self) -> bool:
        """Check if Docker is available"""
        try:
            process = await asyncio.create_subprocess_exec(
                "docker",
                "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.wait()
            return process.returncode == 0
        except:
            return False

    def _create_container_config(
        self, command: str, working_dir: str
    ) -> Dict[str, Any]:
        """Create Docker container configuration"""
        config = {
            "image": "python:3.11-alpine",  # Lightweight base image
            "command": ["sh", "-c", command],
            "working_dir": "/workspace",
            "volumes": {
                os.path.abspath(working_dir): {
                    "bind": "/workspace",
                    "mode": "ro" if not self._command_needs_write(command) else "rw",
                }
            },
            "mem_limit": f"{self.limits.memory_mb}m",
            "cpus": self.limits.cpu_percent / 100.0,
            "network_mode": "bridge" if self.limits.network else "none",
            "remove": True,  # Auto-remove container when it stops
            "detach": True,
            "user": "nobody",  # Run as non-root user
            "read_only": True,  # Read-only root filesystem
            "tmpfs": {"/tmp": "noexec,nosuid,size=100m"},
            "security_opt": ["no-new-privileges:true"],
        }

        return config

    def _command_needs_write(self, command: str) -> bool:
        """Check if command needs write access to working directory"""
        write_commands = ["install", "build", "compile", "test", "npm", "pip", "make"]
        return any(cmd in command.lower() for cmd in write_commands)

    async def _run_container(
        self, config: Dict[str, Any], violations: List[str]
    ) -> Optional[str]:
        """Run Docker container with configuration"""
        try:
            # Build Docker run command
            docker_cmd = ["docker", "run"]

            # Add resource limits
            docker_cmd.extend(["--memory", config["mem_limit"]])
            docker_cmd.extend(["--cpus", str(config["cpus"])])

            # Add network settings
            docker_cmd.extend(["--network", config["network_mode"]])

            # Add security settings
            docker_cmd.extend(["--user", config["user"]])
            docker_cmd.extend(["--read-only"])
            docker_cmd.extend(["--tmpfs", "/tmp:noexec,nosuid,size=100m"])
            docker_cmd.extend(["--security-opt", "no-new-privileges:true"])

            # Add volumes
            for host_path, mount_config in config["volumes"].items():
                mount_str = f"{host_path}:{mount_config['bind']}:{mount_config['mode']}"
                docker_cmd.extend(["-v", mount_str])

            # Add working directory
            docker_cmd.extend(["-w", config["working_dir"]])

            # Add auto-remove and detach
            docker_cmd.extend(["--rm", "-d"])

            # Add image and command
            docker_cmd.append(config["image"])
            docker_cmd.extend(config["command"])

            # Execute Docker command
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                container_id = stdout.decode().strip()
                return container_id
            else:
                error_msg = stderr.decode() if stderr else "Unknown Docker error"
                violations.append(f"Docker run failed: {error_msg}")
                return None

        except Exception as e:
            violations.append(f"Container start error: {str(e)}")
            return None

    async def _wait_for_container(
        self, container_id: str, timeout: int, violations: List[str]
    ) -> Tuple[int, str, str]:
        """Wait for container to complete and get results"""
        try:
            # Wait for container with timeout
            wait_process = await asyncio.create_subprocess_exec(
                "docker", "wait", container_id, stdout=asyncio.subprocess.PIPE
            )

            try:
                stdout, _ = await asyncio.wait_for(
                    wait_process.communicate(), timeout=timeout
                )
                exit_code = int(stdout.decode().strip()) if stdout else 1
            except asyncio.TimeoutError:
                violations.append(f"Container timeout ({timeout}s)")
                # Kill the container
                await asyncio.create_subprocess_exec("docker", "kill", container_id)
                exit_code = 124

            # Get container logs
            logs_process = await asyncio.create_subprocess_exec(
                "docker",
                "logs",
                container_id,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await logs_process.communicate()
            output = stdout.decode("utf-8", errors="replace") if stdout else ""
            error = stderr.decode("utf-8", errors="replace") if stderr else ""

            return exit_code, output, error

        except Exception as e:
            violations.append(f"Container wait error: {str(e)}")
            return 1, "", str(e)

    async def _get_container_stats(self, container_id: str) -> Dict[str, Any]:
        """Get container resource usage statistics"""
        try:
            stats_process = await asyncio.create_subprocess_exec(
                "docker",
                "stats",
                container_id,
                "--no-stream",
                "--format",
                "table {{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}}",
                stdout=asyncio.subprocess.PIPE,
            )

            stdout, _ = await stats_process.communicate()
            if stdout:
                stats_line = stdout.decode().strip().split("\n")[-1]
                if "," in stats_line:
                    cpu, mem, net, block = stats_line.split(",")
                    return {
                        "cpu_percent": cpu.strip(),
                        "memory_usage": mem.strip(),
                        "network_io": net.strip(),
                        "block_io": block.strip(),
                    }

        except Exception as e:
            pass

        return {}

    async def _collect_container_evidence(
        self, container_id: str, command: str, output: str, error: str, exit_code: int
    ) -> str:
        """Collect evidence from container execution"""
        timestamp = int(time.time())
        evidence_file = (
            self.evidence_collector.base_path / "logs" / f"{timestamp}_container.json"
        )

        evidence_data = {
            "container_id": container_id,
            "command": command,
            "exit_code": exit_code,
            "output": output,
            "error": error,
            "sandbox_type": "container",
            "resource_limits": {
                "memory_mb": self.limits.memory_mb,
                "cpu_percent": self.limits.cpu_percent,
                "network": self.limits.network,
                "time_limit": self.limits.time_limit,
            },
            "timestamp": time.time(),
        }

        with open(evidence_file, "w") as f:
            json.dump(evidence_data, f, indent=2)

        return str(evidence_file)

    async def _cleanup_container(self, container_id: str):
        """Clean up container"""
        try:
            # Container should auto-remove, but ensure cleanup
            await asyncio.create_subprocess_exec(
                "docker",
                "rm",
                "-f",
                container_id,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except:
            pass

    def _create_error_result(
        self, error: str, violations: List[str], evidence_paths: List[str]
    ) -> SandboxResult:
        """Create error result"""
        return SandboxResult(
            success=False,
            exit_code=1,
            output="",
            error=error,
            duration=0,
            resources_used={},
            violations=violations,
            evidence_paths=evidence_paths,
            sandbox_type=SandboxType.CONTAINER,
        )


class SandboxManager:
    """Main sandbox manager for secure command execution"""

    def __init__(self):
        self.security_policy = SecurityPolicy()

    async def execute_safely(
        self,
        command: str,
        agent: str = "unknown",
        working_dir: str = ".",
        preferred_sandbox: SandboxType = SandboxType.PROCESS,
    ) -> SandboxResult:
        """Execute command safely with appropriate sandboxing"""

        # Assess command security
        security_level, violations = self.security_policy.assess_command_security(
            command
        )

        if violations and security_level == SecurityLevel.ISOLATED:
            print(f"🚫 Command blocked due to security violations: {violations}")
            return SandboxResult(
                success=False,
                exit_code=1,
                output="",
                error=f"Command blocked: {', '.join(violations)}",
                duration=0,
                resources_used={},
                violations=violations,
                evidence_paths=[],
                sandbox_type=SandboxType.NONE,
            )

        # Get resource limits for security level
        limits = self.security_policy.security_levels[security_level]

        print(f"🔒 Executing with {security_level.value} security: {command}")

        # Choose sandbox based on security level and preference
        if security_level in [SecurityLevel.ISOLATED, SecurityLevel.RESTRICTED]:
            # High-risk commands should use containers if available
            if preferred_sandbox == SandboxType.CONTAINER:
                sandbox = ContainerSandbox(limits)
                result = await sandbox.execute(command, working_dir)
                if result.success or not result.error == "Docker not available":
                    return result
                # Fall back to process sandbox if container fails

            # Use process sandbox
            sandbox = ProcessSandbox(limits)
            return await sandbox.execute(command, working_dir)

        else:
            # Lower-risk commands can use process sandbox
            sandbox = ProcessSandbox(limits)
            return await sandbox.execute(command, working_dir)

    def get_security_assessment(self, command: str) -> Dict[str, Any]:
        """Get security assessment for a command without executing"""
        security_level, violations = self.security_policy.assess_command_security(
            command
        )
        limits = self.security_policy.security_levels[security_level]

        return {
            "command": command,
            "security_level": security_level.value,
            "violations": violations,
            "resource_limits": {
                "cpu_percent": limits.cpu_percent,
                "memory_mb": limits.memory_mb,
                "network": limits.network,
                "time_limit": limits.time_limit,
            },
            "recommended_sandbox": SandboxType.CONTAINER.value
            if security_level in [SecurityLevel.ISOLATED, SecurityLevel.RESTRICTED]
            else SandboxType.PROCESS.value,
        }


# ---- Test seam for unit tests that patch `termnet.sandbox.Sandbox` ----
# TEST SEAM: Export canonical name for tests
try:  # narrow aliasing only if base exists
    Sandbox  # type: ignore[name-defined]
except NameError:  # alias once
    try:
        from typing import TYPE_CHECKING
        # pick the most appropriate concrete sandbox class if present
        _Preferred = ProcessSandbox  # replace with the best existing class name if available
        class Sandbox(_Preferred):  # pragma: no cover
            """Alias to satisfy tests; tests patch this symbol."""
            pass
    except NameError:
        class Sandbox:  # pragma: no cover
            """Minimal placeholder; tests patch this symbol with a mock."""
            pass

try:
    __all__  # type: ignore[var-annotated]
except NameError:
    __all__ = []
if "Sandbox" not in __all__:
    __all__.append("Sandbox")
# ----------------------------------------------------------------------
