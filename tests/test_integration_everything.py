"""Integration tests with the everything MCP server.

These tests require npx and the @modelcontextprotocol/server-everything package.
They test actual connectivity and tool execution with a real MCP server.
"""

import json
import subprocess

import pytest

from mcpsh import MCPClient


@pytest.mark.integration
class TestEverythingServerCLI:
    """Integration tests using CLI with everything MCP server."""

    @pytest.mark.timeout(10)
    def test_list_tools(self, everything_config_file):
        """Test listing tools from everything server."""
        result = subprocess.run(
            ["mcpsh", "--config", str(everything_config_file), "--format", "json", "everything"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        tools = json.loads(result.stdout)

        assert isinstance(tools, list)
        assert len(tools) > 0

        tool_names = [tool["name"] for tool in tools]

        # The everything server should have these standard tools
        assert "everything_echo" in tool_names or "echo" in tool_names
        assert "everything_add" in tool_names or "add" in tool_names

    @pytest.mark.timeout(10)
    def test_call_echo_tool(self, everything_config_file):
        """Test calling the echo tool."""
        result = subprocess.run(
            ["mcpsh", "--config", str(everything_config_file), "everything", "echo",
             "--args", '{"message": "Hello, MCP!"}'],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert "Hello, MCP!" in result.stdout

    @pytest.mark.timeout(10)
    def test_call_add_tool(self, everything_config_file):
        """Test calling the add tool."""
        result = subprocess.run(
            ["mcpsh", "--config", str(everything_config_file), "everything", "add",
             "--args", '{"a": 10, "b": 32}'],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        # The result should contain the sum
        assert "42" in result.stdout

    @pytest.mark.timeout(10)
    def test_call_tool_with_json_output(self, everything_config_file):
        """Test calling a tool with JSON output format."""
        result = subprocess.run(
            ["mcpsh", "--config", str(everything_config_file), "--format", "json",
             "everything", "add", "--args", '{"a": 15, "b": 27}'],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        # JSON output should contain 42
        assert "42" in result.stdout

    @pytest.mark.timeout(10)
    def test_list_resources(self, everything_config_file):
        """Test listing resources from everything server."""
        result = subprocess.run(
            ["mcpsh", "--config", str(everything_config_file), "everything", "--resources"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Resources listing may be empty or have items - both are valid
        assert result.returncode == 0, f"CLI failed: {result.stderr}"

    @pytest.mark.timeout(10)
    def test_list_prompts(self, everything_config_file):
        """Test listing prompts from everything server."""
        result = subprocess.run(
            ["mcpsh", "--config", str(everything_config_file), "everything", "--prompts"],
            capture_output=True,
            text=True,
            timeout=10
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        # Everything server should have at least one prompt
        assert "Prompts from" in result.stdout or "prompt" in result.stdout.lower()


@pytest.mark.integration
class TestErrorHandling:
    """Integration tests for error handling with everything server."""

    @pytest.mark.timeout(10)
    def test_call_nonexistent_tool(self, everything_config_file):
        """Test calling a tool that doesn't exist."""
        result = subprocess.run(
            ["mcpsh", "--config", str(everything_config_file), "everything", "nonexistent_tool_xyz",
             "--args", '{}'],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0
        # Error message should mention the tool
        error_msg = (result.stderr + result.stdout).lower()
        assert "tool" in error_msg or "not found" in error_msg or "unknown" in error_msg

    @pytest.mark.timeout(10)
    def test_call_tool_with_invalid_arguments(self, everything_config_file):
        """Test calling a tool with invalid arguments."""
        result = subprocess.run(
            ["mcpsh", "--config", str(everything_config_file), "everything", "add",
             "--args", '{}'],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0

    @pytest.mark.timeout(10)
    def test_call_tool_with_wrong_argument_types(self, everything_config_file):
        """Test calling a tool with wrong argument types."""
        result = subprocess.run(
            ["mcpsh", "--config", str(everything_config_file), "everything", "add",
             "--args", '{"a": "not_a_number", "b": "also_not_a_number"}'],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0


# Module-level client for Python API tests
_mcp_client = None
_event_loop = None


@pytest.fixture(scope="module")
def mcp_client_for_all_tests(everything_config_file):
    """Create a single MCP client shared across all tests in this module."""
    import asyncio

    global _mcp_client, _event_loop

    # Create a new event loop for this session
    _event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_event_loop)

    # Create and enter the client context
    client_ctx = MCPClient("everything", config=everything_config_file)
    _mcp_client = _event_loop.run_until_complete(client_ctx.__aenter__())
    _mcp_client._client_wrapper = client_ctx._client_wrapper
    _mcp_client._is_async = True  # Mark as async mode

    yield _mcp_client

    # Cleanup
    try:
        _event_loop.run_until_complete(
            client_ctx._client_wrapper.__aexit__(None, None, None)
        )
    finally:
        _event_loop.close()


@pytest.mark.integration
class TestPythonAPI:
    """Integration tests using Python API with a single shared connection."""

    @pytest.mark.timeout(10)
    def test_list_tools(self, mcp_client_for_all_tests):
        """Test listing tools from everything server."""
        import asyncio
        tools = asyncio.get_event_loop().run_until_complete(
            mcp_client_for_all_tests.list_tools()
        )

        assert tools is not None
        assert len(tools) > 0

        tool_names = [tool.name for tool in tools]
        assert "everything_echo" in tool_names or "echo" in tool_names
        assert "everything_add" in tool_names or "add" in tool_names

    @pytest.mark.timeout(10)
    def test_call_echo_tool(self, mcp_client_for_all_tests):
        """Test calling the echo tool."""
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            mcp_client_for_all_tests.call_tool("echo", {"message": "Hello from Python API!"})
        )

        assert result is not None
        assert result.content is not None
        assert len(result.content) > 0
        assert "Hello from Python API!" in result.content[0].text

    @pytest.mark.timeout(10)
    def test_call_add_tool(self, mcp_client_for_all_tests):
        """Test calling the add tool."""
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(
            mcp_client_for_all_tests.call_tool("add", {"a": 25, "b": 17})
        )

        assert result is not None
        assert result.content is not None
        assert len(result.content) > 0
        assert "42" in result.content[0].text


