"""Tests for the Python API client."""

import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


class TestMCPClient:
    """Tests for MCPClient class - main Python API."""

    @patch('mcpsh.client.Client')
    def test_client_context_manager(self, mock_fastmcp_client, temp_config_file):
        """Test MCPClient can be used as context manager."""
        from mcpsh import MCPClient

        # Setup mock
        mock_instance = MagicMock()
        mock_fastmcp_client.return_value.__enter__.return_value = mock_instance
        mock_fastmcp_client.return_value.__exit__.return_value = None

        with MCPClient("test-server", config=temp_config_file) as client:
            assert client is not None

        mock_fastmcp_client.return_value.__enter__.assert_called_once()
        mock_fastmcp_client.return_value.__exit__.assert_called_once()

    @patch('mcpsh.client.Client')
    def test_client_list_tools(self, mock_fastmcp_client, temp_config_file):
        """Test listing tools through Python API."""
        from mcpsh import MCPClient

        # Setup mock
        mock_instance = MagicMock()
        mock_fastmcp_client.return_value.__enter__.return_value = mock_instance

        mock_tool1 = MagicMock()
        mock_tool1.name = "tool1"
        mock_tool1.description = "Test tool 1"

        mock_tool2 = MagicMock()
        mock_tool2.name = "tool2"
        mock_tool2.description = "Test tool 2"

        # Make list_tools return an async mock
        mock_instance.list_tools = AsyncMock(return_value=[mock_tool1, mock_tool2])

        with MCPClient("test-server", config=temp_config_file) as client:
            tools = client.list_tools()

        assert len(tools) == 2
        assert tools[0].name == "tool1"
        assert tools[1].name == "tool2"

    @patch('mcpsh.client.Client')
    def test_client_call_tool(self, mock_fastmcp_client, temp_config_file):
        """Test calling a tool through Python API."""
        from mcpsh import MCPClient

        # Setup mock
        mock_instance = MagicMock()
        mock_fastmcp_client.return_value.__enter__.return_value = mock_instance

        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = '{"result": "success", "data": 42}'
        mock_result.content = [mock_content]

        mock_instance.call_tool = AsyncMock(return_value=mock_result)

        with MCPClient("test-server", config=temp_config_file) as client:
            result = client.call_tool("my-tool", {"param": "value"})

        assert result is not None
        assert len(result.content) == 1
        assert "success" in result.content[0].text

    @patch('mcpsh.client.Client')
    def test_client_call_tool_returns_parsed_json(self, mock_fastmcp_client, temp_config_file):
        """Test that call_tool can return parsed JSON."""
        from mcpsh import MCPClient

        # Setup mock
        mock_instance = MagicMock()
        mock_fastmcp_client.return_value.__enter__.return_value = mock_instance

        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = '{"result": "success", "data": 42}'
        mock_result.content = [mock_content]

        mock_instance.call_tool = AsyncMock(return_value=mock_result)

        with MCPClient("test-server", config=temp_config_file) as client:
            result = client.call_tool("my-tool", {"param": "value"}, parse_json=True)

        assert isinstance(result, dict)
        assert result["result"] == "success"
        assert result["data"] == 42

    @patch('mcpsh.client.Client')
    def test_client_list_resources(self, mock_fastmcp_client, temp_config_file):
        """Test listing resources through Python API."""
        from mcpsh import MCPClient

        # Setup mock
        mock_instance = MagicMock()
        mock_fastmcp_client.return_value.__enter__.return_value = mock_instance

        mock_resource = MagicMock()
        mock_resource.uri = "resource://test/data"
        mock_resource.name = "Test Resource"

        mock_instance.list_resources = AsyncMock(return_value=[mock_resource])

        with MCPClient("test-server", config=temp_config_file) as client:
            resources = client.list_resources()

        assert len(resources) == 1
        assert resources[0].uri == "resource://test/data"

    @patch('mcpsh.client.Client')
    def test_client_read_resource(self, mock_fastmcp_client, temp_config_file):
        """Test reading a resource through Python API."""
        from mcpsh import MCPClient

        # Setup mock
        mock_instance = MagicMock()
        mock_fastmcp_client.return_value.__enter__.return_value = mock_instance

        mock_content = MagicMock()
        mock_content.text = "Resource content here"

        mock_instance.read_resource = AsyncMock(return_value=[mock_content])

        with MCPClient("test-server", config=temp_config_file) as client:
            content = client.read_resource("resource://test/data")

        assert len(content) == 1
        assert content[0].text == "Resource content here"

    @patch('mcpsh.client.Client')
    def test_client_list_prompts(self, mock_fastmcp_client, temp_config_file):
        """Test listing prompts through Python API."""
        from mcpsh import MCPClient

        # Setup mock
        mock_instance = MagicMock()
        mock_fastmcp_client.return_value.__enter__.return_value = mock_instance

        mock_prompt = MagicMock()
        mock_prompt.name = "test-prompt"
        mock_prompt.description = "A test prompt"

        mock_instance.list_prompts = AsyncMock(return_value=[mock_prompt])

        with MCPClient("test-server", config=temp_config_file) as client:
            prompts = client.list_prompts()

        assert len(prompts) == 1
        assert prompts[0].name == "test-prompt"

    def test_client_invalid_server(self, temp_config_file):
        """Test that invalid server raises appropriate error."""
        from mcpsh import MCPClient

        with pytest.raises(Exception) as exc_info:
            with MCPClient("nonexistent-server", config=temp_config_file) as client:
                pass

        assert "not found" in str(exc_info.value).lower()


class TestAsyncMCPClient:
    """Tests for async MCPClient usage."""

    @pytest.mark.asyncio
    @patch('mcpsh.client.Client')
    async def test_async_client_context_manager(self, mock_fastmcp_client, temp_config_file):
        """Test MCPClient can be used as async context manager."""
        from mcpsh import MCPClient

        # Setup mock
        mock_instance = AsyncMock()
        mock_fastmcp_client.return_value.__aenter__.return_value = mock_instance
        mock_fastmcp_client.return_value.__aexit__.return_value = None

        async with MCPClient("test-server", config=temp_config_file) as client:
            assert client is not None

    @pytest.mark.asyncio
    @patch('mcpsh.client.Client')
    async def test_async_client_call_tool(self, mock_fastmcp_client, temp_config_file):
        """Test calling a tool through async Python API."""
        from mcpsh import MCPClient

        # Setup mock
        mock_instance = AsyncMock()
        mock_fastmcp_client.return_value.__aenter__.return_value = mock_instance

        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = '{"result": "success"}'
        mock_result.content = [mock_content]

        mock_instance.call_tool = AsyncMock(return_value=mock_result)

        async with MCPClient("test-server", config=temp_config_file) as client:
            result = await client.call_tool("my-tool", {"param": "value"})

        assert result is not None
        assert "success" in result.content[0].text


class TestConvenienceFunctions:
    """Tests for convenience functions (one-off calls)."""

    @patch('mcpsh.client.MCPClient')
    def test_list_servers_function(self, mock_client_class, temp_config_file):
        """Test list_servers() convenience function."""
        from mcpsh import list_servers

        servers = list_servers(config=temp_config_file)

        assert isinstance(servers, list)
        assert "test-server" in servers
        assert "another-server" in servers

    @patch('mcpsh.client.MCPClient')
    def test_list_tools_function(self, mock_client_class, temp_config_file):
        """Test list_tools() convenience function."""
        from mcpsh import list_tools

        # Setup mock
        mock_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_instance

        mock_tool = MagicMock()
        mock_tool.name = "test-tool"
        mock_instance.list_tools.return_value = [mock_tool]

        tools = list_tools("test-server", config=temp_config_file)

        assert len(tools) == 1
        assert tools[0].name == "test-tool"

    @patch('mcpsh.client.MCPClient')
    def test_call_tool_function(self, mock_client_class, temp_config_file):
        """Test call_tool() convenience function."""
        from mcpsh import call_tool

        # Setup mock
        mock_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_instance

        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = '{"status": "ok"}'
        mock_result.content = [mock_content]

        mock_instance.call_tool.return_value = mock_result

        result = call_tool("test-server", "my-tool", {"param": "value"}, config=temp_config_file)

        assert result is not None

    @patch('mcpsh.client.MCPClient')
    def test_call_tool_function_with_json_parsing(self, mock_client_class, temp_config_file):
        """Test call_tool() convenience function with JSON parsing."""
        from mcpsh import call_tool

        # Setup mock
        mock_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_instance

        # When parse_json=True, call_tool should return parsed dict
        mock_instance.call_tool.return_value = {"status": "ok", "count": 42}

        result = call_tool(
            "test-server",
            "my-tool",
            {"param": "value"},
            config=temp_config_file,
            parse_json=True
        )

        assert isinstance(result, dict)
        assert result["status"] == "ok"
        assert result["count"] == 42

    @patch('mcpsh.client.MCPClient')
    def test_list_resources_function(self, mock_client_class, temp_config_file):
        """Test list_resources() convenience function."""
        from mcpsh import list_resources

        # Setup mock
        mock_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_instance

        mock_resource = MagicMock()
        mock_resource.uri = "resource://test"
        mock_instance.list_resources.return_value = [mock_resource]

        resources = list_resources("test-server", config=temp_config_file)

        assert len(resources) == 1
        assert resources[0].uri == "resource://test"

    @patch('mcpsh.client.MCPClient')
    def test_read_resource_function(self, mock_client_class, temp_config_file):
        """Test read_resource() convenience function."""
        from mcpsh import read_resource

        # Setup mock
        mock_instance = MagicMock()
        mock_client_class.return_value.__enter__.return_value = mock_instance

        mock_content = MagicMock()
        mock_content.text = "Resource data"
        mock_instance.read_resource.return_value = [mock_content]

        content = read_resource("test-server", "resource://test", config=temp_config_file)

        assert len(content) == 1
        assert content[0].text == "Resource data"


class TestClientOutputFormats:
    """Tests for different output format options."""

    @patch('mcpsh.client.Client')
    def test_client_returns_raw_by_default(self, mock_fastmcp_client, temp_config_file):
        """Test that client returns raw result by default."""
        from mcpsh import MCPClient

        # Setup mock
        mock_instance = MagicMock()
        mock_fastmcp_client.return_value.__enter__.return_value = mock_instance

        mock_result = MagicMock()
        mock_instance.call_tool = AsyncMock(return_value=mock_result)

        with MCPClient("test-server", config=temp_config_file) as client:
            result = client.call_tool("my-tool", {})

        # Should return the raw result object
        assert result == mock_result

    @patch('mcpsh.client.Client')
    def test_client_parse_json_option(self, mock_fastmcp_client, temp_config_file):
        """Test that parse_json=True returns parsed dict."""
        from mcpsh import MCPClient

        # Setup mock
        mock_instance = MagicMock()
        mock_fastmcp_client.return_value.__enter__.return_value = mock_instance

        mock_result = MagicMock()
        mock_content = MagicMock()
        mock_content.text = '{"key": "value", "count": 123}'
        mock_result.content = [mock_content]

        mock_instance.call_tool = AsyncMock(return_value=mock_result)

        with MCPClient("test-server", config=temp_config_file) as client:
            result = client.call_tool("my-tool", {}, parse_json=True)

        # Should return parsed dict
        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["count"] == 123
