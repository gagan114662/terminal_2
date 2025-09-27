#!/usr/bin/env python3
"""Run validation engine on the current project"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from termnet.validation_engine import ValidationEngine
from termnet.validation_rules import (
    ApplicationStartupValidation,
    DatabaseValidation,
    FlaskApplicationValidation,
    PythonSyntaxValidation,
    RequirementsValidation,
)


async def main():
    # Create validation engine instance
    engine = ValidationEngine()

    # Add validation rules
    engine.add_rule(PythonSyntaxValidation())
    engine.add_rule(RequirementsValidation())
    engine.add_rule(ApplicationStartupValidation())
    engine.add_rule(FlaskApplicationValidation())
    engine.add_rule(DatabaseValidation())

    # Run validation on current directory with test context
    results = await engine.validate_project(".", {"test": True})

    # Print results
    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    print(f"Overall Status: {results['overall_status']}")
    print(f"Total Rules: {results['total_rules']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Errors: {results['errors']}")

    return results


if __name__ == "__main__":
    results = asyncio.run(main())
    # Exit with non-zero code if validation failed
    sys.exit(0 if results["overall_status"] == "PASSED" else 1)
