#!/usr/bin/env python3
"""
Single step test for debugging streaming response
"""

import asyncio
import os
import sys

# Add the termnet directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "termnet"))


async def test_single_step():
    """Test just one step with debug output"""
    print("🧪 Testing Single Step")
    print("=" * 30)

    try:
        from termnet.agent import TermNetAgent
        from termnet.config import CONFIG
        from termnet.tools.terminal import TerminalSession

        # Limit max steps to 1 for debugging
        CONFIG["MAX_AI_STEPS"] = 1

        # Create terminal session
        terminal = TerminalSession()
        await terminal.start()

        # Create agent
        agent = TermNetAgent(terminal)

        print(f"Model: {CONFIG['MODEL_NAME']}")
        print("Testing single step...")
        print("-" * 30)

        # Test with simple request
        await agent.chat(
            "What is the current date? Use the terminal_execute tool to run 'date'."
        )

        await terminal.stop()

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_single_step())
