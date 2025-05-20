import uuid

from scripts.database_management.clean_database import clean_database
from tests.regression.test_utils import (
    add_test_document,
    get_document_count,
    start_services,
    stop_services,
)


def generate_unique_document(index):
    """Generates a unique document for testing."""
    return {
        "text": f"This is MCP test document number {index}. It contains unique content. UUID: {uuid.uuid4()}",
        "metadata": {
            "title": f"MCP Test Document {index}",
            "author": "MCP Document Operations Test",
            "category": "Test Data",
            "source": f"MCP Doc Test {index}",
        },
    }


def test_mcp_single_document() -> None:
    """Add doc via MCP."""
    print("\nTesting MCP single document addition...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for MCP single document test"
        print("Services started successfully for MCP single document test.")

        # Clean database
        clean_success, clean_response = clean_database()
        assert clean_success, (
            f"Failed to clean database: {clean_response.get('error', 'Unknown error')}"
        )
        print("Database cleaned.")

        # Add a single document
        doc_data = generate_unique_document(1)
        add_success, add_response = add_test_document(
            doc_data["text"], doc_data["metadata"], use_mcp=True
        )  # Assuming use_mcp flag or similar
        assert add_success, (
            f"Failed to add single document via MCP: {add_response.get('error', 'Unknown error')}"
        )
        print("Single document added via MCP.")

        # Verify the document was added (requires a utility function)
        # assert check_document_exists(doc_data["metadata"]["source"]), "Added document not found in database"
        # print("Added document verified in database.")

        # Basic verification using document count
        count_success, count_response = get_document_count(
            use_mcp=True
        )  # Assuming get_document_count supports MCP
        assert count_success, (
            f"Failed to get document count via MCP: {count_response.get('error', 'Unknown error')}"
        )
        assert count_response.get("count") == 1, (
            f"Expected 1 document, found {count_response.get('count')}"
        )
        print(f"Document count verified: {count_response.get('count')}")

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, (
                "Failed to stop services after MCP single document test"
            )
            print("Services stopped successfully after MCP single document test.")


def test_mcp_bulk_documents() -> None:
    """Add 50 docs via MCP."""
    print("\nTesting MCP bulk document addition...")
    process = None
    num_documents = 50
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for MCP bulk documents test"
        print("Services started successfully for MCP bulk documents test.")

        # Clean database
        clean_success, clean_response = clean_database()
        assert clean_success, (
            f"Failed to clean database: {clean_response.get('error', 'Unknown error')}"
        )
        print("Database cleaned.")

        # Add multiple documents
        print(f"Adding {num_documents} documents via MCP...")
        for i in range(num_documents):
            doc_data = generate_unique_document(i)
            add_success, add_response = add_test_document(
                doc_data["text"], doc_data["metadata"], use_mcp=True
            )  # Assuming use_mcp flag or similar
            assert add_success, (
                f"Failed to add document {i + 1} via MCP: {add_response.get('error', 'Unknown error')}"
            )
        print(f"{num_documents} documents added via MCP.")

        # Verify that 50 documents were added (requires a utility function)
        # assert get_document_count() == num_documents, f"Expected {num_documents} documents, found {get_document_count()}"
        # print(f"Document count verified: {get_documents_count()}")

        # Basic verification using document count
        count_success, count_response = get_document_count(
            use_mcp=True
        )  # Assuming get_document_count supports MCP
        assert count_success, (
            f"Failed to get document count via MCP: {count_response.get('error', 'Unknown error')}"
        )
        assert count_response.get("count") == num_documents, (
            f"Expected {num_documents} documents, found {count_response.get('count')}"
        )
        print(f"Document count verified: {count_response.get('count')}")

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, "Failed to stop services after MCP bulk documents test"
            print("Services stopped successfully after MCP bulk documents test.")


def test_mcp_duplicate() -> None:
    """Duplicate via MCP."""
    print("\nTesting MCP duplicate document addition...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for MCP duplicate document test"
        print("Services started successfully for MCP duplicate document test.")

        # Clean database
        clean_success, clean_response = clean_database()
        assert clean_success, (
            f"Failed to clean database: {clean_response.get('error', 'Unknown error')}"
        )
        print("Database cleaned.")

        # Add a single document
        doc_data = generate_unique_document(1)
        add_success_first, add_response_first = add_test_document(
            doc_data["text"], doc_data["metadata"], use_mcp=True
        )  # Assuming use_mcp flag or similar
        assert add_success_first, (
            f"Failed to add initial document via MCP: {add_response_first.get('error', 'Unknown error')}"
        )
        print("Initial document added via MCP.")

        # Attempt to add the same document again
        add_success_second, add_response_second = add_test_document(
            doc_data["text"], doc_data["metadata"], use_mcp=True
        )  # Assuming use_mcp flag or similar

        # Assert that the duplicate addition fails or is handled correctly
        # This assertion depends on how the API/MCP handles duplicates.
        # Assuming it returns success=False or a specific error message for duplicates.
        assert not add_success_second, (
            f"Duplicate document addition via MCP unexpectedly succeeded: {add_response_second}"
        )
        # Further checks could involve inspecting the error message or response structure
        print(
            "Duplicate document addition via MCP handled as expected (failed or rejected)."
        )

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, (
                "Failed to stop services after MCP duplicate document test"
            )
            print("Services stopped successfully after MCP duplicate document test.")
