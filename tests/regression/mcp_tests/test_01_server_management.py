import pytest
import time
from tests.regression.test_utils import start_services, stop_services, test_mcp_connection

def test_start_stop_servers():
    """Verify clean server start/stop using MCP"""
    print("\nTesting MCP server start/stop...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for MCP start/stop test"
        print("Services started successfully for MCP start/stop test.")

        # Test MCP connection
        mcp_connected = test_mcp_connection()
        assert mcp_connected, "MCP server is not reachable after starting services"
        print("MCP server is reachable.")

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, "Failed to stop services after MCP start/stop test"
            print("Services stopped successfully after MCP start/stop test.")

        # Verify MCP connection fails after stopping
        mcp_connected_after_stop = test_mcp_connection()
        assert not mcp_connected_after_stop, "MCP server is still reachable after stopping services"
        print("MCP server is not reachable after stopping services.")


def test_server_restart():
    """Test server restart with persistence using MCP"""
    print("\nTesting MCP server restart...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for MCP restart test (first start)"
        print("Services started successfully for MCP restart test (first start).")

        # Test MCP connection
        mcp_connected_first = test_mcp_connection()
        assert mcp_connected_first, "MCP server is not reachable after first start"
        print("MCP server is reachable after first start.")

        # Stop services
        if process:
            stop_success_first = stop_services(process)
            assert stop_success_first, "Failed to stop services for MCP restart test (first stop)"
            print("Services stopped successfully for MCP restart test (first stop).")

        # Start services again
        success_restart, process_restart = start_services()
        assert success_restart, "Failed to start services for MCP restart test (second start)"
        print("Services started successfully for MCP restart test (second start).")
        process = process_restart # Update process handle

        # Test MCP connection again
        mcp_connected_second = test_mcp_connection()
        assert mcp_connected_second, "MCP server is not reachable after restart"
        print("MCP server is reachable after restart.")

    finally:
        # Stop services
        if process:
            stop_success_second = stop_services(process)
            assert stop_success_second, "Failed to stop services after MCP restart test (second stop)"
            print("Services stopped successfully after MCP restart test (second stop).")

        # Verify MCP connection fails after final stop
        mcp_connected_after_stop = test_mcp_connection()
        assert not mcp_connected_after_stop, "MCP server is still reachable after final stop"
        print("MCP server is not reachable after final stop.")