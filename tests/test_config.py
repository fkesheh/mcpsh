"""Tests for config loading and parsing."""

import json
import tempfile
from pathlib import Path

import pytest

from mcpsh.config import load_config, list_configured_servers


def test_load_config_from_file(temp_config_file):
    """Test loading config from a specified file."""
    config = load_config(temp_config_file)
    
    assert "test-server" in config
    assert "another-server" in config
    assert config["test-server"]["command"] == "python"
    assert config["test-server"]["args"] == ["-m", "http.server"]


def test_load_config_empty(empty_config_file):
    """Test loading an empty config file."""
    config = load_config(empty_config_file)
    
    assert config == {}
    assert isinstance(config, dict)


def test_load_config_invalid_json(invalid_config_file):
    """Test that invalid JSON raises an error."""
    with pytest.raises(Exception):
        load_config(invalid_config_file)


def test_load_config_nonexistent_file():
    """Test loading config from nonexistent file raises error."""
    with pytest.raises(Exception):
        load_config(Path("/nonexistent/path/config.json"))


def test_list_configured_servers(temp_config_file):
    """Test listing server names from config."""
    servers = list_configured_servers(temp_config_file)
    
    assert len(servers) == 2
    assert "test-server" in servers
    assert "another-server" in servers
    assert isinstance(servers, list)


def test_list_configured_servers_empty(empty_config_file):
    """Test listing servers from empty config."""
    servers = list_configured_servers(empty_config_file)
    
    assert len(servers) == 0
    assert isinstance(servers, list)


def test_config_with_env_vars(temp_config_file):
    """Test that environment variables are preserved in config."""
    config = load_config(temp_config_file)
    
    assert "env" in config["test-server"]
    assert config["test-server"]["env"]["TEST_VAR"] == "test_value"


def test_config_server_without_env():
    """Test config with server that has no env vars."""
    config_data = {
        "mcpServers": {
            "simple-server": {
                "command": "python",
                "args": ["server.py"]
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        temp_path = Path(f.name)
    
    try:
        config = load_config(temp_path)
        assert "simple-server" in config
        assert "env" not in config["simple-server"]
    finally:
        temp_path.unlink(missing_ok=True)

