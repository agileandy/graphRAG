"""Test duplicate document rejection functionality for the web API."""

import pytest
from tests.common_utils.test_utils import (
    print_test_result,
    add_test_document,
    get_test_document_text,
    get_test_document_metadata
)

def test_exact_duplicate() -> None:
    """Test rejection of an exact duplicate document."""
    print("\nTesting exact duplicate rejection...")

    # Add initial document
    document_text = get_test_document_text()
    metadata = get_test_document_metadata()

    success, result = add_test_document(document_text, metadata)
    if not success:
        print_test_result(
            "Add Initial Document",
            False,
            f"Failed to add initial document: {result.get('error', 'Unknown error')}"
        )
        return

    # Try to add the exact same document again
    success, result = add_test_document(document_text, metadata)

    # This should fail - exact duplicates should be rejected
    if success:
        print_test_result(
            "Exact Duplicate Rejection",
            False,
            "Duplicate document was accepted but should have been rejected"
        )
        return

    print_test_result(
        "Exact Duplicate Rejection",
        True,
        "Duplicate document was correctly rejected"
    )

def test_similar_content_different_metadata() -> None:
    """Test handling of similar content with different metadata."""
    print("\nTesting similar content with different metadata...")

    # Add initial document
    document_text = get_test_document_text()
    metadata = get_test_document_metadata()

    success, result = add_test_document(document_text, metadata)
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

    success, result = add_test_document(document_text, different_metadata)

    # This should fail - content is too similar
    if success:
        print_test_result(
            "Similar Content Rejection",
            False,
            "Similar document with different metadata was accepted but should have been rejected"
        )
        return

    print_test_result(
        "Similar Content Rejection",
        True,
        "Similar document was correctly rejected despite different metadata"
    )

def test_slightly_modified_content() -> None:
    """Test handling of slightly modified content."""
    print("\nTesting slightly modified content...")

    # Add initial document
    document_text = get_test_document_text()
    metadata = get_test_document_metadata()

    success, result = add_test_document(document_text, metadata)
    if not success:
        print_test_result(
            "Add Initial Document",
            False,
            f"Failed to add initial document: {result.get('error', 'Unknown error')}"
        )
        return

    # Create slightly modified version
    modified_text = document_text.replace("GraphRAG", "GraphRAG System")
    modified_text = modified_text.replace("innovative", "novel")

    # Try to add modified content
    success, result = add_test_document(modified_text, metadata)

    # This should fail - content is still too similar
    if success:
        print_test_result(
            "Modified Content Rejection",
            False,
            "Slightly modified document was accepted but should have been rejected"
        )
        return

    print_test_result(
        "Modified Content Rejection",
        True,
        "Slightly modified document was correctly rejected"
    )

def test_significantly_different_content() -> None:
    """Test acceptance of significantly different content."""
    print("\nTesting significantly different content...")

    # Add initial document
    document_text = get_test_document_text()
    metadata = get_test_document_metadata()

    success, result = add_test_document(document_text, metadata)
    if not success:
        print_test_result(
            "Add Initial Document",
            False,
            f"Failed to add initial document: {result.get('error', 'Unknown error')}"
        )
        return

    # Create significantly different content
    different_text = """
    Neural Networks in Modern AI Systems

    Neural networks have revolutionized artificial intelligence by providing
    powerful models that can learn complex patterns from data. These systems
    use layers of interconnected nodes to process information in ways that
    mimic biological neural networks.

    Key advantages include:
    1. Pattern recognition
    2. Adaptability
    3. Generalization capability
    4. Robustness to noise

    Modern applications range from computer vision to natural language
    processing, demonstrating the versatility of neural network architectures.
    """

    # Try to add different content
    success, result = add_test_document(different_text, metadata)

    # This should succeed - content is sufficiently different
    if not success:
        print_test_result(
            "Different Content Acceptance",
            False,
            f"Different document was rejected but should have been accepted: {result.get('error', 'Unknown error')}"
        )
        return

    print_test_result(
        "Different Content Acceptance",
        True,
        "Different document was correctly accepted"
    )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])