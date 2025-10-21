"""Main CLI application for interacting with MCP servers."""

import asyncio
import json
import logging
import os
import sys
import warnings
from pathlib import Path
from typing import Optional, Dict, List, Union

import typer
from rich.console import Console
from rich.markdown import Markdown

from fastmcp import Client

from mcpsh.config import load_config, list_configured_servers

app = typer.Typer(
    help="""mcpsh - MCP Shell: Interact with Model Context Protocol servers

Quick Start:
    mcpsh servers                          # List configured servers
    mcpsh tools <server>                   # List available tools
    mcpsh tool-info <server> <tool>        # Get tool details
    mcpsh call <server> <tool> --args '{...}'  # Execute a tool
    
Common Examples:
    mcpsh call my-server query --args '{"sql": "SELECT * FROM users"}'
    mcpsh call my-server my-tool --args '{"param": "value"}'
    mcpsh read my-server "resource://path/to/resource"
    
Use --help on any command for detailed examples.
"""
)
console = Console()


def suppress_logs():
    """Suppress all logging output and warnings."""
    # Suppress Python warnings
    warnings.filterwarnings('ignore')
    
    # Configure root logger to only show CRITICAL messages
    logging.getLogger().setLevel(logging.CRITICAL)
    
    # Suppress specific loggers that are particularly verbose
    for logger_name in ['mcp', 'fastmcp', 'httpx', 'httpcore']:
        logging.getLogger(logger_name).setLevel(logging.CRITICAL)
    
    # Redirect stderr to devnull at file descriptor level (for subprocess logs)
    original_stderr_fd = os.dup(2)
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull_fd, 2)
    
    return original_stderr_fd, devnull_fd


def restore_logs(original_stderr_fd, devnull_fd):
    """Restore logging output and warnings."""
    if original_stderr_fd:
        os.dup2(original_stderr_fd, 2)
        os.close(original_stderr_fd)
    if devnull_fd:
        os.close(devnull_fd)


def json_to_markdown(data: Union[Dict, List, str, int, float, bool, None], level: int = 0) -> str:
    """Convert JSON data to Markdown format."""
    indent = "  " * level
    
    if data is None:
        return f"{indent}*null*"
    
    if isinstance(data, bool):
        return f"{indent}**{str(data).lower()}**"
    
    if isinstance(data, (int, float)):
        return f"{indent}**{data}**"
    
    if isinstance(data, str):
        return f"{indent}{data}"
    
    if isinstance(data, list):
        if not data:
            return f"{indent}*empty list*"
        
        md_lines = []
        for i, item in enumerate(data):
            if isinstance(item, dict):
                md_lines.append(f"{indent}- Item {i + 1}:")
                md_lines.append(json_to_markdown(item, level + 1))
            else:
                md_lines.append(f"{indent}- {json_to_markdown(item, 0).strip()}")
        return "\n".join(md_lines)
    
    if isinstance(data, dict):
        if not data:
            return f"{indent}*empty object*"
        
        md_lines = []
        for key, value in data.items():
            if isinstance(value, dict):
                md_lines.append(f"{indent}**{key}:**")
                md_lines.append(json_to_markdown(value, level + 1))
            elif isinstance(value, list):
                md_lines.append(f"{indent}**{key}:**")
                md_lines.append(json_to_markdown(value, level + 1))
            else:
                formatted_value = json_to_markdown(value, 0).strip()
                md_lines.append(f"{indent}**{key}:** {formatted_value}")
        return "\n".join(md_lines)
    
    return f"{indent}{str(data)}"


@app.command()
def servers(
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to MCP configuration file"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed server logs"
    )
):
    """
    List all configured MCP servers.
    
    Examples:
        mcpsh servers
        mcpsh servers --config ~/my-config.json
        mcpsh servers --verbose
    """
    # Suppress server logs by default
    stderr_fd, devnull_fd = (None, None)
    if not verbose:
        stderr_fd, devnull_fd = suppress_logs()
    
    try:
        server_names = list_configured_servers(config)
        
        console.print("[bold]Configured MCP Servers:[/bold]\n")
        for name in server_names:
            console.print(f"  [cyan]{name}[/cyan]")
        
        console.print(f"\n[dim]Total: {len(server_names)} servers[/dim]")
        
    except Exception as e:
        if not verbose:
            restore_logs(stderr_fd, devnull_fd)
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        if not verbose:
            restore_logs(stderr_fd, devnull_fd)


@app.command()
def tools(
    server: str = typer.Argument(..., help="Name of the MCP server"),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to MCP configuration file"
    ),
    detailed: bool = typer.Option(
        False,
        "--detailed",
        "-d",
        help="Show detailed information including input schemas"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed server logs"
    )
):
    """
    List all available tools from a server.
    
    Examples:
        mcpsh tools my-server
        mcpsh tools my-server --detailed
        mcpsh tools my-server --verbose
    """
    # Suppress server logs by default
    stderr_fd, devnull_fd = (None, None)
    if not verbose:
        stderr_fd, devnull_fd = suppress_logs()
    
    async def _list_tools():
        try:
            servers_config = load_config(config)
            
            if server not in servers_config:
                console.print(f"[red]Server '{server}' not found in configuration[/red]")
                raise typer.Exit(1)
            
            server_config = servers_config[server]
            
            # Create MCPConfig format for Client
            mcp_config = {"mcpServers": {server: server_config}}
            
            async with Client(mcp_config) as client:
                tools_list = await client.list_tools()
                
                if not tools_list:
                    console.print(f"[yellow]No tools found on server '{server}'[/yellow]")
                    return
                
                if detailed:
                    # Show detailed information for each tool
                    for i, tool in enumerate(tools_list):
                        if i > 0:
                            console.print()  # Add spacing between tools
                        
                        # Tool header
                        console.print(f"\n[bold cyan]{tool.name}[/bold cyan]")
                        if tool.description:
                            console.print(f"[dim]{tool.description}[/dim]\n")
                        
                        # Input schema
                        if hasattr(tool, 'inputSchema') and tool.inputSchema:
                            schema_dict = tool.inputSchema
                            if isinstance(schema_dict, dict):
                                console.print("[bold]Input Schema:[/bold]")
                                console.print(json.dumps(schema_dict, indent=2))
                        else:
                            console.print("[dim]No input schema available[/dim]")
                else:
                    # Show simple list view
                    console.print(f"[bold]Tools from '{server}':[/bold]\n")
                    for tool in tools_list:
                        console.print(f"  [cyan]{tool.name}[/cyan]")
                        if tool.description:
                            console.print(f"    {tool.description}")
                        console.print()
                
                console.print(f"[dim]Total: {len(tools_list)} tools[/dim]")
                
        except Exception as e:
            if not verbose:
                restore_logs(stderr_fd, devnull_fd)
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    try:
        asyncio.run(_list_tools())
    finally:
        if not verbose:
            restore_logs(stderr_fd, devnull_fd)


@app.command()
def tool_info(
    server: str = typer.Argument(..., help="Name of the MCP server"),
    tool_name: str = typer.Argument(..., help="Name of the tool"),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to MCP configuration file"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed server logs"
    )
):
    """
    Show detailed information about a specific tool.
    
    Displays tool description, parameter details (including nested parameters),
    and an example usage command with correct argument structure.
    
    Examples:
        mcpsh tool-info my-server my-tool
        mcpsh tool-info my-server query
        mcpsh tool-info my-server run-script
    """
    # Suppress server logs by default
    stderr_fd, devnull_fd = (None, None)
    if not verbose:
        stderr_fd, devnull_fd = suppress_logs()
    
    async def _show_tool_info():
        try:
            servers_config = load_config(config)
            
            if server not in servers_config:
                console.print(f"[red]Server '{server}' not found in configuration[/red]")
                raise typer.Exit(1)
            
            server_config = servers_config[server]
            
            # Create MCPConfig format for Client
            mcp_config = {"mcpServers": {server: server_config}}
            
            async with Client(mcp_config) as client:
                tools_list = await client.list_tools()
                
                # Find the requested tool
                tool = None
                for t in tools_list:
                    if t.name == tool_name:
                        tool = t
                        break
                
                if not tool:
                    console.print(f"[red]Tool '{tool_name}' not found on server '{server}'[/red]")
                    console.print(f"\n[dim]Available tools:[/dim]")
                    for t in tools_list:
                        console.print(f"  - {t.name}")
                    raise typer.Exit(1)
                
                # Display tool information
                console.print(f"\n[bold cyan]Tool: {tool.name}[/bold cyan]")
                console.print(f"[dim]Server: {server}[/dim]\n")
                
                if tool.description:
                    console.print(f"[bold]Description:[/bold]")
                    console.print(tool.description)
                    console.print()
                
                # Input schema
                if hasattr(tool, 'inputSchema') and tool.inputSchema:
                    schema_dict = tool.inputSchema
                    if isinstance(schema_dict, dict):
                        # Extract and display required/optional parameters
                        if 'properties' in schema_dict:
                            console.print("\n[bold]Parameters:[/bold]")
                            required = schema_dict.get('required', [])
                            defs = schema_dict.get('$defs', {})
                            
                            for param_name, param_info in schema_dict['properties'].items():
                                is_required = param_name in required
                                req_label = "[red]*[/red]" if is_required else "[dim](optional)[/dim]"
                                
                                # Check if this is a $ref to resolve it
                                if '$ref' in param_info:
                                    ref_path = param_info['$ref'].split('/')[-1]
                                    if ref_path in defs:
                                        resolved = defs[ref_path]
                                        param_type = resolved.get('type', 'object')
                                        param_desc = resolved.get('description', '')
                                        
                                        console.print(f"  • [cyan]{param_name}[/cyan] {req_label} - [yellow]{param_type}[/yellow]")
                                        if param_desc:
                                            console.print(f"    {param_desc}")
                                        
                                        # Show nested properties
                                        if 'properties' in resolved:
                                            nested_required = resolved.get('required', [])
                                            for nested_name, nested_info in resolved['properties'].items():
                                                nested_req = "[red]*[/red]" if nested_name in nested_required else "[dim](optional)[/dim]"
                                                nested_type = nested_info.get('type', 'unknown')
                                                nested_desc = nested_info.get('description', '')
                                                console.print(f"      - [cyan]{nested_name}[/cyan] {nested_req} - [yellow]{nested_type}[/yellow]")
                                                if nested_desc:
                                                    console.print(f"        {nested_desc}")
                                else:
                                    param_type = param_info.get('type', 'unknown')
                                    param_desc = param_info.get('description', '')
                                    
                                    console.print(f"  • [cyan]{param_name}[/cyan] {req_label} - [yellow]{param_type}[/yellow]")
                                    if param_desc:
                                        console.print(f"    {param_desc}")
                        
                        # Show example usage with properly nested structure
                        console.print("\n[bold]Example Usage:[/bold]")
                        example_args = {}
                        if 'properties' in schema_dict:
                            defs = schema_dict.get('$defs', {})
                            for param_name, param_info in schema_dict['properties'].items():
                                # Check if this is a $ref
                                if '$ref' in param_info:
                                    ref_path = param_info['$ref'].split('/')[-1]
                                    if ref_path in defs:
                                        resolved = defs[ref_path]
                                        # Build nested example from resolved properties
                                        nested_example = {}
                                        if 'properties' in resolved:
                                            nested_required = resolved.get('required', [])
                                            for nested_name, nested_info in resolved['properties'].items():
                                                # Only include required fields in example
                                                if nested_name in nested_required:
                                                    nested_type = nested_info.get('type', 'string')
                                                    if nested_type == 'string':
                                                        nested_example[nested_name] = "example_value"
                                                    elif nested_type == 'number' or nested_type == 'integer':
                                                        nested_example[nested_name] = 0
                                                    elif nested_type == 'boolean':
                                                        nested_example[nested_name] = True
                                        example_args[param_name] = nested_example
                                else:
                                    param_type = param_info.get('type', 'string')
                                    if param_type == 'string':
                                        example_args[param_name] = "example_value"
                                    elif param_type == 'number' or param_type == 'integer':
                                        example_args[param_name] = 0
                                    elif param_type == 'boolean':
                                        example_args[param_name] = True
                                    elif param_type == 'array':
                                        example_args[param_name] = []
                                    elif param_type == 'object':
                                        example_args[param_name] = {}
                        
                        example_cmd = f"mcpsh call {server} {tool_name} --args '{json.dumps(example_args)}'"
                        console.print(example_cmd)
                else:
                    console.print("[yellow]No input schema available[/yellow]")
                
        except Exception as e:
            if not verbose:
                restore_logs(stderr_fd, devnull_fd)
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    try:
        asyncio.run(_show_tool_info())
    finally:
        if not verbose:
            restore_logs(stderr_fd, devnull_fd)


@app.command()
def call(
    server: str = typer.Argument(..., help="Name of the MCP server"),
    tool: str = typer.Argument(..., help="Name of the tool to call"),
    args_json: Optional[str] = typer.Option(
        None,
        "--args",
        "-a",
        help="Tool arguments as JSON string"
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to MCP configuration file"
    ),
    format_type: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="Output format: markdown (default) or json"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed server logs"
    )
):
    """
    Call a tool on an MCP server.
    
    Use 'mcpsh tool-info <server> <tool>' to see parameter requirements first.
    
    Examples:
        # Simple tool with no arguments
        mcpsh call my-server list-items
        
        # Tool with simple arguments
        mcpsh call my-server query --args '{"sql": "SELECT * FROM users LIMIT 5"}'
        
        # Tool with nested arguments
        mcpsh call my-server run-query --args '{
          "query_input": {
            "query": "SELECT count(*) FROM table"
          }
        }'
        
        # Output in JSON format (markdown is default)
        mcpsh call my-server my-tool --args '{"param": "value"}' --format json
        mcpsh call my-server my-tool --args '{"param": "value"}' -f json
        
        # Tool with custom config
        mcpsh call my-server my-tool --args '{"param": "value"}' --config ./config.json
    """
    # Suppress server logs by default
    stderr_fd, devnull_fd = (None, None)
    if not verbose:
        stderr_fd, devnull_fd = suppress_logs()
    
    async def _call_tool():
        try:
            servers_config = load_config(config)
            
            if server not in servers_config:
                console.print(f"[red]Server '{server}' not found in configuration[/red]")
                raise typer.Exit(1)
            
            server_config = servers_config[server]
            
            # Parse arguments
            arguments = {}
            if args_json:
                try:
                    arguments = json.loads(args_json)
                except json.JSONDecodeError as e:
                    console.print(f"[red]Invalid JSON in arguments: {e}[/red]")
                    raise typer.Exit(1)
            
            # Create MCPConfig format for Client
            mcp_config = {"mcpServers": {server: server_config}}
            
            with console.status(f"[bold green]Calling tool '{tool}'..."):
                async with Client(mcp_config) as client:
                    # Construct tool name with server prefix if needed
                    tool_name = f"{server}_{tool}" if "_" not in tool else tool
                    
                    # Try with prefix first, then without
                    try:
                        result = await client.call_tool(tool_name, arguments)
                    except Exception:
                        # Try without prefix
                        result = await client.call_tool(tool, arguments)
                    
                    # Display result
                    console.print("[bold green]✓ Tool executed successfully[/bold green]\n")
                    
                    # Show content blocks
                    if result.content:
                        for i, content in enumerate(result.content):
                            if hasattr(content, 'text'):
                                text_content = content.text
                                
                                # Check format type
                                if format_type.lower() == "json":
                                    # Explicit JSON format - print as-is
                                    console.print(text_content)
                                else:
                                    # Default markdown format
                                    try:
                                        # Try to parse as JSON
                                        json_data = json.loads(text_content)
                                        # Convert to markdown
                                        md_output = json_to_markdown(json_data)
                                        # Render the markdown
                                        console.print(Markdown(md_output))
                                    except json.JSONDecodeError:
                                        # If not JSON, just print as-is
                                        console.print(text_content)
                
        except Exception as e:
            if not verbose:
                restore_logs(stderr_fd, devnull_fd)
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    try:
        asyncio.run(_call_tool())
    finally:
        if not verbose:
            restore_logs(stderr_fd, devnull_fd)


@app.command()
def resources(
    server: str = typer.Argument(..., help="Name of the MCP server"),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to MCP configuration file"
    )
):
    """
    List all available resources from a server.
    
    Examples:
        mcpsh resources my-server
        mcpsh resources my-server --config ~/config.json
    """
    async def _list_resources():
        try:
            servers_config = load_config(config)
            
            if server not in servers_config:
                console.print(f"[red]Server '{server}' not found in configuration[/red]")
                raise typer.Exit(1)
            
            server_config = servers_config[server]
            
            # Create MCPConfig format for Client
            mcp_config = {"mcpServers": {server: server_config}}
            
            async with Client(mcp_config) as client:
                resources_list = await client.list_resources()
                
                if not resources_list:
                    console.print(f"[yellow]No resources found on server '{server}'[/yellow]")
                    return
                
                console.print(f"[bold]Resources from '{server}':[/bold]\n")
                for resource in resources_list:
                    console.print(f"  [cyan]{resource.uri}[/cyan]")
                    if resource.name:
                        console.print(f"    Name: {resource.name}")
                    mime = getattr(resource, 'mimeType', None)
                    if mime:
                        console.print(f"    Type: {mime}")
                    console.print()
                
                console.print(f"[dim]Total: {len(resources_list)} resources[/dim]")
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(_list_resources())


@app.command()
def read(
    server: str = typer.Argument(..., help="Name of the MCP server"),
    uri: str = typer.Argument(..., help="Resource URI to read"),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to MCP configuration file"
    )
):
    """
    Read a resource from an MCP server.
    
    Examples:
        mcpsh read my-server "resource://path/to/resource"
        mcpsh read my-server "data://example/info"
        mcpsh read my-server "schema://public/users"
    """
    async def _read_resource():
        try:
            servers_config = load_config(config)
            
            if server not in servers_config:
                console.print(f"[red]Server '{server}' not found in configuration[/red]")
                raise typer.Exit(1)
            
            server_config = servers_config[server]
            
            # Create MCPConfig format for Client
            mcp_config = {"mcpServers": {server: server_config}}
            
            with console.status(f"[bold green]Reading resource '{uri}'..."):
                async with Client(mcp_config) as client:
                    content_list = await client.read_resource(uri)
                    
                    console.print("[bold green]✓ Resource read successfully[/bold green]\n")
                    
                    for i, content in enumerate(content_list):
                        if hasattr(content, 'text'):
                            # Text content
                            console.print(content.text)
                        elif hasattr(content, 'blob'):
                            # Binary content
                            console.print(f"[dim]Binary data: {len(content.blob)} bytes[/dim]")
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(_read_resource())


@app.command()
def info(
    server: str = typer.Argument(..., help="Name of the MCP server"),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to MCP configuration file"
    )
):
    """
    Show detailed information about a server.
    
    Displays server configuration, connection status, and counts of
    available tools, resources, and prompts.
    
    Examples:
        mcpsh info my-server
        mcpsh info my-server --config ~/config.json
    """
    async def _show_info():
        try:
            servers_config = load_config(config)
            
            if server not in servers_config:
                console.print(f"[red]Server '{server}' not found in configuration[/red]")
                raise typer.Exit(1)
            
            server_config = servers_config[server]
            
            # Display server configuration
            console.print(f"[bold cyan]Server Configuration: {server}[/bold cyan]")
            console.print(json.dumps(server_config, indent=2))
            
            # Try to connect and get server info
            mcp_config = {"mcpServers": {server: server_config}}
            
            with console.status("[bold green]Connecting to server..."):
                async with Client(mcp_config) as client:
                    # Ping server
                    await client.ping()
                    
                    # Get counts
                    tools_list = await client.list_tools()
                    resources_list = await client.list_resources()
                    prompts_list = await client.list_prompts()
                    
                    # Display summary
                    console.print("[bold green]✓ Server is responding[/bold green]\n")
                    
                    console.print("[bold]Server Capabilities:[/bold]")
                    console.print(f"  Tools: {len(tools_list)}")
                    console.print(f"  Resources: {len(resources_list)}")
                    console.print(f"  Prompts: {len(prompts_list)}")
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(_show_info())


@app.command()
def prompts(
    server: str = typer.Argument(..., help="Name of the MCP server"),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to MCP configuration file"
    )
):
    """
    List all available prompts from a server.
    
    Examples:
        mcpsh prompts my-server
        mcpsh prompts my-server --config ~/config.json
    """
    async def _list_prompts():
        try:
            servers_config = load_config(config)
            
            if server not in servers_config:
                console.print(f"[red]Server '{server}' not found in configuration[/red]")
                raise typer.Exit(1)
            
            server_config = servers_config[server]
            
            # Create MCPConfig format for Client
            mcp_config = {"mcpServers": {server: server_config}}
            
            async with Client(mcp_config) as client:
                prompts_list = await client.list_prompts()
                
                if not prompts_list:
                    console.print(f"[yellow]No prompts found on server '{server}'[/yellow]")
                    return
                
                console.print(f"[bold]Prompts from '{server}':[/bold]\n")
                for prompt in prompts_list:
                    console.print(f"  [cyan]{prompt.name}[/cyan]")
                    if prompt.description:
                        console.print(f"    {prompt.description}")
                    if prompt.arguments:
                        arg_names = [arg.name for arg in prompt.arguments]
                        console.print(f"    Arguments: {', '.join(arg_names)}")
                    console.print()
                
                console.print(f"[dim]Total: {len(prompts_list)} prompts[/dim]")
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    
    asyncio.run(_list_prompts())


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()

