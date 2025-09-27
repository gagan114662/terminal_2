#!/usr/bin/env python3
"""
Test script for TermNet with OpenRouter integration
"""

import asyncio
import os
import sys

# Add the termnet directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "termnet"))


async def test_openrouter():
    """Test OpenRouter integration"""
    print("🧪 Testing TermNet with OpenRouter API")
    print("=" * 50)

    try:
        from termnet.config import CONFIG
        from termnet.openrouter_client import OpenRouterClient

        # Test OpenRouter client
        client = OpenRouterClient(CONFIG["OPENROUTER_API_KEY"])

        print("✅ OpenRouter client created successfully")

        # Test a simple chat
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": "Say 'Hello from TermNet with OpenRouter!' and confirm you're working.",
            },
        ]

        print("\n📤 Sending test message...")
        response_text = ""

        async for tag, chunk in client.chat_stream(
            model=CONFIG["MODEL_NAME"], messages=messages, temperature=0.7
        ):
            if tag == "CONTENT":
                print(chunk, end="", flush=True)
                response_text += chunk
            elif tag == "TOOL":
                print(f"\n🔧 Tool call: {chunk}")

        print("\n\n✅ Test completed successfully!")
        print(f"📋 Response length: {len(response_text)} characters")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_full_termnet():
    """Test full TermNet agent"""
    print("\n🤖 Testing full TermNet agent")
    print("=" * 50)

    try:
        from termnet.agent import TermNetAgent
        from termnet.tools.terminal import TerminalSession

        # Create a terminal session
        terminal = TerminalSession()

        # Create agent
        agent = TermNetAgent(terminal)

        print("✅ TermNet agent created successfully")

        # Test a simple interaction
        print("\n📤 Testing agent with: 'What is the current date?'")
        await agent.chat(
            "What is the current date and confirm you're working with OpenRouter?"
        )

        print("\n✅ TermNet agent test completed!")
        return True

    except Exception as e:
        print(f"❌ TermNet agent test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("🚀 TermNet OpenRouter Integration Test")
    print("=" * 60)

    # Test 1: OpenRouter client
    client_ok = await test_openrouter()

    if client_ok:
        # Test 2: Full TermNet
        agent_ok = await test_full_termnet()

        if agent_ok:
            print("\n🎉 ALL TESTS PASSED! TermNet is ready with OpenRouter!")
        else:
            print("\n⚠️  OpenRouter client works, but TermNet agent has issues")
    else:
        print("\n❌ OpenRouter client test failed")


if __name__ == "__main__":
    asyncio.run(main())
