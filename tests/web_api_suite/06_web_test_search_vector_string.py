"""Test vector-based string search functionality for the web API."""

import pytest
from tests.common_utils.test_utils import (
    print_test_result,
    add_test_document,
    search_documents,
    get_test_document_text,
    get_test_document_metadata
)

def setup_test_documents() -> bool:
    """Set up test documents for searching."""
    documents = [
        {
            "text": """
            Vector databases are essential components in modern AI systems.
            They enable efficient similarity search across large collections
            of embeddings, making them ideal for semantic search applications.
            Popular vector databases include Chroma, FAISS, and Milvus.
            """,
            "metadata": {
                "title": "Vector Databases Overview",
                "author": "Test Author",
                "category": "AI",
                "source": "Test Suite"
            }
        },
        {
            "text": """
            Language models have revolutionized NLP tasks. They can understand
            and generate human-like text, perform translations, and answer
            questions. Models like GPT and BERT have shown impressive results.
            """,
            "metadata": {
                "title": "Language Models in AI",
                "author": "Test Author",
                "category": "AI",
                "source": "Test Suite"
            }
        },
        {
            "text": """
            Graph databases excel at storing and querying connected data.
            They represent relationships explicitly, making them perfect for
            social networks, recommendation systems, and knowledge graphs.
            Neo4j is a popular graph database system.
            """,
            "metadata": {
                "title": "Graph Databases",
                "author": "Test Author",
                "category": "Databases",
                "source": "Test Suite"
            }
        }
    ]

    for doc in documents:
        success, result = add_test_document(doc["text"], doc["metadata"])
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

    query = "vector databases similarity search"
    success, result = search_documents(query, n_results=5)

    if not success:
        print_test_result(
            "Exact Match Search",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check if we got any results
    vector_results = result.get("vector_results", {})
    documents = vector_results.get("documents", [])

    if not documents:
        print_test_result(
            "Exact Match Search",
            False,
            "No results found for exact phrase search"
        )
        return

    # First result should be about vector databases
    if "vector database" not in documents[0].lower():
        print_test_result(
            "Exact Match Search",
            False,
            "Expected document about vector databases as top result"
        )
        return

    print_test_result(
        "Exact Match Search",
        True,
        "Found correct document for exact phrase"
    )

def test_semantic_search() -> None:
    """Test searching for semantically similar content."""
    print("\nTesting semantic search...")

    # Use semantically similar but not exact phrase
    query = "embedding similarity retrieval systems"
    success, result = search_documents(query, n_results=5)

    if not success:
        print_test_result(
            "Semantic Search",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check if we got any results
    vector_results = result.get("vector_results", {})
    documents = vector_results.get("documents", [])

    if not documents:
        print_test_result(
            "Semantic Search",
            False,
            "No results found for semantic search"
        )
        return

    # First result should be about vector databases (semantically similar)
    if "vector database" not in documents[0].lower():
        print_test_result(
            "Semantic Search",
            False,
            "Expected document about vector databases as top result"
        )
        return

    print_test_result(
        "Semantic Search",
        True,
        "Found semantically relevant document"
    )

def test_unrelated_search() -> None:
    """Test searching for unrelated content."""
    print("\nTesting unrelated content search...")

    # Use query unrelated to any test documents
    query = "cooking recipes and ingredients"
    success, result = search_documents(query, n_results=5)

    if not success:
        print_test_result(
            "Unrelated Search",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check results
    vector_results = result.get("vector_results", {})
    documents = vector_results.get("documents", [])
    scores = vector_results.get("scores", [])

    if not documents:
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

    pytest.main([__file__, "-v"])