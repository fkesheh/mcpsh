"""Configuration loader for MCP servers."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Tuple

from rich.console import Console

console = Console()


def get_config_path(config_path: Path | None = None) -> Tuple[Path, str]:
    """Resolve the configuration file path.

    Priority order:
    1. Explicit config_path parameter (from --config flag)
    2. MCPSH_CONFIG environment variable
    3. ~/.mcpsh/mcp_config.json (default)
    4. Claude Desktop config
    5. Cursor config

    Args:
        config_path: Path to the configuration file. If None, uses priority order.

    Returns:
        Tuple of (resolved_path, source_description)
    """
    if config_path is not None:
        return config_path, "--config flag"

    # Check MCPSH_CONFIG environment variable
    env_config = os.environ.get("MCPSH_CONFIG")
    if env_config:
        env_path = Path(env_config).expanduser()
        if env_path.exists():
            return env_path, "MCPSH_CONFIG environment variable"

    # Try ~/.mcpsh/mcp_config.json first (default)
    default_path = Path.home() / ".mcpsh" / "mcp_config.json"
    if default_path.exists():
        return default_path, "default location (~/.mcpsh/mcp_config.json)"

    # Fallback to Claude Desktop location
    claude_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if claude_path.exists():
        return claude_path, "Claude Desktop config"

    # Fallback to ~/.cursor/mcp.json
    cursor_path = Path.home() / ".cursor" / "mcp.json"
    if cursor_path.exists():
        return cursor_path, "Cursor config"

    # No config found, return default path for error message
    return default_path, "default location (not found)"


def load_config(config_path: Path | None = None) -> Dict[str, Any]:
    """Load MCP server configuration from a JSON file.

    Args:
        config_path: Path to the configuration file. If None, uses default location.

    Returns:
        Dictionary containing the mcpServers configuration
    """
    resolved_path, _ = get_config_path(config_path)

    if not resolved_path.exists():
        console.print(f"[red]Configuration file not found: {resolved_path}[/red]")
        console.print("\n[yellow]Create a ~/.mcpsh/mcp_config.json file with your MCP servers configuration.[/yellow]")
        console.print("\nExample configuration:")
        console.print(json.dumps({
            "mcpServers": {
                "my-server": {
                    "command": "python",
                    "args": ["server.py"]
                }
            }
        }, indent=2))
        raise FileNotFoundError(f"Configuration file not found: {resolved_path}")

    with open(resolved_path) as f:
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

