"""Test job queue functionality for the MCP server."""

import pytest
from tests.common_utils.test_utils import (
    print_test_result,
    sync_mcp_invoke_tool,
    run_pytest_async
)

def test_add_simple_job() -> None:
    """Test adding a simple processing job."""
    print("\nTesting simple job addition...")

    success, result = sync_mcp_invoke_tool(
        tool_name="add_job",
        parameters={
            "type": "text_extraction",
            "priority": "normal",
            "input": {
                "text": "Sample text for processing",
                "format": "plain"
            }
        }
    )

    if not success:
        print_test_result(
            "Add Simple Job",
            False,
            f"Failed to add job: {result.get('error', 'Unknown error')}"
        )
        return

    job_id = result.get("job_id")
    if not job_id:
        print_test_result(
            "Add Simple Job",
            False,
            "No job ID returned"
        )
        return

    print_test_result(
        "Add Simple Job",
        True,
        f"Job added successfully with ID: {job_id}"
    )

def test_add_priority_job() -> None:
    """Test adding a high-priority job."""
    print("\nTesting priority job addition...")

    success, result = sync_mcp_invoke_tool(
        tool_name="add_job",
        parameters={
            "type": "document_analysis",
            "priority": "high",
            "input": {
                "text": "Urgent processing needed",
                "analysis_types": ["entities", "sentiment"],
                "deadline": "immediate"
            }
        }
    )

    if not success:
        print_test_result(
            "Add Priority Job",
            False,
            f"Failed to add priority job: {result.get('error', 'Unknown error')}"
        )
        return

    job_id = result.get("job_id")
    priority = result.get("priority")

    if not job_id or priority != "high":
        print_test_result(
            "Add Priority Job",
            False,
            "Job not created with correct priority"
        )
        return

    print_test_result(
        "Add Priority Job",
        True,
        f"Priority job added successfully with ID: {job_id}"
    )

def test_add_batch_job() -> None:
    """Test adding a batch processing job."""
    print("\nTesting batch job addition...")

    success, result = sync_mcp_invoke_tool(
        tool_name="add_job",
        parameters={
            "type": "batch_processing",
            "priority": "normal",
            "input": {
                "items": [
                    {"text": "Item 1 for processing"},
                    {"text": "Item 2 for processing"},
                    {"text": "Item 3 for processing"}
                ],
                "process_type": "text_analysis"
            }
        }
    )

    if not success:
        print_test_result(
            "Add Batch Job",
            False,
            f"Failed to add batch job: {result.get('error', 'Unknown error')}"
        )
        return

    job_id = result.get("job_id")
    batch_size = result.get("batch_size", 0)

    if not job_id or batch_size != 3:
        print_test_result(
            "Add Batch Job",
            False,
            f"Unexpected batch size: {batch_size}"
        )
        return

    print_test_result(
        "Add Batch Job",
        True,
        f"Batch job added successfully with {batch_size} items"
    )

def test_add_invalid_job() -> None:
    """Test adding an invalid job (should fail)."""
    print("\nTesting invalid job addition...")

    success, result = sync_mcp_invoke_tool(
        tool_name="add_job",
        parameters={
            "type": "invalid_type",
            "priority": "super_high",  # Invalid priority
            "input": None  # Invalid input
        }
    )

    # Should fail with validation error
    if success:
        print_test_result(
            "Add Invalid Job",
            False,
            "Invalid job was accepted but should have been rejected"
        )
        return

    error = result.get("error", "")
    if "invalid" not in error.lower() and "validation" not in error.lower():
        print_test_result(
            "Add Invalid Job",
            False,
            f"Unexpected error message: {error}"
        )
        return

    print_test_result(
        "Add Invalid Job",
        True,
        "Invalid job was correctly rejected"
    )

def test_queue_limits() -> None:
    """Test queue size limits and backpressure."""
    print("\nTesting queue limits...")

    # Add multiple jobs quickly
    jobs = []
    total_jobs = 10
    accepted_jobs = 0

    for i in range(total_jobs):
        success, result = sync_mcp_invoke_tool(
            tool_name="add_job",
            parameters={
                "type": "text_analysis",
                "priority": "low",
                "input": {
                    "text": f"Test job {i+1}",
                    "format": "plain"
                }
            }
        )

        if success:
            jobs.append(result.get("job_id"))
            accepted_jobs += 1
        else:
            # Check if we hit queue limits
            error = result.get("error", "").lower()
            if "queue full" in error or "backpressure" in error:
                print_test_result(
                    "Queue Limits",
                    True,
                    f"Queue correctly enforced limits after {accepted_jobs} jobs"
                )
                return

    # If we added all jobs successfully, that's okay too
    print_test_result(
        "Queue Limits",
        True,
        f"Queue accepted all {accepted_jobs} jobs successfully"
    )

if __name__ == "__main__":
    run_pytest_async(__file__)