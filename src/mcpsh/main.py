"""Progressive CLI implementation for mcpsh using Click."""

import asyncio
import json
import logging
import os
import re
import sys
import warnings
from pathlib import Path
from typing import Optional, Union, Dict, List

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.traceback import install as install_rich_traceback

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from mcpsh.config import load_config, list_configured_servers

# Global flag to track if we should show tracebacks
_show_tracebacks = False

console = Console()


def enable_verbose_tracebacks():
    """Enable Rich tracebacks for verbose mode."""
    global _show_tracebacks
    _show_tracebacks = True
    install_rich_traceback(show_locals=False)


def suppress_logs():
    """Suppress all logging output and warnings."""
    warnings.filterwarnings('ignore')
    logging.getLogger().setLevel(logging.CRITICAL)

    for logger_name in ['mcp', 'fastmcp', 'httpx', 'httpcore']:
        logging.getLogger(logger_name).setLevel(logging.CRITICAL)

    original_stderr_fd = os.dup(2)
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull_fd, 2)

    return original_stderr_fd, devnull_fd


def restore_logs(original_stderr_fd, devnull_fd):
    """Restore logging output and warnings."""
    if original_stderr_fd:
        try:
            os.dup2(original_stderr_fd, 2)
            os.close(original_stderr_fd)
        except OSError:
            pass
    if devnull_fd:
        try:
            os.close(devnull_fd)
        except OSError:
            pass


def create_client_with_cleanup(server_config: Dict) -> Client:
    """Create a Client with keep_alive=False for proper subprocess cleanup."""
    command = server_config.get("command")
    args = server_config.get("args", [])
    env = server_config.get("env")

    # Create transport with keep_alive=False to ensure subprocess terminates after use
    transport = StdioTransport(
        command=command,
        args=args,
        env=env,
        keep_alive=False
    )

    return Client(transport)


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


def sanitize_error_message(error: Exception, escape_rich_markup: bool = True) -> str:
    """Sanitize error messages to prevent leaking secrets."""
    error_str = str(error).replace('\n', ' ')

    patterns = [
        (r'(\w+)=([^\s,\}\]]+)', r'\1=***'),
        (r'"(api[_-]?key|token|password|secret|auth|credential|bearer)["\s]*:[^,\}]+', r'"\1": "***"'),
        (r"'([a-zA-Z0-9_-]{20,})'", r"'***'"),
        (r'"([a-zA-Z0-9_-]{20,})"', r'"***"'),
        (r'Bearer\s+[a-zA-Z0-9_-]+', r'Bearer ***'),
        (r'Basic\s+[a-zA-Z0-9+/=]+', r'Basic ***'),
    ]

    sanitized = error_str
    for pattern, replacement in patterns:
        sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

    sanitized = re.sub(r"'env':\s*\{[^}]*\}", "'env': {***}", sanitized)
    sanitized = re.sub(r'"env":\s*\{[^}]*\}', '"env": {***}', sanitized)

    if escape_rich_markup:
        sanitized = sanitized.replace('[', r'\[').replace(']', r'\]')

    return sanitized


# Create Click group
@click.command(context_settings=dict(
    help_option_names=['-h', '--help'],
))
@click.argument('args', nargs=-1)
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to MCP configuration file')
@click.option('--format', '-f', 'format_type', default='markdown', help='Output format: markdown or json')
@click.option('--verbose', '-v', is_flag=True, help='Show detailed logs')
@click.option('--resources', is_flag=True, help='List resources from server')
@click.option('--prompts', is_flag=True, help='List prompts from server')
@click.option('--read', 'read_uri', type=str, help='Read resource URI')
@click.option('--args', '-a', 'args_json', type=str, help='Tool arguments as JSON')
@click.pass_context
def cli(ctx, args, config, format_type, verbose, resources, prompts, read_uri, args_json):
    """
    mcpsh - MCP Shell: Progressive CLI for MCP servers

    \b
    Progressive Usage:
        mcpsh                          # List servers
        mcpsh <server>                 # List tools from server
        mcpsh <server> <tool>          # Show tool info
        mcpsh <server> <tool> --args '{...}'  # Execute tool

    \b
    Special flags:
        mcpsh <server> --resources     # List resources
        mcpsh <server> --prompts       # List prompts
        mcpsh <server> --read <uri>    # Read resource

    \b
    Global options:
        -f, --format json              # Output as JSON
        -h, --help                     # Show help
        -v, --verbose                  # Show detailed logs
    """
    if verbose:
        enable_verbose_tracebacks()

    stderr_fd, devnull_fd = (None, None)
    if not verbose:
        stderr_fd, devnull_fd = suppress_logs()

    try:
        # Convert args tuple to list
        args_list = list(args)

        # Case 1: No arguments - list servers
        if len(args_list) == 0:
            _list_servers(config, format_type)

        # Case 2: One argument (server) - check for special flags or list tools
        elif len(args_list) == 1:
            server = args_list[0]
            if resources:
                _list_resources(server, config, format_type)
            elif prompts:
                _list_prompts(server, config, format_type)
            elif read_uri:
                _read_resource(server, read_uri, config, format_type)
            else:
                _list_tools(server, config, format_type)

        # Case 3: Two arguments (server tool) - show info or execute
        elif len(args_list) == 2:
            server, tool = args_list[0], args_list[1]
            if args_json:
                _execute_tool(server, tool, args_json, config, format_type)
            else:
                _show_tool_info(server, tool, config, format_type)

        else:
            click.echo("Error: Too many arguments", err=True)
            ctx.exit(1)

    finally:
        if not verbose:
            restore_logs(stderr_fd, devnull_fd)


def _list_servers(config: Optional[Path], format_type: str):
    """List all configured servers."""
    try:
        if config:
            config = Path(config)
        servers = list_configured_servers(config)

        if format_type.lower() == "json":
            click.echo(json.dumps(servers))
        else:
            console.print("[bold]Configured MCP Servers:[/bold]\n")
            for name in servers:
                console.print(f"  [cyan]{name}[/cyan]")
            console.print(f"\n[dim]Total: {len(servers)} servers[/dim]")
            console.print(f"\n[dim]Next: mcpsh <server> to see tools[/dim]")

    except Exception as e:
        if format_type.lower() == "json":
            click.echo(json.dumps({"error": sanitize_error_message(e, escape_rich_markup=False)}))
        else:
            console.print(f"[red]Error: {sanitize_error_message(e)}[/red]")
        sys.exit(1)


def _list_tools(server: str, config: Optional[Path], format_type: str):
    """List tools from a server."""
    async def _async_list_tools():
        try:
            if config:
                config_path = Path(config)
            else:
                config_path = None

            servers_config = load_config(config_path)

            if server not in servers_config:
                error_msg = f"Server '{server}' not found in configuration"
                if format_type.lower() == "json":
                    click.echo(json.dumps({"error": error_msg}))
                else:
                    console.print(f"[red]{error_msg}[/red]")
                sys.exit(1)

            server_config = servers_config[server]

            # Create client with keep_alive=False for proper subprocess cleanup
            client = create_client_with_cleanup(server_config)
            async with client:
                tools_list = await client.list_tools()

                if not tools_list:
                    if format_type.lower() == "json":
                        click.echo(json.dumps([]))
                    else:
                        console.print(f"[yellow]No tools found on server '{server}'[/yellow]")
                    return

                if format_type.lower() == "json":
                    tools_json = []
                    for tool in tools_list:
                        tool_dict = {
                            "name": tool.name,
                            "description": tool.description if hasattr(tool, 'description') else None
                        }
                        tools_json.append(tool_dict)
                    click.echo(json.dumps(tools_json))
                else:
                    console.print(f"[bold]Tools from '{server}':[/bold]\n")
                    for tool in tools_list:
                        console.print(f"  [cyan]{tool.name}[/cyan]")
                        if tool.description:
                            console.print(f"    {tool.description}")
                        console.print()

                    console.print(f"[dim]Total: {len(tools_list)} tools[/dim]")
                    console.print(f"\n[dim]Next: mcpsh {server} <tool> to see details[/dim]")

        except Exception as e:
            if format_type.lower() == "json":
                click.echo(json.dumps({"error": sanitize_error_message(e, escape_rich_markup=False)}))
            else:
                console.print(f"[red]Error: {sanitize_error_message(e)}[/red]")
            sys.exit(1)

    asyncio.run(_async_list_tools())


def _show_tool_info(server: str, tool_name: str, config: Optional[Path], format_type: str):
    """Show detailed information about a tool."""
    async def _async_show_info():
        try:
            if config:
                config_path = Path(config)
            else:
                config_path = None

            servers_config = load_config(config_path)

            if server not in servers_config:
                console.print(f"[red]Server '{server}' not found in configuration[/red]")
                sys.exit(1)

            server_config = servers_config[server]

            # Create client with keep_alive=False for proper subprocess cleanup
            client = create_client_with_cleanup(server_config)
            async with client:
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
                    sys.exit(1)

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

                        # Show example usage
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
                                                    elif nested_type in ('number', 'integer'):
                                                        nested_example[nested_name] = 0
                                                    elif nested_type == 'boolean':
                                                        nested_example[nested_name] = True
                                        example_args[param_name] = nested_example
                                else:
                                    param_type = param_info.get('type', 'string')
                                    if param_type == 'string':
                                        example_args[param_name] = "example_value"
                                    elif param_type in ('number', 'integer'):
                                        example_args[param_name] = 0
                                    elif param_type == 'boolean':
                                        example_args[param_name] = True
                                    elif param_type == 'array':
                                        example_args[param_name] = []
                                    elif param_type == 'object':
                                        example_args[param_name] = {}

                        example_cmd = f"mcpsh {server} {tool_name} --args '{json.dumps(example_args)}'"
                        console.print(example_cmd)
                else:
                    console.print("[yellow]No input schema available[/yellow]")

        except Exception as e:
            console.print(f"[red]Error: {sanitize_error_message(e)}[/red]")
            sys.exit(1)

    asyncio.run(_async_show_info())


def _execute_tool(server: str, tool_name: str, args_json: str, config: Optional[Path], format_type: str):
    """Execute a tool with arguments."""
    async def _async_execute():
        try:
            if config:
                config_path = Path(config)
            else:
                config_path = None

            servers_config = load_config(config_path)

            if server not in servers_config:
                error_msg = f"Server '{server}' not found in configuration"
                if format_type.lower() == "json":
                    click.echo(json.dumps({"error": error_msg}))
                else:
                    console.print(f"[red]{error_msg}[/red]")
                sys.exit(1)

            server_config = servers_config[server]

            # Parse arguments
            try:
                arguments = json.loads(args_json)
            except json.JSONDecodeError as e:
                if format_type.lower() == "json":
                    error_msg = f"Invalid JSON in arguments: {sanitize_error_message(e, escape_rich_markup=False)}"
                    click.echo(json.dumps({"error": error_msg}))
                else:
                    error_msg = f"Invalid JSON in arguments: {sanitize_error_message(e)}"
                    console.print(f"[red]{error_msg}[/red]")
                sys.exit(1)

            # Create client with keep_alive=False for proper subprocess cleanup
            client = create_client_with_cleanup(server_config)
            async with client:
                # Construct tool name with server prefix if needed
                full_tool_name = f"{server}_{tool_name}" if "_" not in tool_name else tool_name

                # Try with prefix first, then without
                try:
                    result = await client.call_tool(full_tool_name, arguments)
                except Exception:
                    # Try without prefix
                    result = await client.call_tool(tool_name, arguments)

                # Show content blocks
                if result.content:
                    if format_type.lower() != "json":
                        console.print("[bold green]✓ Tool executed successfully[/bold green]\n")

                    for content in result.content:
                        if hasattr(content, 'text'):
                            text_content = content.text

                            if format_type.lower() == "json":
                                click.echo(text_content)
                            else:
                                try:
                                    json_data = json.loads(text_content)
                                    md_output = json_to_markdown(json_data)
                                    console.print(Markdown(md_output))
                                except json.JSONDecodeError:
                                    console.print(text_content)

        except Exception as e:
            if format_type.lower() == "json":
                error_msg = sanitize_error_message(e, escape_rich_markup=False)
                click.echo(json.dumps({"error": error_msg}))
            else:
                error_msg = sanitize_error_message(e)
                console.print(f"[red]Error: {error_msg}[/red]")
            sys.exit(1)

    asyncio.run(_async_execute())


def _list_resources(server: str, config: Optional[Path], format_type: str):
    """List resources from a server."""
    async def _async_list():
        try:
            if config:
                config_path = Path(config)
            else:
                config_path = None

            servers_config = load_config(config_path)

            if server not in servers_config:
                console.print(f"[red]Server '{server}' not found in configuration[/red]")
                sys.exit(1)

            server_config = servers_config[server]

            # Create client with keep_alive=False for proper subprocess cleanup
            client = create_client_with_cleanup(server_config)
            async with client:
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
            console.print(f"[red]Error: {sanitize_error_message(e)}[/red]")
            sys.exit(1)

    asyncio.run(_async_list())


def _list_prompts(server: str, config: Optional[Path], format_type: str):
    """List prompts from a server."""
    async def _async_list():
        try:
            if config:
                config_path = Path(config)
            else:
                config_path = None

            servers_config = load_config(config_path)

            if server not in servers_config:
                console.print(f"[red]Server '{server}' not found in configuration[/red]")
                sys.exit(1)

            server_config = servers_config[server]

            # Create client with keep_alive=False for proper subprocess cleanup
            client = create_client_with_cleanup(server_config)
            async with client:
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
            console.print(f"[red]Error: {sanitize_error_message(e)}[/red]")
            sys.exit(1)

    asyncio.run(_async_list())


def _read_resource(server: str, uri: str, config: Optional[Path], format_type: str):
    """Read a resource from a server."""
    async def _async_read():
        try:
            if config:
                config_path = Path(config)
            else:
                config_path = None

            servers_config = load_config(config_path)

            if server not in servers_config:
                console.print(f"[red]Server '{server}' not found in configuration[/red]")
                sys.exit(1)

            server_config = servers_config[server]

            # Create client with keep_alive=False for proper subprocess cleanup
            client = create_client_with_cleanup(server_config)
            async with client:
                content_list = await client.read_resource(uri)

                console.print("[bold green]✓ Resource read successfully[/bold green]\n")

                for content in content_list:
                    if hasattr(content, 'text'):
                        console.print(content.text)
                    elif hasattr(content, 'blob'):
                        console.print(f"[dim]Binary data: {len(content.blob)} bytes[/dim]")

        except Exception as e:
            console.print(f"[red]Error: {sanitize_error_message(e)}[/red]")
            sys.exit(1)

    asyncio.run(_async_read())


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
