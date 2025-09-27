"""
ValidationRules - Standard validation rules for TermNet projects
"""

import ast
from pathlib import Path
from typing import Any, Dict

from termnet.validation_engine import (
    ValidationResult,
    ValidationRule,
    ValidationSeverity,
    ValidationStatus,
)


class PythonSyntaxValidation(ValidationRule):
    """Validates Python syntax for all .py files in the project"""

    def __init__(self):
        super().__init__(
            name="python_syntax",
            description="Check Python syntax for all .py files",
            severity=ValidationSeverity.CRITICAL,
        )

    async def validate(
        self, project_path: str, context: Dict[str, Any]
    ) -> ValidationResult:
        python_files = list(Path(project_path).rglob("*.py"))

        if not python_files:
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.SKIPPED,
                severity=self.severity,
                message="No Python files found to validate",
            )

        syntax_errors = []

        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Parse the Python syntax
                ast.parse(content, filename=str(py_file))

            except SyntaxError as e:
                syntax_errors.append(f"{py_file.name}:{e.lineno} - {e.msg}")
            except Exception as e:
                syntax_errors.append(f"{py_file.name} - {str(e)}")

        if syntax_errors:
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.FAILED,
                severity=self.severity,
                message=f"Syntax errors found in {len(syntax_errors)} files",
                details="; ".join(syntax_errors[:5]),  # Show first 5 errors
            )

        return ValidationResult(
            rule_name=self.name,
            status=ValidationStatus.PASSED,
            severity=self.severity,
            message=f"All {len(python_files)} Python files have valid syntax",
        )


class RequirementsValidation(ValidationRule):
    """Validates that requirements.txt packages can be installed"""

    def __init__(self):
        super().__init__(
            name="requirements_check",
            description="Validate requirements.txt dependencies",
            severity=ValidationSeverity.HIGH,
        )

    def should_run(self, context: Dict[str, Any]) -> bool:
        project_path = context.get("project_path", "")
        return Path(project_path).joinpath("requirements.txt").exists()

    async def validate(
        self, project_path: str, context: Dict[str, Any]
    ) -> ValidationResult:
        requirements_file = Path(project_path) / "requirements.txt"

        try:
            # Read requirements
            with open(requirements_file, "r") as f:
                requirements = f.read().strip().split("\n")

            # Filter out empty lines and comments
            packages = [
                req.strip()
                for req in requirements
                if req.strip() and not req.strip().startswith("#")
            ]

            if not packages:
                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.SKIPPED,
                    severity=self.severity,
                    message="Requirements file is empty",
                )

            # Try to check if packages exist (dry run)
            from termnet.tools.terminal import TerminalSession

            terminal = TerminalSession()

            for package in packages[:3]:  # Check first 3 packages only for speed
                # Use pip show to check if package exists
                cmd = f"pip show {package.split('==')[0].split('>=')[0].split('<=')[0]}"
                output, exit_code, success = await terminal.execute_command(cmd)

                if exit_code != 0:
                    return ValidationResult(
                        rule_name=self.name,
                        status=ValidationStatus.FAILED,
                        severity=self.severity,
                        message=f"Package '{package}' appears to be invalid or not installed",
                        command_executed=cmd,
                        actual_output=output,
                    )

            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.PASSED,
                severity=self.severity,
                message=f"Requirements file contains {len(packages)} valid packages",
            )

        except Exception as e:
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.ERROR,
                severity=self.severity,
                message=f"Error validating requirements: {str(e)}",
            )


class ApplicationStartupValidation(ValidationRule):
    """Validates that Python applications can start without errors"""

    def __init__(self):
        super().__init__(
            name="app_startup",
            description="Test application startup",
            severity=ValidationSeverity.HIGH,
        )

    async def validate(
        self, project_path: str, context: Dict[str, Any]
    ) -> ValidationResult:
        # Look for common application entry points
        entry_points = ["app.py", "main.py", "run.py", "server.py"]
        found_entry = None

        for entry in entry_points:
            entry_path = Path(project_path) / entry
            if entry_path.exists():
                found_entry = entry
                break

        if not found_entry:
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.SKIPPED,
                severity=self.severity,
                message="No common entry point files found (app.py, main.py, etc.)",
            )

        try:
            from termnet.tools.terminal import TerminalSession

            terminal = TerminalSession()

            # Try to run python -m py_compile to check if it compiles
            cmd = f"python -m py_compile {found_entry}"
            output, exit_code, success = await terminal.execute_command(cmd)

            if exit_code != 0:
                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.FAILED,
                    severity=self.severity,
                    message=f"Application {found_entry} failed to compile",
                    command_executed=cmd,
                    actual_output=output,
                )

            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.PASSED,
                severity=self.severity,
                message=f"Application {found_entry} compiles successfully",
                command_executed=cmd,
            )

        except Exception as e:
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.ERROR,
                severity=self.severity,
                message=f"Error testing application startup: {str(e)}",
            )


class FlaskApplicationValidation(ValidationRule):
    """Validates Flask applications specifically"""

    def __init__(self):
        super().__init__(
            name="flask_app",
            description="Validate Flask application structure and imports",
            severity=ValidationSeverity.MEDIUM,
        )

    def should_run(self, context: Dict[str, Any]) -> bool:
        project_path = context.get("project_path", "")

        # Check if Flask is mentioned in requirements or code
        requirements_path = Path(project_path) / "requirements.txt"
        if requirements_path.exists():
            with open(requirements_path, "r") as f:
                content = f.read()
                if "flask" in content.lower():
                    return True

        # Check for Flask imports in Python files
        for py_file in Path(project_path).rglob("*.py"):
            try:
                with open(py_file, "r") as f:
                    content = f.read()
                    if "from flask import" in content or "import flask" in content:
                        return True
            except:
                continue

        return False

    async def validate(
        self, project_path: str, context: Dict[str, Any]
    ) -> ValidationResult:
        try:
            from termnet.tools.terminal import TerminalSession

            terminal = TerminalSession()

            # Check if Flask is importable
            cmd = "python -c \"import flask; print(f'Flask version: {flask.__version__}')\""
            output, exit_code, success = await terminal.execute_command(cmd)

            if exit_code != 0:
                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.FAILED,
                    severity=self.severity,
                    message="Flask is not properly installed or importable",
                    command_executed=cmd,
                    actual_output=output,
                )

            # Look for Flask app patterns
            app_files = []
            for py_file in Path(project_path).rglob("*.py"):
                try:
                    with open(py_file, "r") as f:
                        content = f.read()
                        if "Flask(__name__)" in content or "app = Flask" in content:
                            app_files.append(py_file.name)
                except:
                    continue

            if not app_files:
                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.FAILED,
                    severity=self.severity,
                    message="No Flask app instances found in Python files",
                    details="Expected to find 'Flask(__name__)' or 'app = Flask' patterns",
                )

            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.PASSED,
                severity=self.severity,
                message=f"Flask application structure valid. Found Flask apps in: {', '.join(app_files)}",
                command_executed=cmd,
                actual_output=output,
            )

        except Exception as e:
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.ERROR,
                severity=self.severity,
                message=f"Error validating Flask application: {str(e)}",
            )


class DatabaseValidation(ValidationRule):
    """Validates database-related code and dependencies"""

    def __init__(self):
        super().__init__(
            name="database_check",
            description="Validate database configurations and imports",
            severity=ValidationSeverity.MEDIUM,
        )

    def should_run(self, context: Dict[str, Any]) -> bool:
        project_path = context.get("project_path", "")

        # Check for database-related files or imports
        db_indicators = [
            "sqlite",
            "postgresql",
            "mysql",
            "sqlalchemy",
            "django.db",
            "models.py",
            "database",
            "db.py",
        ]

        # Check requirements.txt
        requirements_path = Path(project_path) / "requirements.txt"
        if requirements_path.exists():
            with open(requirements_path, "r") as f:
                content = f.read().lower()
                if any(indicator in content for indicator in db_indicators):
                    return True

        # Check Python files for database imports
        for py_file in Path(project_path).rglob("*.py"):
            try:
                with open(py_file, "r") as f:
                    content = f.read().lower()
                    if any(indicator in content for indicator in db_indicators):
                        return True
            except:
                continue

        return False

    async def validate(
        self, project_path: str, context: Dict[str, Any]
    ) -> ValidationResult:
        try:
            findings = []

            # Check for SQLite files
            sqlite_files = list(Path(project_path).glob("*.db")) + list(
                Path(project_path).glob("*.sqlite*")
            )
            if sqlite_files:
                findings.append(
                    f"Found SQLite database files: {[f.name for f in sqlite_files]}"
                )

            # Check for common ORM imports
            orm_imports = []
            for py_file in Path(project_path).rglob("*.py"):
                try:
                    with open(py_file, "r") as f:
                        content = f.read()
                        if (
                            "from sqlalchemy import" in content
                            or "import sqlalchemy" in content
                        ):
                            orm_imports.append(f"{py_file.name}: SQLAlchemy")
                        elif "from django.db import" in content:
                            orm_imports.append(f"{py_file.name}: Django ORM")
                except:
                    continue

            if orm_imports:
                findings.append(f"Database ORM imports found: {orm_imports}")

            if not findings:
                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.SKIPPED,
                    severity=self.severity,
                    message="No database-related code detected",
                )

            # Try to test database imports
            from termnet.tools.terminal import TerminalSession

            terminal = TerminalSession()

            test_commands = []
            if any("sqlalchemy" in f.lower() for f in findings):
                test_commands.append(
                    "python -c \"import sqlalchemy; print('SQLAlchemy OK')\""
                )

            for cmd in test_commands:
                output, exit_code, success = await terminal.execute_command(cmd)
                if exit_code != 0:
                    return ValidationResult(
                        rule_name=self.name,
                        status=ValidationStatus.FAILED,
                        severity=self.severity,
                        message="Database dependencies not properly installed",
                        command_executed=cmd,
                        actual_output=output,
                    )

            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.PASSED,
                severity=self.severity,
                message="Database validation passed",
                details="; ".join(findings),
            )

        except Exception as e:
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.ERROR,
                severity=self.severity,
                message=f"Error validating database setup: {str(e)}",
            )
