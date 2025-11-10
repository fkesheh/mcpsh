"""Tests for main CLI commands."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from click.testing import CliRunner

from mcpsh.main import cli as app


runner = CliRunner()


class TestProgressiveCLI:
    """Tests for the progressive CLI interface."""

    def test_mcpsh_no_args_lists_servers(self, temp_config_file):
        """Test that 'mcpsh' with no args lists servers."""
        result = runner.invoke(app, ["--config", str(temp_config_file)])
        assert result.exit_code == 0
        assert "test-server" in result.stdout
        assert "another-server" in result.stdout

    def test_mcpsh_no_args_json_format(self, temp_config_file):
        """Test that 'mcpsh -f json' outputs servers in JSON."""
        result = runner.invoke(app, ["-f", "json", "--config", str(temp_config_file)])
        assert result.exit_code == 0

        output = result.stdout.strip()
        data = json.loads(output)
        assert isinstance(data, list)
        assert "test-server" in data
        assert "another-server" in data

    @patch('mcpsh.main.Client')
    def test_mcpsh_server_lists_tools(self, mock_client, temp_config_file):
        """Test that 'mcpsh <server>' lists tools."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance

        mock_tool1 = MagicMock()
        mock_tool1.name = "tool1"
        mock_tool1.description = "Test tool 1"

        mock_tool2 = MagicMock()
        mock_tool2.name = "tool2"
        mock_tool2.description = "Test tool 2"

        mock_instance.list_tools = AsyncMock(return_value=[mock_tool1, mock_tool2])

        result = runner.invoke(app, ["test-server", "--config", str(temp_config_file)])

        assert result.exit_code == 0
        assert "tool1" in result.stdout
        assert "tool2" in result.stdout

    @patch('mcpsh.main.Client')
    def test_mcpsh_server_json_format(self, mock_client, temp_config_file):
        """Test that 'mcpsh <server> -f json' outputs tools in JSON."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance

        mock_tool = MagicMock()
        mock_tool.name = "tool1"
        mock_tool.description = "Test tool 1"

        mock_instance.list_tools = AsyncMock(return_value=[mock_tool])

        result = runner.invoke(app, ["test-server", "-f", "json", "--config", str(temp_config_file)])

        assert result.exit_code == 0
        output = result.stdout.strip()
        data = json.loads(output)
        assert isinstance(data, list)
        assert data[0]["name"] == "tool1"

    @patch('mcpsh.main.Client')
    def test_mcpsh_server_tool_shows_info(self, mock_client, temp_config_file):
        """Test that 'mcpsh <server> <tool>' shows tool info."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance

        mock_tool = MagicMock()
        mock_tool.name = "my-tool"
        mock_tool.description = "A test tool"
        mock_tool.inputSchema = {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "First param"}
            },
            "required": ["param1"]
        }

        mock_instance.list_tools = AsyncMock(return_value=[mock_tool])

        result = runner.invoke(app, ["test-server", "my-tool", "--config", str(temp_config_file)])

        assert result.exit_code == 0
        assert "my-tool" in result.stdout
        assert "param1" in result.stdout

    @patch('mcpsh.main.Client')
    def test_mcpsh_server_tool_with_args_executes(self, mock_client, temp_config_file):
        """Test that 'mcpsh <server> <tool> --args ...' executes the tool."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance

        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = '{"result": "success"}'
        mock_result.content = [mock_content]

        mock_instance.call_tool = AsyncMock(return_value=mock_result)

        result = runner.invoke(app, [
            "test-server",
            "my-tool",
            "--args", '{"param": "value"}',
            "--config", str(temp_config_file)
        ])

        assert result.exit_code == 0
        assert "success" in result.stdout

    @patch('mcpsh.main.Client')
    def test_mcpsh_server_tool_args_json_format(self, mock_client, temp_config_file):
        """Test that 'mcpsh <server> <tool> --args ... -f json' outputs pure JSON."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance

        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = '{"result": "success", "data": 123}'
        mock_result.content = [mock_content]

        mock_instance.call_tool = AsyncMock(return_value=mock_result)

        result = runner.invoke(app, [
            "test-server",
            "my-tool",
            "--args", '{"param": "value"}',
            "-f", "json",
            "--config", str(temp_config_file)
        ])

        assert result.exit_code == 0
        output = result.stdout.strip()
        data = json.loads(output)
        assert data["result"] == "success"

    @patch('mcpsh.main.Client')
    def test_mcpsh_server_with_resources_flag(self, mock_client, temp_config_file):
        """Test that 'mcpsh <server> --resources' lists resources."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance

        mock_resource = MagicMock()
        mock_resource.uri = "resource://test/data"
        mock_resource.name = "Test Resource"

        mock_instance.list_resources = AsyncMock(return_value=[mock_resource])

        result = runner.invoke(app, [
            "test-server",
            "--resources",
            "--config", str(temp_config_file)
        ])

        assert result.exit_code == 0
        assert "resource://test/data" in result.stdout

    @patch('mcpsh.main.Client')
    def test_mcpsh_server_with_prompts_flag(self, mock_client, temp_config_file):
        """Test that 'mcpsh <server> --prompts' lists prompts."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance

        mock_prompt = MagicMock()
        mock_prompt.name = "test-prompt"
        mock_prompt.description = "A test prompt"
        mock_prompt.arguments = []

        mock_instance.list_prompts = AsyncMock(return_value=[mock_prompt])

        result = runner.invoke(app, [
            "test-server",
            "--prompts",
            "--config", str(temp_config_file)
        ])

        assert result.exit_code == 0
        assert "test-prompt" in result.stdout

    @patch('mcpsh.main.Client')
    def test_mcpsh_server_read_resource(self, mock_client, temp_config_file):
        """Test that 'mcpsh <server> --read <uri>' reads a resource."""
        mock_instance = AsyncMock()
        mock_client.return_value = mock_instance

        mock_content = MagicMock()
        mock_content.text = "Resource content here"

        mock_instance.read_resource = AsyncMock(return_value=[mock_content])

        result = runner.invoke(app, [
            "test-server",
            "--read", "resource://test/data",
            "--config", str(temp_config_file)
        ])

        assert result.exit_code == 0
        assert "Resource content here" in result.stdout
