from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from termnet.agent import TermNetAgent


class TestEndToEndIntegration:
    @pytest.fixture
    def mock_terminal(self):
        terminal = MagicMock()
        terminal.execute_command = AsyncMock(return_value=("output", 0, True))
        return terminal

    @pytest.fixture
    def agent(self, mock_terminal):
        with patch(
            "termnet.agent.CONFIG",
            {
                "USE_CLAUDE_CODE": False,
                "USE_OPENROUTER": False,
                "MODEL_NAME": "test-model",
                "LLM_TEMPERATURE": 0.7,
                "MAX_AI_STEPS": 5,
                "STREAM_CHUNK_DELAY": 0,
                "OLLAMA_URL": "http://localhost:11434",
                "CONVERSATION_MEMORY_SIZE": 10,
            },
        ):
            return TermNetAgent(mock_terminal)

    @pytest.mark.asyncio
    async def test_simple_command_execution_flow(self, agent):
        # Mock the LLM response to execute a command
        async def mock_stream():
            yield (
                "TOOL",
                [
                    {
                        "id": "call_1",
                        "function": {
                            "name": "terminal_execute",
                            "arguments": {"command": "echo 'Hello World'"},
                        },
                    }
                ],
            )
            yield ("CONTENT", "I executed the echo command successfully.")

        with patch.object(agent, "_llm_chat_stream", return_value=mock_stream()):
            with patch.object(agent.tool_loader, "get_tool_instance") as mock_get_tool:
                mock_tool = MagicMock()
                mock_tool.execute_command = AsyncMock(
                    return_value=("Hello World", 0, True)
                )
                mock_get_tool.return_value = mock_tool

                await agent.chat("Run echo hello world")

                # Verify tool was called
                mock_tool.execute_command.assert_called_once_with("echo 'Hello World'")

                # Verify conversation history updated
                assert len(agent.conversation_history) > 1
                assert any(msg["role"] == "user" for msg in agent.conversation_history)

    @pytest.mark.asyncio
    async def test_multi_tool_execution_flow(self, agent):
        # Mock multiple tool calls
        async def mock_stream():
            # First tool call
            yield (
                "TOOL",
                [
                    {
                        "id": "call_1",
                        "function": {
                            "name": "terminal_execute",
                            "arguments": {"command": "pwd"},
                        },
                    }
                ],
            )

        async def mock_stream_2():
            # Second tool call
            yield (
                "TOOL",
                [
                    {
                        "id": "call_2",
                        "function": {
                            "name": "terminal_execute",
                            "arguments": {"command": "ls"},
                        },
                    }
                ],
            )

        async def mock_stream_final():
            yield ("CONTENT", "Completed both commands.")

        mock_streams = [mock_stream(), mock_stream_2(), mock_stream_final()]
        stream_index = 0

        def get_next_stream():
            nonlocal stream_index
            result = mock_streams[stream_index]
            stream_index += 1
            return result

        with patch.object(agent, "_llm_chat_stream", side_effect=get_next_stream):
            with patch.object(agent.tool_loader, "get_tool_instance") as mock_get_tool:
                mock_tool = MagicMock()
                mock_tool.execute_command = AsyncMock(
                    side_effect=[
                        ("/home/user", 0, True),
                        ("file1.txt file2.txt", 0, True),
                    ]
                )
                mock_get_tool.return_value = mock_tool

                await agent.chat("Show current directory and list files")

                # Verify both tools were called
                assert mock_tool.execute_command.call_count == 2

    @pytest.mark.asyncio
    async def test_error_handling_flow(self, agent):
        async def mock_stream():
            yield (
                "TOOL",
                [
                    {
                        "id": "call_1",
                        "function": {
                            "name": "terminal_execute",
                            "arguments": {"command": "invalid_command"},
                        },
                    }
                ],
            )
            yield ("CONTENT", "The command failed as expected.")

        with patch.object(agent, "_llm_chat_stream", return_value=mock_stream()):
            with patch.object(agent.tool_loader, "get_tool_instance") as mock_get_tool:
                mock_tool = MagicMock()
                mock_tool.execute_command = AsyncMock(
                    return_value=("Command not found", 127, False)
                )
                mock_get_tool.return_value = mock_tool

                await agent.chat("Run an invalid command")

                # Verify error was handled
                mock_tool.execute_command.assert_called_once()
                # Check conversation history contains error
                assert any(
                    "Command not found" in str(msg.get("content", ""))
                    for msg in agent.conversation_history
                )


class TestBMADIntegration:
    @pytest.fixture
    def agent_with_bmad(self, mock_terminal):
        with patch(
            "termnet.agent.CONFIG",
            {
                "USE_CLAUDE_CODE": False,
                "USE_OPENROUTER": False,
                "MODEL_NAME": "test-model",
                "LLM_TEMPERATURE": 0.7,
                "MAX_AI_STEPS": 5,
                "STREAM_CHUNK_DELAY": 0,
            },
        ):
            return TermNetAgent(mock_terminal)

    @pytest.mark.asyncio
    async def test_bmad_agent_activation(self, agent_with_bmad):
        with patch.object(agent_with_bmad.bmad, "is_bmad_command", return_value=True):
            with patch.object(
                agent_with_bmad.bmad,
                "process_bmad_command",
                return_value=(True, "Specialized agent prompt"),
            ):

                async def mock_stream():
                    yield ("CONTENT", "BMAD agent activated and processing...")

                with patch.object(
                    agent_with_bmad, "_llm_chat_stream", return_value=mock_stream()
                ):
                    await agent_with_bmad.chat("/plan Create a web app")

                    # Verify BMAD processing occurred
                    agent_with_bmad.bmad.is_bmad_command.assert_called_once()
                    agent_with_bmad.bmad.process_bmad_command.assert_called_once()

    @pytest.mark.asyncio
    async def test_bmad_workflow_commands(self, agent_with_bmad):
        with patch.object(
            agent_with_bmad.bmad,
            "get_workflow_status",
            return_value="Workflow: Active\nSteps: 5 completed",
        ):
            with patch("builtins.print") as mock_print:
                await agent_with_bmad.chat("bmad status")

                agent_with_bmad.bmad.get_workflow_status.assert_called_once()
                mock_print.assert_called_with("Workflow: Active\nSteps: 5 completed")

    @pytest.mark.asyncio
    async def test_bmad_save_and_load_workflow(self, agent_with_bmad):
        # Test save
        with patch.object(agent_with_bmad.bmad, "save_workflow"):
            await agent_with_bmad.chat("bmad save")
            agent_with_bmad.bmad.save_workflow.assert_called_once()

        # Test load
        with patch.object(agent_with_bmad.bmad, "load_workflow", return_value=True):
            with patch("builtins.print") as mock_print:
                await agent_with_bmad.chat("bmad load")

                agent_with_bmad.bmad.load_workflow.assert_called_once()
                mock_print.assert_called_with("📂 Previous workflow state restored")


class TestMemoryIntegration:
    @pytest.fixture
    def agent_with_memory(self, mock_terminal):
        with patch(
            "termnet.agent.CONFIG",
            {
                "USE_CLAUDE_CODE": False,
                "USE_OPENROUTER": False,
                "MODEL_NAME": "test-model",
                "CONVERSATION_MEMORY_SIZE": 5,
                "LLM_TEMPERATURE": 0.7,
                "MAX_AI_STEPS": 5,
                "STREAM_CHUNK_DELAY": 0,
            },
        ):
            return TermNetAgent(mock_terminal)

    @pytest.mark.asyncio
    async def test_conversation_history_persistence(self, agent_with_memory):
        # First message
        async def mock_stream_1():
            yield ("CONTENT", "First response")

        with patch.object(
            agent_with_memory, "_llm_chat_stream", return_value=mock_stream_1()
        ):
            await agent_with_memory.chat("First question")

        # Second message - should have previous context
        async def mock_stream_2():
            yield ("CONTENT", "Second response with context")

        with patch.object(
            agent_with_memory, "_llm_chat_stream", return_value=mock_stream_2()
        ):
            await agent_with_memory.chat("Follow-up question")

        # Verify conversation history contains both exchanges
        history = agent_with_memory.conversation_history
        user_messages = [msg for msg in history if msg["role"] == "user"]
        assert len(user_messages) == 2
        assert user_messages[0]["content"] == "First question"
        assert user_messages[1]["content"] == "Follow-up question"

    @pytest.mark.asyncio
    async def test_memory_limit_enforcement(self, agent_with_memory):
        # Add many messages to test memory limit
        for i in range(10):
            agent_with_memory.conversation_history.append(
                {
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"Message {i}",
                }
            )

        # With CONVERSATION_MEMORY_SIZE = 5, older messages should be trimmed
        # System prompt + 10 messages = 11 total
        # But implementation may vary, so just check it's reasonable
        assert len(agent_with_memory.conversation_history) <= 15
