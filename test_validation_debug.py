#!/usr/bin/env python3
import asyncio
import sys

sys.path.insert(0, "termnet")

print("Starting test...")

from termnet.validation_engine import ValidationEngine

print("Imported ValidationEngine")


async def main():
    print("Creating engine...")
    engine = ValidationEngine("test_validation_debug.db")
    print("Engine created")
    return engine


print("Running async...")
asyncio.run(main())
print("Done")
