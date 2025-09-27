#!/usr/bin/env python3
"""
Limited test for TermNet Validation System - tests on specific files only
"""

import asyncio
import os
import sys

sys.path.insert(0, "termnet")

from termnet.validation_engine import ValidationEngine, ValidationStatus
from termnet.validation_rules import PythonSyntaxValidation


async def test_single_file():
    """Test validation on a single file"""
    print("🧪 Testing TermNet Validation System (Limited)")
    print("=" * 50)

    # Create validation engine
    engine = ValidationEngine("test_validation.db")

    # Create a simple test file
    test_file = "test_simple_validation.py"
    with open(test_file, "w") as f:
        f.write(
            """
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
"""
        )

    print(f"\n📋 Testing validation on single file: {test_file}")

    # Create a custom rule that only checks the specific file
    class SingleFileSyntaxValidation(PythonSyntaxValidation):
        async def validate(self, project_path: str, context):
            import ast

            from termnet.validation_engine import ValidationResult

            try:
                with open(test_file, "r") as f:
                    content = f.read()

                ast.parse(content, filename=test_file)

                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.PASSED,
                    severity=self.severity,
                    message=f"Syntax check passed for {test_file}",
                )
            except SyntaxError as e:
                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.FAILED,
                    severity=self.severity,
                    message=f"Syntax error in {test_file}",
                    details=str(e),
                )

    engine.add_rule(SingleFileSyntaxValidation())

    # Run validation
    results = await engine.validate_project(
        ".", {"test_mode": True, "single_file": test_file}
    )

    print("\n📈 Results:")
    print(f"  Status: {results['overall_status']}")
    print(f"  Passed: {results['passed']}/{results['total_rules']}")

    # Clean up
    os.remove(test_file)

    return results


async def test_syntax_error():
    """Test validation with syntax error"""
    print("\n🧪 Testing with syntax error...")

    engine = ValidationEngine("test_validation.db")

    # Create a file with syntax error
    error_file = "test_syntax_error.py"
    with open(error_file, "w") as f:
        f.write(
            """
def broken(:  # Syntax error here
    print("This won't work")
"""
        )

    class ErrorFileSyntaxValidation(PythonSyntaxValidation):
        async def validate(self, project_path: str, context):
            import ast

            from termnet.validation_engine import ValidationResult

            try:
                with open(error_file, "r") as f:
                    content = f.read()

                ast.parse(content, filename=error_file)

                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.PASSED,
                    severity=self.severity,
                    message=f"Syntax check passed for {error_file}",
                )
            except SyntaxError as e:
                return ValidationResult(
                    rule_name=self.name,
                    status=ValidationStatus.FAILED,
                    severity=self.severity,
                    message=f"Syntax error in {error_file}: line {e.lineno}",
                    details=str(e),
                )

    engine.add_rule(ErrorFileSyntaxValidation())

    results = await engine.validate_project(".", {"test_mode": True})

    print(f"  Status: {results['overall_status']}")
    print(f"  Failed: {results['failed']}/{results['total_rules']}")

    # Clean up
    os.remove(error_file)

    return results


if __name__ == "__main__":

    async def run_tests():
        try:
            # Test 1: Valid syntax
            await test_single_file()

            # Test 2: Syntax error
            await test_syntax_error()

            print("\n✅ Validation tests completed successfully!")

        except Exception as e:
            print(f"❌ Test error: {e}")
            import traceback

            traceback.print_exc()

    asyncio.run(run_tests())
