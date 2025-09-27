#!/usr/bin/env python3
"""Test script to verify BMAD ValidatorAgent import"""

import sys

# Add the BMAD core directory to the Python path
sys.path.insert(0, ".bmad-core")

try:
    # Import the ValidatorAgent
    from agents.validator import ValidatorAgent

    print("✅ BMAD ValidatorAgent imported successfully!")

    # Create an instance
    validator = ValidatorAgent()

    # Test basic functionality
    print(f"Agent Name: {validator.name}")
    print(f"Agent Role: {validator.role}")
    print(f"Description: {validator.description}")

    # Test command support
    test_commands = ["/validate", "/quality", "/check", "/test"]
    for cmd in test_commands:
        supported = validator.supports_command(cmd)
        status = "✅" if supported else "❌"
        print(f'{status} Supports "{cmd}": {supported}')

    # Get validation commands
    commands = validator.get_validation_commands()
    print(f"\n📋 Available validation commands: {len(commands)} commands")

    print("\n🎉 All ValidatorAgent tests passed!")

except ImportError as e:
    print(f"❌ Failed to import ValidatorAgent: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error during testing: {e}")
    sys.exit(1)
