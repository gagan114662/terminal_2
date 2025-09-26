#!/usr/bin/env python3
"""
Run TermNet with OpenRouter - Simple launcher
"""

import asyncio
import os
import sys

# Add the termnet directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "termnet"))


async def main():
    """Main TermNet launcher with OpenRouter"""
    print("🤖 TermNet with OpenRouter API")
    print("=" * 40)

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
        print("Type 'exit' to quit")
        print("-" * 40)

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if user_input.lower() in ["exit", "quit", "q"]:
                    print("Goodbye!")
                    break

                if not user_input:
                    continue

                print("\nTermNet: ", end="", flush=True)

                # Use chat without tools for now to avoid tool calling issues
                # We'll just test the basic OpenRouter integration
                await agent.chat(user_input)

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue

        await terminal.stop()

    except Exception as e:
        print(f"❌ Failed to start TermNet: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
