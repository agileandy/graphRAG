"""Test document addition functionality for the web API."""

import pytest
from tests.common_utils.test_utils import (
    print_test_result,
    add_test_document,
    get_test_document_text,
    get_test_document_metadata
)

def test_add_single_document() -> None:
    """Test adding a single document."""
    print("\nTesting single document addition...")

    # Get test document data
    document_text = get_test_document_text()
    metadata = get_test_document_metadata()

    # Try to add the document
    success, result = add_test_document(document_text, metadata)

    if not success:
        error_msg = result.get("error", "Unknown error")
        print_test_result(
            "Add Single Document",
            False,
            f"Failed to add document: {error_msg}"
        )
        return

    print_test_result(
        "Add Single Document",
        True,
        "Document added successfully"
    )

def test_add_empty_document() -> None:
    """Test adding an empty document (should fail)."""
    print("\nTesting empty document addition...")

    # Try to add empty document
    success, result = add_test_document("", get_test_document_metadata())

    # This should fail - empty documents are not allowed
    if success:
        print_test_result(
            "Add Empty Document",
            False,
            "Empty document was accepted but should have been rejected"
        )
        return

    print_test_result(
        "Add Empty Document",
        True,
        "Empty document was correctly rejected"
    )

def test_add_document_without_metadata() -> None:
    """Test adding a document without metadata (should fail)."""
    print("\nTesting document addition without metadata...")

    # Try to add document without metadata
    success, result = add_test_document(get_test_document_text(), {})

    # This should fail - metadata is required
    if success:
        print_test_result(
            "Add Document Without Metadata",
            False,
            "Document without metadata was accepted but should have been rejected"
        )
        return

    print_test_result(
        "Add Document Without Metadata",
        True,
        "Document without metadata was correctly rejected"
    )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])