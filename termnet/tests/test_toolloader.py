import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from termnet.toolloader import ToolLoader


class TestToolLoader:
    @pytest.fixture
    def tool_loader(self):
        return ToolLoader()

    def test_initialization(self, tool_loader):
        assert tool_loader.loaded_tools == {}
        assert tool_loader.tool_instances == {}
        assert tool_loader.tools_directory.endswith("tools")

    def test_load_tools_directory_exists(self, tool_loader):
        with patch("os.path.exists", return_value=True):
            with patch(
                "os.listdir", return_value=["terminal.py", "browser.py", "__pycache__"]
            ):
                with patch.object(tool_loader, "_load_tool_module") as mock_load:
                    tool_loader.load_tools()
                    assert mock_load.call_count == 2
                    mock_load.assert_any_call("terminal")
                    mock_load.assert_any_call("browser")

    def test_load_tools_directory_not_exists(self, tool_loader):
        with patch("os.path.exists", return_value=False):
            with patch("builtins.print") as mock_print:
                tool_loader.load_tools()
                assert any(
                    "not found" in str(call) for call in mock_print.call_args_list
                )

    def test_load_tool_module_success(self, tool_loader):
        mock_module = MagicMock()
        mock_class = MagicMock()
        mock_module.TerminalTool = mock_class
        mock_instance = MagicMock()
        mock_instance.get_definition.return_value = {
            "name": "terminal_execute",
            "description": "Execute terminal commands",
        }
        mock_class.return_value = mock_instance

        with patch("importlib.util.spec_from_file_location") as mock_spec:
            with patch("importlib.util.module_from_spec", return_value=mock_module):
                mock_spec_obj = MagicMock()
                mock_spec.return_value = mock_spec_obj

                tool_loader._load_tool_module("terminal")

                assert "terminal_execute" in tool_loader.loaded_tools
                assert "terminal_execute" in tool_loader.tool_instances

    def test_load_tool_module_import_error(self, tool_loader):
        with patch(
            "importlib.util.spec_from_file_location",
            side_effect=ImportError("Test error"),
        ):
            with patch("builtins.print") as mock_print:
                tool_loader._load_tool_module("broken_tool")
                assert any(
                    "Error loading" in str(call) for call in mock_print.call_args_list
                )

    def test_get_tool_definitions(self, tool_loader):
        tool_loader.loaded_tools = {
            "tool1": {"name": "tool1", "description": "Tool 1"},
            "tool2": {"name": "tool2", "description": "Tool 2"},
        }

        definitions = tool_loader.get_tool_definitions()
        assert len(definitions) == 2
        assert definitions[0] == {
            "type": "function",
            "function": {"name": "tool1", "description": "Tool 1"},
        }

    def test_get_tool_instance_exists(self, tool_loader):
        mock_instance = MagicMock()
        tool_loader.tool_instances = {"test_tool": mock_instance}

        result = tool_loader.get_tool_instance("test_tool")
        assert result == mock_instance

    def test_get_tool_instance_not_exists(self, tool_loader):
        result = tool_loader.get_tool_instance("non_existent")
        assert result is None

    def test_find_tool_class_in_module(self, tool_loader):
        mock_module = MagicMock()
        mock_class = MagicMock()
        mock_module.TestTool = mock_class
        mock_module.not_a_tool = "string"
        mock_module.__dict__ = {"TestTool": mock_class, "not_a_tool": "string"}

        with patch("inspect.isclass", side_effect=lambda x: x is mock_class):
            tool_class = tool_loader._find_tool_class_in_module(mock_module, "test")
            assert tool_class is mock_class

    def test_find_tool_class_not_found(self, tool_loader):
        mock_module = MagicMock()
        mock_module.__dict__ = {"some_var": "value"}

        with patch("inspect.isclass", return_value=False):
            with patch("builtins.print") as mock_print:
                tool_class = tool_loader._find_tool_class_in_module(mock_module, "test")
                assert tool_class is None
                assert any(
                    "No tool class found" in str(call)
                    for call in mock_print.call_args_list
                )


class TestToolDefinitionFormat:
    @pytest.fixture
    def tool_loader(self):
        return ToolLoader()

    def test_tool_definition_structure(self, tool_loader):
        tool_loader.loaded_tools = {
            "terminal_execute": {
                "name": "terminal_execute",
                "description": "Execute terminal commands",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The command to execute",
                        }
                    },
                    "required": ["command"],
                },
            }
        }

        definitions = tool_loader.get_tool_definitions()
        assert len(definitions) == 1
        assert definitions[0]["type"] == "function"
        assert "function" in definitions[0]
        assert definitions[0]["function"]["name"] == "terminal_execute"
        assert "parameters" in definitions[0]["function"]
