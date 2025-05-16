#!/usr/bin/env python3
"""
GraphRAG Agent Tool: job-status

This tool retrieves the status of a specific job in the GraphRAG system.

Usage:
    python job-status.py --job-id JOB_ID [--url URL] [--verbose]

Arguments:
    --job-id JOB_ID    ID of the job to check
    --url URL          MPC server URL (overrides environment variables)
    --verbose          Enable verbose logging

Environment Variables:
    MPC_HOST     MPC server host (default: localhost)
    MPC_PORT     MPC server port (default: 8766)
"""

import sys
import argparse
import logging
import traceback
from utils import connect_to_mpc, send_request, get_mcp_url, format_json
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)
logger = logging.getLogger('job-status')

def display_job_status(result: Dict[str, Any]) -> None:
    """Display job status in a readable format."""
    logger.debug(f"Processing job status result: {result}")

    if "error" in result:
        error_msg = result['error']
        logger.error(f"Error in job status response: {error_msg}")
        print(f"❌ Error: {error_msg}")
        return

    # Direct job status response from MCP server
    if "job_id" in result:
        logger.debug("Found direct job status response format")
        job = result
    else:
        # Response wrapped in a success object
        logger.debug("Found wrapped job status response format")
        if result.get("status") != "success":
            error_msg = result.get("message", "Unknown error")
            logger.error(f"Error status in job response: {error_msg}")
            print(f"❌ Error: {error_msg}")
            return
        job = result.get("job", {})
        logger.debug(f"Extracted job data: {job}")

    # Extract job details with verbose logging
    job_id = job.get('job_id', 'Unknown')
    job_type = job.get('job_type', 'Unknown')
    status = job.get('status', 'Unknown')
    progress = job.get('progress', 0)
    processed = job.get("processed_items", 0)
    total = job.get("total_items", 0)
    created_at = job.get("created_at", "Unknown")
    started_at = job.get("started_at", "Not started")
    completed_at = job.get("completed_at", "Not completed")

    logger.info(f"Job {job_id} ({job_type}) status: {status}, progress: {progress:.1f}%")
    logger.debug(f"Job {job_id} processed items: {processed}/{total}")
    logger.debug(f"Job {job_id} timestamps: created={created_at}, started={started_at}, completed={completed_at}")

    # Display to user
    print("\n=== Job Status ===")
    print(f"Job ID: {job_id}")
    print(f"Type: {job_type}")
    print(f"Status: {status}")
    print(f"Progress: {progress:.1f}%")
    print(f"Processed items: {processed} of {total}")
    print(f"\nCreated at: {created_at}")
    print(f"Started at: {started_at}")
    print(f"Completed at: {completed_at}")

    # Display result or error
    if job.get("status") == "completed":
        result_data = job.get("result", {})
        logger.debug(f"Job {job_id} completed with result: {result_data}")

        print("\nResult:")
        if isinstance(result_data, dict):
            for key, value in result_data.items():
                if isinstance(value, list):
                    print(f"  {key}: {len(value)} items")
                    logger.debug(f"Result field '{key}' contains {len(value)} items")
                else:
                    print(f"  {key}: {value}")
                    logger.debug(f"Result field '{key}': {value}")
        else:
            print(f"  {result_data}")
            logger.debug(f"Result (non-dict): {result_data}")

    if job.get("status") == "failed" and "error" in job:
        error_msg = job['error']
        logger.error(f"Job {job_id} failed with error: {error_msg}")
        print(f"\nError: {error_msg}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Check the status of a job in the GraphRAG system")
    parser.add_argument("--job-id", required=True, help="ID of the job to check")
    parser.add_argument("--url", default=None, help="MPC server URL (overrides environment variables)")
    parser.add_argument("--raw", action="store_true", help="Display raw JSON response")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Get the MPC URL
    url = args.url or get_mcp_url()
    logger.info(f"Using MCP server URL: {url}")

    try:
        # Connect to the MPC server
        logger.debug(f"Connecting to MCP server at {url}")
        conn = connect_to_mpc(url)
        logger.info("Connected to MCP server successfully")

        try:
            # Get job status
            job_id = args.job_id
            logger.info(f"Checking status of job: {job_id}")
            print(f"Checking status of job: {job_id}")

            # Send the request
            logger.debug(f"Sending job-status request with job_id={job_id}")
            response = send_request(conn, "job-status", job_id=job_id)
            logger.debug(f"Received response: {response}")

            # Display results
            if args.raw:
                logger.debug("Displaying raw response")
                print("\nRaw response:")
                formatted_json = format_json(response)
                print(formatted_json)
            else:
                logger.debug("Displaying formatted job status")
                display_job_status(response)

            return 0
        except Exception as e:
            logger.error(f"Error checking job status: {e}")
            logger.debug(f"Exception details: {traceback.format_exc()}")
            print(f"❌ Error checking job status: {e}")
            return 1
        finally:
            # Close the connection
            logger.debug("Closing MCP server connection")
            conn.close()
    except Exception as e:
        logger.error(f"Error connecting to MCP server: {e}")
        logger.debug(f"Exception details: {traceback.format_exc()}")
        print(f"❌ Error connecting to MCP server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())