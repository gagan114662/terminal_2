#!/usr/bin/env python3
"""
Direct test of tool calling with proper command argument
"""

import asyncio
import os
import sys

# Add the termnet directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "termnet"))


async def test_direct_tool_call():
    """Test direct tool calling with GPT-OSS"""
    print("🧪 Testing Direct Tool Call with GPT-OSS")
    print("=" * 50)

    try:
        from termnet.agent import TermNetAgent
        from termnet.config import CONFIG
        from termnet.tools.terminal import TerminalSession

        # Create terminal session
        terminal = TerminalSession()
        await terminal.start()

        # Create agent
        agent = TermNetAgent(terminal)

        print(f"Model: {CONFIG['MODEL_NAME']}")
        print("Testing with explicit tool request...")
        print("-" * 50)

        # Test with explicit command request
        await agent.chat(
            "Please use the terminal_execute tool to run the command 'date' and tell me what the current date is."
        )

        await terminal.stop()

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_direct_tool_call())
