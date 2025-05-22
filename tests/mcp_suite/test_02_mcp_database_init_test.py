"""Test database initialization functionality for the MCP server."""

import pytest
from tests.common_utils.test_utils import (
    print_test_result,
    sync_mcp_invoke_tool,
    run_pytest_async
)

def test_database_connection() -> None:
    """Test if the MCP server can connect to its database."""
    print("\nTesting MCP database connection...")

    success, result = sync_mcp_invoke_tool(
        tool_name="check_database",
        parameters={"operation": "connection_test"}
    )

    if not success:
        print_test_result(
            "Database Connection",
            False,
            f"Failed to connect to database: {result.get('error', 'Unknown error')}"
        )
        return

    print_test_result(
        "Database Connection",
        True,
        "Successfully connected to database"
    )

def test_database_initialization() -> None:
    """Test if the database is properly initialized with required schemas."""
    print("\nTesting database initialization...")

    success, result = sync_mcp_invoke_tool(
        tool_name="check_database",
        parameters={"operation": "verify_schema"}
    )

    if not success:
        print_test_result(
            "Database Schema",
            False,
            f"Schema verification failed: {result.get('error', 'Unknown error')}"
        )
        return

    print_test_result(
        "Database Schema",
        True,
        "Database schema verified successfully"
    )

def test_database_indexes() -> None:
    """Test if required database indexes are created."""
    print("\nTesting database indexes...")

    success, result = sync_mcp_invoke_tool(
        tool_name="check_database",
        parameters={"operation": "verify_indexes"}
    )

    if not success:
        print_test_result(
            "Database Indexes",
            False,
            f"Index verification failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check for specific required indexes
    indexes = result.get("indexes", [])
    required_indexes = {
        "documents_content": False,
        "documents_metadata": False,
        "concepts_name": False
    }

    for index in indexes:
        index_name = index.get("name", "")
        if index_name in required_indexes:
            required_indexes[index_name] = True

    missing_indexes = [name for name, exists in required_indexes.items() if not exists]

    if missing_indexes:
        print_test_result(
            "Database Indexes",
            False,
            f"Missing required indexes: {', '.join(missing_indexes)}"
        )
        return

    print_test_result(
        "Database Indexes",
        True,
        f"All required indexes are present: {', '.join(required_indexes.keys())}"
    )

def test_database_reset() -> None:
    """Test database reset functionality."""
    print("\nTesting database reset...")

    # First verify we can connect
    success, result = sync_mcp_invoke_tool(
        tool_name="check_database",
        parameters={"operation": "connection_test"}
    )

    if not success:
        print_test_result(
            "Database Reset",
            False,
            "Failed to verify database connection before reset"
        )
        return

    # Attempt database reset
    success, result = sync_mcp_invoke_tool(
        tool_name="reset_database",
        parameters={"confirm": True}
    )

    if not success:
        print_test_result(
            "Database Reset",
            False,
            f"Failed to reset database: {result.get('error', 'Unknown error')}"
        )
        return

    # Verify database is empty but properly initialized
    success, result = sync_mcp_invoke_tool(
        tool_name="check_database",
        parameters={"operation": "verify_empty"}
    )

    if not success:
        print_test_result(
            "Database Reset",
            False,
            f"Database not properly reset: {result.get('error', 'Unknown error')}"
        )
        return

    print_test_result(
        "Database Reset",
        True,
        "Database reset successfully"
    )

if __name__ == "__main__":
    run_pytest_async(__file__)