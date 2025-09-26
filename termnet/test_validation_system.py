#!/usr/bin/env python3
"""
Test script for TermNet Validation System
Demonstrates validation engine and rules functionality
"""

import asyncio
import os
import sys
from pathlib import Path

# Add termnet to path
sys.path.insert(0, "termnet")

from termnet.validation_engine import (ValidationEngine, ValidationSeverity,
                                       ValidationStatus)
from termnet.validation_rules import (ApplicationStartupValidation,
                                      DatabaseValidation,
                                      FlaskApplicationValidation,
                                      PythonSyntaxValidation,
                                      RequirementsValidation)


async def test_validation_engine():
    """Test the core validation engine"""
    print("🧪 Testing TermNet Validation System")
    print("=" * 50)

    # Create validation engine
    engine = ValidationEngine("test_validation.db")

    # Add standard validation rules
    print("\n📋 Adding validation rules...")
    engine.add_rule(PythonSyntaxValidation())
    engine.add_rule(RequirementsValidation())
    engine.add_rule(ApplicationStartupValidation())
    engine.add_rule(FlaskApplicationValidation())
    engine.add_rule(DatabaseValidation())

    # Show rule statistics
    stats = engine.get_rule_statistics()
    print(f"✅ Total rules loaded: {stats['total_rules']}")
    print(f"📊 Rules by severity: {stats['rules_by_severity']}")

    return engine


async def test_project_validation(engine: ValidationEngine, project_path: str):
    """Test validation on a specific project"""
    if not Path(project_path).exists():
        print(f"⚠️ Project path does not exist: {project_path}")
        return None

    print(f"\n🔍 Testing validation on: {project_path}")
    print("-" * 40)

    # Run validation
    results = await engine.validate_project(
        project_path, {"test_mode": True, "project_type": "auto-detect"}
    )

    return results


async def test_current_directory():
    """Test validation on current TermNet directory"""
    engine = await test_validation_engine()

    print(f"\n🏠 Testing validation on current TermNet project...")
    current_dir = os.getcwd()

    results = await test_project_validation(engine, current_dir)

    if results:
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


async def test_created_projects():
    """Test validation on previously created projects"""
    engine = await test_validation_engine()

    # Test Flask projects
    test_projects = [
        "simple_flask_app.py",
        "flask_app.py",
        "flask_app_with_models.py",
        "auth_api.py",
        "blog_app.py",
        "todo_app.py",
    ]

    for project_file in test_projects:
        if Path(project_file).exists():
            print(f"\n🧪 Testing single file project: {project_file}")
            # Create a temporary directory context for single files
            temp_context = {"project_type": "single_file", "main_file": project_file}

            # For single files, test in current directory but focus on that file
            try:
                results = await engine.validate_project(".", temp_context)
                status_emoji = "✅" if results["overall_status"] == "PASSED" else "❌"
                print(
                    f"  {status_emoji} {project_file}: {results['overall_status']} ({results['passed']}/{results['total_rules']})"
                )
            except Exception as e:
                print(f"  🚫 {project_file}: Error - {e}")


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


async def test_command_validation():
    """Test the command validation helper"""
    print(f"\n⚙️ Testing command validation...")

    engine = ValidationEngine("test_validation.db")

    # Test a simple command
    result = await engine.validate_command_output(
        command="python --version", expected_patterns=["Python"], project_path="."
    )

    status_emoji = "✅" if result.status == ValidationStatus.PASSED else "❌"
    print(f"  {status_emoji} Python version check: {result.message}")

    # Test a command that should fail
    result = await engine.validate_command_output(
        command="python -c \"print('Hello World')\"",
        expected_patterns=["Hello World"],
        project_path=".",
    )

    status_emoji = "✅" if result.status == ValidationStatus.PASSED else "❌"
    print(f"  {status_emoji} Hello World test: {result.message}")


if __name__ == "__main__":
    print("🚀 TermNet Validation System Test Suite")
    print("=" * 50)

    async def run_all_tests():
        """Run all validation tests"""
        try:
            # Test 1: Core engine functionality
            await test_current_directory()

            # Test 2: Created project validation
            await test_created_projects()

            # Test 3: Validation history
            await test_validation_history()

            # Test 4: Command validation
            await test_command_validation()

            print(f"\n✅ All validation tests completed!")
            print(f"\n💡 Next steps:")
            print(f"  1. Check test_validation.db for stored results")
            print(f"  2. Try validation on your own projects")
            print(f"  3. Integrate with BMAD workflow")

        except Exception as e:
            print(f"❌ Test error: {e}")
            import traceback

            traceback.print_exc()

    # Run the test suite
    asyncio.run(run_all_tests())
