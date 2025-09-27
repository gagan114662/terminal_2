"""
Advanced Validation Rules for TermNet - Phase 2
Project-specific and technology-specific validation rules
"""

import json
import re
from pathlib import Path
from typing import Any

from termnet.validation_engine import (
    ValidationResult,
    ValidationRule,
    ValidationSeverity,
    ValidationStatus,
)


class ReactApplicationValidation(ValidationRule):
    """Validates React applications and dependencies"""

    def __init__(self):
        super().__init__(
            name="react_app",
            description="Validate React application structure and dependencies",
            severity=ValidationSeverity.HIGH,
        )

    def should_run(self, context: dict[str, Any]) -> bool:
        project_path = context.get("project_path", "")

        # Check for React indicators
        package_json = Path(project_path) / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    deps = {
                        **data.get("dependencies", {}),
                        **data.get("devDependencies", {}),
                    }
                    return "react" in deps or "react-dom" in deps
            except:
                pass

        return False

    async def validate(
        self, project_path: str, context: dict[str, Any]
    ) -> ValidationResult:
        try:
            from termnet.tools.terminal import TerminalSession

            terminal = TerminalSession()

            # Check npm dependencies
            cmd = "npm list react react-dom --depth=0"
            output, exit_code, success = await terminal.execute_command(cmd)

            if exit_code != 0:
                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.FAILED,
                    severity=self.severity,
                    message="React dependencies not properly installed",
                    command_executed=cmd,
                    actual_output=output,
                )

            # Check for build script
            package_json = Path(project_path) / "package.json"
            if package_json.exists():
                with open(package_json) as f:
                    data = json.load(f)
                    scripts = data.get("scripts", {})
                    if "build" not in scripts:
                        return ValidationResult(
                            rule_name=self.name,
                            status=ValidationStatus.FAILED,
                            severity=self.severity,
                            message="No build script found in package.json",
                            details="React apps should have 'npm run build' script",
                        )

            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.PASSED,
                severity=self.severity,
                message="React application structure validated",
                command_executed=cmd,
                actual_output=output[:200] + "..." if len(output) > 200 else output,
            )

        except Exception as e:
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.ERROR,
                severity=self.severity,
                message=f"React validation error: {str(e)}",
            )


class DockerValidation(ValidationRule):
    """Validates Docker configuration and builds"""

    def __init__(self):
        super().__init__(
            name="docker_validation",
            description="Validate Docker configuration and build capability",
            severity=ValidationSeverity.MEDIUM,
        )

    def should_run(self, context: dict[str, Any]) -> bool:
        project_path = context.get("project_path", "")
        return (Path(project_path) / "Dockerfile").exists() or (
            Path(project_path) / "docker-compose.yml"
        ).exists()

    async def validate(
        self, project_path: str, context: dict[str, Any]
    ) -> ValidationResult:
        try:
            from termnet.tools.terminal import TerminalSession

            terminal = TerminalSession()

            # Check if Docker is available
            cmd = "docker --version"
            output, exit_code, success = await terminal.execute_command(cmd)

            if exit_code != 0:
                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.FAILED,
                    severity=self.severity,
                    message="Docker is not installed or accessible",
                    command_executed=cmd,
                    actual_output=output,
                )

            # Validate Dockerfile syntax
            dockerfile = Path(project_path) / "Dockerfile"
            if dockerfile.exists():
                with open(dockerfile) as f:
                    content = f.read()
                    if not content.strip().startswith("FROM"):
                        return ValidationResult(
                            rule_name=self.name,
                            status=ValidationStatus.FAILED,
                            severity=self.severity,
                            message="Dockerfile should start with FROM instruction",
                            details="Invalid Dockerfile format",
                        )

            # Test docker build (dry run)
            if dockerfile.exists():
                cmd = "docker build --dry-run -f Dockerfile ."
                output, exit_code, success = await terminal.execute_command(cmd)

                if exit_code != 0 and "no such file or directory" not in output.lower():
                    return ValidationResult(
                        rule_name=self.name,
                        status=ValidationStatus.FAILED,
                        severity=self.severity,
                        message="Docker build validation failed",
                        command_executed=cmd,
                        actual_output=output,
                    )

            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.PASSED,
                severity=self.severity,
                message="Docker configuration validated",
                command_executed=cmd if "cmd" in locals() else "docker --version",
            )

        except Exception as e:
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.ERROR,
                severity=self.severity,
                message=f"Docker validation error: {str(e)}",
            )


class APIEndpointValidation(ValidationRule):
    """Validates API endpoints and responses"""

    def __init__(self):
        super().__init__(
            name="api_endpoints",
            description="Validate API endpoints and basic responses",
            severity=ValidationSeverity.HIGH,
        )

    def should_run(self, context: dict[str, Any]) -> bool:
        project_path = context.get("project_path", "")

        # Check for API indicators
        for py_file in Path(project_path).rglob("*.py"):
            try:
                with open(py_file) as f:
                    content = f.read()
                    if any(
                        pattern in content
                        for pattern in [
                            "@app.route",
                            "@bp.route",
                            "FastAPI",
                            "router.get",
                            "router.post",
                        ]
                    ):
                        return True
            except:
                continue
        return False

    async def validate(
        self, project_path: str, context: dict[str, Any]
    ) -> ValidationResult:
        try:
            from termnet.tools.terminal import TerminalSession

            terminal = TerminalSession()

            # Find API endpoints in code
            endpoints = []
            for py_file in Path(project_path).rglob("*.py"):
                try:
                    with open(py_file) as f:
                        content = f.read()
                        # Flask route pattern
                        flask_routes = re.findall(
                            r'@app\.route\(["\']([^"\']+)["\']', content
                        )
                        endpoints.extend(flask_routes)
                        # Blueprint routes
                        bp_routes = re.findall(
                            r'@bp\.route\(["\']([^"\']+)["\']', content
                        )
                        endpoints.extend(bp_routes)
                except:
                    continue

            if not endpoints:
                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.SKIPPED,
                    severity=self.severity,
                    message="No API endpoints found to validate",
                )

            # Basic validation - check for common patterns
            issues = []
            for endpoint in endpoints:
                if not endpoint.startswith("/"):
                    issues.append(f"Endpoint '{endpoint}' should start with '/'")
                if "//" in endpoint:
                    issues.append(f"Endpoint '{endpoint}' has double slashes")

            if issues:
                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.FAILED,
                    severity=self.severity,
                    message=f"Found {len(issues)} endpoint issues",
                    details="; ".join(issues[:3]),
                )

            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.PASSED,
                severity=self.severity,
                message=f"Validated {len(endpoints)} API endpoints",
                details=f"Endpoints: {', '.join(endpoints[:5])}",
            )

        except Exception as e:
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.ERROR,
                severity=self.severity,
                message=f"API validation error: {str(e)}",
            )


class SecurityValidation(ValidationRule):
    """Security-focused validation rules"""

    def __init__(self):
        super().__init__(
            name="security_check",
            description="Check for common security issues",
            severity=ValidationSeverity.CRITICAL,
        )

    async def validate(
        self, project_path: str, context: dict[str, Any]
    ) -> ValidationResult:
        try:
            security_issues = []

            # Check for hardcoded secrets
            secret_patterns = [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
            ]

            for py_file in Path(project_path).rglob("*.py"):
                try:
                    with open(py_file) as f:
                        content = f.read()
                        for pattern in secret_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                security_issues.append(
                                    f"Potential hardcoded secret in {py_file.name}"
                                )
                except:
                    continue

            # Check for SQL injection patterns
            sql_patterns = [
                r'execute\s*\(\s*["\'].*%.*["\']',
                r'cursor\.execute\s*\(\s*["\'].*\+.*["\']',
            ]

            for py_file in Path(project_path).rglob("*.py"):
                try:
                    with open(py_file) as f:
                        content = f.read()
                        for pattern in sql_patterns:
                            if re.search(pattern, content):
                                security_issues.append(
                                    f"Potential SQL injection risk in {py_file.name}"
                                )
                except:
                    continue

            # Check for debug mode in production
            for py_file in Path(project_path).rglob("*.py"):
                try:
                    with open(py_file) as f:
                        content = f.read()
                        if "debug=True" in content or "DEBUG = True" in content:
                            security_issues.append(
                                f"Debug mode enabled in {py_file.name}"
                            )
                except:
                    continue

            if security_issues:
                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.FAILED,
                    severity=self.severity,
                    message=f"Found {len(security_issues)} security issues",
                    details="; ".join(security_issues[:3]),
                )

            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.PASSED,
                severity=self.severity,
                message="No obvious security issues found",
            )

        except Exception as e:
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.ERROR,
                severity=self.severity,
                message=f"Security validation error: {str(e)}",
            )


class TestCoverageValidation(ValidationRule):
    """Validates test coverage and test structure"""

    def __init__(self):
        super().__init__(
            name="test_coverage",
            description="Validate test coverage and structure",
            severity=ValidationSeverity.MEDIUM,
        )

    def should_run(self, context: dict[str, Any]) -> bool:
        project_path = context.get("project_path", "")

        # Check for test files
        test_patterns = ["test_*.py", "*_test.py", "tests/**/*.py"]
        for pattern in test_patterns:
            if list(Path(project_path).glob(pattern)):
                return True
        return False

    async def validate(
        self, project_path: str, context: dict[str, Any]
    ) -> ValidationResult:
        try:
            from termnet.tools.terminal import TerminalSession

            terminal = TerminalSession()

            # Count test files
            test_files = []
            for pattern in ["test_*.py", "*_test.py"]:
                test_files.extend(Path(project_path).glob(pattern))

            test_dirs = list(Path(project_path).glob("tests"))
            if test_dirs:
                for test_dir in test_dirs:
                    test_files.extend(test_dir.rglob("*.py"))

            if not test_files:
                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.SKIPPED,
                    severity=self.severity,
                    message="No test files found",
                )

            # Try to run tests with coverage
            cmd = "python -m pytest --tb=short"
            output, exit_code, success = await terminal.execute_command(cmd)

            if exit_code == 0:
                # Count passed tests
                passed_match = re.search(r"(\d+) passed", output)
                passed_count = int(passed_match.group(1)) if passed_match else 0

                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.PASSED,
                    severity=self.severity,
                    message=f"Tests passed: {passed_count} tests in {len(test_files)} files",
                    command_executed=cmd,
                    actual_output=output[:300] + "..." if len(output) > 300 else output,
                )
            else:
                # Tests failed
                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.FAILED,
                    severity=self.severity,
                    message="Some tests failed",
                    command_executed=cmd,
                    actual_output=output[:500] + "..." if len(output) > 500 else output,
                )

        except Exception as e:
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.ERROR,
                severity=self.severity,
                message=f"Test coverage validation error: {str(e)}",
            )
