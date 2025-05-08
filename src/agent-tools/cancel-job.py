#!/usr/bin/env python3
"""
GraphRAG Agent Tool: cancel-job

This tool cancels a job in the GraphRAG system.

Usage:
    python cancel-job.py --job-id JOB_ID [--url URL]

Arguments:
    --job-id JOB_ID    ID of the job to cancel
    --url URL          MPC server URL (overrides environment variables)

Environment Variables:
    MPC_HOST     MPC server host (default: localhost)
    MPC_PORT     MPC server port (default: 8766)
"""

import sys
import argparse
from utils import connect_to_mpc, send_request, get_mpc_url, format_json
from typing import Dict, Any

def display_cancel_result(result: Dict[str, Any]) -> None:
    """Display the result of cancelling a job."""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    if result.get("status") == "success":
        print("✅ Job cancelled successfully")
        
        # Display job details
        job = result.get("job", {})
        if job:
            print(f"\nJob ID: {job.get('job_id', 'Unknown')}")
            print(f"Type: {job.get('job_type', 'Unknown')}")
            print(f"Status: {job.get('status', 'Unknown')}")
            
            # Display processed items
            processed = job.get("processed_items", 0)
            total = job.get("total_items", 0)
            print(f"Processed items: {processed} of {total} ({job.get('progress', 0):.1f}%)")
    else:
        print(f"❌ Error: {result.get('message', 'Unknown error')}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Cancel a job in the GraphRAG system")
    parser.add_argument("--job-id", required=True, help="ID of the job to cancel")
    parser.add_argument("--url", default=None, help="MPC server URL (overrides environment variables)")
    parser.add_argument("--raw", action="store_true", help="Display raw JSON response")
    args = parser.parse_args()
    
    # Get the MPC URL
    url = args.url or get_mpc_url()
    
    # Connect to the MPC server
    conn = connect_to_mpc(url)
    
    try:
        # Cancel job
        print(f"Cancelling job: {args.job_id}")
        
        response = send_request(conn, "cancel-job", job_id=args.job_id)
        
        # Display results
        if args.raw:
            print("\nRaw response:")
            print(format_json(response))
        else:
            display_cancel_result(response)
        
        return 0
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    sys.exit(main())