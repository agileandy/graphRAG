import time
import uuid

from scripts.database_management.clean_database import clean_database
from tests.regression.test_utils import (
    add_test_document,
    cancel_job,
    get_job_status,
    start_services,
    stop_services,
)  # Assuming these support MCP interaction


def generate_unique_document(index):
    """Generates a unique document for testing."""
    # Using a simple placeholder text structure
    return {
        "text": f"This is MCP job test document number {index}. It contains unique content. UUID: {uuid.uuid4()}",
        "metadata": {
            "title": f"MCP Job Test Document {index}",
            "author": "MCP Job Management Test",
            "category": "Test Data",
            "source": f"MCP Job Test {index}",
        },
    }


def test_mcp_job_status() -> None:
    """View job status via MCP."""
    print("\nTesting MCP job status monitoring...")
    process = None
    job_id = None
    num_documents = 50
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for MCP job status monitoring test"
        print("Services started successfully for MCP job status monitoring test.")

        # Clean database
        clean_success, clean_response = clean_database()
        assert clean_success, (
            f"Failed to clean database: {clean_response.get('error', 'Unknown error')}"
        )
        print("Database cleaned.")

        # Add multiple documents to create a job via MCP
        print(f"Adding {num_documents} documents to create a job via MCP...")
        for i in range(num_documents):
            doc_data = generate_unique_document(i)
            add_success, add_response = add_test_document(
                doc_data["text"], doc_data["metadata"], use_mcp=True
            )  # Assuming use_mcp flag or similar
            assert add_success, (
                f"Failed to add document {i + 1} via MCP: {add_response.get('error', 'Unknown error')}"
            )
            if i == 0:  # Capture job ID from the first document addition response
                job_id = add_response.get("job_id")
                assert job_id is not None, (
                    "Job ID not returned in add document response via MCP"
                )
                print(f"Captured job ID: {job_id}")

        assert job_id is not None, (
            "No job ID was captured after adding documents via MCP"
        )
        print(
            f"All {num_documents} documents added. Monitoring job {job_id} status via MCP..."
        )

        # Monitor job status via MCP
        timeout = 120  # seconds
        start_time = time.time()
        job_status = None

        while time.time() - start_time < timeout:
            status_success, status_response = get_job_status(
                job_id, use_mcp=True
            )  # Assuming use_mcp flag or similar
            assert status_success, (
                f"Failed to get job status for {job_id} via MCP: {status_response.get('error', 'Unknown error')}"
            )
            job_status = status_response.get("status")
            print(f"Job {job_id} status via MCP: {job_status}")

            if job_status in ["completed", "failed", "cancelled"]:
                break
            time.sleep(5)  # Wait before checking again

        # Assert that the job completed successfully
        assert job_status == "completed", (
            f"Job {job_id} did not complete via MCP. Final status: {job_status}"
        )
        print(f"Job {job_id} completed successfully via MCP.")

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, (
                "Failed to stop services after MCP job status monitoring test"
            )
            print("Services stopped successfully after MCP job status monitoring test.")


def test_mcp_job_cancellation() -> None:
    """Cancel job via MCP."""
    print("\nTesting MCP job cancellation...")
    process = None
    job_id = None
    num_documents = 50  # Add enough documents to ensure job is in progress
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for MCP job cancellation test"
        print("Services started successfully for MCP job cancellation test.")

        # Clean database
        clean_success, clean_response = clean_database()
        assert clean_success, (
            f"Failed to clean database: {clean_response.get('error', 'Unknown error')}"
        )
        print("Database cleaned.")

        # Add multiple documents to create a job via MCP
        print(
            f"Adding {num_documents} documents to create a job for cancellation via MCP..."
        )
        for i in range(num_documents):
            doc_data = generate_unique_document(i)
            add_success, add_response = add_test_document(
                doc_data["text"], doc_data["metadata"], use_mcp=True
            )  # Assuming use_mcp flag or similar
            assert add_success, (
                f"Failed to add document {i + 1} via MCP: {add_response.get('error', 'Unknown error')}"
            )
            if i == 0:  # Capture job ID from the first document addition response
                job_id = add_response.get("job_id")
                assert job_id is not None, (
                    "Job ID not returned in add document response for cancellation test via MCP"
                )
                print(f"Captured job ID for cancellation: {job_id}")

        assert job_id is not None, (
            "No job ID was captured after adding documents for cancellation via MCP"
        )
        print(
            f"All {num_documents} documents added. Attempting to cancel job {job_id} via MCP..."
        )

        # Wait briefly for the job to start processing
        time.sleep(5)

        # Cancel the job via MCP
        cancel_success, cancel_response = cancel_job(
            job_id, use_mcp=True
        )  # Assuming use_mcp flag or similar
        assert cancel_success, (
            f"Failed to cancel job {job_id} via MCP: {cancel_response.get('error', 'Unknown error')}"
        )
        print(f"Job {job_id} cancellation request successful via MCP.")

        # Monitor job status until cancelled or finished via MCP
        timeout = 60  # seconds
        start_time = time.time()
        job_status = None

        while time.time() - start_time < timeout:
            status_success, status_response = get_job_status(
                job_id, use_mcp=True
            )  # Assuming use_mcp flag or similar
            assert status_success, (
                f"Failed to get job status for {job_id} after cancellation via MCP: {status_response.get('error', 'Unknown error')}"
            )
            job_status = status_response.get("status")
            print(f"Job {job_id} status after cancellation via MCP: {job_status}")

            if job_status in ["cancelled", "completed", "failed"]:
                break
            time.sleep(5)  # Wait before checking again

        # Assert that the job was cancelled
        assert job_status == "cancelled", (
            f"Job {job_id} did not get cancelled via MCP. Final status: {job_status}"
        )
        print(f"Job {job_id} successfully cancelled via MCP.")

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, (
                "Failed to stop services after MCP job cancellation test"
            )
            print("Services stopped successfully after MCP job cancellation test.")
