"""Test graph-based concept search functionality for the web API."""

import pytest
from tests.common_utils.test_utils import (
    print_test_result,
    add_test_document,
    get_concept,
    get_all_concepts,
    get_documents_for_concept
)

def setup_test_documents() -> bool:
    """Set up test documents with concepts for searching."""
    documents = [
        {
            "text": """
            Vector embeddings are numerical representations of data in high-dimensional
            space. They capture semantic meaning, allowing for similarity comparisons
            between different pieces of content. In NLP, word embeddings like Word2Vec
            and GloVe have been particularly successful.
            """,
            "metadata": {
                "title": "Understanding Vector Embeddings",
                "author": "Test Author",
                "category": "AI",
                "source": "Test Suite",
                "concepts": ["Vector Embeddings", "NLP", "Word2Vec"]
            }
        },
        {
            "text": """
            Natural Language Processing (NLP) is a branch of AI focused on enabling
            computers to understand and process human language. It combines linguistics,
            computer science, and machine learning. Modern NLP systems use transformer
            architectures extensively.
            """,
            "metadata": {
                "title": "Introduction to NLP",
                "author": "Test Author",
                "category": "AI",
                "source": "Test Suite",
                "concepts": ["NLP", "Transformers", "Machine Learning"]
            }
        },
        {
            "text": """
            Transformer models have revolutionized machine learning, especially in NLP.
            Their self-attention mechanism allows them to process sequences effectively.
            BERT and GPT are prominent examples of transformer-based models.
            """,
            "metadata": {
                "title": "Transformer Models",
                "author": "Test Author",
                "category": "AI",
                "source": "Test Suite",
                "concepts": ["Transformers", "BERT", "GPT", "Self-Attention"]
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

def test_direct_concept_search() -> None:
    """Test searching for documents directly related to a concept."""
    print("\nTesting direct concept search...")

    concept_name = "NLP"
    success, result = get_documents_for_concept(concept_name)

    if not success:
        print_test_result(
            "Direct Concept Search",
            False,
            f"Failed to search for concept {concept_name}: {result.get('error', 'Unknown error')}"
        )
        return

    documents = result.get("documents", [])
    if not documents:
        print_test_result(
            "Direct Concept Search",
            False,
            f"No documents found for concept {concept_name}"
        )
        return

    # Should find at least 2 documents (explicitly mentioning NLP)
    if len(documents) < 2:
        print_test_result(
            "Direct Concept Search",
            False,
            f"Expected at least 2 documents for {concept_name}, found {len(documents)}"
        )
        return

    print_test_result(
        "Direct Concept Search",
        True,
        f"Found {len(documents)} documents for concept {concept_name}"
    )

def test_related_concept_search() -> None:
    """Test finding documents through related concepts."""
    print("\nTesting related concept search...")

    # First get details about the Transformers concept
    success, concept_result = get_concept("Transformers")

    if not success:
        print_test_result(
            "Related Concept Search",
            False,
            f"Failed to get concept details: {concept_result.get('error', 'Unknown error')}"
        )
        return

    # Get related concepts
    related_concepts = concept_result.get("related_concepts", [])
    if not related_concepts:
        print_test_result(
            "Related Concept Search",
            False,
            "No related concepts found"
        )
        return

    # Should find related concepts like BERT, GPT, Self-Attention
    expected_related = {"BERT", "GPT", "Self-Attention"}
    found_related = set(related_concepts)
    if not expected_related.intersection(found_related):
        print_test_result(
            "Related Concept Search",
            False,
            f"Expected to find some of {expected_related}, found {found_related}"
        )
        return

    print_test_result(
        "Related Concept Search",
        True,
        f"Found expected related concepts: {found_related.intersection(expected_related)}"
    )

def test_concept_hierarchy() -> None:
    """Test traversing concept hierarchies."""
    print("\nTesting concept hierarchy traversal...")

    # Get all concepts to analyze the hierarchy
    success, result = get_all_concepts()

    if not success:
        print_test_result(
            "Concept Hierarchy",
            False,
            f"Failed to get concepts: {result.get('error', 'Unknown error')}"
        )
        return

    concepts = result.get("concepts", [])
    if not concepts:
        print_test_result(
            "Concept Hierarchy",
            False,
            "No concepts found in the system"
        )
        return

    # Check for expected hierarchy relationships
    # e.g., NLP should be related to both Vector Embeddings and Transformers
    nlp_concept = next((c for c in concepts if c["name"] == "NLP"), None)
    if not nlp_concept:
        print_test_result(
            "Concept Hierarchy",
            False,
            "NLP concept not found"
        )
        return

    related = set(nlp_concept.get("related", []))
    expected = {"Vector Embeddings", "Transformers"}
    if not expected.intersection(related):
        print_test_result(
            "Concept Hierarchy",
            False,
            f"Expected NLP to be related to some of {expected}, found {related}"
        )
        return

    print_test_result(
        "Concept Hierarchy",
        True,
        f"Found expected concept relationships: {related.intersection(expected)}"
    )

if __name__ == "__main__":
    # Set up test documents first
    if not setup_test_documents():
        print("Failed to set up test documents. Skipping tests.")
        exit(1)

    pytest.main([__file__, "-v"])