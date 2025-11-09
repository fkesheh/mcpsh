"""Tests for main CLI commands."""

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from mcpsh.main import app


runner = CliRunner()


def test_help_command():
    """Test that --help works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "mcpsh" in result.stdout
    assert "Quick Start" in result.stdout


def test_servers_help():
    """Test servers command help."""
    result = runner.invoke(app, ["servers", "--help"])
    assert result.exit_code == 0
    assert "List all configured MCP servers" in result.stdout
    assert "Examples:" in result.stdout


def test_tools_help():
    """Test tools command help."""
    result = runner.invoke(app, ["tools", "--help"])
    assert result.exit_code == 0
    assert "List all available tools" in result.stdout
    assert "Examples:" in result.stdout


def test_tool_info_help():
    """Test tool-info command help."""
    result = runner.invoke(app, ["tool-info", "--help"])
    assert result.exit_code == 0
    assert "Show detailed information about a specific tool" in result.stdout
    assert "Examples:" in result.stdout


def test_call_help():
    """Test call command help."""
    result = runner.invoke(app, ["call", "--help"])
    assert result.exit_code == 0
    assert "Call a tool on an MCP server" in result.stdout
    assert "nested arguments" in result.stdout


def test_servers_with_config(temp_config_file):
    """Test listing servers with a config file."""
    result = runner.invoke(app, ["servers", "--config", str(temp_config_file)])
    assert result.exit_code == 0
    assert "test-server" in result.stdout
    assert "another-server" in result.stdout
    assert "Total:" in result.stdout


def test_servers_with_invalid_config(invalid_config_file):
    """Test that invalid config shows error."""
    result = runner.invoke(app, ["servers", "--config", str(invalid_config_file)])
    assert result.exit_code == 1
    assert "Error" in result.stdout


def test_servers_with_nonexistent_config():
    """Test that nonexistent config shows error."""
    result = runner.invoke(app, ["servers", "--config", "/nonexistent/config.json"])
    assert result.exit_code == 1


@patch('mcpsh.main.Client')
def test_tools_command_mock(mock_client, temp_config_file):
    """Test tools command with mocked client."""
    # Setup mock
    mock_instance = AsyncMock()
    mock_client.return_value.__aenter__.return_value = mock_instance
    
    # Create mock tools
    mock_tool1 = MagicMock()
    mock_tool1.name = "tool1"
    mock_tool1.description = "Test tool 1"
    
    mock_tool2 = MagicMock()
    mock_tool2.name = "tool2"
    mock_tool2.description = "Test tool 2"
    
    mock_instance.list_tools.return_value = [mock_tool1, mock_tool2]
    
    result = runner.invoke(app, ["tools", "test-server", "--config", str(temp_config_file)])
    
    assert result.exit_code == 0
    assert "tool1" in result.stdout
    assert "tool2" in result.stdout
    assert "Total:" in result.stdout


@patch('mcpsh.main.Client')
def test_call_command_with_args_mock(mock_client, temp_config_file):
    """Test call command with arguments."""
    # Setup mock
    mock_instance = AsyncMock()
    mock_client.return_value.__aenter__.return_value = mock_instance
    
    # Create mock result
    mock_result = MagicMock()
    mock_content = MagicMock()
    mock_content.text = '{"result": "success"}'
    mock_result.content = [mock_content]
    
    mock_instance.call_tool.return_value = mock_result
    
    result = runner.invoke(app, [
        "call", 
        "test-server", 
        "test-tool",
        "--args", '{"param": "value"}',
        "--config", str(temp_config_file)
    ])
    
    assert result.exit_code == 0
    assert "Tool executed successfully" in result.stdout
    assert "success" in result.stdout


def test_call_with_invalid_json(temp_config_file):
    """Test that invalid JSON in args shows error."""
    result = runner.invoke(app, [
        "call", 
        "test-server", 
        "test-tool",
        "--args", 'invalid json {{',
        "--config", str(temp_config_file)
    ])
    
    assert result.exit_code == 1
    assert "Invalid JSON" in result.stdout


@patch('mcpsh.main.Client')
def test_call_command_json_format(mock_client, temp_config_file):
    """Test call command with JSON format output."""
    # Setup mock
    mock_instance = AsyncMock()
    mock_client.return_value.__aenter__.return_value = mock_instance
    
    # Create mock result with JSON containing brackets (to test markup escape)
    mock_result = MagicMock()
    mock_content = MagicMock()
    mock_content.text = '[{"id": 1, "name": "test"}, {"id": 2, "name": "example"}]'
    mock_result.content = [mock_content]
    
    mock_instance.call_tool.return_value = mock_result
    
    result = runner.invoke(app, [
        "call", 
        "test-server", 
        "test-tool",
        "--format", "json",
        "--config", str(temp_config_file)
    ])
    
    assert result.exit_code == 0
    assert "Tool executed successfully" in result.stdout
    # JSON should be printed as-is without Rich markup errors
    assert '"id": 1' in result.stdout or "id" in result.stdout


def test_sanitize_error_message_escapes_brackets():
    """Test that error message sanitization escapes Rich markup characters."""
    from mcpsh.main import sanitize_error_message

    # Test error with brackets
    error = Exception("Error: [test] failed")
    sanitized = sanitize_error_message(error)
    assert r"\[" in sanitized
    assert r"\]" in sanitized

    # Test error with JSON-like content
    error = Exception('Invalid response: {"error": ["item1", "item2"]}')
    sanitized = sanitize_error_message(error)
    assert r"\[" in sanitized or "item1" in sanitized  # Should escape or preserve content


class TestConfigPathCommand:
    """Tests for the config-path command."""

    def test_config_path_help(self):
        """Test config-path command help."""
        result = runner.invoke(app, ["config-path", "--help"])
        assert result.exit_code == 0
        assert "Show which configuration file" in result.stdout

    def test_config_path_with_explicit_config(self, temp_config_file):
        """Test config-path with --config flag."""
        result = runner.invoke(app, ["config-path", "--config", str(temp_config_file)])
        assert result.exit_code == 0
        assert str(temp_config_file) in result.stdout
        assert "--config flag" in result.stdout

    def test_config_path_with_env_var(self, temp_config_file):
        """Test config-path with MCPSH_CONFIG environment variable."""
        os.environ["MCPSH_CONFIG"] = str(temp_config_file)

        try:
            result = runner.invoke(app, ["config-path"])
            assert result.exit_code == 0
            assert str(temp_config_file) in result.stdout
            assert "MCPSH_CONFIG" in result.stdout
        finally:
            os.environ.pop("MCPSH_CONFIG", None)

    def test_config_path_with_default_location(self):
        """Test config-path with default location."""
        # Ensure no env var is set
        os.environ.pop("MCPSH_CONFIG", None)

        result = runner.invoke(app, ["config-path"])

        # Should return successfully and show a source
        assert result.exit_code == 0
        # Should show one of the default locations
        assert any(loc in result.stdout for loc in [
            "~/.mcpsh/mcp_config.json",
            "Claude Desktop",
            "Cursor",
            "not found"
        ])

    def test_config_path_env_var_overrides_default(self, temp_config_file):
        """Test that MCPSH_CONFIG env var takes precedence over default locations."""
        os.environ["MCPSH_CONFIG"] = str(temp_config_file)

        try:
            result = runner.invoke(app, ["config-path"])

            assert result.exit_code == 0
            # Should show env var as source, not default
            assert "MCPSH_CONFIG" in result.stdout
            assert "default location" not in result.stdout
        finally:
            os.environ.pop("MCPSH_CONFIG", None)

    def test_config_path_flag_overrides_env_var(self, temp_config_file):
        """Test that --config flag takes precedence over MCPSH_CONFIG env var."""
        # Create another temp config
        import tempfile
        other_config = {
            "mcpServers": {
                "other-server": {
                    "command": "python"
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(other_config, f)
            other_path = Path(f.name)

        try:
            os.environ["MCPSH_CONFIG"] = str(temp_config_file)

            result = runner.invoke(app, ["config-path", "--config", str(other_path)])

            assert result.exit_code == 0
            # Should use --config flag, not env var
            assert str(other_path) in result.stdout
            assert "--config flag" in result.stdout
            assert "MCPSH_CONFIG" not in result.stdout or str(temp_config_file) not in result.stdout
        finally:
            os.environ.pop("MCPSH_CONFIG", None)
            other_path.unlink(missing_ok=True)

