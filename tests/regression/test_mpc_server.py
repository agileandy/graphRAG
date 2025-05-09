#!/usr/bin/env python3
"""
Regression test for the GraphRAG MPC server.

This test verifies that the MPC server is running and responding to requests.
It tests the following functionality:
1. Connection to the MPC server
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

# Import test utilities
from tests.regression.test_utils import (
    print_test_header,
    print_test_result,
    print_section,
    test_mpc_connection,
    mpc_search
)

async def test_mpc_search():
    """Test MPC search functionality."""
    print_section("Testing MPC Search")
    
    # Test search
    print("\nTesting search...")
    success, result = await mpc_search(
        query="What is GraphRAG?",
        n_results=3,
        max_hops=2
    )
    print(f"Success: {success}")
    print(f"Result: {json.dumps(result, indent=2)}")
    
    return success

async def test_mpc_concept():
    """Test MPC concept functionality."""
    print_section("Testing MPC Concept")
    
    # Test concept
    print("\nTesting concept...")
    try:
        import websockets
        
        uri = "ws://localhost:8766"
        async with websockets.connect(uri) as websocket:
            # Prepare concept message
            message = {
                'action': 'concept',
                'concept_name': 'GraphRAG'
            }
            
            # Send concept query
            await websocket.send(json.dumps(message))
            
            # Receive response
            response = await websocket.recv()
            response_data = json.loads(response)
            
            print(f"Result: {json.dumps(response_data, indent=2)}")
            
            return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_test():
    """Run the MPC server test."""
    print_test_header("MPC Server Test")
    
    # Test connection to MPC server
    success, message = test_mpc_connection()
    print(f"MPC Server Connection: {message}")
    
    if not success:
        print_test_result("MPC Server Test", False, "Failed to connect to MPC server")
        return False
    
    # Test search
    search_success = asyncio.run(test_mpc_search())
    
    # Test concept
    concept_success = asyncio.run(test_mpc_concept())
    
    success = search_success and concept_success
    
    print_test_result("MPC Server Test", success, "All tests passed" if success else "Some tests failed")
    return success

if __name__ == "__main__":
    run_test()
