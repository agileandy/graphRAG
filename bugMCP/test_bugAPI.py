#!/usr/bin/env python3
"""Test script for the Bug Tracking API server.

This script tests the API server by:
1. Starting the server in a separate process
2. Connecting to it using the requests library
3. Testing all the bug tracking endpoints
"""

import json
import os
import subprocess
import sys
import time

import requests

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_bug_tracking_api(host: str = "localhost", port: int = 5007) -> None:
    """Test the bug tracking API."""
    print("\n=== Testing Bug Tracking API Server ===\n")

    base_url = f"http://{host}:{port}"

    # Test list_bugs
    print("Testing list_bugs...")
    response = requests.get(f"{base_url}/bugs")
    response.raise_for_status()
    result = response.json()
    print(f"✅ list_bugs result: {json.dumps(result, indent=2)}")

    # Test add_bug
    print("\nTesting add_bug...")
    response = requests.post(
        f"{base_url}/bugs",
        json={
            "description": "Test bug from API client",
            "cause": "Testing the API implementation",
        },
    )
    response.raise_for_status()
    result = response.json()
    print(f"✅ add_bug result: {json.dumps(result, indent=2)}")

    # Get the bug ID from the result
    bug_id = result.get("bug_id")

    # Test get_bug
    print(f"\nTesting get_bug with ID {bug_id}...")
    response = requests.get(f"{base_url}/bugs/{bug_id}")
    response.raise_for_status()
    result = response.json()
    print(f"✅ get_bug result: {json.dumps(result, indent=2)}")

    # Test update_bug
    print(f"\nTesting update_bug with ID {bug_id}...")
    response = requests.put(
        f"{base_url}/bugs/{bug_id}",
        json={"status": "fixed", "resolution": "Fixed in API implementation"},
    )
    response.raise_for_status()
    result = response.json()
    print(f"✅ update_bug result: {json.dumps(result, indent=2)}")

    # Test get_bug again to verify update
    print(f"\nTesting get_bug again with ID {bug_id}...")
    response = requests.get(f"{base_url}/bugs/{bug_id}")
    response.raise_for_status()
    result = response.json()
    print(f"✅ get_bug result after update: {json.dumps(result, indent=2)}")

    # Test delete_bug
    print(f"\nTesting delete_bug with ID {bug_id}...")
    response = requests.delete(f"{base_url}/bugs/{bug_id}")
    response.raise_for_status()
    result = response.json()
    print(f"✅ delete_bug result: {json.dumps(result, indent=2)}")

    # Test list_bugs again to verify deletion
    print("\nTesting list_bugs again...")
    response = requests.get(f"{base_url}/bugs")
    response.raise_for_status()
    result = response.json()
    print(f"✅ list_bugs result after deletion: {json.dumps(result, indent=2)}")

    print("\n=== All tests completed successfully ===")


def main() -> None:
    """Main function."""
    # Start the API server in a separate process
    server_process = subprocess.Popen(
        [sys.executable, "bugMCP/bugAPI.py", "--port", "5007"],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for the server to start
    print("Starting API server...")
    time.sleep(2)

    try:
        # Run the tests
        test_bug_tracking_api(port=5007)
    finally:
        # Terminate the server process
        server_process.terminate()
        stdout, stderr = server_process.communicate()

        if stdout:
            print("\nServer stdout:")
            print(stdout.decode())

        if stderr:
            print("\nServer stderr:")
            print(stderr.decode())


if __name__ == "__main__":
    main()
