"""MCP CLI - A simple command-line interface for interacting with MCP servers."""

__version__ = "1.0.0"

# Python API exports
from mcpsh.client import (
    MCPClient,
    list_servers,
    list_tools,
    call_tool,
    list_resources,
    read_resource,
)

__all__ = [
    "MCPClient",
    "list_servers",
    "list_tools",
    "call_tool",
    "list_resources",
    "read_resource",
]
