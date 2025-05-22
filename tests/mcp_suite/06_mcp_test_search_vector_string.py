"""Test vector-based string search functionality for the MCP server."""

import pytest
from tests.common_utils.test_utils import (
    print_test_result,
    get_test_document_text,
    get_test_document_metadata,
    sync_mcp_invoke_tool,
    sync_mcp_search,
    run_pytest_async
)

def setup_test_documents() -> bool:
    """Set up test documents for searching."""
    documents = [
        {
            "text": """
            Vector embeddings are mathematical representations of data in
            high-dimensional space. They capture semantic relationships
            between words and documents, enabling similarity comparisons.
            Common embedding models include Word2Vec and FastText.
            """,
            "metadata": {
                "title": "Vector Embeddings Overview",
                "author": "Test Author",
                "category": "AI",
                "source": "Test Suite"
            }
        },
        {
            "text": """
            Natural Language Processing (NLP) has been transformed by
            deep learning approaches. Modern models use contextual embeddings
            to understand language nuances and relationships between words.
            """,
            "metadata": {
                "title": "Modern NLP Approaches",
                "author": "Test Author",
                "category": "AI",
                "source": "Test Suite"
            }
        },
        {
            "text": """
            Semantic search goes beyond keyword matching to understand
            the meaning and context of search queries. It uses vector
            similarity to find relevant results even when terms don't
            exactly match the query.
            """,
            "metadata": {
                "title": "Semantic Search Systems",
                "author": "Test Author",
                "category": "Search",
                "source": "Test Suite"
            }
        }
    ]

    for doc in documents:
        success, result = sync_mcp_invoke_tool(
            tool_name="add_document",
            parameters={
                "text": doc["text"],
                "metadata": doc["metadata"]
            }
        )
        if not success:
            print_test_result(
                "Setup Test Documents",
                False,
                f"Failed to add test document: {result.get('error', 'Unknown error')}"
            )
            return False

    return True

def test_exact_match_search() -> None:
    """Test searching for exact phrase matches."""
    print("\nTesting exact phrase search...")

    query = "vector embeddings mathematical representations"
    success, result = sync_mcp_search(query=query, max_results=5)

    if not success:
        print_test_result(
            "Exact Match Search",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check results
    results = result.get("results", [])
    if not results:
        print_test_result(
            "Exact Match Search",
            False,
            "No results found for exact phrase"
        )
        return

    # First result should be about vector embeddings
    first_result = results[0]
    if "vector embedding" not in first_result.get("text", "").lower():
        print_test_result(
            "Exact Match Search",
            False,
            "Expected vector embeddings document as top result"
        )
        return

    print_test_result(
        "Exact Match Search",
        True,
        "Found exact matching document"
    )

def test_semantic_search() -> None:
    """Test searching with semantic understanding."""
    print("\nTesting semantic search...")

    # Use semantically related but not exact terms
    query = "data representation dimensionality mathematical space"
    success, result = sync_mcp_search(query=query, max_results=5)

    if not success:
        print_test_result(
            "Semantic Search",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check results
    results = result.get("results", [])
    if not results:
        print_test_result(
            "Semantic Search",
            False,
            "No results found for semantic search"
        )
        return

    # Should find vector embeddings document despite different terms
    first_result = results[0]
    if "vector embedding" not in first_result.get("text", "").lower():
        print_test_result(
            "Semantic Search",
            False,
            "Expected vector embeddings document as top result"
        )
        return

    print_test_result(
        "Semantic Search",
        True,
        "Found semantically relevant document"
    )

def test_multilingual_search() -> None:
    """Test searching across different languages (if supported)."""
    print("\nTesting multilingual search capability...")

    # Try searching with English terms for non-English content
    multilingual_doc = {
        "text": """
        Les embeddings vectoriels sont des représentations mathématiques
        des données dans un espace multidimensionnel. Ils capturent les
        relations sémantiques entre les mots et les documents.
        """,
        "metadata": {
            "title": "Embeddings Vectoriels",
            "author": "Test Author",
            "language": "French",
            "category": "AI",
            "source": "Test Suite"
        }
    }

    # Add multilingual test document
    success, result = sync_mcp_invoke_tool(
        tool_name="add_document",
        parameters={
            "text": multilingual_doc["text"],
            "metadata": multilingual_doc["metadata"]
        }
    )

    if not success:
        print_test_result(
            "Multilingual Search",
            False,
            "Failed to add multilingual test document"
        )
        return

    # Search using English terms
    query = "vector embeddings mathematical representations"
    success, result = sync_mcp_search(query=query, max_results=5)

    if not success:
        print_test_result(
            "Multilingual Search",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check if French document is in results
    results = result.get("results", [])
    found_french = any(
        "embeddings vectoriels" in r.get("text", "").lower()
        for r in results
    )

    if not found_french:
        print_test_result(
            "Multilingual Search",
            False,
            "French document not found in results"
        )
        return

    print_test_result(
        "Multilingual Search",
        True,
        "Successfully found multilingual content"
    )

def test_unrelated_search() -> None:
    """Test searching for unrelated content."""
    print("\nTesting unrelated content search...")

    query = "cooking recipes ingredients culinary techniques"
    success, result = sync_mcp_search(query=query, max_results=5)

    if not success:
        print_test_result(
            "Unrelated Search",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check results
    results = result.get("results", [])
    scores = result.get("scores", [])

    if not results:
        print_test_result(
            "Unrelated Search",
            True,
            "Correctly returned no results for unrelated query"
        )
        return

    # If we got results, their similarity scores should be low
    if scores and max(scores) > 0.5:  # Threshold can be adjusted
        print_test_result(
            "Unrelated Search",
            False,
            f"Got high similarity score ({max(scores)}) for unrelated content"
        )
        return

    print_test_result(
        "Unrelated Search",
        True,
        "Correctly identified low similarity for unrelated query"
    )

if __name__ == "__main__":
    # Set up test documents first
    if not setup_test_documents():
        print("Failed to set up test documents. Skipping tests.")
        exit(1)

    run_pytest_async(__file__)