#!/usr/bin/env python3
"""
Comprehensive verification script for all TermNet fixes
"""

import asyncio
import os
import sys

# Add TermNet to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def verify_all_fixes():
    """Run comprehensive verification of all fixes"""

    print("=" * 60)
    print("TERMNET COMPREHENSIVE FIX VERIFICATION")
    print("=" * 60)

    results = []

    # 1. Test imports
    print("\n1. Testing all imports...")
    try:
        from termnet.agent import TermNetAgent
        from termnet.safety import SafetyChecker
        from termnet.toolloader import ToolLoader
        from termnet.tools.browsersearch import BrowserSearchTool
        from termnet.tools.scratchpad import ScratchpadTool
        from termnet.tools.terminal import TerminalSession, TerminalTool
        from termnet.trajectory_evaluator import (
            Step,
            StepPhase,
            TrajectoryEvaluator,
            TrajectoryStatus,
        )
        from termnet.trend_analysis import TrendAnalyzer

        print("   ✅ All imports successful")
        results.append(("Imports", True))
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        results.append(("Imports", False))

    # 2. Test Agent async contract
    print("\n2. Testing Agent async contract...")
    try:
        terminal = TerminalSession()
        agent = TermNetAgent(terminal)

        # Test async methods
        start_result = await agent.start()
        await agent.stop()

        # Test attributes
        assert hasattr(agent, "async_supported"), "Missing async_supported attribute"
        assert agent.async_supported == True, "async_supported should be True"
        assert hasattr(
            agent, "_tool_execution_history"
        ), "Missing _tool_execution_history"
        assert hasattr(
            agent, "get_tool_execution_history"
        ), "Missing get_tool_execution_history method"
        assert hasattr(
            agent, "clear_tool_execution_history"
        ), "Missing clear_tool_execution_history method"
        assert hasattr(agent, "_current_turn_tools"), "Missing deduplication tracking"

        print("   ✅ Agent async contract working")
        results.append(("Agent async", True))
    except Exception as e:
        print(f"   ❌ Agent error: {e}")
        results.append(("Agent async", False))

    # 3. Test SafetyChecker API
    print("\n3. Testing SafetyChecker API...")
    try:
        sc = SafetyChecker()

        # Test new methods
        safe_cmd = sc.is_safe_command("ls -la")
        assert safe_cmd[0] == True, "Safe command should pass"

        dangerous_cmd = sc.is_safe_command("rm -rf /")
        assert dangerous_cmd[0] == False, "Dangerous command should fail"
        assert "dangerous" in dangerous_cmd[1].lower(), "Should mention 'dangerous'"

        path_check = sc.check_file_path("/etc/passwd")
        assert path_check[0] == False, "System path should be restricted"

        url_check = sc.is_safe_url("https://example.com")
        assert url_check[0] == True, "Valid URL should pass"

        # Test attributes
        assert hasattr(sc, "dangerous_patterns"), "Missing dangerous_patterns attribute"
        assert hasattr(sc, "allowed_commands"), "Missing allowed_commands attribute"

        print("   ✅ SafetyChecker API complete")
        results.append(("SafetyChecker", True))
    except Exception as e:
        print(f"   ❌ SafetyChecker error: {e}")
        results.append(("SafetyChecker", False))

    # 4. Test ToolLoader API
    print("\n4. Testing ToolLoader API...")
    try:
        tl = ToolLoader()
        tl.load_tools()

        # Test attributes
        assert hasattr(tl, "loaded_tools"), "Missing loaded_tools attribute"
        assert hasattr(tl, "tool_instances"), "Missing tool_instances attribute"
        assert (
            len(tl.loaded_tools) >= 2
        ), f"Should load at least 2 tools, got {len(tl.loaded_tools)}"

        # Test tool definitions filtering
        defs = tl.get_tool_definitions()
        for d in defs:
            assert (
                "type" in d and d["type"] == "function"
            ), "Should only return function types"
            assert "enabled" not in d, "Should not include 'enabled' field in output"

        print(f"   ✅ ToolLoader API complete (loaded {len(tl.loaded_tools)} tools)")
        results.append(("ToolLoader", True))
    except Exception as e:
        print(f"   ❌ ToolLoader error: {e}")
        results.append(("ToolLoader", False))

    # 5. Test Tool contracts
    print("\n5. Testing Tool contracts...")
    try:
        # Terminal Tool
        tt = TerminalTool()
        assert hasattr(tt, "set_offline_mode"), "TerminalTool missing set_offline_mode"
        assert hasattr(tt, "get_definition"), "TerminalTool missing get_definition"
        tt.set_offline_mode()
        result = tt.run("echo test")
        assert (
            "stdout" in result and "stderr" in result and "exit_code" in result
        ), "Invalid terminal result format"

        # Browser Tool
        bs = BrowserSearchTool()
        assert hasattr(
            bs, "set_offline_mode"
        ), "BrowserSearchTool missing set_offline_mode"
        assert hasattr(bs, "get_definition"), "BrowserSearchTool missing get_definition"
        bs.set_offline_mode()
        search_result = bs.search_sync("test")
        assert isinstance(search_result, list), "Browser search should return list"

        # Scratchpad Tool
        st = ScratchpadTool()
        assert hasattr(st, "write"), "ScratchpadTool missing write method"
        assert hasattr(st, "append"), "ScratchpadTool missing append method"
        assert hasattr(st, "delete"), "ScratchpadTool missing delete method"
        assert hasattr(st, "clear"), "ScratchpadTool missing clear method"
        assert hasattr(st, "search"), "ScratchpadTool missing search method"
        write_result = st.write("test", "content")
        assert "test" in write_result, "Write result should mention key"

        print("   ✅ Tool contracts complete")
        results.append(("Tool contracts", True))
    except Exception as e:
        print(f"   ❌ Tool contract error: {e}")
        results.append(("Tool contracts", False))

    # 6. Test Telemetry
    print("\n6. Testing Telemetry system...")
    try:
        import time
        from datetime import datetime

        ev = TrajectoryEvaluator(":memory:")  # Use in-memory DB for test
        rid = f"verify-{int(time.time())}"

        ev.start_trajectory(rid, ["verification"])
        ev.record_step(rid, Step(0, StepPhase.THINK, datetime.now().isoformat(), 50))
        ev.finish_trajectory(rid, TrajectoryStatus.COMPLETED)

        # Test TrendAnalyzer
        ta = TrendAnalyzer()
        ta.collect_request_metrics(1, 1.0, 50, rid)

        print("   ✅ Telemetry system working")
        results.append(("Telemetry", True))
    except Exception as e:
        print(f"   ❌ Telemetry error: {e}")
        results.append(("Telemetry", False))

    # Final summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name:20s}: {status}")

    total = len(results)
    passed = sum(1 for _, p in results if p)

    print("\n" + "-" * 60)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎯 ALL FIXES VERIFIED SUCCESSFULLY!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    # Run in virtual environment context
    venv_python = ".venv/bin/python3"
    if os.path.exists(venv_python) and sys.executable != os.path.abspath(venv_python):
        # Re-run with venv Python
        import subprocess

        result = subprocess.run([venv_python, __file__], capture_output=False)
        sys.exit(result.returncode)

    # Run verification
    exit_code = asyncio.run(verify_all_fixes())
    sys.exit(exit_code)
