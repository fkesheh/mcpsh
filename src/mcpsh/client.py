"""Python API for MCP client interactions."""

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastmcp import Client

from mcpsh.config import load_config


class MCPClient:
    """
    Python API for interacting with MCP servers.

    Can be used as both a sync and async context manager.

    Example (sync):
        with MCPClient("postgres") as client:
            result = client.call_tool("query", {"sql": "SELECT * FROM users"})

    Example (async):
        async with MCPClient("postgres") as client:
            result = await client.call_tool("query", {"sql": "SELECT * FROM users"})
    """

    def __init__(
        self,
        server_name: str,
        config: Optional[Path] = None
    ):
        """
        Initialize MCP client for a specific server.

        Args:
            server_name: Name of the MCP server from config
            config: Optional path to config file (uses default if not provided)
        """
        self.server_name = server_name
        self.config_path = config
        self._client = None
        self._is_async = False

        # Load server configuration
        servers_config = load_config(config)
        if server_name not in servers_config:
            raise ValueError(f"Server '{server_name}' not found in configuration")

        server_config = servers_config[server_name].copy()

        # Set keep_alive to False for proper subprocess cleanup
        if "keep_alive" not in server_config:
            server_config["keep_alive"] = False

        # Create MCPConfig format for FastMCP Client
        self._mcp_config = {"mcpServers": {server_name: server_config}}

    def __enter__(self):
        """Sync context manager entry."""
        client_wrapper = Client(self._mcp_config)
        self._client = client_wrapper.__enter__()
        self._client_wrapper = client_wrapper
        self._is_async = False
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit."""
        if hasattr(self, '_client_wrapper'):
            return self._client_wrapper.__exit__(exc_type, exc_val, exc_tb)

    async def __aenter__(self):
        """Async context manager entry."""
        client_wrapper = Client(self._mcp_config)
        self._client = await client_wrapper.__aenter__()
        self._client_wrapper = client_wrapper
        self._is_async = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if hasattr(self, '_client_wrapper'):
            return await self._client_wrapper.__aexit__(exc_type, exc_val, exc_tb)

    def _run_async(self, coro):
        """Helper to run async operations in sync mode."""
        return asyncio.run(coro)

    def list_tools(self):
        """
        List all available tools from the server.

        Returns:
            List of tool objects
        """
        if self._is_async:
            # In async mode, return the coroutine
            return self._client.list_tools()
        else:
            # In sync mode, run it synchronously
            return self._run_async(self._client.list_tools())

    def call_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        parse_json: bool = False
    ):
        """
        Call a tool on the server.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as a dictionary
            parse_json: If True, parse the result as JSON and return dict

        Returns:
            Tool result object, or parsed dict if parse_json=True
        """
        if arguments is None:
            arguments = {}

        # Note: We create single-server configs in __init__ (line 57),
        # so FastMCP doesn't add prefixes. Call tools by their direct name.
        async def _call():
            result = await self._client.call_tool(tool_name, arguments)

            if parse_json:
                # Extract and parse JSON from result
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    if hasattr(content, 'text'):
                        return json.loads(content.text)
                return {}

            return result

        if self._is_async:
            return _call()
        else:
            return self._run_async(_call())

    def list_resources(self):
        """
        List all available resources from the server.

        Returns:
            List of resource objects
        """
        if self._is_async:
            return self._client.list_resources()
        else:
            return self._run_async(self._client.list_resources())

    def read_resource(self, uri: str):
        """
        Read a resource from the server.

        Args:
            uri: Resource URI to read

        Returns:
            List of content objects
        """
        if self._is_async:
            return self._client.read_resource(uri)
        else:
            return self._run_async(self._client.read_resource(uri))

    def list_prompts(self):
        """
        List all available prompts from the server.

        Returns:
            List of prompt objects
        """
        if self._is_async:
            return self._client.list_prompts()
        else:
            return self._run_async(self._client.list_prompts())


# Convenience functions for one-off operations

def list_servers(config: Optional[Path] = None) -> List[str]:
    """
    List all configured MCP servers.

    Args:
        config: Optional path to config file

    Returns:
        List of server names
    """
    from mcpsh.config import list_configured_servers
    return list_configured_servers(config)


def list_tools(server_name: str, config: Optional[Path] = None):
    """
    List all available tools from a server.

    Args:
        server_name: Name of the MCP server
        config: Optional path to config file

    Returns:
        List of tool objects
    """
    with MCPClient(server_name, config=config) as client:
        return client.list_tools()


def call_tool(
    server_name: str,
    tool_name: str,
    arguments: Optional[Dict[str, Any]] = None,
    config: Optional[Path] = None,
    parse_json: bool = False
):
    """
    Call a tool on an MCP server.

    Args:
        server_name: Name of the MCP server
        tool_name: Name of the tool to call
        arguments: Tool arguments as a dictionary
        config: Optional path to config file
        parse_json: If True, parse result as JSON and return dict

    Returns:
        Tool result object, or parsed dict if parse_json=True

    Example:
        result = call_tool("postgres", "query", {"sql": "SELECT * FROM users"})

        # With JSON parsing
        data = call_tool("postgres", "query", {"sql": "SELECT * FROM users"}, parse_json=True)
    """
    with MCPClient(server_name, config=config) as client:
        return client.call_tool(tool_name, arguments, parse_json=parse_json)


def list_resources(server_name: str, config: Optional[Path] = None):
    """
    List all available resources from a server.

    Args:
        server_name: Name of the MCP server
        config: Optional path to config file

    Returns:
        List of resource objects
    """
    with MCPClient(server_name, config=config) as client:
        return client.list_resources()


def read_resource(server_name: str, uri: str, config: Optional[Path] = None):
    """
    Read a resource from an MCP server.

    Args:
        server_name: Name of the MCP server
        uri: Resource URI to read
        config: Optional path to config file

    Returns:
        List of content objects
    """
    with MCPClient(server_name, config=config) as client:
        return client.read_resource(uri)
