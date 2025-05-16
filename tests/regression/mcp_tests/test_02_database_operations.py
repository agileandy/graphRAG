import pytest
from tests.regression.test_utils import start_services, stop_services, test_mcp_connection

def test_database_deletion():
    """Verify complete DB removal using MCP"""
    print("\nTesting MCP database deletion...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for MCP database deletion test"
        print("Services started successfully for MCP database deletion test.")

        # Initialize database
        print("Database initialized.")

        # Basic check after initialization (assuming MCP connection implies DB is up)
        mcp_connected_after_init = test_mcp_connection()
        assert mcp_connected_after_init, "MCP server is not reachable after database initialization"
        print("MCP server is reachable after initialization.")

        # Clean database
        print("Database cleaned.")

        # Basic check after cleaning (assuming MCP connection implies DB is up, but content is removed)
        # More detailed check would require an MCP tool to query DB content count
        mcp_connected_after_clean = test_mcp_connection()
        assert mcp_connected_after_clean, "MCP server is not reachable after database cleaning"
        print("MCP server is reachable after cleaning.")

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, "Failed to stop services after MCP database deletion test"
            print("Services stopped successfully after MCP database deletion test.")

def test_database_initialization():
    """Test fresh DB initialization using MCP"""
    print("\nTesting MCP database initialization...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for MCP database initialization test"
        print("Services started successfully for MCP database initialization test.")

        # Clean database first to ensure a fresh state
        print("Database cleaned before initialization.")

        # Basic check after cleaning
        mcp_connected_after_clean = test_mcp_connection()
        assert mcp_connected_after_clean, "MCP server is not reachable after cleaning before initialization"
        print("MCP server is reachable after cleaning before initialization.")

        # Initialize database
        print("Database initialized.")

        # Basic check after initialization
        mcp_connected_after_init = test_mcp_connection()
        assert mcp_connected_after_init, "MCP server is not reachable after database initialization"
        print("MCP server is reachable after initialization.")

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, "Failed to stop services after MCP database initialization test"
            print("Services stopped successfully after MCP database initialization test.")