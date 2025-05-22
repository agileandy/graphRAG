"""Test duplicate document rejection functionality for the MCP server."""

import pytest
from tests.common_utils.test_utils import (
    print_test_result,
    get_test_document_text,
    get_test_document_metadata,
    sync_mcp_invoke_tool,
    run_pytest_async
)

def test_exact_duplicate() -> None:
    """Test rejection of an exact duplicate document."""
    print("\nTesting exact duplicate rejection...")

    # Add initial document
    document_text = get_test_document_text()
    metadata = get_test_document_metadata()

    success, result = sync_mcp_invoke_tool(
        tool_name="add_document",
        parameters={
            "text": document_text,
            "metadata": metadata
        }
    )

    if not success:
        print_test_result(
            "Add Initial Document",
            False,
            f"Failed to add initial document: {result.get('error', 'Unknown error')}"
        )
        return

    # Try to add the exact same document again
    success, result = sync_mcp_invoke_tool(
        tool_name="add_document",
        parameters={
            "text": document_text,
            "metadata": metadata
        }
    )

    # This should fail - exact duplicates should be rejected
    if success:
        print_test_result(
            "Exact Duplicate Rejection",
            False,
            "Duplicate document was accepted but should have been rejected"
        )
        return

    error_message = result.get("error", "")
    if "duplicate" not in error_message.lower():
        print_test_result(
            "Exact Duplicate Rejection",
            False,
            f"Unexpected error message: {error_message}"
        )
        return

    print_test_result(
        "Exact Duplicate Rejection",
        True,
        "Duplicate document was correctly rejected"
    )

def test_duplicate_with_different_metadata() -> None:
    """Test rejection of duplicate content with different metadata."""
    print("\nTesting duplicate with different metadata...")

    # Add initial document
    document_text = get_test_document_text()
    metadata = get_test_document_metadata()

    success, result = sync_mcp_invoke_tool(
        tool_name="add_document",
        parameters={
            "text": document_text,
            "metadata": metadata
        }
    )

    if not success:
        print_test_result(
            "Add Initial Document",
            False,
            f"Failed to add initial document: {result.get('error', 'Unknown error')}"
        )
        return

    # Try to add same content with different metadata
    different_metadata = {
        "title": "Different Title",
        "author": "Different Author",
        "category": "Different Category",
        "source": "Different Source"
    }

    success, result = sync_mcp_invoke_tool(
        tool_name="add_document",
        parameters={
            "text": document_text,
            "metadata": different_metadata
        }
    )

    # Should fail despite different metadata
    if success:
        print_test_result(
            "Duplicate with Different Metadata",
            False,
            "Duplicate content was accepted despite similarity check"
        )
        return

    error_message = result.get("error", "")
    if "duplicate" not in error_message.lower() and "similar" not in error_message.lower():
        print_test_result(
            "Duplicate with Different Metadata",
            False,
            f"Unexpected error message: {error_message}"
        )
        return

    print_test_result(
        "Duplicate with Different Metadata",
        True,
        "Duplicate content was correctly rejected despite different metadata"
    )

def test_near_duplicate() -> None:
    """Test rejection of near-duplicate content."""
    print("\nTesting near-duplicate rejection...")

    # Add initial document
    document_text = get_test_document_text()
    metadata = get_test_document_metadata()

    success, result = sync_mcp_invoke_tool(
        tool_name="add_document",
        parameters={
            "text": document_text,
            "metadata": metadata
        }
    )

    if not success:
        print_test_result(
            "Add Initial Document",
            False,
            f"Failed to add initial document: {result.get('error', 'Unknown error')}"
        )
        return

    # Create slightly modified version
    modified_text = document_text.replace("system", "application")
    modified_text = modified_text.replace("process", "handle")

    # Try to add modified content
    success, result = sync_mcp_invoke_tool(
        tool_name="add_document",
        parameters={
            "text": modified_text,
            "metadata": metadata
        }
    )

    # Should fail - content is too similar
    if success:
        print_test_result(
            "Near-Duplicate Rejection",
            False,
            "Near-duplicate content was accepted but should have been rejected"
        )
        return

    error_message = result.get("error", "")
    if "similar" not in error_message.lower():
        print_test_result(
            "Near-Duplicate Rejection",
            False,
            f"Unexpected error message: {error_message}"
        )
        return

    similarity_score = result.get("similarity_score", 0)
    print_test_result(
        "Near-Duplicate Rejection",
        True,
        f"Near-duplicate content was correctly rejected (similarity: {similarity_score:.2%})"
    )

def test_unique_content() -> None:
    """Test acceptance of sufficiently different content."""
    print("\nTesting unique content acceptance...")

    # Add initial document
    document_text = get_test_document_text()
    metadata = get_test_document_metadata()

    success, result = sync_mcp_invoke_tool(
        tool_name="add_document",
        parameters={
            "text": document_text,
            "metadata": metadata
        }
    )

    if not success:
        print_test_result(
            "Add Initial Document",
            False,
            f"Failed to add initial document: {result.get('error', 'Unknown error')}"
        )
        return

    # Create significantly different content
    unique_text = """
    Database Management Systems (DBMS) are essential for modern applications.
    They provide reliable data storage, transaction management, and querying
    capabilities. Popular DBMS solutions include PostgreSQL, MongoDB, and Redis.
    """

    # Try to add unique content
    success, result = sync_mcp_invoke_tool(
        tool_name="add_document",
        parameters={
            "text": unique_text,
            "metadata": metadata
        }
    )

    if not success:
        print_test_result(
            "Unique Content",
            False,
            f"Failed to add unique content: {result.get('error', 'Unknown error')}"
        )
        return

    similarity_score = result.get("similarity_score", 0)
    print_test_result(
        "Unique Content",
        True,
        f"Unique content was correctly accepted (similarity: {similarity_score:.2%})"
    )

if __name__ == "__main__":
    run_pytest_async(__file__)