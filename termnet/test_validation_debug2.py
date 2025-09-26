#!/usr/bin/env python3
import asyncio
import sys

sys.path.insert(0, "termnet")

from termnet.validation_engine import ValidationEngine
from termnet.validation_rules import PythonSyntaxValidation


async def main():
    print("Creating engine...")
    engine = ValidationEngine("test_validation_debug.db")

    print("Adding PythonSyntaxValidation rule...")
    engine.add_rule(PythonSyntaxValidation())

    print("Running validation on current directory...")
    results = await engine.validate_project(".", {"test_mode": True})

    print(f"Results: {results['overall_status']}")
    return results


print("Starting...")
asyncio.run(main())
print("Done")
