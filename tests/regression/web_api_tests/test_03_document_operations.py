import pytest
import uuid
from tests.regression.test_utils import start_services, stop_services, add_test_document, get_test_document_text, get_test_document_metadata

def generate_unique_document(index):
    """Generates a unique document for testing."""
    base_text = get_test_document_text()
    base_metadata = get_test_document_metadata()
    unique_id = str(uuid.uuid4())
    return {
        "text": f"{base_text}\nUnique content for document {index}: {unique_id}",
        "metadata": {
            **base_metadata,
            "title": f"{base_metadata['title']} - {index}",
            "source": f"{base_metadata['source']} - {unique_id}"
        }
    }

def test_single_document_addition():
    """Add one document via API"""
    print("\nTesting single document addition...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for single document addition test"
        print("Services started successfully for single document addition test.")

        # Add a single test document
        doc_text = get_test_document_text()
        doc_metadata = get_test_document_metadata()
        add_success, add_response = add_test_document(doc_text, doc_metadata)
        assert add_success, f"Failed to add single test document: {add_response.get('error', 'Unknown error')}"
        print("Single test document added successfully.")
        # Optional: Add assertions to check the response structure or content

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, "Failed to stop services after single document addition test"
            print("Services stopped successfully after single document addition test.")


def test_bulk_document_addition():
    """Add 50 random documents"""
    print("\nTesting bulk document addition...")
    process = None
    num_documents = 50
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for bulk document addition test"
        print("Services started successfully for bulk document addition test.")

        # Generate and add multiple documents
        print(f"Adding {num_documents} random documents...")
        for i in range(num_documents):
            doc_data = generate_unique_document(i)
            add_success, add_response = add_test_document(doc_data["text"], doc_data["metadata"])
            assert add_success, f"Failed to add document {i+1}: {add_response.get('error', 'Unknown error')}"
            # Optional: Add assertions to check the response for each document

        print(f"Successfully added {num_documents} documents.")

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, "Failed to stop services after bulk document addition test"
            print("Services stopped successfully after bulk document addition test.")


def test_duplicate_document():
    """Attempt to add duplicate document"""
    print("\nTesting duplicate document addition...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for duplicate document test"
        print("Services started successfully for duplicate document test.")

        # Add the first document
        doc_text = get_test_document_text()
        doc_metadata = get_test_document_metadata()
        add_success_first, add_response_first = add_test_document(doc_text, doc_metadata)
        assert add_success_first, f"Failed to add the first document: {add_response_first.get('error', 'Unknown error')}"
        print("First document added successfully.")

        # Attempt to add the same document again
        print("Attempting to add the same document again...")
        add_success_second, add_response_second = add_test_document(doc_text, doc_metadata)

        # Assert that the second attempt failed
        assert not add_success_second, "Duplicate document addition unexpectedly succeeded"
        print("Duplicate document addition correctly failed.")

        # Optional: Assert on the specific error message or status code if the API provides one
        # For example, if the API returns a 409 Conflict status code for duplicates:
        # assert add_response_second.get('status_code') == 409, f"Expected 409 status code for duplicate, but got {add_response_second.get('status_code')}"
        # Or if there's a specific error message:
        # assert "duplicate" in add_response_second.get('error', '').lower(), f"Expected duplicate error message, but got {add_response_second.get('error')}"

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, "Failed to stop services after duplicate document test"
            print("Services stopped successfully after duplicate document test.")