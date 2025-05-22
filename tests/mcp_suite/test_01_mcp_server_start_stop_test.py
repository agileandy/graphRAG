"""Test server start/stop functionality for the MCP server."""

import pytest
from tests.common_utils.test_utils import (
    print_test_result,
    sync_mcp_connection,
    run_pytest_async
)

def test_server_start() -> None:
    """Test if the MCP server is running and accessible."""
    print("\nTesting MCP server start...")

    success, message = sync_mcp_connection()

    print_test_result(
        "MCP Server Start",
        success,
        f"Connection test result: {message}"
    )

def test_server_response() -> None:
    """Test if the MCP server responds to basic ping."""
    print("\nTesting MCP server response...")

    # Test with shorter timeout for quick response check
    success, message = sync_mcp_connection(timeout=2)

    if not success:
        print_test_result(
            "MCP Server Response",
            False,
            f"Server not responding: {message}"
        )
        return

    print_test_result(
        "MCP Server Response",
        True,
        "Server responded to ping successfully"
    )

def test_server_timeout() -> None:
    """Test server timeout handling."""
    print("\nTesting MCP server timeout handling...")

    # Test with very short timeout
    success, message = sync_mcp_connection(timeout=1)

    # Should fail with timeout
    if success:
        print_test_result(
            "MCP Server Timeout",
            False,
            "Server responded despite very short timeout"
        )
        return

    if "timeout" not in message.lower():
        print_test_result(
            "MCP Server Timeout",
            False,
            f"Unexpected error message: {message}"
        )
        return

    print_test_result(
        "MCP Server Timeout",
        True,
        "Timeout handled correctly"
    )

def test_invalid_port() -> None:
    """Test connecting to invalid port."""
    print("\nTesting invalid port connection...")

    # Test connection to invalid port
    success, message = sync_mcp_connection(port=9999)

    # Should fail with connection error
    if success:
        print_test_result(
            "Invalid Port Test",
            False,
            "Connection succeeded on invalid port"
        )
        return

    if "connection failed" not in message.lower():
        print_test_result(
            "Invalid Port Test",
            False,
            f"Unexpected error message: {message}"
        )
        return

    print_test_result(
        "Invalid Port Test",
        True,
        "Invalid port handled correctly"
    )

if __name__ == "__main__":
    run_pytest_async(__file__)