#!/usr/bin/env python3
"""
Test script for the Bug Tracking MCP server.

This script tests the MCP server by:
1. Starting the server in a separate process
2. Connecting to it using the MCP client
3. Testing all the bug tracking tools
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from typing import Dict, Any, List, Optional

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def test_bug_tracking_tools():
    """Test the bug tracking tools."""
    print("\n=== Testing Bug Tracking MCP Server ===\n")
    
    # Connect to the MCP server
    print("Connecting to MCP server...")
    async with streamablehttp_client("http://localhost:5007") as (read_stream, write_stream, _):
        # Create a session
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            print("✅ Connected to MCP server")
            
            # List available tools
            tools = await session.list_tools()
            print(f"✅ Found {len(tools)} tools")
            
            # Test list_bugs
            print("\nTesting list_bugs...")
            result = await session.call_tool("list_bugs", {})
            print(f"✅ list_bugs result: {json.dumps(result, indent=2)}")
            
            # Test add_bug
            print("\nTesting add_bug...")
            result = await session.call_tool("add_bug", {
                "description": "Test bug from MCP client",
                "cause": "Testing the MCP implementation"
            })
            print(f"✅ add_bug result: {json.dumps(result, indent=2)}")
            
            # Get the bug ID from the result
            bug_id = result.get("bug_id")
            
            # Test get_bug
            print(f"\nTesting get_bug with ID {bug_id}...")
            result = await session.call_tool("get_bug", {
                "id": bug_id
            })
            print(f"✅ get_bug result: {json.dumps(result, indent=2)}")
            
            # Test update_bug
            print(f"\nTesting update_bug with ID {bug_id}...")
            result = await session.call_tool("update_bug", {
                "id": bug_id,
                "status": "fixed",
                "resolution": "Fixed in MCP implementation"
            })
            print(f"✅ update_bug result: {json.dumps(result, indent=2)}")
            
            # Test get_bug again to verify update
            print(f"\nTesting get_bug again with ID {bug_id}...")
            result = await session.call_tool("get_bug", {
                "id": bug_id
            })
            print(f"✅ get_bug result after update: {json.dumps(result, indent=2)}")
            
            # Test delete_bug
            print(f"\nTesting delete_bug with ID {bug_id}...")
            result = await session.call_tool("delete_bug", {
                "id": bug_id
            })
            print(f"✅ delete_bug result: {json.dumps(result, indent=2)}")
            
            # Test list_bugs again to verify deletion
            print("\nTesting list_bugs again...")
            result = await session.call_tool("list_bugs", {})
            print(f"✅ list_bugs result after deletion: {json.dumps(result, indent=2)}")
            
            print("\n=== All tests completed successfully ===")

async def main():
    """Main function."""
    # Start the MCP server in a separate process
    server_process = subprocess.Popen(
        [sys.executable, "bugMCP/standalone_server.py", "--port", "5007"],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), '..')),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for the server to start
    print("Starting MCP server...")
    time.sleep(2)
    
    try:
        # Run the tests
        await test_bug_tracking_tools()
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
    asyncio.run(main())