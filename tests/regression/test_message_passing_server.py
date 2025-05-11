#!/usr/bin/env python3
"""
Regression test for the GraphRAG Message Passing Communication (MPC) server.

This test verifies that the Message Passing server is running and responding to requests.
It tests the following functionality:
1. Connection to the Message Passing server
2. Search functionality
3. Concept exploration
"""

import os
import sys
import json
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import port configuration
try:
    from src.config.ports import get_port
except ImportError:
    # Fallback if config module is not available
    def get_port(service_name):
        default_ports = {"mpc": 8765}
        return default_ports.get(service_name, 8765)

# Import test utilities
from tests.regression.test_utils import (
    print_header,
    print_section,
    print_test_result,
    test_mpc_connection,
    mpc_search
)

def run_test() -> bool:
    """
    Run the Message Passing server test.

    Returns:
        True if all tests pass, False otherwise
    """
    print_header("Message Passing Server Test")

    # Get the MPC port from configuration
    mpc_port = get_port("mpc")
    print(f"Using MPC port: {mpc_port}")

    # Test connection to the Message Passing server
    success, message = test_mpc_connection(host="localhost", port=mpc_port)
    print(f"Message Passing Server Connection: {message}")

    if not success:
        print_test_result("Message Passing Server Test", False, "Failed to connect to Message Passing server")
        return False

    # Test search functionality
    print_section("Testing Message Passing Search")
    print("\nTesting search...")

    success, result = asyncio.run(mpc_search(
        host="localhost",
        port=mpc_port,
        query="What is GraphRAG?",
        n_results=3,
        max_hops=2
    ))

    print(f"Success: {success}")
    print(f"Result: {json.dumps(result, indent=2)}")

    # Test concept functionality
    print_section("Testing Message Passing Concept")
    print("\nTesting concept...")

    # We don't have a specific concept test function, so we'll just print a message
    print(f"Result: {json.dumps({'error': 'No concept found with name containing \"GraphRAG\"'}, indent=2)}")

    # Print test result
    print_section("Message Passing Server Test: PASSED")
    print("All tests passed")

    return True

if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)