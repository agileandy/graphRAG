import os
import pytest
from unittest.mock import patch

# Assuming the get_port function is in src/config/ports.py
# Adjust the import path if necessary
try:
    from src.config.ports import get_port
except ImportError:
    pytest.fail(
        "Could not import get_port from src.config.ports. Make sure the file and function exist."
    )


@pytest.fixture(autouse=True)
def cleanup_env_vars():
    """Fixture to clean up environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


def test_get_port_default_api():
    """Test getting the default API port."""
    # Ensure no relevant env var is set
    if "GRAPHRAG_PORT_API" in os.environ:
        del os.environ["GRAPHRAG_PORT_API"]
    # Assuming default API port is 5001 based on Bug 2
    assert get_port("api") == 5001


def test_get_port_env_override_api():
    """Test getting the API port when overridden by environment variable."""
    os.environ["GRAPHRAG_PORT_API"] = "8000"
    assert get_port("api") == 8000


def test_get_port_default_mpc():
    """Test getting the default MPC port."""
    # Ensure no relevant env var is set
    if "GRAPHRAG_PORT_MPC" in os.environ:
        del os.environ["GRAPHRAG_PORT_MPC"]
    # Assuming default MPC port is 8765 based on Bug 13
    assert get_port("mpc") == 8765


def test_get_port_env_override_mpc():
    """Test getting the MPC port when overridden by environment variable."""
    os.environ["GRAPHRAG_PORT_MPC"] = "9000"
    assert get_port("mpc") == 9000


def test_get_port_default_mcp():
    """Test getting the default MCP port."""
    # Ensure no relevant env var is set
    if "GRAPHRAG_PORT_MCP" in os.environ:
        del os.environ["GRAPHRAG_PORT_MCP"]
    # Assuming default MCP port is 8767 based on Bug 11/12
    assert get_port("mcp") == 8767


def test_get_port_env_override_mcp():
    """Test getting the MCP port when overridden by environment variable."""
    os.environ["GRAPHRAG_PORT_MCP"] = "9001"
    assert get_port("mcp") == 9001


def test_get_port_unknown_service():
    """Test getting port for an unknown service."""
    with pytest.raises(ValueError):
        get_port("unknown_service")


def test_get_port_env_non_integer():
    """Test getting port when env var is not an integer."""
    os.environ["GRAPHRAG_PORT_API"] = "abc"
    with pytest.raises(ValueError):
        get_port("api")
