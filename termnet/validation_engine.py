"""
ValidationEngine - Core validation infrastructure for TermNet
Automatically verifies build accuracy by running terminal commands
"""

import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class ValidationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class ValidationSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ValidationResult:
    rule_name: str
    status: ValidationStatus
    severity: ValidationSeverity
    message: str
    details: Optional[str] = None
    execution_time: float = 0.0
    command_executed: Optional[str] = None
    expected_output: Optional[str] = None
    actual_output: Optional[str] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class ValidationRule:
    """Base class for validation rules"""

    def __init__(self, name: str, description: str, severity: ValidationSeverity):
        self.name = name
        self.description = description
        self.severity = severity

    async def validate(
        self, project_path: str, context: Dict[str, Any]
    ) -> ValidationResult:
        """Override this method to implement validation logic"""
        raise NotImplementedError("Subclasses must implement validate method")

    def should_run(self, context: Dict[str, Any]) -> bool:
        """Override to add conditional logic for when this rule should run"""
        return True


class ValidationEngine:
    def __init__(self, db_path: str = "termnet_validation.db"):
        self.db_path = db_path
        self.rules: List[ValidationRule] = []
        self.results: List[ValidationResult] = []
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for validation history"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS validation_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_name TEXT,
                    project_path TEXT,
                    timestamp TEXT,
                    total_rules INTEGER,
                    passed_rules INTEGER,
                    failed_rules INTEGER,
                    execution_time REAL,
                    overall_status TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS validation_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    rule_name TEXT,
                    status TEXT,
                    severity TEXT,
                    message TEXT,
                    details TEXT,
                    execution_time REAL,
                    command_executed TEXT,
                    expected_output TEXT,
                    actual_output TEXT,
                    timestamp TEXT,
                    FOREIGN KEY (run_id) REFERENCES validation_runs (id)
                )
            """
            )
            conn.commit()

    def add_rule(self, rule: ValidationRule):
        """Add a validation rule to the engine"""
        self.rules.append(rule)
        print(f"✅ Added validation rule: {rule.name}")

    def remove_rule(self, rule_name: str):
        """Remove a validation rule by name"""
        self.rules = [rule for rule in self.rules if rule.name != rule_name]
        print(f"🗑️ Removed validation rule: {rule_name}")

    async def validate_project(
        self, project_path: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Run all validation rules against a project"""
        if context is None:
            context = {}

        print(f"\n🔍 Starting validation for project: {project_path}")
        print("=" * 60)

        start_time = time.time()
        self.results = []

        # Store context info
        context.update(
            {
                "project_path": project_path,
                "project_name": Path(project_path).name,
                "validation_start_time": start_time,
            }
        )

        # Run all applicable rules
        for rule in self.rules:
            if not rule.should_run(context):
                print(f"⏭️ Skipping rule: {rule.name} (not applicable)")
                continue

            print(f"🧪 Running validation: {rule.name}")

            try:
                rule_start_time = time.time()
                result = await rule.validate(project_path, context)
                result.execution_time = time.time() - rule_start_time

                # Display result
                status_emoji = {
                    ValidationStatus.PASSED: "✅",
                    ValidationStatus.FAILED: "❌",
                    ValidationStatus.ERROR: "🚫",
                    ValidationStatus.SKIPPED: "⏭️",
                }.get(result.status, "❓")

                print(
                    f"  {status_emoji} {result.message} ({result.execution_time:.2f}s)"
                )
                if result.details:
                    print(f"    Details: {result.details}")

                self.results.append(result)

            except Exception as e:
                error_result = ValidationResult(
                    rule_name=rule.name,
                    status=ValidationStatus.ERROR,
                    severity=rule.severity,
                    message=f"Validation error: {str(e)}",
                    execution_time=time.time() - rule_start_time,
                )
                self.results.append(error_result)
                print(f"  🚫 Error in {rule.name}: {str(e)}")

        # Calculate overall results
        total_time = time.time() - start_time
        summary = self._generate_summary(total_time, context)

        # Store results in database
        await self._store_results(summary, context)

        print("\n📊 Validation Summary:")
        print(f"  Total Rules: {summary['total_rules']}")
        print(f"  Passed: {summary['passed']} ✅")
        print(f"  Failed: {summary['failed']} ❌")
        print(f"  Errors: {summary['errors']} 🚫")
        print(f"  Overall Status: {summary['overall_status']}")
        print(f"  Execution Time: {total_time:.2f}s")

        return summary

    def _generate_summary(
        self, total_time: float, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate validation summary statistics"""
        passed = len([r for r in self.results if r.status == ValidationStatus.PASSED])
        failed = len([r for r in self.results if r.status == ValidationStatus.FAILED])
        errors = len([r for r in self.results if r.status == ValidationStatus.ERROR])
        skipped = len([r for r in self.results if r.status == ValidationStatus.SKIPPED])

        # Determine overall status
        if errors > 0:
            overall_status = "ERROR"
        elif failed > 0:
            overall_status = "FAILED"
        elif passed > 0:
            overall_status = "PASSED"
        else:
            overall_status = "NO_TESTS"

        return {
            "project_name": context.get("project_name", "unknown"),
            "project_path": context.get("project_path", ""),
            "total_rules": len(self.results),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "skipped": skipped,
            "overall_status": overall_status,
            "execution_time": total_time,
            "results": self.results,
            "timestamp": datetime.now().isoformat(),
        }

    async def _store_results(self, summary: Dict[str, Any], context: Dict[str, Any]):
        """Store validation results in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Insert validation run record
                cursor = conn.execute(
                    """
                    INSERT INTO validation_runs
                    (project_name, project_path, timestamp, total_rules, passed_rules, failed_rules, execution_time, overall_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        summary["project_name"],
                        summary["project_path"],
                        summary["timestamp"],
                        summary["total_rules"],
                        summary["passed"],
                        summary["failed"],
                        summary["execution_time"],
                        summary["overall_status"],
                    ),
                )

                run_id = cursor.lastrowid

                # Insert individual results
                for result in self.results:
                    conn.execute(
                        """
                        INSERT INTO validation_results
                        (run_id, rule_name, status, severity, message, details, execution_time, command_executed, expected_output, actual_output, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            run_id,
                            result.rule_name,
                            result.status.value,
                            result.severity.value,
                            result.message,
                            result.details,
                            result.execution_time,
                            result.command_executed,
                            result.expected_output,
                            result.actual_output,
                            result.timestamp,
                        ),
                    )

                conn.commit()
                print(f"💾 Stored validation results (run_id: {run_id})")

        except Exception as e:
            print(f"⚠️ Failed to store results in database: {e}")

    def get_validation_history(
        self, project_name: Optional[str] = None, limit: int = 10
    ) -> List[Dict]:
        """Get validation history from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Return results as dictionaries

                if project_name:
                    cursor = conn.execute(
                        """
                        SELECT * FROM validation_runs
                        WHERE project_name = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """,
                        (project_name, limit),
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT * FROM validation_runs
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """,
                        (limit,),
                    )

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            print(f"⚠️ Failed to retrieve validation history: {e}")
            return []

    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get statistics about validation rules"""
        return {
            "total_rules": len(self.rules),
            "rules_by_severity": {
                severity.value: len([r for r in self.rules if r.severity == severity])
                for severity in ValidationSeverity
            },
            "rule_names": [rule.name for rule in self.rules],
        }

    async def validate_command_output(
        self, command: str, expected_patterns: List[str], project_path: str
    ) -> ValidationResult:
        """Helper method to validate command output against expected patterns"""
        from termnet.tools.terminal import TerminalSession

        terminal = TerminalSession()

        try:
            # Execute command
            output, exit_code, success = await terminal.execute_command(command)

            if not success or exit_code != 0:
                return ValidationResult(
                    rule_name="command_execution",
                    status=ValidationStatus.FAILED,
                    severity=ValidationSeverity.HIGH,
                    message=f"Command failed with exit code {exit_code}",
                    command_executed=command,
                    actual_output=output,
                )

            # Check patterns
            missing_patterns = []
            for pattern in expected_patterns:
                if pattern not in output:
                    missing_patterns.append(pattern)

            if missing_patterns:
                return ValidationResult(
                    rule_name="output_validation",
                    status=ValidationStatus.FAILED,
                    severity=ValidationSeverity.MEDIUM,
                    message=f"Missing expected patterns: {missing_patterns}",
                    command_executed=command,
                    expected_output=str(expected_patterns),
                    actual_output=output,
                )

            return ValidationResult(
                rule_name="command_validation",
                status=ValidationStatus.PASSED,
                severity=ValidationSeverity.INFO,
                message="Command executed successfully with expected output",
                command_executed=command,
                actual_output=output[:200] + "..." if len(output) > 200 else output,
            )

        except Exception as e:
            return ValidationResult(
                rule_name="command_execution",
                status=ValidationStatus.ERROR,
                severity=ValidationSeverity.CRITICAL,
                message=f"Command execution error: {str(e)}",
                command_executed=command,
            )
