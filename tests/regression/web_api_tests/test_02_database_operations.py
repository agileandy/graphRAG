import pytest
import time
import subprocess
from tests.regression.test_utils import start_services, stop_services, add_test_document, get_test_document_text, get_test_document_metadata, search_documents, check_api_health

def test_database_deletion():
    """Verify complete DB removal"""
    print("\nTesting database deletion...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for database deletion test"
        print("Services started successfully for database deletion test.")

        # Add a test document
        doc_text = get_test_document_text()
        doc_metadata = get_test_document_metadata()
        add_success, add_response = add_test_document(doc_text, doc_metadata)
        assert add_success, f"Failed to add test document: {add_response.get('error', 'Unknown error')}"
        print("Test document added successfully.")

        # Execute database cleanup script (services should be running)
        print("Executing database cleanup script...")
        cleanup_result = subprocess.run(
            ["python", "./scripts/database_management/clean_database.py", "--yes"],
            capture_output=True,
            text=True
        )
        print(f"Cleanup script stdout:\n{cleanup_result.stdout}")
        print(f"Cleanup script stderr:\n{cleanup_result.stderr}")
        assert cleanup_result.returncode == 0, f"Database cleanup script failed with error: {cleanup_result.stderr}"
        print("Database cleanup script executed successfully.")

        # Services are already started from the beginning of the test.
        # If cleanup requires a restart, that should be handled by the script or test_utils.
        # For now, assume services are still up or cleanup script handles restart if needed.

        # Verify database is empty by searching for the added document
        # A short delay might be needed for the index to reflect changes
        time.sleep(5)
        search_query = doc_metadata["title"]
        search_success, search_response = search_documents(search_query, n_results=1)
        assert search_success, f"Search failed after database deletion: {search_response.get('error', 'Unknown error')}"

        # Check if the document is found - it should not be
        vector_results = search_response.get('vector_results', {})
        documents = vector_results.get('documents', [])

        # Check if documents list is empty or contains empty lists
        is_empty = not documents or (isinstance(documents, list) and all(not doc for doc in documents))

        assert is_empty, f"Document '{search_query}' found after database deletion."
        print("Database is empty after deletion (correct).")

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, "Failed to stop services after database deletion test"
            print("Services stopped successfully after database deletion test.")


def test_database_initialization():
    """Test fresh DB initialization"""
    print("\nTesting database initialization...")
    process = None
    try:
        # Start services first
        success_start, process = start_services()
        assert success_start, "Failed to start services for database initialization test"
        print("Services started successfully for database initialization test.")

        # Ensure database is clean (services are now running)
        print("Ensuring database is clean before initialization test...")
        cleanup_result = subprocess.run(
            ["python", "./scripts/database_management/clean_database.py", "--yes"],
            capture_output=True,
            text=True
        )
        print(f"Cleanup script stdout:\n{cleanup_result.stdout}")
        print(f"Cleanup script stderr:\n{cleanup_result.stderr}")
        assert cleanup_result.returncode == 0, f"Database cleanup script failed before initialization: {cleanup_result.stderr}"
        print("Database cleaned successfully before initialization test.")

        # Execute database initialization script
        print("Executing database initialization script...")
        init_result = subprocess.run(
            ["python", "./scripts/database_management/initialize_database.py", "--yes"],
            capture_output=True,
            text=True
        )
        print(f"Initialization script stdout:\n{init_result.stdout}")
        print(f"Initialization script stderr:\n{init_result.stderr}")
        assert init_result.returncode == 0, f"Database initialization script failed with error: {init_result.stderr}"
        print("Database initialization script executed successfully.")

        # Verify database is initialized (e.g., check API health, which might indicate DB status)
        # A short delay might be needed for the database to be fully ready
        time.sleep(5)
        is_healthy, health_data = check_api_health()
        # Depending on the health check implementation, 'ok' or 'degraded' might be acceptable
        assert health_data.get('status') in ['ok', 'degraded'], f"API health check failed after initialization: {health_data}"
        print(f"API health check passed after initialization. Status: {health_data.get('status')}")

        # More specific checks could be added here if the initialization script
        # adds known data or sets specific database properties.

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, "Failed to stop services after database initialization test"
            print("Services stopped successfully after database initialization test.")