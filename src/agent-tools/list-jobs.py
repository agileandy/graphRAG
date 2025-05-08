#!/usr/bin/env python3
"""
GraphRAG Agent Tool: list-jobs

This tool lists jobs in the GraphRAG system.

Usage:
    python list-jobs.py [--status STATUS] [--type TYPE] [--url URL]

Arguments:
    --status STATUS    Filter jobs by status (queued, running, completed, failed, cancelled)
    --type TYPE        Filter jobs by type (add-document, add-folder)
    --url URL          MPC server URL (overrides environment variables)

Environment Variables:
    MPC_HOST     MPC server host (default: localhost)
    MPC_PORT     MPC server port (default: 8766)
"""

import sys
import argparse
from utils import connect_to_mpc, send_request, get_mpc_url, format_json
from typing import Dict, Any

def display_jobs(result: Dict[str, Any]) -> None:
    """Display jobs in a readable format."""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    if result.get("status") != "success":
        print(f"❌ Error: {result.get('message', 'Unknown error')}")
        return
    
    jobs = result.get("jobs", [])
    
    if not jobs:
        print("No jobs found matching the criteria.")
        return
    
    print(f"\n=== Jobs ({len(jobs)} total) ===")
    
    # Group jobs by status
    jobs_by_status = {}
    for job in jobs:
        status = job.get("status", "unknown")
        if status not in jobs_by_status:
            jobs_by_status[status] = []
        jobs_by_status[status].append(job)
    
    # Display jobs by status
    for status, status_jobs in jobs_by_status.items():
        print(f"\n== {status.upper()} JOBS ({len(status_jobs)}) ==")
        
        for job in status_jobs:
            job_id = job.get("job_id", "Unknown")
            job_type = job.get("job_type", "Unknown")
            progress = job.get("progress", 0)
            
            print(f"\n[{job_id}] {job_type}")
            print(f"  Progress: {progress:.1f}%")
            
            # Display processed items
            processed = job.get("processed_items", 0)
            total = job.get("total_items", 0)
            if total > 0:
                print(f"  Processed: {processed}/{total} items")
            
            # Display timestamps
            created_at = job.get("created_at", "Unknown")
            print(f"  Created: {created_at}")
            
            # Display additional info based on status
            if status == "completed":
                completed_at = job.get("completed_at", "Unknown")
                print(f"  Completed: {completed_at}")
            elif status == "failed":
                error = job.get("error", "Unknown error")
                print(f"  Error: {error}")
            elif status == "running":
                started_at = job.get("started_at", "Unknown")
                print(f"  Started: {started_at}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="List jobs in the GraphRAG system")
    parser.add_argument("--status", help="Filter jobs by status (queued, running, completed, failed, cancelled)")
    parser.add_argument("--type", dest="job_type", help="Filter jobs by type (add-document, add-folder)")
    parser.add_argument("--url", default=None, help="MPC server URL (overrides environment variables)")
    parser.add_argument("--raw", action="store_true", help="Display raw JSON response")
    args = parser.parse_args()
    
    # Get the MPC URL
    url = args.url or get_mpc_url()
    
    # Connect to the MPC server
    conn = connect_to_mpc(url)
    
    try:
        # List jobs
        print("Listing jobs...")
        if args.status:
            print(f"Filtering by status: {args.status}")
        if args.job_type:
            print(f"Filtering by type: {args.job_type}")
        
        # Prepare request parameters
        params = {}
        if args.status:
            params["status"] = args.status
        if args.job_type:
            params["job_type"] = args.job_type
        
        response = send_request(conn, "list-jobs", **params)
        
        # Display results
        if args.raw:
            print("\nRaw response:")
            print(format_json(response))
        else:
            display_jobs(response)
        
        return 0
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    sys.exit(main())