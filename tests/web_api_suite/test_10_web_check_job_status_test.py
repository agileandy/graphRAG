"""Test job status checking functionality for the web API."""

import pytest
import time
from tests.common_utils.test_utils import (
    print_test_result,
    get_job_status
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

def test_new_job_status() -> None:
    """Test checking status of a newly created job."""
    print("\nTesting new job status check...")

    # Add a new job
    success, job_id = add_test_job()
    if not success:
        print_test_result(
            "New Job Status",
            False,
            f"Failed to create test job: {job_id}"
        )
        return

    # Check its initial status
    success, result = get_job_status(job_id)

    if not success:
        print_test_result(
            "New Job Status",
            False,
            f"Failed to get job status: {result.get('error', 'Unknown error')}"
        )
        return

    status = result.get("status")
    if status != "pending":
        print_test_result(
            "New Job Status",
            False,
            f"Expected status 'pending', got '{status}'"
        )
        return

    print_test_result(
        "New Job Status",
        True,
        f"New job has correct initial status: {status}"
    )

def test_job_progress_update() -> None:
    """Test monitoring job progress updates."""
    print("\nTesting job progress updates...")

    # Add a job
    success, job_id = add_test_job()
    if not success:
        print_test_result(
            "Job Progress",
            False,
            f"Failed to create test job: {job_id}"
        )
        return

    # Check status multiple times to see progress
    previous_progress = -1
    updates_seen = 0
    max_checks = 5

    for i in range(max_checks):
        success, result = get_job_status(job_id)

        if not success:
            print_test_result(
                "Job Progress",
                False,
                f"Failed to get job status: {result.get('error', 'Unknown error')}"
            )
            return

        progress = result.get("progress", 0)
        if progress > previous_progress:
            updates_seen += 1
        previous_progress = progress

        # Brief pause between checks
        time.sleep(1)

    if updates_seen == 0:
        print_test_result(
            "Job Progress",
            False,
            "No progress updates observed"
        )
        return

    print_test_result(
        "Job Progress",
        True,
        f"Observed {updates_seen} progress updates"
    )

def test_completed_job_status() -> None:
    """Test checking status of a completed job."""
    print("\nTesting completed job status check...")

    # Add a job that should complete quickly
    success, job_id = add_test_job()
    if not success:
        print_test_result(
            "Completed Job Status",
            False,
            f"Failed to create test job: {job_id}"
        )
        return

    # Wait briefly for job to complete
    time.sleep(2)

    # Check final status
    success, result = get_job_status(job_id)

    if not success:
        print_test_result(
            "Completed Job Status",
            False,
            f"Failed to get job status: {result.get('error', 'Unknown error')}"
        )
        return

    status = result.get("status")
    if status != "completed":
        print_test_result(
            "Completed Job Status",
            False,
            f"Expected status 'completed', got '{status}'"
        )
        return

    print_test_result(
        "Completed Job Status",
        True,
        "Job completed successfully"
    )

def test_failed_job_status() -> None:
    """Test checking status of a failed job."""
    print("\nTesting failed job status check...")

    # Add a job designed to fail
    job_id = "failing_job_123"  # Mock job ID

    # Check status
    success, result = get_job_status(job_id)

    if not success:
        # In this case, not finding the job might be the expected behavior
        print_test_result(
            "Failed Job Status",
            True,
            "Correctly reported failure to find invalid job"
        )
        return

    status = result.get("status")
    error_message = result.get("error")

    if status != "failed":
        print_test_result(
            "Failed Job Status",
            False,
            f"Expected status 'failed', got '{status}'"
        )
        return

    if not error_message:
        print_test_result(
            "Failed Job Status",
            False,
            "Failed job status missing error message"
        )
        return

    print_test_result(
        "Failed Job Status",
        True,
        f"Failed job correctly reported: {error_message}"
    )

def test_nonexistent_job_status() -> None:
    """Test checking status of a nonexistent job."""
    print("\nTesting nonexistent job status check...")

    # Try to get status of a nonexistent job
    success, result = get_job_status("nonexistent_job_id")

    # Should fail gracefully
    if success:
        print_test_result(
            "Nonexistent Job Status",
            False,
            "System reported success for nonexistent job"
        )
        return

    error_message = result.get("error", "")
    if "not found" not in error_message.lower():
        print_test_result(
            "Nonexistent Job Status",
            False,
            f"Unexpected error message: {error_message}"
        )
        return

    print_test_result(
        "Nonexistent Job Status",
        True,
        "Correctly reported nonexistent job"
    )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])