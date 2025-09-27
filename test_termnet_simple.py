#!/usr/bin/env python3
"""
Simple test of TermNetAgent with terminal tool
"""

import asyncio
import sys

sys.path.insert(0, ".")

from termnet.agent import TermNetAgent
from termnet.tools.terminal import TerminalSession


async def main():
    print("🧪 Simple TermNet Agent Test")
    print("=" * 50)

    # Create terminal session
    terminal = TerminalSession()
    await terminal.start()

    # Create agent
    agent = TermNetAgent(terminal)

    # Check configuration
    print("✅ Agent initialized")
    print("✅ Terminal session ready")

    # Test 1: Direct terminal execution
    print("\n📝 Test 1: Direct Terminal Execution")
    print("-" * 40)
    result = await terminal.execute_command("echo 'Direct test'")
    print(f"Result: {result[0].strip()}")
    print(f"Exit code: {result[1]}")
    print(f"Success: {result[2]}")

    # Test 2: Agent with simple command
    print("\n📝 Test 2: Agent Tool Execution")
    print("-" * 40)
    print("Asking agent to run a command...")
    await agent.chat("Run the command: echo 'Hello from agent'")

    # Test 3: System info
    print("\n📝 Test 3: System Information")
    print("-" * 40)
    await agent.chat("Show the current date and time")

    # Clean up
    await terminal.stop()
    print("\n✅ Test completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
