"""Test finding related documents functionality for the web API."""

import pytest
from tests.common_utils.test_utils import (
    print_test_result,
    add_test_document,
    get_documents_for_concept,
    search_documents
)

def setup_test_documents() -> bool:
    """Set up a network of related test documents."""
    documents = [
        {
            "text": """
            GraphRAG combines vector search with graph traversal to enhance document
            retrieval. Its hybrid approach leverages both semantic similarity and
            explicit concept relationships, providing more comprehensive search results.
            """,
            "metadata": {
                "title": "GraphRAG Overview",
                "author": "Test Author",
                "category": "AI",
                "source": "Test Suite",
                "concepts": ["GraphRAG", "Vector Search", "Graph Traversal"]
            }
        },
        {
            "text": """
            Vector search systems use embeddings to find similar documents. They convert
            text into high-dimensional vectors and use distance metrics to measure
            similarity. This approach is particularly effective for semantic search.
            """,
            "metadata": {
                "title": "Vector Search Systems",
                "author": "Test Author",
                "category": "AI",
                "source": "Test Suite",
                "concepts": ["Vector Search", "Embeddings", "Semantic Search"]
            }
        },
        {
            "text": """
            Graph traversal algorithms explore connections between nodes in a graph.
            Common algorithms include depth-first search and breadth-first search.
            In knowledge graphs, this enables finding related concepts efficiently.
            """,
            "metadata": {
                "title": "Graph Traversal",
                "author": "Test Author",
                "category": "Computer Science",
                "source": "Test Suite",
                "concepts": ["Graph Traversal", "Graph Algorithms", "Knowledge Graphs"]
            }
        },
        {
            "text": """
            Semantic search goes beyond keyword matching to understand the meaning
            of queries. It uses techniques like word embeddings and contextual
            analysis to find relevant results even when exact terms don't match.
            """,
            "metadata": {
                "title": "Semantic Search",
                "author": "Test Author",
                "category": "Information Retrieval",
                "source": "Test Suite",
                "concepts": ["Semantic Search", "Word Embeddings", "Information Retrieval"]
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

def test_vector_similarity_relations() -> None:
    """Test finding documents related by vector similarity."""
    print("\nTesting vector similarity relations...")

    # Search using content similar to the vector search document
    query = "vector embeddings similarity search systems"
    success, result = search_documents(query, n_results=3)

    if not success:
        print_test_result(
            "Vector Similarity Relations",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check results
    vector_results = result.get("vector_results", {})
    documents = vector_results.get("documents", [])

    if len(documents) < 2:
        print_test_result(
            "Vector Similarity Relations",
            False,
            f"Expected at least 2 related documents, found {len(documents)}"
        )
        return

    # The top results should be about vector search and semantic search
    found_topics = sum(
        1 for doc in documents
        if "vector" in doc.lower() or "semantic" in doc.lower()
    )

    if found_topics < 2:
        print_test_result(
            "Vector Similarity Relations",
            False,
            "Did not find expected related documents about vector and semantic search"
        )
        return

    print_test_result(
        "Vector Similarity Relations",
        True,
        f"Found {found_topics} related documents through vector similarity"
    )

def test_concept_based_relations() -> None:
    """Test finding documents related through shared concepts."""
    print("\nTesting concept-based relations...")

    # Get documents related to the "Vector Search" concept
    success, result = get_documents_for_concept("Vector Search")

    if not success:
        print_test_result(
            "Concept Relations",
            False,
            f"Failed to get related documents: {result.get('error', 'Unknown error')}"
        )
        return

    documents = result.get("documents", [])
    if len(documents) < 2:
        print_test_result(
            "Concept Relations",
            False,
            f"Expected at least 2 documents sharing the concept, found {len(documents)}"
        )
        return

    # Should find both GraphRAG and vector search system documents
    topics_found = {
        "graphrag": any("graphrag" in doc.lower() for doc in documents),
        "vector search": any("vector search" in doc.lower() for doc in documents)
    }

    if not all(topics_found.values()):
        print_test_result(
            "Concept Relations",
            False,
            f"Missing some expected related documents. Found: {list(k for k, v in topics_found.items() if v)}"
        )
        return

    print_test_result(
        "Concept Relations",
        True,
        f"Found all expected related documents through concepts: {list(topics_found.keys())}"
    )

def test_hybrid_relations() -> None:
    """Test finding documents related through both vector similarity and concepts."""
    print("\nTesting hybrid relations...")

    # Search with both semantic similarity and concept overlap
    query = "graph-based search systems with semantic understanding"
    success, result = search_documents(query, n_results=4)

    if not success:
        print_test_result(
            "Hybrid Relations",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check results
    vector_results = result.get("vector_results", {})
    documents = vector_results.get("documents", [])

    if len(documents) < 3:
        print_test_result(
            "Hybrid Relations",
            False,
            f"Expected at least 3 related documents, found {len(documents)}"
        )
        return

    # Should find documents about GraphRAG, vector search, and semantic search
    topics_found = {
        "graphrag": any("graphrag" in doc.lower() for doc in documents),
        "vector search": any("vector search" in doc.lower() for doc in documents),
        "semantic search": any("semantic search" in doc.lower() for doc in documents)
    }

    if not all(topics_found.values()):
        print_test_result(
            "Hybrid Relations",
            False,
            f"Missing some expected related documents. Found: {list(k for k, v in topics_found.items() if v)}"
        )
        return

    print_test_result(
        "Hybrid Relations",
        True,
        f"Found all expected related documents through hybrid approach: {list(topics_found.keys())}"
    )

if __name__ == "__main__":
    # Set up test documents first
    if not setup_test_documents():
        print("Failed to set up test documents. Skipping tests.")
        exit(1)

    pytest.main([__file__, "-v"])