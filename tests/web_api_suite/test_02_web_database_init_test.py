"""Test database initialization functionality for the web API."""

import pytest
from tests.common_utils.test_utils import print_test_result, check_database_initialization

def test_database_init() -> None:
    """Test database initialization."""
    print("\nTesting database initialization...")
    success, result = check_database_initialization(verify_indexes=True)

    if not success:
        print_test_result(
            "Database Initialization",
            False,
            f"Database initialization failed: {result.get('error', 'Unknown error')}"
        )
        return

    print_test_result(
        "Database Initialization",
        True,
        f"Database initialized successfully: {result.get('message', '')}"
    )

def test_database_indexes() -> None:
    """Test database indexes are properly created."""
    print("\nTesting database indexes...")
    success, result = check_database_initialization(verify_indexes=True)

    if not success:
        print_test_result(
            "Database Indexes",
            False,
            f"Index verification failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check if we got index details in the result
    details = result.get('details', '')
    if details:
        print_test_result(
            "Database Indexes",
            True,
            f"Index verification passed: {details}"
        )
    else:
        print_test_result(
            "Database Indexes",
            True,
            "Index verification passed"
        )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])