# mcpsh

A clean, simple command-line interface for interacting with Model Context Protocol (MCP) servers using FastMCP.

**Transform any MCP server into a CLI tool** - perfect for AI agents, automation scripts, and manual operations. Get the rich ecosystem of MCP tools with the simplicity and universality of the command line.

## Features

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

**Example skill using mcpsh:**

```python
# In a skill-mcp skill script
import subprocess
import json

# Query database using mcpsh
result = subprocess.run([
    "mcpsh", "call", "postgres", "query",
    "--args", '{"sql": "SELECT * FROM users WHERE active = true"}',
    "-f", "json"
], capture_output=True, text=True)

data = json.loads(result.stdout.split('\n')[-2])  # Skip success message
# Process data...
```

**More AI Agent Examples:**

```bash
# AI coding assistant queries your database
mcpsh call postgres query --args '{"sql": "SELECT * FROM users WHERE active = true"}'

# AI ops agent checks production metrics  
mcpsh call new-relic run_nrql_query --args '{"query_input": {"nrql": "SELECT count(*) FROM Transaction WHERE appName = 'api' SINCE 1 hour ago"}}'

# AI assistant manages your infrastructure
mcpsh call databricks list_clusters
mcpsh call skill-mcp run_skill_script --args '{"skill_name": "deploy", "script_path": "deploy.py"}'
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
uvx mcpsh servers
uvx mcpsh call <server> <tool> --args '{...}'

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
mcpsh servers
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

### Basic Workflow

```bash
# 1. List your servers
mcpsh servers

# 2. Explore a server
mcpsh info postgres

# 3. List available tools
mcpsh tools postgres

# 4. Get detailed info about a tool
mcpsh tool-info postgres query

# 5. Call a tool
mcpsh call postgres list_tables

# 6. Call a tool with arguments (output in Markdown format by default)
mcpsh call postgres query --args '{"sql": "SELECT * FROM users LIMIT 5"}'

# 7. Get results in JSON format
mcpsh call postgres query --args '{"sql": "SELECT * FROM users LIMIT 5"}' --format json

# 8. Verbose mode - show server logs (for debugging)
mcpsh tools postgres --verbose
```

## Configuration

### Default Configuration Locations

The CLI automatically looks for configuration in this order:
1. Path specified with `--config` flag
2. `~/.mcpsh/mcp_config.json` (recommended default location)
3. `~/Library/Application Support/Claude/claude_desktop_config.json` (Claude Desktop)
4. `~/.cursor/mcp.json` (Cursor MCP config)

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

## Commands

### List Servers

```bash
mcpsh servers [--config PATH] [--verbose]
```

Lists all configured MCP servers with their status.

**Options:**
- `--config`, `-c` - Path to MCP configuration file
- `--verbose`, `-v` - Show detailed server logs (suppressed by default)

### Show Server Info

```bash
mcpsh info <server-name> [--config PATH]
```

Shows detailed information about a server including:
- Server configuration
- Connection status
- Number of tools, resources, and prompts

### List Tools

```bash
mcpsh tools <server-name> [--config PATH] [--detailed] [--verbose]
```

Lists all available tools from a server with their descriptions.

**Options:**
- `--config`, `-c` - Path to MCP configuration file
- `--detailed`, `-d` - Show detailed information including input schemas for all tools
- `--verbose`, `-v` - Show detailed server logs (suppressed by default)

**Examples:**

```bash
# Simple list of tools (clean output by default)
mcpsh tools postgres

# Detailed view with input schemas
mcpsh tools postgres --detailed

# Show server logs for debugging
mcpsh tools postgres --verbose
```

### Get Tool Info

```bash
mcpsh tool-info <server-name> <tool-name> [--config PATH]
```

Shows detailed information about a specific tool including:
- Tool description
- Complete input schema (JSON Schema format)
- Parameter details (required/optional, types, descriptions)
- Example usage command

**Examples:**

```bash
# Get details about a specific tool
mcpsh tool-info new_relic_mcp run_nrql_query

# Check parameter requirements before calling a tool
mcpsh tool-info postgres query
```

### Call a Tool

```bash
mcpsh call <server-name> <tool-name> [--args JSON] [--format FORMAT] [--config PATH] [--verbose]
```

Executes a tool on an MCP server. Output is clean by default (server logs suppressed).

**Options:**
- `--args`, `-a` - Tool arguments as JSON string
- `--config`, `-c` - Path to MCP configuration file
- `--format`, `-f` - Output format: `markdown` (default) or `json`
- `--verbose`, `-v` - Show detailed server logs (suppressed by default)

**Examples:**

```bash
# Simple tool (no arguments)
mcpsh call postgres list_tables

# Tool with arguments
mcpsh call postgres query --args '{"sql": "SELECT * FROM users LIMIT 5"}'

# Complex nested arguments
mcpsh call shippo-new-relic-mcp run_nrql_query --args '{
  "query_input": {
    "nrql": "SELECT count(*) FROM Transaction SINCE 1 hour ago"
  }
}'

# Output in Markdown format (default - more readable):
# ✓ Tool executed successfully
# 
# results:
#   • Item 1: count: 4246161
# query_id: null
# completed: true
# ...

# Output in JSON format (use --format json):
mcpsh call shippo-new-relic-mcp run_nrql_query --args '{
  "query_input": {
    "nrql": "SELECT count(*) FROM Transaction SINCE 1 hour ago"
  }
}' --format json

# Or use shorthand:
mcpsh call postgres query --args '{"sql": "SELECT * FROM users"}' -f json

# Show server logs for debugging
mcpsh call postgres query --args '{"sql": "SELECT * FROM users"}' --verbose
```

### List Resources

```bash
mcpsh resources <server-name> [--config PATH]
```

Lists all available resources from a server.

### Read a Resource

```bash
mcpsh read <server-name> <resource-uri> [--config PATH]
```

Reads and displays the content of a resource.

**Examples:**

```bash
# Read static resource
mcpsh read example "data://example/info"

# Read templated resource
mcpsh read example "data://example/apple"

# Read skill documentation
mcpsh read skill-mcp "skill://data-analysis/SKILL.md"
```

### List Prompts

```bash
mcpsh prompts <server-name> [--config PATH]
```

Lists all available prompts from a server.

## Usage Examples

### Discovering Tool Schemas

Before calling a tool, you can inspect its input schema to understand what arguments it expects:

```bash
# Get detailed info about a specific tool
mcpsh tool-info new_relic_mcp run_nrql_query

# This shows:
# - Tool description
# - Complete JSON schema
# - Parameter details (required/optional)
# - Example usage command

# Now use the tool with correct arguments
mcpsh call new_relic_mcp run_nrql_query --args '{
  "query_input": {
    "nrql": "SELECT count(*) FROM Transaction SINCE 1 hour ago"
  }
}'
```

### Database Operations

```bash
# List database tables
mcpsh call postgres list_tables

# Get table structure
mcpsh call postgres describe_table --args '{"table": "users"}'

# Run a query
mcpsh call postgres query --args '{
  "sql": "SELECT name, email FROM users WHERE active = true ORDER BY created_at DESC LIMIT 5"
}'

# Count records
mcpsh call postgres query --args '{
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
# List available skills
mcpsh tools skill-mcp

# Read skill documentation
mcpsh read skill-mcp "skill://data-analysis/SKILL.md"

# Get skill details
mcpsh call skill-mcp get_skill_details --args '{"skill_name": "data-processor"}'

# Execute a skill script
mcpsh call skill-mcp run_skill_script --args '{
  "skill_name": "data-processor",
  "script_path": "scripts/process.py",
  "args": ["--input", "data/input.csv", "--output", "data/output.json"]
}'
```

**Using mcpsh Inside Skills:**

Skills can use `mcpsh` to access any MCP server, giving them superpowers:

```python
# Example: skill that queries database and sends alerts
# ~/.skill-mcp/skills/db-monitor/scripts/check_health.py

import subprocess
import json

def run_mcpsh(server, tool, args):
    """Helper to run mcpsh and parse JSON output"""
    result = subprocess.run([
        "mcpsh", "call", server, tool,
        "--args", json.dumps(args),
        "-f", "json"
    ], capture_output=True, text=True)
    
    # Skip success message, get JSON
    output = result.stdout.strip().split('\n')[-1]
    return json.loads(output)

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

This approach gives your skills access to:
- Databases (PostgreSQL, MySQL, etc.)
- Monitoring tools (New Relic, Datadog, etc.)
- Cloud platforms (Databricks, AWS, etc.)
- Any MCP server in your config!

### API Exploration

```bash
# List API explorer capabilities
mcpsh tools api-explorer

# Make a GET request
mcpsh call api-explorer make_request --args '{
  "url": "https://jsonplaceholder.typicode.com/posts/1",
  "method": "GET"
}'

# Make a POST request
mcpsh call api-explorer make_request --args '{
  "url": "https://api.example.com/data",
  "method": "POST",
  "body": {"title": "New Item", "completed": false},
  "headers": {"Content-Type": "application/json"}
}'
```

### Monitoring with New Relic

```bash
# List available monitoring tools
mcpsh tools new_relic_mcp

# Query application metrics
mcpsh call new_relic_mcp query_nrql --args '{
  "query": "SELECT average(duration) FROM Transaction WHERE appName = '\''MyApp'\'' SINCE 1 hour ago"
}'

# Get service health
mcpsh call new_relic_mcp get_service_health --args '{
  "service_name": "api-gateway"
}'
```

### Scripting and Automation

The CLI has clean output by default, making it perfect for scripts and automation.

```bash
# Clean output - ready for scripting
mcpsh call shippo-new-relic-mcp run_nrql_query \
  --args '{"query_input":{"nrql":"SELECT count(*) FROM Transaction SINCE 1 hour ago"}}'

# Parse JSON output with jq (skip success message)
RESULT=$(mcpsh call shippo-new-relic-mcp run_nrql_query \
  --args '{"query_input":{"nrql":"SELECT count(*) FROM Transaction SINCE 1 hour ago"}}' \
  | tail -n +3)  # Skip success message and blank line
  
echo "$RESULT" | jq -r '.results[0].count'

# Use in a bash script
#!/bin/bash
TRANSACTION_COUNT=$(mcpsh call shippo-new-relic-mcp run_nrql_query \
  --args '{"query_input":{"nrql":"SELECT count(*) FROM Transaction SINCE 1 hour ago"}}' \
  | tail -n +3 | jq -r '.results[0].count')

echo "Total transactions: $TRANSACTION_COUNT"

# Error handling in scripts
if OUTPUT=$(mcpsh call postgres query \
  --args '{"sql": "SELECT COUNT(*) FROM users"}'); then
  echo "Success: $OUTPUT"
else
  echo "Failed to query database"
  exit 1
fi
```

**Tips for Scripting:**
- Output is clean by default (no server logs or fancy formatting)
- Use `tail -n +3` to skip the success message if you only want the JSON
- Pipe to `jq` for JSON parsing and extraction
- Check exit codes for error handling
- Use `--verbose` flag only when debugging issues

## Advanced Usage

### Custom Configuration Files

```bash
# Development configuration
mcpsh servers --config ./config/dev.json

# Production configuration  
mcpsh servers --config ./config/prod.json

# Testing with example server
mcpsh tools example --config ./example_config.json
```

### Piping and Automation

```bash
# Save tool output to file
mcpsh call postgres query --args '{"sql": "SELECT * FROM users"}' > users.txt

# Use in scripts
#!/bin/bash
TABLES=$(mcpsh call postgres list_tables --args '{}')
echo "Database has these tables: $TABLES"

# Process with other tools
mcpsh call postgres query --args '{"sql": "SELECT * FROM metrics"}' | jq '.[] | select(.value > 100)'
```

### Working with Different Server Types

```bash
# Local Python servers
mcpsh tools example --config example_config.json

# Remote HTTP servers (configure with "url" and "transport": "http")
mcpsh tools remote-api

# NPX/UVX servers (configure with "command": "uvx" or "npx")
mcpsh tools mcp-package-server
```

## Example Server

The repository includes an example MCP server for testing:

### Running the Example

```bash
# In one terminal, start the example server:
python example_server.py

# In another terminal, use the CLI:
mcpsh tools example --config example_config.json
mcpsh call example greet --args '{"name": "World"}'
mcpsh call example add --args '{"a": 5, "b": 3}'
mcpsh resources example --config example_config.json
mcpsh read example "data://example/apple" --config example_config.json
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
mcpsh servers
```

### "Tool not found"

List tools to see the exact name (some servers add prefixes):

```bash
mcpsh tools <server-name>

# Note: Multi-server configs may prefix tool names
# Example: "servername_toolname"
```

### "Invalid JSON"

Ensure your arguments are valid JSON with proper quoting:

```bash
# ✓ Good - single quotes outside, double quotes inside
mcpsh call server tool --args '{"key": "value"}'

# ✗ Bad - missing quotes
mcpsh call server tool --args '{key: value}'
```

### Connection Issues

```bash
# Test server connectivity
mcpsh info <server-name>

# This will show if the server is responding and any errors
```

## Tips and Best Practices

1. **Check tool names first**: Use `mcpsh tools <server>` to see exact names and descriptions
2. **Use valid JSON for arguments**: Single quotes around the JSON, double quotes inside
3. **Start simple**: Test with `servers` and `info` before calling tools
4. **Read descriptions**: Tool and resource descriptions often include usage hints
5. **Test with example server**: Use `example_config.json` to verify the CLI is working
6. **Use custom configs**: Separate configs for different environments (dev, staging, prod)

## Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `servers` | List all configured servers | `mcpsh servers` |
| `info` | Show server details | `mcpsh info postgres` |
| `tools` | List tools from a server | `mcpsh tools postgres` |
| `call` | Execute a tool | `mcpsh call postgres query --args '{"sql":"..."}` |
| `resources` | List resources from a server | `mcpsh resources skill-mcp` |
| `read` | Read a resource | `mcpsh read skill-mcp "skill://..."` |
| `prompts` | List prompts from a server | `mcpsh prompts server-name` |

## Common Patterns

### Exploration Pattern

```bash
# 1. See what servers are available
mcpsh servers

# 2. Check what a server offers
mcpsh info postgres

# 3. Look at specific capabilities
mcpsh tools postgres
mcpsh resources postgres
mcpsh prompts postgres

# 4. Try it out
mcpsh call postgres list_tables
```

### Integration Pattern

```bash
# Use MCP CLI in larger workflows
#!/bin/bash

# Get data from MCP server
DATA=$(mcpsh call postgres query --args '{"sql": "SELECT * FROM metrics"}')

# Process with other tools
echo "$DATA" | jq '.[] | select(.value > 100)'

# Store results
mcpsh call postgres query --args '{"sql": "..."}' > output.json
```

## Getting Help

```bash
# General help
mcpsh --help

# Command-specific help
mcpsh servers --help
mcpsh call --help
mcpsh tools --help
```

## Requirements

- Python 3.10+
- FastMCP 2.12.5+
- Typer 0.20.0+
- Rich 14.2.0+

## Development

### Project Structure

```
mcpsh/
├── src/
│   └── mcp_cli/
│       ├── __init__.py
│       ├── main.py        # CLI commands
│       └── config.py      # Configuration loader
├── example_server.py      # Example MCP server for testing
├── example_config.json    # Example configuration
├── pyproject.toml
└── README.md
```

### Running in Development

```bash
# Install in editable mode
uv pip install -e .

# Run the CLI
mcpsh --help

# Test with example server
python example_server.py  # In one terminal
mcpsh tools example --config example_config.json  # In another
```

## Related Projects

- [FastMCP](https://gofastmcp.com) - The framework used to build this CLI
- [Model Context Protocol](https://modelcontextprotocol.io/) - Official MCP specification
- [Claude Desktop](https://claude.ai/download) - Uses the same configuration format

## License

MIT

## Contributing

Contributions welcome! This is a simple tool focused on making MCP server interaction easy from the command line.
