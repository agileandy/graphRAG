import time

from tests.regression.test_utils import (
    add_test_document,
    get_concept,
    get_documents_for_concept,
    search_documents,
    start_services,
    stop_services,
)

# Define test documents for search operations
CHROMA_TEST_DOC_TEXT = """
Vector databases like ChromaDB are essential for efficient similarity search
in high-dimensional spaces. They store vector embeddings and allow for
fast retrieval of similar vectors based on distance metrics.
"""
CHROMA_TEST_DOC_METADATA = {
    "title": "Introduction to Vector Databases",
    "author": "Search Test",
    "category": "Databases",
    "source": "Search Test",
}

HYBRID_TEST_DOC_AI_TEXT = """
Artificial Intelligence (AI) is a broad field focused on creating intelligent agents
that perceive their environment and take actions to maximize their chance of achieving goals.
Machine Learning is a key subfield of AI.
"""
HYBRID_TEST_DOC_AI_METADATA = {
    "title": "Overview of Artificial Intelligence",
    "author": "Hybrid Search Test",
    "category": "AI",
    "source": "Hybrid Search Test",
}

HYBRID_TEST_DOC_ML_TEXT = """
Machine Learning (ML) is a subfield of Artificial Intelligence that focuses on
the development of algorithms that allow computers to learn from data.
Neural Networks are a popular type of model used in Machine Learning.
"""
HYBRID_TEST_DOC_ML_METADATA = {
    "title": "Introduction to Machine Learning",
    "author": "Hybrid Search Test",
    "category": "AI",
    "source": "Hybrid Search Test",
}

CONCEPT_RELATIONSHIP_DOC_TEXT = """
A Book is a type of Document.
A Book can have an Author.
An Author writes a Book.
"""
CONCEPT_RELATIONSHIP_DOC_METADATA = {
    "title": "Defining Document Relationships",
    "author": "Concept Test",
    "category": "Metadata",
    "source": "Concept Test",
}


def test_chroma_search() -> None:
    """Basic Chroma search."""
    print("\nTesting Chroma search...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for Chroma search test"
        print("Services started successfully for Chroma search test.")

        # Add a test document
        add_success, add_response = add_test_document(
            CHROMA_TEST_DOC_TEXT, CHROMA_TEST_DOC_METADATA
        )
        assert add_success, (
            f"Failed to add Chroma test document: {add_response.get('error', 'Unknown error')}"
        )
        print("Chroma test document added successfully.")

        # Allow time for processing and indexing
        time.sleep(10)

        # Perform a search that should match the document content
        search_query = "What are vector databases used for?"
        search_success, search_response = search_documents(search_query, n_results=1)
        assert search_success, (
            f"Chroma search failed: {search_response.get('error', 'Unknown error')}"
        )
        print("Chroma search performed successfully.")

        # Assert that the relevant document is returned in vector results
        vector_results = search_response.get("vector_results", {})
        documents = vector_results.get("documents", [])
        metadatas = vector_results.get("metadatas", [])

        assert len(documents) > 0 and len(documents[0]) > 0, (
            "Chroma search returned no documents"
        )
        assert CHROMA_TEST_DOC_METADATA["title"] in metadatas[0][0].get("title", ""), (
            "Chroma search did not return the expected document"
        )
        print("Chroma search returned the expected document.")

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, "Failed to stop services after Chroma search test"
            print("Services stopped successfully after Chroma search test.")


def test_hybrid_search() -> None:
    """Chroma + Neo4j related concepts."""
    print("\nTesting hybrid search...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for hybrid search test"
        print("Services started successfully for hybrid search test.")

        # Add documents with related concepts
        add_success_ai, add_response_ai = add_test_document(
            HYBRID_TEST_DOC_AI_TEXT, HYBRID_TEST_DOC_AI_METADATA
        )
        assert add_success_ai, (
            f"Failed to add AI test document: {add_response_ai.get('error', 'Unknown error')}"
        )
        print("AI test document added successfully.")

        add_success_ml, add_response_ml = add_test_document(
            HYBRID_TEST_DOC_ML_TEXT, HYBRID_TEST_DOC_ML_METADATA
        )
        assert add_success_ml, (
            f"Failed to add ML test document: {add_response_ml.get('error', 'Unknown error')}"
        )
        print("ML test document added successfully.")

        # Allow time for processing, indexing, and graph creation
        time.sleep(20)

        # Perform a hybrid search (query related to ML, with hops)
        search_query = "Tell me about Machine Learning"
        search_success, search_response = search_documents(
            search_query, n_results=1, max_hops=1
        )
        assert search_success, (
            f"Hybrid search failed: {search_response.get('error', 'Unknown error')}"
        )
        print("Hybrid search performed successfully.")

        # Assert that results from both vector and graph search are present and relevant
        vector_results = search_response.get("vector_results", {})
        graph_results = search_response.get("graph_results", {})

        assert len(vector_results.get("documents", [])) > 0, (
            "Hybrid search returned no vector results"
        )
        assert (
            len(graph_results.get("nodes", [])) > 0
            or len(graph_results.get("relationships", [])) > 0
        ), "Hybrid search returned no graph results"

        # Verify that the ML document is in vector results and AI concept/document is in graph results
        vector_metadatas = vector_results.get("metadatas", [])
        assert any(
            HYBRID_TEST_DOC_ML_METADATA["title"] in meta.get("title", "")
            for meta_list in vector_metadatas
            for meta in meta_list
        ), "ML document not found in vector results"

        graph_nodes = graph_results.get("nodes", [])
        assert any(
            node.get("properties", {}).get("name") == "Artificial Intelligence"
            for node in graph_nodes
        ), "Artificial Intelligence concept not found in graph results"

        print("Hybrid search returned expected results from both vector and graph.")

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, "Failed to stop services after hybrid search test"
            print("Services stopped successfully after hybrid search test.")


def test_concept_relationships() -> None:
    """Find books by concept relationships."""
    print("\nTesting concept relationships...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for concept relationships test"
        print("Services started successfully for concept relationships test.")

        # Add a document defining relationships
        add_success_rel, add_response_rel = add_test_document(
            CONCEPT_RELATIONSHIP_DOC_TEXT, CONCEPT_RELATIONSHIP_DOC_METADATA
        )
        assert add_success_rel, (
            f"Failed to add concept relationship document: {add_response_rel.get('error', 'Unknown error')}"
        )
        print("Concept relationship document added successfully.")

        # Add a document that is a "Book" and has an "Author"
        book_doc_text = """
        This is the content of a test book.
        The author of this book is Jane Doe.
        """
        book_doc_metadata = {
            "title": "Test Book Title",
            "author": "Jane Doe",
            "category": "Fiction",
            "source": "Concept Test Book",
            "type": "Book",  # Explicitly define type for testing
        }
        add_success_book, add_response_book = add_test_document(
            book_doc_text, book_doc_metadata
        )
        assert add_success_book, (
            f"Failed to add book document: {add_response_book.get('error', 'Unknown error')}"
        )
        print("Book document added successfully.")

        # Allow time for processing and graph creation
        time.sleep(20)

        # Verify the "Book" concept exists and has relationships
        concept_name = "Book"
        concept_success, concept_response = get_concept(concept_name)
        assert concept_success, (
            f"Failed to get concept '{concept_name}': {concept_response.get('error', 'Unknown error')}"
        )
        print(f"Concept '{concept_name}' retrieved successfully.")
        # Assert that the concept has expected properties or relationships if available in the response

        # Verify documents related to the "Book" concept can be retrieved
        docs_for_concept_success, docs_for_concept_response = get_documents_for_concept(
            concept_name
        )
        assert docs_for_concept_success, (
            f"Failed to get documents for concept '{concept_name}': {docs_for_concept_response.get('error', 'Unknown error')}"
        )
        print(f"Documents for concept '{concept_name}' retrieved successfully.")

        # Assert that the added book document is in the results
        concept_docs = docs_for_concept_response.get("documents", [])
        assert any(
            doc.get("metadata", {}).get("title") == book_doc_metadata["title"]
            for doc in concept_docs
        ), "Added book document not found when searching by concept"
        print("Added book document found when searching by concept.")

        # Optional: Verify relationships via graph search if a specific tool exists for it
        # For example, searching for books by author concept

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, (
                "Failed to stop services after concept relationships test"
            )
            print("Services stopped successfully after concept relationships test.")
