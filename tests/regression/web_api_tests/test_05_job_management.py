import time
import uuid

from tests.regression.test_utils import (
    add_test_document,
    cancel_job,
    get_job_status,
    start_services,
    stop_services,
)


def generate_unique_document(index):
    """Generates a unique document for testing."""
    # Using a simple placeholder text structure
    return {
        "text": f"This is test document number {index}. It contains unique content. UUID: {uuid.uuid4()}",
        "metadata": {
            "title": f"Test Document {index}",
            "author": "Job Management Test",
            "category": "Test Data",
            "source": f"Job Test {index}",
        },
    }


def test_job_status_monitoring() -> None:
    """View 50-doc job status."""
    print("\nTesting job status monitoring...")
    process = None
    job_id = None
    num_documents = 50
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for job status monitoring test"
        print("Services started successfully for job status monitoring test.")

        # Add multiple documents to create a job
        print(f"Adding {num_documents} documents to create a job...")
        for i in range(num_documents):
            doc_data = generate_unique_document(i)
            add_success, add_response = add_test_document(
                doc_data["text"], doc_data["metadata"]
            )
            assert add_success, (
                f"Failed to add document {i + 1}: {add_response.get('error', 'Unknown error')}"
            )
            if i == 0:  # Capture job ID from the first document addition response
                job_id = add_response.get("job_id")
                assert job_id is not None, (
                    "Job ID not returned in add document response"
                )
                print(f"Captured job ID: {job_id}")

        assert job_id is not None, "No job ID was captured after adding documents"
        print(f"All {num_documents} documents added. Monitoring job {job_id} status...")

        # Monitor job status
        timeout = 120  # seconds
        start_time = time.time()
        job_status = None

        while time.time() - start_time < timeout:
            status_success, status_response = get_job_status(job_id)
            assert status_success, (
                f"Failed to get job status for {job_id}: {status_response.get('error', 'Unknown error')}"
            )
            job_status = status_response.get("status")
            print(f"Job {job_id} status: {job_status}")

            if job_status in ["completed", "failed", "cancelled"]:
                break
            time.sleep(5)  # Wait before checking again

        # Assert that the job completed successfully
        assert job_status == "completed", (
            f"Job {job_id} did not complete. Final status: {job_status}"
        )
        print(f"Job {job_id} completed successfully.")

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, (
                "Failed to stop services after job status monitoring test"
            )
            print("Services stopped successfully after job status monitoring test.")


def test_job_cancellation() -> None:
    """Cancel in-progress job."""
    print("\nTesting job cancellation...")
    process = None
    job_id = None
    num_documents = 50  # Add enough documents to ensure job is in progress
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services for job cancellation test"
        print("Services started successfully for job cancellation test.")

        # Add multiple documents to create a job
        print(f"Adding {num_documents} documents to create a job for cancellation...")
        for i in range(num_documents):
            doc_data = generate_unique_document(i)
            add_success, add_response = add_test_document(
                doc_data["text"], doc_data["metadata"]
            )
            assert add_success, (
                f"Failed to add document {i + 1}: {add_response.get('error', 'Unknown error')}"
            )
            if i == 0:  # Capture job ID from the first document addition response
                job_id = add_response.get("job_id")
                assert job_id is not None, (
                    "Job ID not returned in add document response for cancellation test"
                )
                print(f"Captured job ID for cancellation: {job_id}")

        assert job_id is not None, (
            "No job ID was captured after adding documents for cancellation"
        )
        print(
            f"All {num_documents} documents added. Attempting to cancel job {job_id}..."
        )

        # Wait briefly for the job to start processing
        time.sleep(5)

        # Cancel the job
        cancel_success, cancel_response = cancel_job(job_id)
        assert cancel_success, (
            f"Failed to cancel job {job_id}: {cancel_response.get('error', 'Unknown error')}"
        )
        print(f"Job {job_id} cancellation request successful.")

        # Monitor job status until cancelled or finished
        timeout = 60  # seconds
        start_time = time.time()
        job_status = None

        while time.time() - start_time < timeout:
            status_success, status_response = get_job_status(job_id)
            assert status_success, (
                f"Failed to get job status for {job_id} after cancellation: {status_response.get('error', 'Unknown error')}"
            )
            job_status = status_response.get("status")
            print(f"Job {job_id} status after cancellation: {job_status}")

            if job_status in ["cancelled", "completed", "failed"]:
                break
            time.sleep(5)  # Wait before checking again

        # Assert that the job was cancelled
        assert job_status == "cancelled", (
            f"Job {job_id} did not get cancelled. Final status: {job_status}"
        )
        print(f"Job {job_id} successfully cancelled.")

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, "Failed to stop services after job cancellation test"
            print("Services stopped successfully after job cancellation test.")
