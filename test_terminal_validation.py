#!/usr/bin/env python3

import asyncio
import sys

sys.path.insert(0, ".")

from termnet.tools.terminal import TerminalSession


async def main():
    # Create a terminal session
    t = TerminalSession()

    # Check if validation is enabled
    validation_status = t.validation_engine is not None
    print(f"✅ Terminal validation enabled: {validation_status}")

    # Show validation engine details if available
    if t.validation_engine:
        print("   - Validation engine initialized")
        print("   - Database: termnet_terminal_validation.db")
    else:
        print("   - Validation engine not available")

    # Test executing a safe command
    print("\n🔧 Testing command execution with validation:")
    result, exit_code, success = await t.execute_command(
        'echo "Hello from validated terminal"'
    )
    print(f"   Command output: {result.strip()}")
    print(f"   Exit code: {exit_code}")
    print(f"   Success: {success}")

    # Test pwd command
    result, _, _ = await t.execute_command("pwd")
    print(f"\n📁 Current directory: {result.strip()}")

    # Test ls command
    result, _, _ = await t.execute_command("ls -la | head -5")
    print("\n📋 Directory listing (first 5 items):")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
