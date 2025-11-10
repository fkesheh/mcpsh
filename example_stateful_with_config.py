#!/usr/bin/env python3
# /// script
# dependencies = [
#   "mcpsh>=1.1.1",
# ]
# ///
"""
Stateful MCP workflow example with embedded configuration.

Demonstrates how to maintain state across multiple tool calls by keeping
a single long-lived async context. Perfect for scenarios like loading
OpenAPI specs and making multiple queries against them.

Run with: uv run example_stateful_with_config.py
"""

import asyncio
import tempfile
import json
from pathlib import Path
from mcpsh.client import MCPClient


# Embedded MCP server configuration
MCP_CONFIG = {
    "mcpServers": {
        "api-explorer": {
            "command": "uv",
            "args": [
                "run",
                "--with",
                "api-explorer-mcp",
                "api-explorer-mcp",
                "stdio"
            ]
        }
    }
}


async def main():
    """Demonstrate stateful workflow with api-explorer MCP server."""
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(MCP_CONFIG, f, indent=2)
        config_path = Path(f.name)

    try:
        # Single long-lived context maintains state across all operations
        async with MCPClient("api-explorer", config=config_path) as client:
            # Step 1: Load OpenAPI spec (state stored in server)
            print("Loading OpenAPI specification...")
            await client.call_tool("load-openapi-spec", {
                "file_path_or_url": "https://petstore3.swagger.io/api/v3/openapi.json"
            })
            print("✓ Spec loaded")

            # Step 2-4: Query the loaded spec multiple times
            # State persists within the same context
            print("\nQuerying endpoints...")
            result = await client.call_tool("get-endpoint-details", {
                "path": "/pet",
                "method": "POST"
            })
            print(f"✓ POST /pet: {result.content[0].text[:100]}...")

            result = await client.call_tool("get-endpoint-details", {
                "path": "/pet/{petId}",
                "method": "GET"
            })
            print(f"✓ GET /pet/{{petId}}: {result.content[0].text[:100]}...")

            print("\n✓ All operations completed in a single stateful session")

    finally:
        config_path.unlink()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
