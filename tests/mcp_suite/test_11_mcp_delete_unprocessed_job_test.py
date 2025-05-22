"""Test deleting unprocessed jobs functionality for the MCP server."""

import pytest
import time
from tests.common_utils.test_utils import (
    print_test_result,
    sync_mcp_invoke_tool,
    run_pytest_async
)

def create_test_job(job_type: str = "text_analysis") -> tuple[bool, str]:
    """Create a test job and return its ID."""
    success, result = sync_mcp_invoke_tool(
        tool_name="add_job",
        parameters={
            "type": job_type,
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

def test_delete_pending_job() -> None:
    """Test deleting a job that is still pending."""
    print("\nTesting pending job deletion...")

    # Create a new job
    success, result = create_test_job()
    if not success:
        print_test_result(
            "Delete Pending Job",
            False,
            result
        )
        return

    job_id = result

    # Verify it's pending
    success, result = sync_mcp_invoke_tool(
        tool_name="get_job_status",
        parameters={"job_id": job_id}
    )

    if not success or result.get("status") not in ["pending", "queued"]:
        print_test_result(
            "Delete Pending Job",
            False,
            "Job not in expected pending state"
        )
        return

    # Try to delete it
    success, result = sync_mcp_invoke_tool(
        tool_name="delete_job",
        parameters={"job_id": job_id}
    )

    if not success:
        print_test_result(
            "Delete Pending Job",
            False,
            f"Failed to delete job: {result.get('error', 'Unknown error')}"
        )
        return

    # Verify job is gone
    success, result = sync_mcp_invoke_tool(
        tool_name="get_job_status",
        parameters={"job_id": job_id}
    )

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

def test_delete_running_job() -> None:
    """Test deleting a job that is currently running."""
    print("\nTesting running job deletion...")

    # Create a long-running job
    success, result = create_test_job("long_task")
    if not success:
        print_test_result(
            "Delete Running Job",
            False,
            result
        )
        return

    job_id = result

    # Wait briefly for job to start
    time.sleep(1)

    # Try to delete it
    success, result = sync_mcp_invoke_tool(
        tool_name="delete_job",
        parameters={
            "job_id": job_id,
            "force": True  # Force deletion of running job
        }
    )

    if not success:
        print_test_result(
            "Delete Running Job",
            False,
            f"Failed to delete job: {result.get('error', 'Unknown error')}"
        )
        return

    # Verify job is marked as cancelled
    success, result = sync_mcp_invoke_tool(
        tool_name="get_job_status",
        parameters={"job_id": job_id}
    )

    if not success:
        print_test_result(
            "Delete Running Job",
            False,
            "Failed to get job status after deletion"
        )
        return

    status = result.get("status")
    if status != "cancelled":
        print_test_result(
            "Delete Running Job",
            False,
            f"Expected status 'cancelled', got '{status}'"
        )
        return

    print_test_result(
        "Delete Running Job",
        True,
        "Running job successfully cancelled"
    )

def test_delete_completed_job() -> None:
    """Test attempting to delete a completed job (should fail)."""
    print("\nTesting completed job deletion...")

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
            "Delete Completed Job",
            False,
            f"Failed to create job: {result.get('error', 'Unknown error')}"
        )
        return

    job_id = result.get("job_id")

    # Wait for completion
    time.sleep(2)

    # Verify it's completed
    success, result = sync_mcp_invoke_tool(
        tool_name="get_job_status",
        parameters={"job_id": job_id}
    )

    if not success or result.get("status") != "completed":
        print_test_result(
            "Delete Completed Job",
            False,
            "Job not in expected completed state"
        )
        return

    # Try to delete it - should fail
    success, result = sync_mcp_invoke_tool(
        tool_name="delete_job",
        parameters={"job_id": job_id}
    )

    if success:
        print_test_result(
            "Delete Completed Job",
            False,
            "System allowed deletion of completed job"
        )
        return

    error = result.get("error", "").lower()
    if "completed" not in error:
        print_test_result(
            "Delete Completed Job",
            False,
            f"Unexpected error message: {error}"
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

    success, result = sync_mcp_invoke_tool(
        tool_name="delete_job",
        parameters={"job_id": "nonexistent_job_id"}
    )

    # Should fail gracefully
    if success:
        print_test_result(
            "Delete Nonexistent Job",
            False,
            "System reported success for nonexistent job deletion"
        )
        return

    error = result.get("error", "").lower()
    if "not found" not in error and "does not exist" not in error:
        print_test_result(
            "Delete Nonexistent Job",
            False,
            f"Unexpected error message: {error}"
        )
        return

    print_test_result(
        "Delete Nonexistent Job",
        True,
        "Correctly handled nonexistent job deletion attempt"
    )

if __name__ == "__main__":
    run_pytest_async(__file__)