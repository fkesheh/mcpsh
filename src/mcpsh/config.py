"""Configuration loader for MCP servers."""

import json
from pathlib import Path
from typing import Dict, Any

from rich.console import Console

console = Console()


def load_config(config_path: Path | None = None) -> Dict[str, Any]:
    """Load MCP server configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file. If None, uses default location.
        
    Returns:
        Dictionary containing the mcpServers configuration
    """
    if config_path is None:
        # Try default Claude Desktop location
        default_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        if default_path.exists():
            config_path = default_path
        else:
            # Try current directory
            config_path = Path("mcp_config.json")
    
    if not config_path.exists():
        console.print(f"[red]Configuration file not found: {config_path}[/red]")
        console.print("\n[yellow]Create a mcp_config.json file with your MCP servers configuration.[/yellow]")
        console.print("\nExample configuration:")
        console.print(json.dumps({
            "mcpServers": {
                "my-server": {
                    "command": "python",
                    "args": ["server.py"]
                }
            }
        }, indent=2))
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path) as f:
        config = json.load(f)
    
    if "mcpServers" not in config:
        raise ValueError("Configuration must contain 'mcpServers' key")
    
    return config["mcpServers"]


def list_configured_servers(config_path: Path | None = None) -> list[str]:
    """List all configured MCP server names.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        List of server names
    """
    servers = load_config(config_path)
    return list(servers.keys())

