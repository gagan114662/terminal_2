import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from termnet.agent import TermNetAgent


class TestTermNetAgent:
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
            },
        ):
            return TermNetAgent(mock_terminal)

    def test_agent_initialization(self, agent, mock_terminal):
        assert agent.terminal == mock_terminal
        assert agent.session_id is not None
        assert len(agent.session_id) == 8
        assert agent.current_goal == ""
        assert agent.cache == {}
        assert agent.tool_loader is not None
        assert agent.bmad is not None

    def test_conversation_history_initialization(self, agent):
        assert len(agent.conversation_history) == 1
        assert agent.conversation_history[0]["role"] == "system"
        assert "TermNet" in agent.conversation_history[0]["content"]

    def test_get_tool_definitions(self, agent):
        with patch.object(agent.tool_loader, "get_tool_definitions") as mock_get_tools:
            mock_get_tools.return_value = [
                {"function": {"name": "terminal_execute"}},
                {"function": {"name": "browser_search"}},
            ]
            tools = agent._get_tool_definitions()
            assert len(tools) == 2
            assert tools[0]["function"]["name"] == "terminal_execute"

    @pytest.mark.asyncio
    async def test_execute_tool_terminal(self, agent):
        with patch.object(agent.tool_loader, "get_tool_instance") as mock_get_tool:
            mock_tool = MagicMock()
            mock_tool.execute_command = AsyncMock(return_value=("ls output", 0, True))
            mock_get_tool.return_value = mock_tool

            result = await agent._execute_tool(
                "terminal_execute", {"command": "ls"}, "listing files"
            )
            assert "ls output" in result
            mock_tool.execute_command.assert_called_once_with("ls")

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self, agent):
        with patch.object(agent.tool_loader, "get_tool_instance") as mock_get_tool:
            mock_get_tool.return_value = None

            result = await agent._execute_tool("non_existent_tool", {}, "test")
            assert "Tool non_existent_tool not found" in result

    @pytest.mark.asyncio
    async def test_execute_tool_error_handling(self, agent):
        with patch.object(agent.tool_loader, "get_tool_instance") as mock_get_tool:
            mock_tool = MagicMock()
            mock_tool.execute_command = AsyncMock(side_effect=Exception("Test error"))
            mock_get_tool.return_value = mock_tool

            result = await agent._execute_tool(
                "terminal_execute", {"command": "test"}, "test"
            )
            assert "Tool execution error" in result
            assert "Test error" in result

    def test_bmad_command_detection(self, agent):
        with patch.object(agent.bmad, "is_bmad_command") as mock_is_bmad:
            mock_is_bmad.return_value = True
            assert agent.bmad.is_bmad_command("/plan test") is True

            mock_is_bmad.return_value = False
            assert agent.bmad.is_bmad_command("regular text") is False

    @pytest.mark.asyncio
    async def test_chat_with_bmad_command(self, agent):
        with patch.object(agent.bmad, "is_bmad_command", return_value=True):
            with patch.object(
                agent.bmad,
                "process_bmad_command",
                return_value=(True, "specialized prompt"),
            ):
                with patch.object(agent, "_llm_chat_stream", return_value=AsyncMock()):
                    # Mock the async generator
                    async def mock_stream():
                        yield ("CONTENT", "Response")

                    agent._llm_chat_stream = AsyncMock(return_value=mock_stream())
                    await agent.chat("/plan test")

                    # Check that the conversation history has the specialized prompt
                    assert any(
                        "specialized prompt" in msg.get("content", "")
                        for msg in agent.conversation_history
                        if msg["role"] == "user"
                    )

    @pytest.mark.asyncio
    async def test_handle_bmad_workflow_status(self, agent):
        with patch.object(
            agent.bmad, "get_workflow_status", return_value="Workflow status"
        ):
            with patch("builtins.print") as mock_print:
                await agent._handle_bmad_workflow_command("bmad status")
                mock_print.assert_called_with("Workflow status")

    @pytest.mark.asyncio
    async def test_handle_bmad_workflow_help(self, agent):
        with patch.object(agent.bmad, "get_help_text", return_value="Help text"):
            with patch("builtins.print") as mock_print:
                await agent._handle_bmad_workflow_command("bmad help")
                mock_print.assert_called_with("Help text")

    @pytest.mark.asyncio
    async def test_handle_bmad_workflow_save(self, agent):
        with patch.object(agent.bmad, "save_workflow"):
            await agent._handle_bmad_workflow_command("bmad save")
            agent.bmad.save_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_bmad_workflow_reset(self, agent):
        with patch.object(agent.bmad, "reset_workflow"):
            await agent._handle_bmad_workflow_command("bmad reset")
            agent.bmad.reset_workflow.assert_called_once()


class TestClaudeCodeIntegration:
    @pytest.fixture
    def agent_with_claude(self, mock_terminal):
        with patch(
            "termnet.agent.CONFIG",
            {
                "USE_CLAUDE_CODE": True,
                "CLAUDE_CODE_OAUTH_TOKEN": "test-token",
                "MODEL_NAME": "claude-3",
                "LLM_TEMPERATURE": 0.7,
                "MAX_AI_STEPS": 5,
            },
        ):
            with patch("termnet.agent.ClaudeCodeClient"):
                return TermNetAgent(mock_terminal)

    def test_claude_code_client_initialization(self, agent_with_claude):
        assert agent_with_claude.claude_code_client is not None
        assert agent_with_claude.openrouter_client is None


class TestOpenRouterIntegration:
    @pytest.fixture
    def agent_with_openrouter(self, mock_terminal):
        with patch(
            "termnet.agent.CONFIG",
            {
                "USE_CLAUDE_CODE": False,
                "USE_OPENROUTER": True,
                "OPENROUTER_API_KEY": "test-key",
                "OPENROUTER_BASE_URL": "https://openrouter.ai/api/v1",
                "MODEL_NAME": "gpt-4",
                "LLM_TEMPERATURE": 0.7,
                "MAX_AI_STEPS": 5,
            },
        ):
            with patch("termnet.agent.OpenRouterClient"):
                return TermNetAgent(mock_terminal)

    def test_openrouter_client_initialization(self, agent_with_openrouter):
        assert agent_with_openrouter.openrouter_client is not None
        assert agent_with_openrouter.claude_code_client is None
