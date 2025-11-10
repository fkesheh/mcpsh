# mcpsh

A progressive CLI and Python API for interacting with Model Context Protocol (MCP) servers using FastMCP.

**Transform any MCP server into a CLI tool** - perfect for AI agents, automation scripts, and manual operations. Get the rich ecosystem of MCP tools with the simplicity and universality of the command line.

## Features

- 🎯 **Progressive Interface** - Natural, intuitive command flow that guides you through discovery
- 🐍 **Python API** - Import directly in Python scripts for programmatic access
- 🚀 **Simple & Fast** - Built with FastMCP for reliable MCP communication
- ⚡ **Zero Install** - Run with `uvx mcpsh` without installation
- 📋 **List & Discover** - Explore tools, resources, and prompts from any MCP server
- 🔍 **Schema Inspection** - View detailed tool schemas and parameter requirements
- 🔧 **Execute Tools** - Call MCP tools directly from the command line
- 📖 **Read Resources** - Access resource data with formatted output
- 🎯 **Clean Output** - Server logs suppressed by default for clean, parseable output
- 📝 **Flexible Formatting** - Output results in JSON or Markdown format
- ⚙️ **Config-Based** - Use standard MCP configuration format (compatible with Claude Desktop)

## Why CLI for MCP?

### 🤖 **Perfect for AI Agent Automation**

While MCP (Model Context Protocol) is powerful, exposing MCP servers through CLI offers critical advantages for AI/LLM agents:

**Reduced Context Overhead**
- MCP requires embedding **every tool's schema** into the LLM's context window
- As you add more MCP tools, the context bloats and model performance degrades
- CLI invocation is lean - just command names and simple arguments
- **Result**: Your AI agent can access more tools without hitting context limits

**Universal LLM Support**  
- **Any LLM that can execute shell commands** can use these tools
- Works with Claude, GPT-4, local models, Cursor, Aider, and custom agents
- No need for MCP-specific integration or protocol support
- **Result**: Use the same tools across all your AI coding assistants

**Simpler, More Reliable Function Calling**
- LLMs generate CLI commands more reliably than complex protocol calls
- Familiar bash syntax reduces hallucination and errors
- Standard input/output makes debugging trivial
- **Result**: Higher success rates and fewer agent failures

**Use in Claude Skills & skill-mcp**

Claude Skills allow you to upload code that Claude can execute. However, **[skill-mcp](https://github.com/fkesheh/skill-mcp)** provides a superior approach using MCP:

- ✅ **Not locked to Claude** - Skills work in Claude, Cursor, and any MCP client
- ✅ **No manual uploads** - Manage skills programmatically via MCP
- ✅ **Better tool access** - Use `mcpsh` in your skills to access databases, APIs, monitoring tools, etc.
- ✅ **Universal & future-proof** - MCP protocol vs proprietary Claude feature

**Example skill using mcpsh CLI:**

```python
# In a skill-mcp skill script
import subprocess
import json

# Query database using mcpsh progressive CLI
result = subprocess.run([
    "mcpsh", "postgres", "query",
    "--args", '{"sql": "SELECT * FROM users WHERE active = true"}',
    "-f", "json"
], capture_output=True, text=True)

data = json.loads(result.stdout)  # Pure JSON output - no need to skip lines!
# Process data...
```

**Even better - use the Python API:**

```python
# In a skill-mcp skill script
from mcpsh import call_tool

# Query database - much cleaner!
data = call_tool("postgres", "query",
    {"sql": "SELECT * FROM users WHERE active = true"},
    parse_json=True)
# Process data...
```

**More AI Agent Examples:**

```bash
# AI coding assistant queries your database
mcpsh postgres query --args '{"sql": "SELECT * FROM users WHERE active = true"}'

# AI ops agent checks production metrics
mcpsh new-relic run_nrql_query --args '{"query_input": {"nrql": "SELECT count(*) FROM Transaction WHERE appName = 'api' SINCE 1 hour ago"}}'

# AI assistant manages your infrastructure
mcpsh databricks list_clusters --args '{}'
mcpsh skill-mcp run_skill_script --args '{"skill_name": "deploy", "script_path": "deploy.py"}'
```

### 🌉 **Bridge Between Worlds**

Get the **best of both**:
- Access the rich ecosystem of MCP servers (databases, APIs, monitoring, etc.)
- Use them with the simplicity and universality of CLI tools  
- Perfect for [skill-mcp](https://github.com/fkesheh/skill-mcp) skills - combine MCP tool access with skill execution
- No need to choose - MCP servers become CLI tools!

## Quick Start

### Installation

```bash
# Option 1: Run directly with uvx (no installation required)
uvx mcpsh
uvx mcpsh <server> <tool> --args '{...}'

# Option 2: Install from PyPI
pip install mcpsh
# or using uv
uv pip install mcpsh

# Option 3: Install from source
git clone https://github.com/fkesheh/mcpsh
cd mcpsh
uv pip install -e .
```

### Setup Configuration

#### Option 1: Use Existing Claude Desktop Config

If you already have Claude Desktop installed and configured, the CLI will automatically use it:

```bash
mcpsh
```

#### Option 2: Create Custom Configuration

Create a `~/.mcpsh/mcp_config.json` file in your home directory:

```bash
# Create the directory
mkdir -p ~/.mcpsh

# Create the config file
cat > ~/.mcpsh/mcp_config.json << 'EOF'
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["path/to/server.py"]
    }
  }
}
EOF
```

### Progressive CLI Workflow

The CLI uses a progressive interface - each command level adds more context:

```bash
# 1. Start with no arguments - see available servers
mcpsh

# 2. Add server name - see available tools
mcpsh postgres

# 3. Add tool name - see tool info and example usage
mcpsh postgres query

# 4. Add arguments - execute the tool
mcpsh postgres query --args '{"sql": "SELECT * FROM users LIMIT 5"}'

# Use -f json for pure JSON output (perfect for scripting)
mcpsh postgres query --args '{"sql": "SELECT * FROM users LIMIT 5"}' -f json

# Get help at any level with -h
mcpsh -h
mcpsh postgres -h
mcpsh postgres query -h
```

### Python API Workflow

Import mcpsh directly in Python scripts for programmatic access:

```python
from mcpsh import MCPClient, call_tool, list_tools

# Option 1: Use convenience functions (simplest)
result = call_tool("postgres", "query", {"sql": "SELECT * FROM users LIMIT 5"})
tools = list_tools("postgres")

# Option 2: Use MCPClient for more control
with MCPClient("postgres") as client:
    tools = client.list_tools()
    result = client.call_tool("query", {"sql": "SELECT * FROM users"})

    # Parse JSON results automatically
    data = client.call_tool("query", {"sql": "SELECT * FROM users"}, parse_json=True)
    print(data["users"][0])

# Async support
import asyncio

async def main():
    async with MCPClient("postgres") as client:
        result = await client.call_tool("query", {"sql": "SELECT * FROM users"})

asyncio.run(main())
```

## Configuration

### Default Configuration Locations

The CLI automatically looks for configuration in this priority order:
1. Path specified with `--config` flag
2. `MCPSH_CONFIG` environment variable
3. `~/.mcpsh/mcp_config.json` (recommended default location)
4. `~/Library/Application Support/Claude/claude_desktop_config.json` (Claude Desktop)
5. `~/.cursor/mcp.json` (Cursor MCP config)

**Pro Tip:** Set the `MCPSH_CONFIG` environment variable to avoid using `--config` flag on every command:

```bash
# Add to your ~/.bashrc, ~/.zshrc, or ~/.profile
export MCPSH_CONFIG=~/.mcpsh/mcp_config.json

# Or use Claude Desktop's config
export MCPSH_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Check which config is being used
mcpsh config-path
```

### Configuration Format

The CLI supports the standard MCP configuration format:

```json
{
  "mcpServers": {
    "local-server": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "API_KEY": "your-api-key-here"
      }
    },
    "remote-server": {
      "url": "https://example.com/mcp",
      "transport": "http",
      "headers": {
        "Authorization": "Bearer your-token-here"
      }
    },
    "package-server": {
      "command": "uvx",
      "args": ["--from", "some-mcp-package", "mcp-server-command"]
    }
  }
}
```

## Progressive CLI Commands

The progressive CLI adapts based on the number of arguments you provide:

### No Arguments - List Servers

```bash
mcpsh [--config PATH] [-f FORMAT]
```

Lists all configured MCP servers with their status.

**Examples:**

```bash
# List servers in Markdown format (default)
mcpsh

# List servers in JSON format
mcpsh -f json

# Use custom config
mcpsh --config ./my_config.json
```

### One Argument - List Tools

```bash
mcpsh <server-name> [--config PATH] [-f FORMAT] [--resources] [--prompts]
```

Lists all available tools from a server.

**Options:**
- `--resources` - List resources instead of tools
- `--prompts` - List prompts instead of tools

**Examples:**

```bash
# List tools from a server
mcpsh postgres

# List tools in JSON format
mcpsh postgres -f json

# List resources instead
mcpsh postgres --resources

# List prompts
mcpsh postgres --prompts
```

### Two Arguments - Show Tool Info or Execute

```bash
mcpsh <server-name> <tool-name> [--args JSON] [--config PATH] [-f FORMAT]
```

Without `--args`: Shows detailed tool information including parameters and example usage.

With `--args`: Executes the tool with the provided arguments.

**Examples:**

```bash
# Get detailed info about a tool
mcpsh postgres query

# Execute tool with arguments
mcpsh postgres query --args '{"sql": "SELECT * FROM users LIMIT 5"}'

# Execute with JSON output (perfect for scripting)
mcpsh postgres query --args '{"sql": "SELECT * FROM users"}' -f json

# Complex nested arguments
mcpsh new-relic run_nrql_query --args '{
  "query_input": {
    "nrql": "SELECT count(*) FROM Transaction SINCE 1 hour ago"
  }
}'
```

### Special Flags Available at All Levels

**Common Options:**
- `--config`, `-c` - Path to MCP configuration file
- `--format`, `-f` - Output format: `markdown` (default) or `json`
- `--help`, `-h` - Show help message

**Examples:**

```bash
# Get help at any level
mcpsh -h
mcpsh postgres -h
mcpsh postgres query -h

# Use JSON format at any level
mcpsh -f json
mcpsh postgres -f json
mcpsh postgres query --args '{"sql": "SELECT 1"}' -f json
```

### Resource Operations

Resources are accessed using special flags:

**CLI:**

```bash
# List resources from a server
mcpsh <server-name> --resources

# Read a specific resource
mcpsh <server-name> --read <resource-uri>

# List prompts from a server
mcpsh <server-name> --prompts
```

**Examples:**

```bash
# List all resources
mcpsh skill-mcp --resources

# Read specific resource
mcpsh skill-mcp --read "skill://data-analysis/SKILL.md"

# List prompts
mcpsh skill-mcp --prompts

# Works with -f json too
mcpsh skill-mcp --resources -f json
```

**Python API:**

```python
from mcpsh import MCPClient, list_resources, read_resource

# Use convenience functions
resources = list_resources("skill-mcp")
content = read_resource("skill-mcp", "skill://data-analysis/SKILL.md")

# Or use MCPClient
with MCPClient("skill-mcp") as client:
    resources = client.list_resources()
    content = client.read_resource("skill://data-analysis/SKILL.md")
    prompts = client.list_prompts()
```

## Usage Examples

### Discovering Tool Schemas

The progressive interface guides you through tool discovery:

```bash
# 1. See what tools are available
mcpsh new-relic

# 2. Get detailed info about a specific tool
mcpsh new-relic run_nrql_query

# This shows:
# - Tool description
# - Parameter details (required/optional, types, descriptions)
# - Nested parameter structures
# - Example usage command

# 3. Copy the example and modify it
mcpsh new-relic run_nrql_query --args '{
  "query_input": {
    "nrql": "SELECT count(*) FROM Transaction SINCE 1 hour ago"
  }
}'
```

### Database Operations

```bash
# List database tools
mcpsh postgres

# List database tables
mcpsh postgres list_tables --args '{}'

# Get table structure
mcpsh postgres describe_table --args '{"table": "users"}'

# Run a query
mcpsh postgres query --args '{
  "sql": "SELECT name, email FROM users WHERE active = true ORDER BY created_at DESC LIMIT 5"
}'

# Count records
mcpsh postgres query --args '{
  "sql": "SELECT COUNT(*) as total FROM orders WHERE status = '\''completed'\''"
}'
```

### Skill Management with skill-mcp

[skill-mcp](https://github.com/fkesheh/skill-mcp) is an MCP server that lets you create, manage, and execute skills programmatically. It's superior to Claude Skills because it:

- ✅ Works in Claude, Cursor, and any MCP client (not locked to Claude)
- ✅ No manual file uploads - manage skills via MCP protocol
- ✅ Skills can use `mcpsh` to access any MCP server (databases, APIs, etc.)
- ✅ Local-first, future-proof, and open standard

**Managing Skills:**

```bash
# List available skill tools
mcpsh skill-mcp

# Read skill documentation
mcpsh skill-mcp --read-uri "skill://data-analysis/SKILL.md"

# Get skill details
mcpsh skill-mcp get_skill_details --args '{"skill_name": "data-processor"}'

# Execute a skill script
mcpsh skill-mcp run_skill_script --args '{
  "skill_name": "data-processor",
  "script_path": "scripts/process.py",
  "args": ["--input", "data/input.csv", "--output", "data/output.json"]
}'
```

**Using mcpsh Inside Skills (CLI approach):**

Skills can use the `mcpsh` CLI to access any MCP server:

```python
# Example: skill that queries database and sends alerts
# ~/.skill-mcp/skills/db-monitor/scripts/check_health.py

import subprocess
import json

def run_mcpsh(server, tool, args):
    """Helper to run mcpsh and parse JSON output"""
    result = subprocess.run([
        "mcpsh", server, tool,
        "--args", json.dumps(args),
        "-f", "json"
    ], capture_output=True, text=True)

    # Pure JSON output - no need to skip lines!
    return json.loads(result.stdout)

# Query database
users = run_mcpsh("postgres", "query", {
    "sql": "SELECT COUNT(*) as count FROM users WHERE last_login < NOW() - INTERVAL '30 days'"
})

# Check metrics
metrics = run_mcpsh("new-relic", "run_nrql_query", {
    "query_input": {
        "nrql": "SELECT average(duration) FROM Transaction SINCE 1 hour ago"
    }
})

# Send alert if needed
if users['count'] > 100:
    print(f"Alert: {users['count']} inactive users found")
```

**Using mcpsh Python API Inside Skills (recommended):**

Even better - use the Python API directly:

```python
# Example: skill that queries database and sends alerts
# ~/.skill-mcp/skills/db-monitor/scripts/check_health.py

from mcpsh import call_tool

# Query database - much simpler!
users = call_tool("postgres", "query", {
    "sql": "SELECT COUNT(*) as count FROM users WHERE last_login < NOW() - INTERVAL '30 days'"
}, parse_json=True)

# Check metrics
metrics = call_tool("new-relic", "run_nrql_query", {
    "query_input": {
        "nrql": "SELECT average(duration) FROM Transaction SINCE 1 hour ago"
    }
}, parse_json=True)

# Send alert if needed
if users['results'][0]['count'] > 100:
    print(f"Alert: {users['results'][0]['count']} inactive users found")
```

This approach gives your skills access to:
- Databases (PostgreSQL, MySQL, etc.)
- Monitoring tools (New Relic, Datadog, etc.)
- Cloud platforms (Databricks, AWS, etc.)
- Any MCP server in your config!

### API Exploration

```bash
# List API explorer capabilities
mcpsh api-explorer

# Make a GET request
mcpsh api-explorer make_request --args '{
  "url": "https://jsonplaceholder.typicode.com/posts/1",
  "method": "GET"
}'

# Make a POST request
mcpsh api-explorer make_request --args '{
  "url": "https://api.example.com/data",
  "method": "POST",
  "body": {"title": "New Item", "completed": false},
  "headers": {"Content-Type": "application/json"}
}'
```

### Monitoring with New Relic

```bash
# List available monitoring tools
mcpsh new-relic

# Query application metrics
mcpsh new-relic query_nrql --args '{
  "query": "SELECT average(duration) FROM Transaction WHERE appName = '\''MyApp'\'' SINCE 1 hour ago"
}'

# Get service health
mcpsh new-relic get_service_health --args '{
  "service_name": "api-gateway"
}'
```

### Scripting and Automation

**Using the CLI in Bash Scripts:**

```bash
# Pure JSON output - perfect for scripting (use -f json)
mcpsh new-relic run_nrql_query \
  --args '{"query_input":{"nrql":"SELECT count(*) FROM Transaction SINCE 1 hour ago"}}' \
  -f json

# Parse JSON output with jq - pure JSON, no need to skip lines!
RESULT=$(mcpsh new-relic run_nrql_query \
  --args '{"query_input":{"nrql":"SELECT count(*) FROM Transaction SINCE 1 hour ago"}}' \
  -f json)

echo "$RESULT" | jq -r '.results[0].count'

# Use in a bash script
#!/bin/bash
TRANSACTION_COUNT=$(mcpsh new-relic run_nrql_query \
  --args '{"query_input":{"nrql":"SELECT count(*) FROM Transaction SINCE 1 hour ago"}}' \
  -f json | jq -r '.results[0].count')

echo "Total transactions: $TRANSACTION_COUNT"

# Error handling in scripts
if OUTPUT=$(mcpsh postgres query \
  --args '{"sql": "SELECT COUNT(*) FROM users"}'); then
  echo "Success: $OUTPUT"
else
  echo "Failed to query database"
  exit 1
fi
```

**Using the Python API in Scripts (Recommended):**

```python
#!/usr/bin/env python3
from mcpsh import call_tool, MCPClient

# Simple one-off calls
result = call_tool("postgres", "query", {"sql": "SELECT COUNT(*) FROM users"}, parse_json=True)
print(f"Total users: {result}")

# Multiple calls with context manager (reuses connection)
with MCPClient("new-relic") as client:
    # Check transaction count
    transactions = client.call_tool("run_nrql_query", {
        "query_input": {"nrql": "SELECT count(*) FROM Transaction SINCE 1 hour ago"}
    }, parse_json=True)

    # Check error rate
    errors = client.call_tool("run_nrql_query", {
        "query_input": {"nrql": "SELECT count(*) FROM TransactionError SINCE 1 hour ago"}
    }, parse_json=True)

    print(f"Transactions: {transactions['results'][0]['count']}")
    print(f"Errors: {errors['results'][0]['count']}")
```

**Tips for Scripting:**
- Use `-f json` for pure JSON output (no extra messages)
- JSON output can be directly piped to `jq` or parsed with `json.loads()` - no preprocessing needed!
- Markdown format (default) includes success messages and formatting for human readability
- Pipe to `jq` for JSON parsing and extraction
- Check exit codes for error handling
- Use `--verbose` flag only when debugging issues

## Advanced Usage

### Custom Configuration Files

```bash
# Development configuration
mcpsh --config ./config/dev.json

# Production configuration
mcpsh --config ./config/prod.json

# Testing with example server
mcpsh example --config ./example_config.json
```

### Piping and Automation

```bash
# Save tool output to file
mcpsh postgres query --args '{"sql": "SELECT * FROM users"}' > users.txt

# Use in scripts
#!/bin/bash
TABLES=$(mcpsh postgres list_tables --args '{}')
echo "Database has these tables: $TABLES"

# Process with other tools (use -f json for clean output)
mcpsh postgres query --args '{"sql": "SELECT * FROM metrics"}' -f json | jq '.[] | select(.value > 100)'
```

### Working with Different Server Types

```bash
# Local Python servers
mcpsh example --config example_config.json

# Remote HTTP servers (configure with "url" and "transport": "http")
mcpsh remote-api

# NPX/UVX servers (configure with "command": "uvx" or "npx")
mcpsh mcp-package-server
```

## Example Server

The repository includes an example MCP server for testing:

### Running the Example

```bash
# In one terminal, start the example server:
python example_server.py

# In another terminal, use the progressive CLI:
mcpsh example --config example_config.json
mcpsh example greet --args '{"name": "World"}'
mcpsh example add --args '{"a": 5, "b": 3}'
mcpsh example --resources --config example_config.json
mcpsh example --read "data://example/apple" --config example_config.json
mcpsh example --prompts --config example_config.json
```

The example server provides:
- **Tools**: `greet`, `add`, `multiply`
- **Resources**: `data://example/info`, `data://example/{item}` (template)
- **Prompts**: `analyze_data`

## Troubleshooting

### "Server not found"

Make sure the server name matches exactly what's in your configuration:

```bash
# List servers to see exact names
mcpsh
```

### "Tool not found"

List tools to see the exact name (some servers add prefixes):

```bash
mcpsh <server-name>

# Note: Multi-server configs may prefix tool names
# Example: "servername_toolname"
```

### "Invalid JSON"

Ensure your arguments are valid JSON with proper quoting:

```bash
# ✓ Good - single quotes outside, double quotes inside
mcpsh server tool --args '{"key": "value"}'

# ✗ Bad - missing quotes
mcpsh server tool --args '{key: value}'
```

### Connection Issues

```bash
# Test server connectivity by listing tools
mcpsh <server-name>

# This will show if the server is responding and any errors
```

## Tips and Best Practices

1. **Follow the progressive pattern**: Start with `mcpsh`, then add server, then tool, then args
2. **Use `-h` for help at any level**: Get contextual help as you build your command
3. **Check tool info before executing**: Run `mcpsh <server> <tool>` to see parameters and examples
4. **Use valid JSON for arguments**: Single quotes around the JSON, double quotes inside
5. **Use `-f json` for scripting**: Get pure JSON output perfect for pipes and parsing
6. **Try the Python API**: Cleaner code, better error handling, connection reuse
7. **Test with example server**: Use `example_config.json` to verify the CLI is working
8. **Use custom configs**: Separate configs for different environments (dev, staging, prod)

## Progressive Command Reference

The CLI uses a progressive interface where commands build on each other:

| Arguments | Action | Example |
|-----------|--------|---------|
| None | List servers | `mcpsh` |
| `<server>` | List tools | `mcpsh postgres` |
| `<server> <tool>` | Show tool info | `mcpsh postgres query` |
| `<server> <tool> --args` | Execute tool | `mcpsh postgres query --args '{"sql":"..."}'` |

**Special Flags (available at any level):**

| Flag | Description | Example |
|------|-------------|---------|
| `-f json` | JSON output | `mcpsh -f json` |
| `-h` | Show help | `mcpsh postgres -h` |
| `--resources` | List resources | `mcpsh skill-mcp --resources` |
| `--prompts` | List prompts | `mcpsh postgres --prompts` |
| `--read <uri>` | Read resource | `mcpsh skill-mcp --read "skill://..."` |
| `--config <path>` | Custom config | `mcpsh --config ./config.json` |

## Common Patterns

### Exploration Pattern

```bash
# 1. See what servers are available
mcpsh

# 2. Check what a server offers
mcpsh postgres

# 3. Look at specific capabilities
mcpsh postgres --resources
mcpsh postgres --prompts

# 4. Get tool details
mcpsh postgres query

# 5. Try it out
mcpsh postgres query --args '{"sql": "SELECT 1"}'
```

### Integration Pattern (CLI)

```bash
# Use MCP CLI in larger workflows
#!/bin/bash

# Get data from MCP server
DATA=$(mcpsh postgres query --args '{"sql": "SELECT * FROM metrics"}' -f json)

# Process with other tools
echo "$DATA" | jq '.[] | select(.value > 100)'

# Store results
mcpsh postgres query --args '{"sql": "..."}' > output.json
```

### Integration Pattern (Python API)

```python
#!/usr/bin/env python3
from mcpsh import MCPClient

# Reuse connection for multiple operations
with MCPClient("postgres") as client:
    # Get data
    metrics = client.call_tool("query",
        {"sql": "SELECT * FROM metrics"},
        parse_json=True)

    # Process with Python
    high_values = [m for m in metrics if m['value'] > 100]

    # Store results
    import json
    with open('output.json', 'w') as f:
        json.dump(high_values, f)
```

## Getting Help

The progressive interface supports help at every level:

```bash
# General help
mcpsh --help
mcpsh -h

# Server-level help
mcpsh postgres --help
mcpsh postgres -h

# Tool-level help
mcpsh postgres query --help
mcpsh postgres query -h
```

## Python API Reference

Import mcpsh for programmatic access:

```python
from mcpsh import (
    MCPClient,      # Main client class
    list_servers,   # List configured servers
    list_tools,     # List tools from a server
    call_tool,      # Execute a tool
    list_resources, # List resources
    read_resource,  # Read a resource
)

# All functions support both sync and async
# Use MCPClient for connection reuse across multiple calls
```

## Requirements

- Python 3.10+
- FastMCP 2.12.5+
- Click 8.0.0+
- Rich 14.2.0+

## Development

### Project Structure

```
mcpsh/
├── src/
│   └── mcpsh/
│       ├── __init__.py    # Package exports (Python API)
│       ├── main.py        # Progressive CLI implementation
│       ├── client.py      # Python API for importing
│       └── config.py      # Configuration loader
├── tests/
│   ├── test_main.py       # CLI tests
│   └── test_client.py     # Python API tests
├── example_server.py      # Example MCP server for testing
├── example_config.json    # Example configuration
├── pyproject.toml
└── README.md
```

### Running in Development

```bash
# Install in editable mode
uv pip install -e .

# Run tests
uv run pytest

# Run the CLI
mcpsh --help
mcpsh

# Test with example server
python example_server.py  # In one terminal
mcpsh example --config example_config.json  # In another
```

## Related Projects

- [FastMCP](https://gofastmcp.com) - The framework used to build this CLI
- [Model Context Protocol](https://modelcontextprotocol.io/) - Official MCP specification
- [Claude Desktop](https://claude.ai/download) - Uses the same configuration format

## License

MIT

## Contributing

Contributions welcome! This is a simple tool focused on making MCP server interaction easy from the command line.
