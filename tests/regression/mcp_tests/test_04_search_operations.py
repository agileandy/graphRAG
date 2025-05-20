from scripts.database_management.clean_database import clean_database
from tests.regression.test_utils import (
    add_test_document,
    perform_search,
    start_services,
    stop_services,
)  # Assuming perform_search supports MCP and different search types


def add_documents_for_search() -> None:
    """Adds documents with content and relationships for search tests."""
    doc1_text = "This document is about artificial intelligence and machine learning."
    doc1_metadata = {"title": "AI and ML Intro", "source": "doc1"}

    doc2_text = "Natural language processing is a subfield of artificial intelligence."
    doc2_metadata = {"title": "NLP Basics", "source": "doc2"}

    doc3_text = "Graph databases like Neo4j are useful for storing relationships."
    doc3_metadata = {"title": "Graph Databases", "source": "doc3"}

    add_test_document(doc1_text, doc1_metadata, use_mcp=True)
    add_test_document(doc2_text, doc2_metadata, use_mcp=True)
    add_test_document(doc3_text, doc3_metadata, use_mcp=True)
    # Add more documents and potentially define relationships if the utility function supports it
    # For now, relying on automatic concept/relationship extraction during document addition


def test_mcp_chroma_search() -> None:
    """Basic Chroma search via MCP."""
    print("\nTesting MCP Chroma search...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for MCP Chroma search test"
        print("Services started successfully for MCP Chroma search test.")

        # Clean database
        clean_success, clean_response = clean_database()
        assert clean_success, (
            f"Failed to clean database: {clean_response.get('error', 'Unknown error')}"
        )
        print("Database cleaned.")

        # Add documents for searching
        add_documents_for_search()
        # Add a small delay to allow processing
        import time

        time.sleep(10)  # Adjust based on expected processing time

        # Perform Chroma search
        search_query = "artificial intelligence"
        search_success, search_response = perform_search(
            search_query, search_type="Chroma", use_mcp=True
        )  # Assuming search_type and use_mcp flags
        assert search_success, (
            f"Chroma search via MCP failed: {search_response.get('error', 'Unknown error')}"
        )
        print(f"Chroma search for '{search_query}' successful via MCP.")

        # Assert that relevant results are returned
        assert len(search_response.get("results", [])) > 0, (
            "Chroma search returned no results"
        )
        # Further assertions could check for specific document titles or content in results
        print(
            f"Chroma search returned {len(search_response.get('results', []))} results."
        )

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, "Failed to stop services after MCP Chroma search test"
            print("Services stopped successfully after MCP Chroma search test.")


def test_mcp_hybrid_search() -> None:
    """Hybrid search via MCP."""
    print("\nTesting MCP Hybrid search...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for MCP Hybrid search test"
        print("Services started successfully for MCP Hybrid search test.")

        # Clean database
        clean_success, clean_response = clean_database()
        assert clean_success, (
            f"Failed to clean database: {clean_response.get('error', 'Unknown error')}"
        )
        print("Database cleaned.")

        # Add documents with concepts and relationships
        add_documents_for_search()
        # Add a small delay to allow processing
        import time

        time.sleep(10)  # Adjust based on expected processing time

        # Perform Hybrid search
        search_query = "AI and graph databases"
        search_success, search_response = perform_search(
            search_query, search_type="Hybrid", use_mcp=True
        )  # Assuming search_type and use_mcp flags
        assert search_success, (
            f"Hybrid search via MCP failed: {search_response.get('error', 'Unknown error')}"
        )
        print(f"Hybrid search for '{search_query}' successful via MCP.")

        # Assert that relevant results are returned (combining vector and graph)
        assert len(search_response.get("results", [])) > 0, (
            "Hybrid search returned no results"
        )
        # Further assertions could check for results related to both AI and graph databases
        print(
            f"Hybrid search returned {len(search_response.get('results', []))} results."
        )

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, "Failed to stop services after MCP Hybrid search test"
            print("Services stopped successfully after MCP Hybrid search test.")


def test_mcp_concept_relationships() -> None:
    """Concept relations via MCP."""
    print("\nTesting MCP concept relationships search...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for MCP concept relationships test"
        print("Services started successfully for MCP concept relationships test.")

        # Clean database
        clean_success, clean_response = clean_database()
        assert clean_success, (
            f"Failed to clean database: {clean_response.get('error', 'Unknown error')}"
        )
        print("Database cleaned.")

        # Add documents with concepts and relationships
        add_documents_for_search()
        # Add a small delay to allow processing
        import time

        time.sleep(10)  # Adjust based on expected processing time

        # Search by concept relationships
        concept_query = "artificial intelligence"  # Assuming searching for documents related to this concept
        search_success, search_response = perform_search(
            concept_query, search_type="ConceptRelationships", use_mcp=True
        )  # Assuming search_type and use_mcp flags
        assert search_success, (
            f"Concept relationships search via MCP failed: {search_response.get('error', 'Unknown error')}"
        )
        print(f"Concept relationships search for '{concept_query}' successful via MCP.")

        # Assert that relevant results are returned based on relationships
        assert len(search_response.get("results", [])) > 0, (
            "Concept relationships search returned no results"
        )
        # Further assertions could check for documents linked to the concept 'artificial intelligence'
        print(
            f"Concept relationships search returned {len(search_response.get('results', []))} results."
        )

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, (
                "Failed to stop services after MCP concept relationships test"
            )
            print("Services stopped successfully after MCP concept relationships test.")
