"""Test graph-based concept search functionality for the MCP server."""

import pytest
from tests.common_utils.test_utils import (
    print_test_result,
    sync_mcp_invoke_tool,
    sync_mcp_search,
    run_pytest_async
)

def setup_test_documents() -> bool:
    """Set up test documents with concept relationships."""
    documents = [
        {
            "text": """
            Neural networks form the backbone of deep learning systems.
            They process information through layers of interconnected nodes,
            similar to biological neural networks in the brain.
            """,
            "metadata": {
                "title": "Neural Networks Basics",
                "author": "Test Author",
                "category": "AI",
                "source": "Test Suite",
                "concepts": ["Neural Networks", "Deep Learning", "Artificial Intelligence"]
            }
        },
        {
            "text": """
            Deep learning has revolutionized artificial intelligence.
            Through multiple layers of abstraction, these models can learn
            complex patterns from large amounts of data.
            """,
            "metadata": {
                "title": "Deep Learning Overview",
                "author": "Test Author",
                "category": "AI",
                "source": "Test Suite",
                "concepts": ["Deep Learning", "Machine Learning", "Data Science"]
            }
        },
        {
            "text": """
            Convolutional Neural Networks (CNNs) excel at image processing
            tasks. Their architecture is specifically designed to handle
            spatial relationships in visual data.
            """,
            "metadata": {
                "title": "CNNs in Computer Vision",
                "author": "Test Author",
                "category": "AI",
                "source": "Test Suite",
                "concepts": ["CNN", "Neural Networks", "Computer Vision"]
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

def test_direct_concept_search() -> None:
    """Test searching for documents directly related to a concept."""
    print("\nTesting direct concept search...")

    success, result = sync_mcp_invoke_tool(
        tool_name="search_by_concept",
        parameters={
            "concept": "Neural Networks",
            "max_results": 5
        }
    )

    if not success:
        print_test_result(
            "Direct Concept Search",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check results
    documents = result.get("documents", [])
    if len(documents) < 2:
        print_test_result(
            "Direct Concept Search",
            False,
            f"Expected at least 2 documents about neural networks, found {len(documents)}"
        )
        return

    print_test_result(
        "Direct Concept Search",
        True,
        f"Found {len(documents)} documents related to Neural Networks"
    )

def test_concept_graph_traversal() -> None:
    """Test finding documents through concept relationships."""
    print("\nTesting concept graph traversal...")

    success, result = sync_mcp_invoke_tool(
        tool_name="search_by_concept",
        parameters={
            "concept": "Artificial Intelligence",
            "max_depth": 2,  # Follow relationships up to 2 hops
            "max_results": 5
        }
    )

    if not success:
        print_test_result(
            "Concept Graph Traversal",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check results
    documents = result.get("documents", [])
    concepts_found = set()

    for doc in documents:
        doc_concepts = doc.get("metadata", {}).get("concepts", [])
        concepts_found.update(doc_concepts)

    expected_concepts = {
        "Artificial Intelligence",
        "Neural Networks",
        "Deep Learning",
        "Machine Learning"
    }

    found_expected = concepts_found.intersection(expected_concepts)
    if len(found_expected) < 2:
        print_test_result(
            "Concept Graph Traversal",
            False,
            f"Expected to find related concepts, only found: {found_expected}"
        )
        return

    print_test_result(
        "Concept Graph Traversal",
        True,
        f"Found documents with related concepts: {found_expected}"
    )

def test_concept_hierarchy() -> None:
    """Test traversing concept hierarchies."""
    print("\nTesting concept hierarchy traversal...")

    success, result = sync_mcp_invoke_tool(
        tool_name="get_concept_hierarchy",
        parameters={
            "concept": "Deep Learning",
            "max_depth": 2
        }
    )

    if not success:
        print_test_result(
            "Concept Hierarchy",
            False,
            f"Failed to get concept hierarchy: {result.get('error', 'Unknown error')}"
        )
        return

    # Check hierarchy
    hierarchy = result.get("hierarchy", {})
    parent_concepts = hierarchy.get("parents", [])
    child_concepts = hierarchy.get("children", [])

    expected_parents = {"Artificial Intelligence", "Machine Learning"}
    expected_children = {"Neural Networks", "CNN"}

    found_parents = set(parent_concepts)
    found_children = set(child_concepts)

    if not (found_parents.intersection(expected_parents) and
            found_children.intersection(expected_children)):
        print_test_result(
            "Concept Hierarchy",
            False,
            "Missing expected hierarchical relationships"
        )
        return

    print_test_result(
        "Concept Hierarchy",
        True,
        f"Found concept relationships - Parents: {found_parents.intersection(expected_parents)}, "
        f"Children: {found_children.intersection(expected_children)}"
    )

def test_combined_concept_search() -> None:
    """Test searching with multiple related concepts."""
    print("\nTesting multi-concept search...")

    success, result = sync_mcp_invoke_tool(
        tool_name="search_by_concepts",
        parameters={
            "concepts": ["Neural Networks", "Computer Vision"],
            "operator": "AND",  # Require both concepts
            "max_results": 5
        }
    )

    if not success:
        print_test_result(
            "Multi-Concept Search",
            False,
            f"Search failed: {result.get('error', 'Unknown error')}"
        )
        return

    # Check results
    documents = result.get("documents", [])
    if not documents:
        print_test_result(
            "Multi-Concept Search",
            False,
            "No documents found matching both concepts"
        )
        return

    # Should find CNN document
    found_cnn = any(
        "cnn" in doc.get("text", "").lower()
        for doc in documents
    )

    if not found_cnn:
        print_test_result(
            "Multi-Concept Search",
            False,
            "Expected to find CNN document matching both concepts"
        )
        return

    print_test_result(
        "Multi-Concept Search",
        True,
        f"Found {len(documents)} documents matching multiple concepts"
    )

if __name__ == "__main__":
    # Set up test documents first
    if not setup_test_documents():
        print("Failed to set up test documents. Skipping tests.")
        exit(1)

    run_pytest_async(__file__)