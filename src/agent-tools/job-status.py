#!/usr/bin/env python3
"""
GraphRAG Agent Tool: job-status

This tool retrieves the status of a specific job in the GraphRAG system.

Usage:
    python job-status.py --job-id JOB_ID [--url URL]

Arguments:
    --job-id JOB_ID    ID of the job to check
    --url URL          MPC server URL (overrides environment variables)

Environment Variables:
    MPC_HOST     MPC server host (default: localhost)
    MPC_PORT     MPC server port (default: 8766)
"""

import sys
import argparse
from utils import connect_to_mpc, send_request, get_mpc_url, format_json
from typing import Dict, Any

def display_job_status(result: Dict[str, Any]) -> None:
    """Display job status in a readable format."""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    if result.get("status") != "success":
        print(f"❌ Error: {result.get('message', 'Unknown error')}")
        return
    
    job = result.get("job", {})
    
    print("\n=== Job Status ===")
    print(f"Job ID: {job.get('job_id', 'Unknown')}")
    print(f"Type: {job.get('job_type', 'Unknown')}")
    print(f"Status: {job.get('status', 'Unknown')}")
    print(f"Progress: {job.get('progress', 0):.1f}%")
    
    # Display processed items
    processed = job.get("processed_items", 0)
    total = job.get("total_items", 0)
    print(f"Processed items: {processed} of {total}")
    
    # Display timestamps
    created_at = job.get("created_at", "Unknown")
    started_at = job.get("started_at", "Not started")
    completed_at = job.get("completed_at", "Not completed")
    
    print(f"\nCreated at: {created_at}")
    print(f"Started at: {started_at}")
    print(f"Completed at: {completed_at}")
    
    # Display result or error
    if job.get("status") == "completed":
        print("\nResult:")
        result_data = job.get("result", {})
        if isinstance(result_data, dict):
            for key, value in result_data.items():
                if isinstance(value, list):
                    print(f"  {key}: {len(value)} items")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"  {result_data}")
    
    if job.get("status") == "failed" and "error" in job:
        print(f"\nError: {job['error']}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Check the status of a job in the GraphRAG system")
    parser.add_argument("--job-id", required=True, help="ID of the job to check")
    parser.add_argument("--url", default=None, help="MPC server URL (overrides environment variables)")
    parser.add_argument("--raw", action="store_true", help="Display raw JSON response")
    args = parser.parse_args()
    
    # Get the MPC URL
    url = args.url or get_mpc_url()
    
    # Connect to the MPC server
    conn = connect_to_mpc(url)
    
    try:
        # Get job status
        print(f"Checking status of job: {args.job_id}")
        
        response = send_request(conn, "job-status", job_id=args.job_id)
        
        # Display results
        if args.raw:
            print("\nRaw response:")
            print(format_json(response))
        else:
            display_job_status(response)
        
        return 0
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    sys.exit(main())