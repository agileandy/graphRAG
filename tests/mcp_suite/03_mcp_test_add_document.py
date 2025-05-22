"""Test document addition functionality for the MCP server."""

import pytest
from tests.common_utils.test_utils import (
    print_test_result,
    get_test_document_text,
    get_test_document_metadata,
    sync_mcp_invoke_tool,
    run_pytest_async
)

def test_add_single_document() -> None:
    """Test adding a single document via MCP."""
    print("\nTesting single document addition...")

    # Get test document data
    document_text = get_test_document_text()
    metadata = get_test_document_metadata()

    # Try to add the document via MCP
    success, result = sync_mcp_invoke_tool(
        tool_name="add_document",
        parameters={
            "text": document_text,
            "metadata": metadata
        }
    )

    if not success:
        print_test_result(
            "Add Single Document",
            False,
            f"Failed to add document: {result.get('error', 'Unknown error')}"
        )
        return

    # Verify document was added
    document_id = result.get("document_id")
    if not document_id:
        print_test_result(
            "Add Single Document",
            False,
            "No document ID returned"
        )
        return

    print_test_result(
        "Add Single Document",
        True,
        f"Document added successfully with ID: {document_id}"
    )

def test_add_empty_document() -> None:
    """Test adding an empty document (should fail)."""
    print("\nTesting empty document addition...")

    # Try to add empty document via MCP
    success, result = sync_mcp_invoke_tool(
        tool_name="add_document",
        parameters={
            "text": "",
            "metadata": get_test_document_metadata()
        }
    )

    # This should fail - empty documents are not allowed
    if success:
        print_test_result(
            "Add Empty Document",
            False,
            "Empty document was accepted but should have been rejected"
        )
        return

    error_message = result.get("error", "")
    if "empty" not in error_message.lower():
        print_test_result(
            "Add Empty Document",
            False,
            f"Unexpected error message: {error_message}"
        )
        return

    print_test_result(
        "Add Empty Document",
        True,
        "Empty document was correctly rejected"
    )

def test_add_document_with_concepts() -> None:
    """Test adding a document with concept extraction."""
    print("\nTesting document addition with concept extraction...")

    # Get test document with concepts
    document_text = """
    Neural networks are fundamental to modern AI systems. Deep learning models
    like transformers have revolutionized natural language processing tasks.
    BERT and GPT are prominent examples of transformer architectures.
    """
    metadata = {
        "title": "Neural Networks and Transformers",
        "author": "Test Author",
        "category": "AI",
        "source": "Test Suite",
        "extract_concepts": True  # Enable concept extraction
    }

    # Try to add document with concept extraction
    success, result = sync_mcp_invoke_tool(
        tool_name="add_document",
        parameters={
            "text": document_text,
            "metadata": metadata,
            "extract_concepts": True
        }
    )

    if not success:
        print_test_result(
            "Add Document with Concepts",
            False,
            f"Failed to add document: {result.get('error', 'Unknown error')}"
        )
        return

    # Verify concepts were extracted
    concepts = result.get("extracted_concepts", [])
    expected_concepts = {"Neural Networks", "Deep Learning", "Transformers", "BERT", "GPT"}
    found_concepts = set(c.get("name") for c in concepts)

    if not found_concepts.intersection(expected_concepts):
        print_test_result(
            "Add Document with Concepts",
            False,
            f"Expected some of {expected_concepts}, found {found_concepts}"
        )
        return

    print_test_result(
        "Add Document with Concepts",
        True,
        f"Document added with concepts: {found_concepts.intersection(expected_concepts)}"
    )

def test_add_document_with_invalid_metadata() -> None:
    """Test adding a document with invalid metadata (should fail)."""
    print("\nTesting document addition with invalid metadata...")

    # Try to add document with invalid metadata
    success, result = sync_mcp_invoke_tool(
        tool_name="add_document",
        parameters={
            "text": get_test_document_text(),
            "metadata": {
                "title": 123,  # Invalid type: should be string
                "author": None,  # Invalid type: should be string
                "category": ["AI"],  # Invalid type: should be string
                "source": ""  # Invalid: empty string
            }
        }
    )

    # This should fail - metadata validation should catch errors
    if success:
        print_test_result(
            "Add Document with Invalid Metadata",
            False,
            "Invalid metadata was accepted but should have been rejected"
        )
        return

    error_message = result.get("error", "")
    if "metadata" not in error_message.lower():
        print_test_result(
            "Add Document with Invalid Metadata",
            False,
            f"Unexpected error message: {error_message}"
        )
        return

    print_test_result(
        "Add Document with Invalid Metadata",
        True,
        "Invalid metadata was correctly rejected"
    )

if __name__ == "__main__":
    run_pytest_async(__file__)