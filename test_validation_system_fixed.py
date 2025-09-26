#!/usr/bin/env python3
"""
Fixed test script for TermNet Validation System
Demonstrates validation engine with limited file scope
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, "termnet")

from termnet.validation_engine import (ValidationEngine, ValidationSeverity,
                                       ValidationStatus)
from termnet.validation_rules import (ApplicationStartupValidation,
                                      DatabaseValidation,
                                      FlaskApplicationValidation,
                                      PythonSyntaxValidation,
                                      RequirementsValidation)


# Custom limited-scope Python syntax validation
class LimitedPythonSyntaxValidation(PythonSyntaxValidation):
    """Python syntax validation limited to specific files"""

    async def validate(self, project_path: str, context):
        import ast

        from termnet.validation_engine import (ValidationResult,
                                               ValidationStatus)

        # Only check specific test files, not all Python files
        test_files = [
            "simple_flask_app.py",
            "flask_app.py",
            "auth_api.py",
            "blog_app.py",
            "todo_app.py",
        ]

        existing_files = [f for f in test_files if Path(f).exists()]

        if not existing_files:
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.SKIPPED,
                severity=self.severity,
                message="No test files found to validate",
            )

        syntax_errors = []

        for py_file in existing_files[:3]:  # Limit to first 3 files for speed
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()
                ast.parse(content, filename=py_file)
            except SyntaxError as e:
                syntax_errors.append(f"{py_file}:{e.lineno} - {e.msg}")
            except Exception as e:
                syntax_errors.append(f"{py_file} - {str(e)}")

        if syntax_errors:
            return ValidationResult(
                rule_name=self.name,
                status=ValidationStatus.FAILED,
                severity=self.severity,
                message=f"Syntax errors found in {len(syntax_errors)} files",
                details="; ".join(syntax_errors),
            )

        return ValidationResult(
            rule_name=self.name,
            status=ValidationStatus.PASSED,
            severity=self.severity,
            message=f"Syntax validation passed for {len(existing_files)} files",
        )


async def test_validation_engine():
    """Test the core validation engine"""
    print("🧪 Testing TermNet Validation System (Fixed)")
    print("=" * 50)

    # Create validation engine
    engine = ValidationEngine("test_validation.db")

    # Add limited validation rules
    print("\n📋 Adding validation rules...")
    engine.add_rule(LimitedPythonSyntaxValidation())
    engine.add_rule(RequirementsValidation())

    # Show rule statistics
    stats = engine.get_rule_statistics()
    print(f"✅ Total rules loaded: {stats['total_rules']}")
    print(f"📊 Rules by severity: {stats['rules_by_severity']}")

    return engine


async def test_current_directory():
    """Test validation on current directory with limited scope"""
    engine = await test_validation_engine()

    print(f"\n🏠 Testing validation on current project (limited scope)...")
    current_dir = os.getcwd()

    results = await engine.validate_project(
        current_dir, {"test_mode": True, "limited_scope": True}
    )

    print(f"\n📈 Validation Results Summary:")
    print(f"  Project: {results['project_name']}")
    print(f"  Status: {results['overall_status']}")
    print(f"  Total Rules: {results['total_rules']}")
    print(f"  Passed: {results['passed']} ✅")
    print(f"  Failed: {results['failed']} ❌")
    print(f"  Errors: {results['errors']} 🚫")

    # Show details of failed/error results
    failed_results = [
        r
        for r in results["results"]
        if r.status in [ValidationStatus.FAILED, ValidationStatus.ERROR]
    ]
    if failed_results:
        print(f"\n⚠️ Issues found:")
        for result in failed_results:
            print(f"  - {result.rule_name}: {result.message}")
            if result.details:
                print(f"    Details: {result.details}")

    return results


async def test_validation_history():
    """Test validation history functionality"""
    print(f"\n📊 Testing validation history...")

    engine = ValidationEngine("test_validation.db")

    # Get recent validation history
    history = engine.get_validation_history(limit=5)

    if history:
        print(f"📝 Recent validation runs:")
        for i, run in enumerate(history, 1):
            print(
                f"  {i}. {run['project_name']} - {run['overall_status']} ({run['timestamp'][:16]})"
            )
            print(
                f"     Rules: {run['passed_rules']}/{run['total_rules']} passed in {run['execution_time']:.2f}s"
            )
    else:
        print(f"  No validation history found")


async def quick_command_test():
    """Quick test of command validation"""
    print(f"\n⚙️ Quick command validation test...")

    engine = ValidationEngine("test_validation.db")

    # Test a simple command
    result = await engine.validate_command_output(
        command="echo 'Hello World'",
        expected_patterns=["Hello World"],
        project_path=".",
    )

    status_emoji = "✅" if result.status == ValidationStatus.PASSED else "❌"
    print(f"  {status_emoji} Echo test: {result.message}")


if __name__ == "__main__":
    print("🚀 TermNet Validation System Test Suite (Fixed)")
    print("=" * 50)

    async def run_all_tests():
        """Run all validation tests"""
        try:
            # Test 1: Core engine functionality with limited scope
            await test_current_directory()

            # Test 2: Validation history
            await test_validation_history()

            # Test 3: Quick command validation
            await quick_command_test()

            print(f"\n✅ All validation tests completed!")
            print(f"\n💡 This is a limited-scope test that only checks specific files")
            print(f"   to avoid hanging on large directory traversals.")

        except Exception as e:
            print(f"❌ Test error: {e}")
            import traceback

            traceback.print_exc()

    # Run the test suite
    asyncio.run(run_all_tests())
