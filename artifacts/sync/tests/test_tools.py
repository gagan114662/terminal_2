import asyncio
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from termnet.tools.browsersearch import BrowserSearchTool
from termnet.tools.scratchpad import ScratchpadTool
from termnet.tools.terminal import TerminalTool


class TestTerminalTool:
    @pytest.fixture
    def terminal_tool(self):
        return TerminalTool()

    @pytest.mark.asyncio
    async def test_execute_command_success(self, terminal_tool):
        with patch("asyncio.create_subprocess_shell") as mock_create:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"output", b"")
            mock_process.returncode = 0
            mock_create.return_value = mock_process

            output, exit_code, success = await terminal_tool.execute_command("ls")

            assert output == "output"
            assert exit_code == 0
            assert success is True

    @pytest.mark.asyncio
    async def test_execute_command_with_error(self, terminal_tool):
        with patch("asyncio.create_subprocess_shell") as mock_create:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"error message")
            mock_process.returncode = 1
            mock_create.return_value = mock_process

            output, exit_code, success = await terminal_tool.execute_command(
                "invalid_command"
            )

            assert "error message" in output
            assert exit_code == 1
            assert success is False

    @pytest.mark.asyncio
    async def test_execute_command_timeout(self, terminal_tool):
        with patch("asyncio.create_subprocess_shell") as mock_create:
            mock_process = AsyncMock()
            mock_process.communicate.side_effect = asyncio.TimeoutError()
            mock_process.terminate = MagicMock()
            mock_create.return_value = mock_process

            output, exit_code, success = await terminal_tool.execute_command(
                "sleep 100"
            )

            assert "Command timed out" in output
            assert exit_code == -1
            assert success is False
            mock_process.terminate.assert_called_once()

    def test_get_definition(self, terminal_tool):
        definition = terminal_tool.get_definition()

        assert definition["name"] == "terminal_execute"
        assert "description" in definition
        assert "parameters" in definition
        assert definition["parameters"]["type"] == "object"
        assert "command" in definition["parameters"]["properties"]
        assert "command" in definition["parameters"]["required"]

    @pytest.mark.asyncio
    async def test_execute_command_with_safety_check(self, terminal_tool):
        with patch.object(
            terminal_tool.safety_checker, "is_safe_command"
        ) as mock_safety:
            mock_safety.return_value = (False, "Dangerous command detected")

            output, exit_code, success = await terminal_tool.execute_command("rm -rf /")

            assert "Dangerous command detected" in output
            assert exit_code == -1
            assert success is False

    @pytest.mark.asyncio
    async def test_execute_command_with_working_directory(self, terminal_tool):
        with patch("asyncio.create_subprocess_shell") as mock_create:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"/home/user", b"")
            mock_process.returncode = 0
            mock_create.return_value = mock_process

            output, _, _ = await terminal_tool.execute_command("pwd", cwd="/home/user")

            mock_create.assert_called_with(
                "pwd",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/home/user",
            )


class TestBrowserSearchTool:
    @pytest.fixture
    def browser_tool(self):
        return BrowserSearchTool()

    @pytest.mark.asyncio
    async def test_search_success(self, browser_tool):
        with patch("playwright.async_api.async_playwright") as mock_playwright:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_context = AsyncMock()

            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value.chromium.launch.return_value = (
                mock_browser
            )
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page

            mock_page.content.return_value = "<html><body>Search results</body></html>"

            mock_playwright.return_value = mock_context_manager

            results = await browser_tool.search("test query")

            assert "Search results" in results
            mock_page.goto.assert_called()
            mock_browser.close.assert_called()

    @pytest.mark.asyncio
    async def test_search_with_error(self, browser_tool):
        with patch("playwright.async_api.async_playwright") as mock_playwright:
            mock_playwright.side_effect = Exception("Browser error")

            results = await browser_tool.search("test query")

            assert "Error" in results or "Failed" in results

    def test_get_definition(self, browser_tool):
        definition = browser_tool.get_definition()

        assert definition["name"] == "browser_search"
        assert "description" in definition
        assert "parameters" in definition
        assert "query" in definition["parameters"]["properties"]

    @pytest.mark.asyncio
    async def test_click_and_collect(self, browser_tool):
        with patch("playwright.async_api.async_playwright") as mock_playwright:
            mock_browser = AsyncMock()
            mock_page = AsyncMock()
            mock_context = AsyncMock()

            mock_context_manager = AsyncMock()
            mock_context_manager.__aenter__.return_value.chromium.launch.return_value = (
                mock_browser
            )
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page

            mock_page.content.return_value = "<html><body>Page content</body></html>"

            mock_playwright.return_value = mock_context_manager

            results = await browser_tool.click_and_collect(
                "https://example.com", "button.submit"
            )

            assert "Page content" in results or isinstance(results, str)
            mock_page.goto.assert_called_with("https://example.com", timeout=30000)


class TestScratchpadTool:
    @pytest.fixture
    def scratchpad_tool(self):
        return ScratchpadTool()

    def test_write_note(self, scratchpad_tool):
        result = scratchpad_tool.write("test_key", "test content")

        assert "Saved" in result or "Written" in result
        assert scratchpad_tool.notes.get("test_key") == "test content"

    def test_read_existing_note(self, scratchpad_tool):
        scratchpad_tool.notes["test_key"] = "test content"

        result = scratchpad_tool.read("test_key")

        assert result == "test content"

    def test_read_non_existing_note(self, scratchpad_tool):
        result = scratchpad_tool.read("non_existent")

        assert "not found" in result.lower() or result == ""

    def test_list_notes_empty(self, scratchpad_tool):
        result = scratchpad_tool.list()

        assert "No notes" in result or result == "[]" or result == ""

    def test_list_notes_with_content(self, scratchpad_tool):
        scratchpad_tool.notes["key1"] = "content1"
        scratchpad_tool.notes["key2"] = "content2"

        result = scratchpad_tool.list()

        assert "key1" in result
        assert "key2" in result

    def test_delete_existing_note(self, scratchpad_tool):
        scratchpad_tool.notes["test_key"] = "test content"

        result = scratchpad_tool.delete("test_key")

        assert "Deleted" in result or "Removed" in result
        assert "test_key" not in scratchpad_tool.notes

    def test_delete_non_existing_note(self, scratchpad_tool):
        result = scratchpad_tool.delete("non_existent")

        assert "not found" in result.lower() or "doesn't exist" in result.lower()

    def test_clear_all_notes(self, scratchpad_tool):
        scratchpad_tool.notes["key1"] = "content1"
        scratchpad_tool.notes["key2"] = "content2"

        result = scratchpad_tool.clear()

        assert "Cleared" in result or "Deleted all" in result
        assert len(scratchpad_tool.notes) == 0

    def test_get_definition(self, scratchpad_tool):
        definition = scratchpad_tool.get_definition()

        assert definition["name"] == "scratchpad"
        assert "description" in definition
        assert "parameters" in definition
        assert "action" in definition["parameters"]["properties"]
        assert "key" in definition["parameters"]["properties"]

    def test_append_to_existing_note(self, scratchpad_tool):
        scratchpad_tool.notes["test_key"] = "initial content"

        result = scratchpad_tool.append("test_key", " additional content")

        assert "Appended" in result or "Added" in result
        assert scratchpad_tool.notes["test_key"] == "initial content additional content"

    def test_append_to_new_note(self, scratchpad_tool):
        result = scratchpad_tool.append("new_key", "new content")

        assert scratchpad_tool.notes["new_key"] == "new content"

    def test_search_notes(self, scratchpad_tool):
        scratchpad_tool.notes["key1"] = "Python programming"
        scratchpad_tool.notes["key2"] = "JavaScript development"
        scratchpad_tool.notes["key3"] = "Python testing"

        results = scratchpad_tool.search("Python")

        assert "key1" in results
        assert "key3" in results
        assert "key2" not in results or "JavaScript" not in results
