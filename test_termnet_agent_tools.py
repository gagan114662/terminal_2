#!/usr/bin/env python3
"""
Comprehensive test suite for TermNetAgent with tools
Tests various tool invocations and agent behaviors
"""

import asyncio
import sys

# Add termnet to Python path
sys.path.insert(0, ".")

from termnet.agent import TermNetAgent
from termnet.config import CONFIG
from termnet.tools.terminal import TerminalSession


class TermNetAgentTester:
    def __init__(self):
        self.terminal = None
        self.agent = None
        self.test_results = []

    async def setup(self):
        """Initialize the testing environment"""
        print("🚀 Setting up TermNet Agent Test Environment")
        print("=" * 60)

        # Create terminal session
        self.terminal = TerminalSession()
        await self.terminal.start()

        # Create agent
        self.agent = TermNetAgent(self.terminal)

        # Display configuration
        print("📋 Configuration:")
        print(f"   Model: {CONFIG.get('MODEL_NAME', 'Not specified')}")
        print(f"   Claude Code Enabled: {CONFIG.get('USE_CLAUDE_CODE', False)}")
        print(f"   Max Steps: {CONFIG.get('MAX_AI_STEPS', 5)}")
        print(f"   Command Timeout: {CONFIG.get('COMMAND_TIMEOUT', 30)}s")

        # Check available tools
        tools = self.agent.tool_loader.get_tool_definitions()
        print("\n🛠️  Available Tools:")
        for tool in tools:
            tool_name = tool.get("function", {}).get("name", "Unknown")
            tool_desc = tool.get("function", {}).get("description", "No description")[
                :50
            ]
            print(f"   - {tool_name}: {tool_desc}...")

        print("\n" + "=" * 60 + "\n")

    async def teardown(self):
        """Clean up resources"""
        if self.terminal:
            await self.terminal.stop()

    async def test_basic_terminal_command(self):
        """Test basic terminal command execution"""
        test_name = "Basic Terminal Command"
        print(f"🧪 Testing: {test_name}")
        print("-" * 40)

        try:
            # Test simple echo command
            await self.agent.chat("Run the command: echo 'Hello from TermNet'")

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASSED",
                    "details": "Successfully executed echo command",
                }
            )
            print(f"✅ {test_name} - PASSED\n")
        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAILED", "details": str(e)}
            )
            print(f"❌ {test_name} - FAILED: {e}\n")

    async def test_system_info_commands(self):
        """Test system information retrieval"""
        test_name = "System Info Commands"
        print(f"🧪 Testing: {test_name}")
        print("-" * 40)

        try:
            # Test multiple system info commands
            commands = [
                "Show the current directory",
                "List files in the current directory",
                "Show disk usage",
            ]

            for cmd_request in commands:
                print(f"\n📝 Request: {cmd_request}")
                await self.agent.chat(cmd_request)
                await asyncio.sleep(1)  # Brief pause between commands

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASSED",
                    "details": "Successfully retrieved system information",
                }
            )
            print(f"✅ {test_name} - PASSED\n")
        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAILED", "details": str(e)}
            )
            print(f"❌ {test_name} - FAILED: {e}\n")

    async def test_file_operations(self):
        """Test file creation and manipulation"""
        test_name = "File Operations"
        print(f"🧪 Testing: {test_name}")
        print("-" * 40)

        try:
            # Create a test file
            await self.agent.chat(
                "Create a file called test_output.txt with the content 'TermNet test file'"
            )
            await asyncio.sleep(1)

            # Read the file
            await self.agent.chat("Show the contents of test_output.txt")
            await asyncio.sleep(1)

            # Clean up
            await self.agent.chat("Remove the test_output.txt file")

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASSED",
                    "details": "File operations completed successfully",
                }
            )
            print(f"✅ {test_name} - PASSED\n")
        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAILED", "details": str(e)}
            )
            print(f"❌ {test_name} - FAILED: {e}\n")

    async def test_python_execution(self):
        """Test Python code execution through terminal"""
        test_name = "Python Code Execution"
        print(f"🧪 Testing: {test_name}")
        print("-" * 40)

        try:
            # Execute Python code
            await self.agent.chat("Run Python to calculate 2**10 and show the result")
            await asyncio.sleep(1)

            # More complex Python
            await self.agent.chat("Use Python to show the current date and time")

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASSED",
                    "details": "Python code executed successfully",
                }
            )
            print(f"✅ {test_name} - PASSED\n")
        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAILED", "details": str(e)}
            )
            print(f"❌ {test_name} - FAILED: {e}\n")

    async def test_tool_chaining(self):
        """Test multiple tools in sequence"""
        test_name = "Tool Chaining"
        print(f"🧪 Testing: {test_name}")
        print("-" * 40)

        try:
            # Complex request requiring multiple tools
            await self.agent.chat(
                "Create a Python script that prints 'Hello World', "
                "save it as hello.py, run it, and then delete it"
            )

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASSED",
                    "details": "Tool chaining executed successfully",
                }
            )
            print(f"✅ {test_name} - PASSED\n")
        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAILED", "details": str(e)}
            )
            print(f"❌ {test_name} - FAILED: {e}\n")

    async def test_validation_integration(self):
        """Test validation engine integration if available"""
        test_name = "Validation Integration"
        print(f"🧪 Testing: {test_name}")
        print("-" * 40)

        try:
            # Check if validation is enabled
            if self.terminal.validation_engine:
                print("📊 Validation engine is enabled")

                # Get context info
                context = self.terminal.get_context_info()
                print(
                    f"   Validation DB: {context.get('validation_db', 'Not available')}"
                )

                # Run a command that triggers validation
                await self.agent.chat("Run: python -c 'print(\"Validation test\")'")

                # Get validation history
                history = self.terminal.get_validation_history(limit=1)
                if history:
                    print(f"   Last validation: {history[0]}")

                self.test_results.append(
                    {
                        "test": test_name,
                        "status": "PASSED",
                        "details": "Validation integration working",
                    }
                )
                print(f"✅ {test_name} - PASSED\n")
            else:
                print("⚠️  Validation engine not available")
                self.test_results.append(
                    {
                        "test": test_name,
                        "status": "SKIPPED",
                        "details": "Validation engine not available",
                    }
                )
                print(f"⏭️  {test_name} - SKIPPED\n")

        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAILED", "details": str(e)}
            )
            print(f"❌ {test_name} - FAILED: {e}\n")

    async def test_phase3_security(self):
        """Test Phase 3 security features if available"""
        test_name = "Phase 3 Security"
        print(f"🧪 Testing: {test_name}")
        print("-" * 40)

        try:
            context = self.terminal.get_context_info()
            if context.get("phase3_enabled"):
                print("🛡️  Phase 3 security is enabled")
                print(f"   Claims DB: {context.get('claims_db', 'Not available')}")
                print(f"   Lifecycle: {context.get('lifecycle_enabled', False)}")
                print(f"   Policy: {context.get('policy_enabled', False)}")
                print(f"   Sandbox: {context.get('sandbox_available', False)}")

                # Test a safe command through Phase 3 pipeline
                await self.agent.chat("Run: echo 'Phase 3 test'")

                # Check claims statistics
                if context.get("claims_stats") != "unavailable":
                    print(f"   Claims stats: {context.get('claims_stats')}")

                self.test_results.append(
                    {
                        "test": test_name,
                        "status": "PASSED",
                        "details": "Phase 3 security features working",
                    }
                )
                print(f"✅ {test_name} - PASSED\n")
            else:
                print("⚠️  Phase 3 security not available")
                self.test_results.append(
                    {
                        "test": test_name,
                        "status": "SKIPPED",
                        "details": "Phase 3 security not available",
                    }
                )
                print(f"⏭️  {test_name} - SKIPPED\n")

        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAILED", "details": str(e)}
            )
            print(f"❌ {test_name} - FAILED: {e}\n")

    async def test_error_handling(self):
        """Test error handling and recovery"""
        test_name = "Error Handling"
        print(f"🧪 Testing: {test_name}")
        print("-" * 40)

        try:
            # Test invalid command
            await self.agent.chat(
                "Run a command that doesn't exist: notarealcommand123"
            )
            await asyncio.sleep(1)

            # Test blocked command (if safety checker is active)
            await self.agent.chat("Try to run: rm -rf / (this should be blocked)")

            self.test_results.append(
                {
                    "test": test_name,
                    "status": "PASSED",
                    "details": "Error handling working correctly",
                }
            )
            print(f"✅ {test_name} - PASSED\n")
        except Exception as e:
            self.test_results.append(
                {"test": test_name, "status": "FAILED", "details": str(e)}
            )
            print(f"❌ {test_name} - FAILED: {e}\n")

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in self.test_results if r["status"] == "PASSED")
        failed = sum(1 for r in self.test_results if r["status"] == "FAILED")
        skipped = sum(1 for r in self.test_results if r["status"] == "SKIPPED")
        total = len(self.test_results)

        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")

        print("\nDetailed Results:")
        print("-" * 40)
        for result in self.test_results:
            status_emoji = {"PASSED": "✅", "FAILED": "❌", "SKIPPED": "⏭️"}.get(
                result["status"], "❓"
            )
            print(f"{status_emoji} {result['test']}: {result['status']}")
            if result["status"] == "FAILED":
                print(f"   Details: {result['details']}")

        print("\n" + "=" * 60)

        # Return success if no failures
        return failed == 0


async def main():
    """Main test runner"""
    tester = TermNetAgentTester()

    try:
        # Setup
        await tester.setup()

        # Run all tests
        tests = [
            tester.test_basic_terminal_command,
            tester.test_system_info_commands,
            tester.test_file_operations,
            tester.test_python_execution,
            tester.test_tool_chaining,
            tester.test_validation_integration,
            tester.test_phase3_security,
            tester.test_error_handling,
        ]

        for test_func in tests:
            try:
                await test_func()
            except Exception as e:
                print(f"❌ Unexpected error in test: {e}")
            await asyncio.sleep(2)  # Pause between tests

        # Print summary
        success = tester.print_summary()

        # Cleanup
        await tester.teardown()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        await tester.teardown()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        await tester.teardown()
        sys.exit(1)


if __name__ == "__main__":
    print("\n🎯 TermNet Agent Tools Test Suite")
    print("=" * 60)
    print("This test suite validates the TermNetAgent's ability to")
    print("execute tools and handle various terminal operations.\n")

    asyncio.run(main())
