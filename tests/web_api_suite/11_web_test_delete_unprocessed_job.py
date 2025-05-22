"""Test deleting unprocessed jobs functionality for the web API."""

import pytest
import time
from tests.common_utils.test_utils import (
    print_test_result,
    get_job_status,
    cancel_job
)

def add_test_job() -> tuple[bool, str]:
    """Helper function to add a test job.

    This is a placeholder - actual implementation would use the API.
    """
    try:
        # Mock successful job creation
        job_id = "test_job_123"
        return True, job_id
    except Exception as e:
        return False, str(e)

def test_delete_pending_job() -> None:
    """Test deleting a job that is still pending."""
    print("\nTesting pending job deletion...")

    # Add a new job
    success, job_id = add_test_job()
    if not success:
        print_test_result(
            "Delete Pending Job",
            False,
            f"Failed to create test job: {job_id}"
        )
        return

    # Verify it's in pending state
    success, result = get_job_status(job_id)
    if not success or result.get("status") != "pending":
        print_test_result(
            "Delete Pending Job",
            False,
            "Job not in expected pending state"
        )
        return

    # Try to delete it
    success, result = cancel_job(job_id)

    if not success:
        print_test_result(
            "Delete Pending Job",
            False,
            f"Failed to delete job: {result.get('error', 'Unknown error')}"
        )
        return

    # Verify job is no longer found
    success, status_result = get_job_status(job_id)
    if success:
        print_test_result(
            "Delete Pending Job",
            False,
            "Job still exists after deletion"
        )
        return

    print_test_result(
        "Delete Pending Job",
        True,
        "Pending job successfully deleted"
    )

def test_delete_in_progress_job() -> None:
    """Test deleting a job that is currently in progress."""
    print("\nTesting in-progress job deletion...")

    # Add a new job
    success, job_id = add_test_job()
    if not success:
        print_test_result(
            "Delete In-Progress Job",
            False,
            f"Failed to create test job: {job_id}"
        )
        return

    # Wait briefly to let job start processing
    time.sleep(1)

    # Try to delete it
    success, result = cancel_job(job_id)

    if not success:
        print_test_result(
            "Delete In-Progress Job",
            False,
            f"Failed to delete job: {result.get('error', 'Unknown error')}"
        )
        return

    # Verify job is marked as cancelled
    success, status_result = get_job_status(job_id)
    if not success:
        print_test_result(
            "Delete In-Progress Job",
            False,
            "Failed to get job status after deletion"
        )
        return

    status = status_result.get("status")
    if status != "cancelled":
        print_test_result(
            "Delete In-Progress Job",
            False,
            f"Expected status 'cancelled', got '{status}'"
        )
        return

    print_test_result(
        "Delete In-Progress Job",
        True,
        "In-progress job successfully cancelled"
    )

def test_delete_completed_job() -> None:
    """Test attempting to delete a completed job (should fail)."""
    print("\nTesting completed job deletion...")

    # Add a new job
    success, job_id = add_test_job()
    if not success:
        print_test_result(
            "Delete Completed Job",
            False,
            f"Failed to create test job: {job_id}"
        )
        return

    # Wait for job to complete
    time.sleep(2)

    # Verify it's completed
    success, result = get_job_status(job_id)
    if not success or result.get("status") != "completed":
        print_test_result(
            "Delete Completed Job",
            False,
            "Job not in expected completed state"
        )
        return

    # Try to delete it - should fail
    success, result = cancel_job(job_id)

    if success:
        print_test_result(
            "Delete Completed Job",
            False,
            "System allowed deletion of completed job"
        )
        return

    error_message = result.get("error", "")
    if "completed" not in error_message.lower():
        print_test_result(
            "Delete Completed Job",
            False,
            f"Unexpected error message: {error_message}"
        )
        return

    print_test_result(
        "Delete Completed Job",
        True,
        "Correctly prevented deletion of completed job"
    )

def test_delete_nonexistent_job() -> None:
    """Test attempting to delete a nonexistent job."""
    print("\nTesting nonexistent job deletion...")

    # Try to delete a nonexistent job
    success, result = cancel_job("nonexistent_job_id")

    if success:
        print_test_result(
            "Delete Nonexistent Job",
            False,
            "System reported success for nonexistent job deletion"
        )
        return

    error_message = result.get("error", "")
    if "not found" not in error_message.lower():
        print_test_result(
            "Delete Nonexistent Job",
            False,
            f"Unexpected error message: {error_message}"
        )
        return

    print_test_result(
        "Delete Nonexistent Job",
        True,
        "Correctly handled nonexistent job deletion attempt"
    )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])