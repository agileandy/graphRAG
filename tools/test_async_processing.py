#!/usr/bin/env python3
"""
Test script for asynchronous processing in the GraphRAG MPC server.

This script demonstrates how to:
1. Add a document asynchronously
2. Add a folder asynchronously
3. Check job status
4. List jobs
5. Cancel a job
"""

import os
import sys
import json
import time
import argparse
import websockets.sync.client as ws
from typing import Dict, Any, List, Optional

# Default MPC server URL
DEFAULT_MPC_URL = "ws://localhost:8766"

def connect_to_mpc(url: str = DEFAULT_MPC_URL):
    """Connect to the MPC server."""
    try:
        return ws.connect(url)
    except Exception as e:
        print(f"Error connecting to MPC server at {url}: {e}")
        sys.exit(1)

def send_request(conn, action: str, **kwargs) -> Dict[str, Any]:
    """Send a request to the MPC server and return the response."""
    # Create the message
    message = {"action": action, **kwargs}
    
    # Send the message
    try:
        conn.send(json.dumps(message))
        
        # Receive the response
        response = conn.recv()
        return json.loads(response)
    except Exception as e:
        print(f"Error communicating with MPC server: {e}")
        sys.exit(1)

def add_document_async(conn, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Add a document to the GraphRAG system asynchronously."""
    return send_request(conn, "add-document", text=text, metadata=metadata, async=True)

def add_folder_async(conn, folder_path: str, recursive: bool = False) -> Dict[str, Any]:
    """Add a folder to the GraphRAG system asynchronously."""
    return send_request(conn, "add-folder", folder_path=folder_path, recursive=recursive, async=True)

def get_job_status(conn, job_id: str) -> Dict[str, Any]:
    """Get the status of a job."""
    return send_request(conn, "job-status", job_id=job_id)

def list_jobs(conn, status: Optional[str] = None, job_type: Optional[str] = None) -> Dict[str, Any]:
    """List jobs."""
    params = {}
    if status:
        params["status"] = status
    if job_type:
        params["job_type"] = job_type
    
    return send_request(conn, "list-jobs", **params)

def cancel_job(conn, job_id: str) -> Dict[str, Any]:
    """Cancel a job."""
    return send_request(conn, "cancel-job", job_id=job_id)

def wait_for_job_completion(conn, job_id: str, poll_interval: float = 1.0, timeout: float = 300.0) -> Dict[str, Any]:
    """Wait for a job to complete."""
    start_time = time.time()
    last_progress = -1
    
    while True:
        # Check if we've exceeded the timeout
        if time.time() - start_time > timeout:
            print(f"Timeout waiting for job {job_id} to complete")
            return {"status": "timeout"}
        
        # Get job status
        status = get_job_status(conn, job_id)
        
        # Check if job is complete
        if status.get("status") in ["completed", "failed", "cancelled"]:
            return status
        
        # Print progress if it has changed
        progress = status.get("progress", 0)
        if progress != last_progress:
            print(f"Job {job_id} progress: {progress:.1f}% ({status.get('processed_items', 0)}/{status.get('total_items', 0)})")
            last_progress = progress
        
        # Wait before polling again
        time.sleep(poll_interval)

def test_add_document_async(conn):
    """Test adding a document asynchronously."""
    print("\n=== Testing Asynchronous Document Addition ===")
    
    # Create a test document
    text = "This is a test document for asynchronous processing."
    metadata = {
        "title": "Async Test Document",
        "author": "Test Script",
        "source": "Test"
    }
    
    # Add document asynchronously
    print("Adding document asynchronously...")
    response = add_document_async(conn, text, metadata)
    
    if response.get("status") != "accepted":
        print(f"Error adding document: {response}")
        return
    
    print(f"Document addition accepted with job ID: {response.get('job_id')}")
    
    # Wait for job to complete
    job_id = response.get("job_id")
    print(f"Waiting for job {job_id} to complete...")
    
    result = wait_for_job_completion(conn, job_id)
    
    if result.get("status") == "completed":
        print(f"Job completed successfully: {result}")
    else:
        print(f"Job did not complete successfully: {result}")

def test_add_folder_async(conn, folder_path: str, recursive: bool = False):
    """Test adding a folder asynchronously."""
    print("\n=== Testing Asynchronous Folder Addition ===")
    
    # Add folder asynchronously
    print(f"Adding folder {folder_path} asynchronously (recursive={recursive})...")
    response = add_folder_async(conn, folder_path, recursive)
    
    if response.get("status") != "accepted":
        print(f"Error adding folder: {response}")
        return
    
    print(f"Folder addition accepted with job ID: {response.get('job_id')}")
    print(f"Total files to process: {response.get('total_files', 'unknown')}")
    
    # Wait for job to complete
    job_id = response.get("job_id")
    print(f"Waiting for job {job_id} to complete...")
    
    result = wait_for_job_completion(conn, job_id)
    
    if result.get("status") == "completed":
        print(f"Job completed successfully")
        print(f"Result: {json.dumps(result.get('result', {}), indent=2)}")
    else:
        print(f"Job did not complete successfully: {result}")

def test_list_jobs(conn):
    """Test listing jobs."""
    print("\n=== Testing Job Listing ===")
    
    # List all jobs
    print("Listing all jobs...")
    response = list_jobs(conn)
    
    if response.get("status") != "success":
        print(f"Error listing jobs: {response}")
        return
    
    jobs = response.get("jobs", [])
    print(f"Found {len(jobs)} jobs")
    
    for job in jobs:
        print(f"Job {job['job_id']}: {job['job_type']} - {job['status']} ({job['progress']:.1f}%)")

def test_cancel_job(conn, job_id: str):
    """Test cancelling a job."""
    print("\n=== Testing Job Cancellation ===")
    
    # Cancel job
    print(f"Cancelling job {job_id}...")
    response = cancel_job(conn, job_id)
    
    if response.get("status") != "success":
        print(f"Error cancelling job: {response}")
        return
    
    print(f"Job cancelled successfully: {response.get('message')}")

def main():
    parser = argparse.ArgumentParser(description="Test asynchronous processing in the GraphRAG MPC server")
    parser.add_argument("--url", default=DEFAULT_MPC_URL, help="MPC server URL")
    parser.add_argument("--test-document", action="store_true", help="Test adding a document asynchronously")
    parser.add_argument("--test-folder", help="Test adding a folder asynchronously")
    parser.add_argument("--recursive", action="store_true", help="Process folder recursively")
    parser.add_argument("--list-jobs", action="store_true", help="List all jobs")
    parser.add_argument("--cancel-job", help="Cancel a job by ID")
    args = parser.parse_args()
    
    # Connect to the MPC server
    conn = connect_to_mpc(args.url)
    
    try:
        # Run tests based on arguments
        if args.test_document:
            test_add_document_async(conn)
        
        if args.test_folder:
            test_add_folder_async(conn, args.test_folder, args.recursive)
        
        if args.list_jobs:
            test_list_jobs(conn)
        
        if args.cancel_job:
            test_cancel_job(conn, args.cancel_job)
        
        # If no specific test was requested, run all tests
        if not (args.test_document or args.test_folder or args.list_jobs or args.cancel_job):
            test_add_document_async(conn)
            
            # Use a test folder if available
            test_folder = args.test_folder or os.path.join(os.path.dirname(__file__), "..")
            test_add_folder_async(conn, test_folder, False)
            
            test_list_jobs(conn)
    
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    main()
