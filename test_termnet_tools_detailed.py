#!/usr/bin/env python3
"""
Detailed test of TermNetAgent tool capabilities
Including GPT-OSS format testing
"""

import asyncio
import json
import sys

sys.path.insert(0, ".")

from termnet.agent import TermNetAgent
from termnet.config import CONFIG
from termnet.tools.terminal import TerminalSession


async def test_tool_execution():
    """Test various tool execution scenarios"""
    print("🧪 TermNet Agent Tool Execution Test")
    print("=" * 60)

    # Create terminal session
    terminal = TerminalSession()
    await terminal.start()

    # Create agent
    agent = TermNetAgent(terminal)

    # Display configuration
    print("📋 Configuration:")
    print(f"   Model: {CONFIG.get('MODEL_NAME', 'Not configured')}")
    print(f"   Using Claude Code: {bool(agent.claude_code_client)}")
    print(f"   GPT-OSS Model: {agent._is_gpt_oss_model()}")
    print()

    # Test 1: Basic tool call
    print("Test 1: Basic Tool Call")
    print("-" * 40)
    result = await agent._execute_tool(
        "terminal_execute",
        {"command": "echo 'Test 1 passed'"},
        "Testing basic tool execution",
    )
    print(f"Result: {result}")
    print()

    # Test 2: GPT-OSS format parsing
    print("Test 2: GPT-OSS Format Parsing")
    print("-" * 40)
    gpt_oss_text = '<|start|>assistant<|channel|>commentary to=terminal_execute <|constrain|>json<|message|>{"cmd":["pwd"]}<|call|>'

    if agent._has_gpt_oss_tool_call(gpt_oss_text):
        print("✅ GPT-OSS tool call detected")
        tool_calls = agent._parse_gpt_oss_tool_calls(gpt_oss_text)
        print(f"Parsed calls: {json.dumps(tool_calls, indent=2)}")

        if tool_calls:
            # Execute the parsed command
            call = tool_calls[0]
            result = await agent._execute_tool(
                call["name"], call["args"], "GPT-OSS parsed command"
            )
            print(f"Execution result: {result}")
    else:
        print("❌ GPT-OSS tool call not detected")
    print()

    # Test 3: Multiple format variations
    print("Test 3: GPT-OSS Format Variations")
    print("-" * 40)
    test_formats = [
        '<|channel|>commentary to=terminal_execute <|message|>{"cmd":["ls", "-la"]}<|call|>',
        'commentary to=functions.terminal_execute <|message|>{"cmd":["date"]}<|call|>',
        '<|start|>assistant<|channel|>commentary to=terminal_execute <|constrain|>json<|message|>{"cmd":["bash", "-lc", "whoami"]}<|call|>',
    ]

    for i, format_text in enumerate(test_formats, 1):
        print(f"\nVariation {i}:")
        if agent._has_gpt_oss_tool_call(format_text):
            calls = agent._parse_gpt_oss_tool_calls(format_text)
            if calls:
                print(f"✅ Parsed: {calls[0]['args']}")
            else:
                print("❌ Failed to parse")
        else:
            print("❌ Not recognized as tool call")
    print()

    # Test 4: Tool chaining
    print("Test 4: Tool Chaining")
    print("-" * 40)

    # Execute multiple tools in sequence
    commands = [
        ("echo 'Step 1'", "terminal_execute"),
        ("pwd", "terminal_execute"),
        ("echo 'Step 3'", "terminal_execute"),
    ]

    for cmd, tool in commands:
        result = await agent._execute_tool(
            tool, {"command": cmd}, f"Chained command: {cmd}"
        )
        print(f"   {cmd}: {result.strip()}")
    print()

    # Test 5: Error handling
    print("Test 5: Error Handling")
    print("-" * 40)

    # Test with invalid tool
    result = await agent._execute_tool("nonexistent_tool", {}, "Testing invalid tool")
    print(f"Invalid tool result: {result}")

    # Test with empty command
    result = await agent._execute_tool(
        "terminal_execute", {"command": ""}, "Testing empty command"
    )
    print(f"Empty command result: {result}")
    print()

    # Test 6: Tool definitions
    print("Test 6: Available Tools")
    print("-" * 40)
    tools = agent._get_tool_definitions()
    for tool in tools:
        name = tool.get("function", {}).get("name", "Unknown")
        params = tool.get("function", {}).get("parameters", {})
        required = params.get("required", [])
        print(f"   {name}: Required params: {required}")
    print()

    # Test 7: Conversation history tracking
    print("Test 7: Conversation History")
    print("-" * 40)
    print(f"History length: {len(agent.conversation_history)}")
    print(
        f"Last role: {agent.conversation_history[-1]['role'] if agent.conversation_history else 'None'}"
    )

    # Add a user message and check
    agent.conversation_history.append({"role": "user", "content": "test message"})
    print(f"After adding user message: {len(agent.conversation_history)} entries")
    print()

    # Test 8: Terminal session context
    print("Test 8: Terminal Session Context")
    print("-" * 40)
    context = terminal.get_context_info()
    for key, value in context.items():
        if not key.endswith("_stats"):
            print(f"   {key}: {value}")
    print()

    # Clean up
    await terminal.stop()
    print("✅ All tests completed!")


async def main():
    try:
        await test_tool_execution()
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
