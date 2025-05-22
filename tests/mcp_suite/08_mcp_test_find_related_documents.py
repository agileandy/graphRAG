"""Test finding related documents functionality for the MCP server."""

import pytest
from tests.common_utils.test_utils import (
    print_test_result,
    sync_mcp_invoke_tool,
    sync_mcp_search,
    run_pytest_async
)

def setup_test_documents() -> bool:
    """Set up test documents with relationships."""
    documents = [
        {
            "text": """
            GraphRAG enhances document retrieval by combining vector search
            with graph traversal. It uses both semantic similarity and
            explicit concept relationships to find relevant information.
            """,
            "metadata": {
                "title": "GraphRAG Overview",
                "author": "Test Author",
                "category": "AI",
                "source": "Test Suite",
                "concepts": ["GraphRAG", "Information Retrieval", "Graph Search"]
            }
        },
        {
            "text": """
            Vector search systems use embeddings to measure document
            similarity. By converting text to vectors, they can find
            semantically similar content efficiently.
            """,
            "metadata": {
                "title": "Vector Search",
                "author": "Test Author",
                "category": "Search",
                "source": "Test Suite",
                "concepts": ["Vector Search", "Document Similarity", "Embeddings"]
            }
        },
        {
            "text": """
            Knowledge graphs represent relationships between concepts
            explicitly. Graph traversal algorithms can follow these
            connections to discover related information.
            """,
            "metadata": {
                "title": "Knowledge Graphs",
                "author": "Test Author",
                "category": "Databases",
                "source": "Test Suite",
                "concepts": ["Knowledge Graphs", "Graph Algorithms", "Information Retrieval"]
            }
        }
    ]

    for doc in documents:
        success, result = sync_mcp_invoke_tool(
            tool_name="add_document",
            parameters={
                "text": doc["text"],
                "metadata": doc["metadata"],
                "extract_concepts": True
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

def test_vector_similarity() -> None:
    """Test finding documents related by vector similarity."""
    print("\nTesting vector similarity relationships...")

    # Search using text similar to vector search document
    query = "document similarity using vector embeddings"
    success, result = sync_mcp_search(query=query, max_results=3)

    if not success:
        print_test_result(
            "Vector Similarity",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check results
    results = result.get("results", [])
    if len(results) < 2:
        print_test_result(
            "Vector Similarity",
            False,
            f"Expected at least 2 similar documents, found {len(results)}"
        )
        return

    # Should find vector search document and possibly GraphRAG document
    found_topics = {
        "vector": False,
        "graphrag": False
    }

    for doc in results:
        text = doc.get("text", "").lower()
        if "vector" in text:
            found_topics["vector"] = True
        if "graphrag" in text:
            found_topics["graphrag"] = True

    print_test_result(
        "Vector Similarity",
        True,
        f"Found related documents through vector similarity: {[k for k, v in found_topics.items() if v]}"
    )

def test_concept_relationships() -> None:
    """Test finding documents related through concepts."""
    print("\nTesting concept relationships...")

    success, result = sync_mcp_invoke_tool(
        tool_name="find_related_documents",
        parameters={
            "document_id": "graphrag_overview",  # ID from first test document
            "relationship_type": "concept",
            "max_distance": 2
        }
    )

    if not success:
        print_test_result(
            "Concept Relationships",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check results
    related_docs = result.get("documents", [])
    if len(related_docs) < 2:
        print_test_result(
            "Concept Relationships",
            False,
            f"Expected at least 2 related documents, found {len(related_docs)}"
        )
        return

    # Should find documents sharing concepts like Information Retrieval
    shared_concepts = set()
    for doc in related_docs:
        concepts = doc.get("metadata", {}).get("concepts", [])
        shared_concepts.update(concepts)

    expected_concepts = {"Information Retrieval", "Graph Search"}
    found_concepts = shared_concepts.intersection(expected_concepts)

    print_test_result(
        "Concept Relationships",
        bool(found_concepts),
        f"Found documents related through concepts: {found_concepts}"
    )

def test_hybrid_relationships() -> None:
    """Test finding documents through both vector and concept relationships."""
    print("\nTesting hybrid relationship discovery...")

    success, result = sync_mcp_invoke_tool(
        tool_name="find_related_documents",
        parameters={
            "document_id": "graphrag_overview",
            "relationship_types": ["vector", "concept"],
            "max_results": 5
        }
    )

    if not success:
        print_test_result(
            "Hybrid Relationships",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check results
    related_docs = result.get("documents", [])
    if len(related_docs) < 2:
        print_test_result(
            "Hybrid Relationships",
            False,
            f"Expected at least 2 related documents, found {len(related_docs)}"
        )
        return

    # Analyze relationship types
    relationship_types = set()
    for doc in related_docs:
        relationships = doc.get("relationship_info", {})
        relationship_types.update(relationships.keys())

    expected_types = {"vector_similarity", "shared_concepts"}
    found_types = relationship_types.intersection(expected_types)

    print_test_result(
        "Hybrid Relationships",
        len(found_types) >= 2,
        f"Found documents through different relationship types: {found_types}"
    )

def test_relationship_scoring() -> None:
    """Test scoring of different relationship types."""
    print("\nTesting relationship scoring...")

    success, result = sync_mcp_invoke_tool(
        tool_name="find_related_documents",
        parameters={
            "document_id": "graphrag_overview",
            "relationship_types": ["vector", "concept"],
            "include_scores": True,
            "max_results": 5
        }
    )

    if not success:
        print_test_result(
            "Relationship Scoring",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check scores
    related_docs = result.get("documents", [])
    if not related_docs:
        print_test_result(
            "Relationship Scoring",
            False,
            "No scored relationships found"
        )
        return

    has_vector_scores = any(
        doc.get("scores", {}).get("vector_similarity") is not None
        for doc in related_docs
    )
    has_concept_scores = any(
        doc.get("scores", {}).get("concept_similarity") is not None
        for doc in related_docs
    )

    print_test_result(
        "Relationship Scoring",
        has_vector_scores and has_concept_scores,
        f"Found scored relationships - Vector: {has_vector_scores}, Concept: {has_concept_scores}"
    )

if __name__ == "__main__":
    # Set up test documents first
    if not setup_test_documents():
        print("Failed to set up test documents. Skipping tests.")
        exit(1)

    run_pytest_async(__file__)