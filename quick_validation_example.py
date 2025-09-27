#!/usr/bin/env python3
"""
Quick example showing how to instantiate and use the ValidationEngine
"""

import asyncio

from termnet.validation_engine import (
    ValidationEngine,
    ValidationResult,
    ValidationRule,
    ValidationSeverity,
    ValidationStatus,
)


# Custom validation rule example
class SimpleFileExistsRule(ValidationRule):
    """Check if a specific file exists"""

    def __init__(self, filename: str):
        super().__init__(
            name=f"file_exists_{filename}",
            description=f"Check if {filename} exists",
            severity=ValidationSeverity.MEDIUM,
        )
        self.filename = filename

    async def validate(self, project_path: str, context: dict) -> ValidationResult:
        import os

        filepath = os.path.join(project_path, self.filename)

        if os.path.exists(filepath):
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.PASSED,
                severity=self.severity,
                message=f"File {self.filename} exists",
                details=f"Found at: {filepath}",
            )
        else:
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.FAILED,
                severity=self.severity,
                message=f"File {self.filename} not found",
                details=f"Expected at: {filepath}",
            )


async def main():
    # Create ValidationEngine instance with custom database
    engine = ValidationEngine("quick.db")

    print("✅ ValidationEngine created with database: quick.db")

    # Add some validation rules
    engine.add_rule(SimpleFileExistsRule("README.md"))
    engine.add_rule(SimpleFileExistsRule("requirements.txt"))
    engine.add_rule(SimpleFileExistsRule("setup.py"))

    # Run validation on current directory
    summary = await engine.validate_project(".")

    # Get validation history
    print("\n📜 Validation History:")
    history = engine.get_validation_history(limit=5)
    for run in history:
        print(
            f"  - {run['timestamp']}: {run['overall_status']} "
            f"(Passed: {run['passed_rules']}/{run['total_rules']})"
        )

    # Get rule statistics
    stats = engine.get_rule_statistics()
    print("\n📊 Rule Statistics:")
    print(f"  Total rules: {stats['total_rules']}")
    print(f"  Rules by severity: {stats['rules_by_severity']}")

    return summary


if __name__ == "__main__":
    # Run the async main function
    result = asyncio.run(main())
    print(f"\n✨ Validation complete! Overall status: {result['overall_status']}")
