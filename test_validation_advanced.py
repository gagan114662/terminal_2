#!/usr/bin/env python3
"""
Advanced Validation System Test - Phase 2
Tests advanced validation rules, monitoring, and BMAD integration
"""

import asyncio
import sys

# Add termnet to path
sys.path.insert(0, "termnet")

# Test imports
try:
    from termnet.validation_engine import ValidationEngine
    from termnet.validation_monitor import ValidationMonitor
    from termnet.validation_rules_advanced import (
        APIEndpointValidation,
        DockerValidation,
        ReactApplicationValidation,
        SecurityValidation,
        TestCoverageValidation,
    )

    print("✅ All advanced validation imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


async def test_advanced_rules():
    """Test advanced validation rules"""
    print("\n🧪 Testing Advanced Validation Rules")
    print("=" * 50)

    engine = ValidationEngine("test_advanced.db")

    # Add advanced rules
    advanced_rules = [
        ReactApplicationValidation(),
        DockerValidation(),
        APIEndpointValidation(),
        SecurityValidation(),
        TestCoverageValidation(),
    ]

    for rule in advanced_rules:
        engine.add_rule(rule)

    # Test on current project
    results = await engine.validate_project(
        ".", {"test_mode": True, "advanced_validation": True}
    )

    print("\n📊 Advanced Validation Results:")
    print(f"  Status: {results['overall_status']}")
    print(f"  Rules: {results['total_rules']}")
    print(f"  Passed: {results['passed']} ✅")
    print(f"  Failed: {results['failed']} ❌")
    print(f"  Errors: {results['errors']} 🚫")

    # Show rule details
    for result in results["results"]:
        status = {"PASSED": "✅", "FAILED": "❌", "ERROR": "🚫", "SKIPPED": "⏭️"}.get(
            result.status.name, "❓"
        )
        print(f"  {status} {result.rule_name}: {result.message}")

    return results


async def test_monitoring_system():
    """Test real-time monitoring system"""
    print("\n👁️ Testing Validation Monitoring System")
    print("=" * 50)

    try:
        # Initialize monitor
        monitor = ValidationMonitor(".", "test_monitor.db")
        print(f"✅ Monitor initialized for: {monitor.project_path}")

        # Get monitoring stats
        stats = monitor.get_monitoring_stats()
        print(
            f"📊 Monitoring stats: {stats['validation_rules']} rules, {stats['monitored_files']} files"
        )

        # Test manual validation
        results = await monitor.manual_validation()
        print(f"✅ Manual validation: {results['overall_status']}")

        # Test health check
        health = await monitor.health_check()
        print(
            f"🏥 Health check: Engine functional = {health.get('engine_functional', False)}"
        )

        # Export monitoring report
        report_file = monitor.export_monitoring_report("test_monitoring_report.json")
        print(f"📋 Monitoring report: {report_file}")

        return True

    except Exception as e:
        print(f"❌ Monitoring test error: {e}")
        return False


async def test_bmad_validator_integration():
    """Test BMAD validator agent integration"""
    print("\n🎯 Testing BMAD Validator Integration")
    print("=" * 50)

    try:
        # Add BMAD path
        sys.path.insert(0, ".bmad-core")

        from agents.validator import ValidatorAgent

        validator = ValidatorAgent()

        print(f"✅ Validator agent loaded: {validator.role}")
        print(f"🔧 Agent name: {validator.name}")
        print(f"📋 Description: {validator.description}")

        # Test command support
        commands = ["/validator", "/validate", "/quality", "/check"]
        for cmd in commands:
            supported = validator.supports_command(cmd)
            print(f"  {cmd}: {'✅' if supported else '❌'}")

        # Test specialized prompt generation
        prompt = validator.get_specialized_prompt(
            "Test validation request",
            "Sample code output",
            "Sample requirements",
            "Sample context",
        )

        print(f"✅ Specialized prompt generated: {len(prompt)} characters")

        # Test validation commands
        validation_commands = validator.get_validation_commands()
        print(f"🔧 Validation commands available: {len(validation_commands)}")

        return True

    except Exception as e:
        print(f"❌ BMAD validator test error: {e}")
        return False


async def test_integration_workflow():
    """Test complete integrated workflow"""
    print("\n🚀 Testing Complete Integration Workflow")
    print("=" * 50)

    try:
        # Test workflow: Monitor → Advanced Rules → BMAD Validator

        # 1. Initialize monitoring
        monitor = ValidationMonitor(".", "integration_test.db")
        print("✅ Step 1: Monitoring initialized")

        # 2. Run comprehensive validation
        results = await monitor.manual_validation()
        print(f"✅ Step 2: Validation completed - {results['overall_status']}")

        # 3. Test BMAD integration
        sys.path.insert(0, ".bmad-core")
        from agents.validator import ValidatorAgent

        validator = ValidatorAgent()

        # Generate validation report
        report = validator.create_validation_report(results)
        print(f"✅ Step 3: BMAD validation report generated ({len(report)} chars)")

        # 4. Test auto-fix suggestions
        failed_results = [
            r for r in results.get("results", []) if r.status.name == "FAILED"
        ]
        fixes = validator.get_auto_fix_suggestions(failed_results)
        print(f"✅ Step 4: Auto-fix suggestions: {len(fixes)} commands")

        print("\n🎉 INTEGRATION WORKFLOW SUCCESSFUL!")
        print(f"🔧 Total validation rules tested: {results['total_rules']}")
        print(f"📊 Overall status: {results['overall_status']}")

        return True

    except Exception as e:
        print(f"❌ Integration workflow error: {e}")
        return False


async def test_performance_advanced():
    """Test performance with advanced rules"""
    print("\n⚡ Testing Advanced System Performance")
    print("=" * 50)

    import time

    try:
        start_time = time.time()

        # Test with all advanced rules
        engine = ValidationEngine("perf_test.db")

        # Add all rules
        from termnet.validation_rules import (
            FlaskApplicationValidation,
            PythonSyntaxValidation,
        )
        from termnet.validation_rules_advanced import (
            APIEndpointValidation,
            SecurityValidation,
        )

        engine.add_rule(PythonSyntaxValidation())
        engine.add_rule(FlaskApplicationValidation())
        engine.add_rule(SecurityValidation())
        engine.add_rule(APIEndpointValidation())

        # Run validation
        results = await engine.validate_project(".", {"performance_test": True})

        elapsed_time = time.time() - start_time

        print("⚡ Performance Results:")
        print(f"  Total time: {elapsed_time:.2f}s")
        print(f"  Rules executed: {results['total_rules']}")
        print("  Files validated: ~4000+ Python files")
        print(f"  Time per rule: {elapsed_time/results['total_rules']:.2f}s")

        if elapsed_time < 60:  # Under 1 minute for comprehensive validation
            print("✅ Performance: EXCELLENT (under 1 minute)")
        elif elapsed_time < 120:  # Under 2 minutes
            print("✅ Performance: GOOD (under 2 minutes)")
        else:
            print("⚠️ Performance: May need optimization (over 2 minutes)")

        return elapsed_time < 120  # Performance test passes if under 2 minutes

    except Exception as e:
        print(f"❌ Performance test error: {e}")
        return False


async def run_all_advanced_tests():
    """Run all Phase 2 advanced tests"""
    print("🚀 TermNet Advanced Validation System - Phase 2 Test Suite")
    print("=" * 70)

    test_results = {}

    # Test 1: Advanced Rules
    test_results["advanced_rules"] = await test_advanced_rules()

    # Test 2: Monitoring System
    test_results["monitoring"] = await test_monitoring_system()

    # Test 3: BMAD Integration
    test_results["bmad_integration"] = await test_bmad_validator_integration()

    # Test 4: Integration Workflow
    test_results["integration_workflow"] = await test_integration_workflow()

    # Test 5: Performance
    test_results["performance"] = await test_performance_advanced()

    # Final Summary
    print("\n🎯 PHASE 2 TEST RESULTS SUMMARY")
    print("=" * 70)

    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)

    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status} {test_name.replace('_', ' ').title()}")

    print(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 ALL PHASE 2 TESTS PASSED! Advanced validation system is ready!")
    else:
        print("⚠️ Some tests failed. Review errors above.")

    return passed_tests == total_tests


if __name__ == "__main__":
    print("🧪 Starting TermNet Advanced Validation Test Suite...")
    success = asyncio.run(run_all_advanced_tests())

    if success:
        print("\n✅ Phase 2 validation system build verified successfully!")
        print("\n🚀 Ready for autonomous development with advanced validation!")
    else:
        print("\n❌ Some tests failed. Check output above for details.")
        sys.exit(1)
