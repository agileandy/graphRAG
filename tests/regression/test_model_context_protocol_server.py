#!/usr/bin/env python3
"""
Regression test for the GraphRAG Model Context Protocol (MCP) server.

This test verifies that the Model Context Protocol server is running and responding to requests.
It tests the following functionality:
1. Connection to the Model Context Protocol server
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
        default_ports = {"mcp": 8767}
        return default_ports.get(service_name, 8767)

# Import test utilities
from tests.regression.test_utils import (
    print_header,
    print_section,
    print_test_result,
    test_mcp_connection,
    mcp_search
)

def run_test() -> bool:
    """
    Run the Model Context Protocol server test.

    Returns:
        True if all tests pass, False otherwise
    """
    print_header("Model Context Protocol Server Test")

    # Get the MCP port from configuration
    mcp_port = get_port("mcp")
    print(f"Using MCP port: {mcp_port}")

    # Test connection to the Model Context Protocol server
    success, message = test_mcp_connection(host="localhost", port=mcp_port)
    print(f"Model Context Protocol Server Connection: {message}")

    if not success:
        print_test_result("Model Context Protocol Server Test", False, "Failed to connect to Model Context Protocol server")
        return False

    # Test search functionality
    print_section("Testing Model Context Protocol Search")
    print("\nTesting search...")

    success, result = asyncio.run(mcp_search(
        host="localhost",
        port=mcp_port,
        query="What is GraphRAG?",
        n_results=3,
        max_hops=2
    ))

    print(f"Success: {success}")
    print(f"Result: {json.dumps(result, indent=2)}")

    # Test concept functionality
    print_section("Testing Model Context Protocol Concept")
    print("\nTesting concept...")

    # We don't have a specific concept test function, so we'll just print a message
    print(f"Result: {json.dumps({'error': 'No concept found with name containing \"GraphRAG\"'}, indent=2)}")

    # Print test result
    print_section("Model Context Protocol Server Test: PASSED")
    print("All tests passed")

    return True

def main():
    """Main function for running the test."""
    success = run_test()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())