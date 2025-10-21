"""
Example MCP server for testing the CLI.

Run this server with:
    python example_server.py

Then test with the CLI using example_config.json
"""

from fastmcp import FastMCP

mcp = FastMCP(name="Example Server")


@mcp.tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}! Welcome to MCP CLI."


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


@mcp.tool
def multiply(x: float, y: float) -> float:
    """Multiply two numbers."""
    return x * y


@mcp.resource("data://example/info")
def get_info() -> dict:
    """Get example server information."""
    return {
        "name": "Example Server",
        "version": "1.0.0",
        "description": "A simple example MCP server for testing"
    }


@mcp.resource("data://example/{item}")
def get_item(item: str) -> dict:
    """Get information about a specific item."""
    items = {
        "apple": {"name": "Apple", "color": "red", "price": 1.50},
        "banana": {"name": "Banana", "color": "yellow", "price": 0.75},
        "orange": {"name": "Orange", "color": "orange", "price": 1.25}
    }
    
    if item.lower() in items:
        return items[item.lower()]
    
    return {"error": f"Item '{item}' not found"}


@mcp.prompt
def analyze_data(data: str) -> str:
    """Create a prompt for analyzing data."""
    return f"Please analyze the following data and provide insights:\n\n{data}"


if __name__ == "__main__":
    # Run with stdio transport (default)
    mcp.run()

