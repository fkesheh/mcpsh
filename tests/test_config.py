"""Tests for config loading and parsing."""

import json
import os
import tempfile
from pathlib import Path

import pytest

from mcpsh.config import load_config, list_configured_servers, get_config_path


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


class TestGetConfigPath:
    """Tests for get_config_path() function and priority chain."""

    def test_explicit_config_path_has_highest_priority(self, temp_config_file):
        """Test that --config flag (explicit path) has highest priority."""
        # Set environment variable
        os.environ["MCPSH_CONFIG"] = "/some/other/path.json"

        try:
            resolved_path, source = get_config_path(temp_config_file)

            assert resolved_path == temp_config_file
            assert source == "--config flag"
        finally:
            # Cleanup
            os.environ.pop("MCPSH_CONFIG", None)

    def test_env_var_has_second_priority(self, temp_config_file):
        """Test that MCPSH_CONFIG env var has second priority (after explicit path)."""
        os.environ["MCPSH_CONFIG"] = str(temp_config_file)

        try:
            resolved_path, source = get_config_path(None)

            assert resolved_path == temp_config_file
            assert source == "MCPSH_CONFIG environment variable"
        finally:
            # Cleanup
            os.environ.pop("MCPSH_CONFIG", None)

    def test_env_var_with_tilde_expansion(self):
        """Test that MCPSH_CONFIG env var expands ~ to home directory."""
        # Create a temp file in home directory for testing
        home_dir = Path.home()
        test_file = home_dir / ".test_mcpsh_config.json"

        config_data = {"mcpServers": {"test": {"command": "python"}}}
        with open(test_file, 'w') as f:
            json.dump(config_data, f)

        # Use tilde notation in env var
        os.environ["MCPSH_CONFIG"] = "~/.test_mcpsh_config.json"

        try:
            resolved_path, source = get_config_path(None)

            assert resolved_path == test_file
            assert resolved_path.exists()
            assert source == "MCPSH_CONFIG environment variable"
        finally:
            # Cleanup
            os.environ.pop("MCPSH_CONFIG", None)
            test_file.unlink(missing_ok=True)

    def test_env_var_nonexistent_file_falls_back(self):
        """Test that nonexistent MCPSH_CONFIG falls back to default locations."""
        os.environ["MCPSH_CONFIG"] = "/nonexistent/config.json"

        try:
            resolved_path, source = get_config_path(None)

            # Should fall back to default location
            # (Not testing which specific fallback, just that it doesn't use the env var)
            assert source != "MCPSH_CONFIG environment variable"
        finally:
            # Cleanup
            os.environ.pop("MCPSH_CONFIG", None)

    def test_default_location_priority_chain(self):
        """Test the default location fallback chain."""
        # Make sure no env var is set
        os.environ.pop("MCPSH_CONFIG", None)

        resolved_path, source = get_config_path(None)

        # Should return one of the default locations
        # The exact location depends on what exists on the system
        assert source in [
            "default location (~/.mcpsh/mcp_config.json)",
            "Claude Desktop config",
            "Cursor config",
            "default location (not found)"
        ]

    def test_returns_tuple_with_path_and_source(self, temp_config_file):
        """Test that get_config_path returns a tuple of (Path, str)."""
        resolved_path, source = get_config_path(temp_config_file)

        assert isinstance(resolved_path, Path)
        assert isinstance(source, str)
        assert len(source) > 0

