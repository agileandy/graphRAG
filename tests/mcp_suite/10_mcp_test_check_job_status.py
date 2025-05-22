"""Test job status checking functionality for the MCP server."""

import pytest
import time
from tests.common_utils.test_utils import (
    print_test_result,
    sync_mcp_invoke_tool,
    run_pytest_async
)

def create_test_job() -> tuple[bool, str]:
    """Create a test job and return its ID."""
    success, result = sync_mcp_invoke_tool(
        tool_name="add_job",
        parameters={
            "type": "text_analysis",
            "priority": "normal",
            "input": {
                "text": "Test job content",
                "format": "plain"
            }
        }
    )

    if not success:
        return False, f"Failed to create job: {result.get('error', 'Unknown error')}"

    job_id = result.get("job_id")
    if not job_id:
        return False, "No job ID returned"

    return True, job_id

def test_initial_job_status() -> None:
    """Test checking status of a newly created job."""
    print("\nTesting initial job status...")

    # Create a new job
    success, result = create_test_job()
    if not success:
        print_test_result(
            "Initial Job Status",
            False,
            result
        )
        return

    job_id = result

    # Check its status
    success, result = sync_mcp_invoke_tool(
        tool_name="get_job_status",
        parameters={"job_id": job_id}
    )

    if not success:
        print_test_result(
            "Initial Job Status",
            False,
            f"Failed to get job status: {result.get('error', 'Unknown error')}"
        )
        return

    status = result.get("status")
    if status not in ["pending", "queued"]:
        print_test_result(
            "Initial Job Status",
            False,
            f"Unexpected initial status: {status}"
        )
        return

    print_test_result(
        "Initial Job Status",
        True,
        f"Job has correct initial status: {status}"
    )

def test_job_progress() -> None:
    """Test monitoring job progress updates."""
    print("\nTesting job progress updates...")

    # Create a job
    success, result = create_test_job()
    if not success:
        print_test_result(
            "Job Progress",
            False,
            result
        )
        return

    job_id = result

    # Check status multiple times to see progress
    previous_progress = -1
    updates_seen = 0
    max_checks = 5

    for i in range(max_checks):
        success, result = sync_mcp_invoke_tool(
            tool_name="get_job_status",
            parameters={"job_id": job_id}
        )

        if not success:
            print_test_result(
                "Job Progress",
                False,
                f"Failed to get job status: {result.get('error', 'Unknown error')}"
            )
            return

        current_progress = result.get("progress", 0)
        if current_progress > previous_progress:
            updates_seen += 1
        previous_progress = current_progress

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
    print("\nTesting completed job status...")

    # Create a quick job
    success, result = sync_mcp_invoke_tool(
        tool_name="add_job",
        parameters={
            "type": "quick_task",
            "priority": "high",
            "input": {
                "text": "Quick processing",
                "timeout": 1
            }
        }
    )

    if not success:
        print_test_result(
            "Completed Job Status",
            False,
            f"Failed to create job: {result.get('error', 'Unknown error')}"
        )
        return

    job_id = result.get("job_id")

    # Wait briefly for completion
    time.sleep(2)

    # Check final status
    success, result = sync_mcp_invoke_tool(
        tool_name="get_job_status",
        parameters={"job_id": job_id}
    )

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
    print("\nTesting failed job status...")

    # Create a job designed to fail
    success, result = sync_mcp_invoke_tool(
        tool_name="add_job",
        parameters={
            "type": "error_task",
            "priority": "normal",
            "input": {
                "should_fail": True
            }
        }
    )

    if not success:
        print_test_result(
            "Failed Job Status",
            False,
            f"Could not create test job: {result.get('error', 'Unknown error')}"
        )
        return

    job_id = result.get("job_id")

    # Wait briefly for failure
    time.sleep(1)

    # Check status
    success, result = sync_mcp_invoke_tool(
        tool_name="get_job_status",
        parameters={"job_id": job_id}
    )

    if not success:
        print_test_result(
            "Failed Job Status",
            False,
            f"Failed to get job status: {result.get('error', 'Unknown error')}"
        )
        return

    status = result.get("status")
    error = result.get("error")

    if status != "failed" or not error:
        print_test_result(
            "Failed Job Status",
            False,
            f"Expected failed status with error, got status '{status}'"
        )
        return

    print_test_result(
        "Failed Job Status",
        True,
        f"Job failed as expected with error: {error}"
    )

def test_nonexistent_job_status() -> None:
    """Test checking status of a nonexistent job."""
    print("\nTesting nonexistent job status...")

    success, result = sync_mcp_invoke_tool(
        tool_name="get_job_status",
        parameters={"job_id": "nonexistent_job_id"}
    )

    # Should fail gracefully
    if success:
        print_test_result(
            "Nonexistent Job Status",
            False,
            "System reported success for nonexistent job"
        )
        return

    error = result.get("error", "").lower()
    if "not found" not in error and "does not exist" not in error:
        print_test_result(
            "Nonexistent Job Status",
            False,
            f"Unexpected error message: {error}"
        )
        return

    print_test_result(
        "Nonexistent Job Status",
        True,
        "Correctly reported nonexistent job"
    )

if __name__ == "__main__":
    run_pytest_async(__file__)