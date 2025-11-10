"""Pytest configuration and fixtures."""

import json
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    config = {
        "mcpServers": {
            "test-server": {
                "command": "python",
                "args": ["-m", "http.server"],
                "env": {"TEST_VAR": "test_value"}
            },
            "another-server": {
                "command": "node",
                "args": ["server.js"]
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        temp_path = f.name
    
    yield Path(temp_path)
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def empty_config_file():
    """Create an empty config file for testing."""
    config = {"mcpServers": {}}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        temp_path = f.name
    
    yield Path(temp_path)
    
    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def invalid_config_file():
    """Create an invalid config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        f.write("invalid json content {{{")
        temp_path = f.name

    yield Path(temp_path)

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture(scope="module")
def everything_config_file():
    """Create a config file with the everything MCP server for integration testing."""
    config = {
        "mcpServers": {
            "everything": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-everything"]
            }
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        temp_path = f.name

    yield Path(temp_path)

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)



