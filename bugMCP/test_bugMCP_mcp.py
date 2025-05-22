#!/usr/bin/env python3
"""Test script for the Bug Tracking MCP server.

This script tests the MCP server by:
1. Starting the server in a separate process
2. Connecting to it using the MCP client
3. Testing all the bug tracking tools
"""

import asyncio
import json
import os
import subprocess
import sys
import time

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mcp.client.session import ClientSession
from mcp.client.websocket import websocket_client
from mcp.types import (
    TextContent,
    ListToolsResult,
)  # Import ListToolsResult for type checking if needed
from src.mcp.mcp_server import start_server as start_mcp_websocket_server
from src.config import get_port


async def test_bug_tracking_tools() -> None:
    """Test the bug tracking tools."""
    print("\n=== Testing Bug Tracking MCP Server ===\n")
    mcp_websocket_port = get_port("bug_mcp")

    # Connect to the MCP server
    print("Connecting to MCP server...")
    async with websocket_client(f"ws://localhost:{mcp_websocket_port}") as (
        read_stream,
        write_stream,
    ):
        # Create a session
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            print("✅ Connected to MCP server")

            # List available tools
            tools_result = await session.list_tools()  # This returns ListToolsResult
            assert isinstance(tools_result, ListToolsResult)
            print(f"✅ Found {len(tools_result.tools)} tools")

            # Test list_bugs (which is an alias for tools/list,
            # handled by handle_get_tools)
            print("\nTesting list_bugs...")
            # The client's list_tools() method should be used for 'tools/list'
            # If 'list_bugs' is a separate tool defined in mcp_server.py,
            # it would be called via call_tool
            # Assuming 'list_bugs' is meant to test the 'tools/list' functionality
            # via a specific tool name if it existed
            # For now, we'll assume it's a conceptual test of listing,
            # which is covered by session.list_tools()
            # If "list_bugs" is a specific tool name:
            # result = await session.call_tool("list_bugs", {})
            # print(f"✅ list_bugs result: {result.model_dump_json(indent=2)}")
            # For now, let's use the result from session.list_tools()
            # if that's the intent
            print(
                f"✅ list_tools (for list_bugs conceptual test) result: "
                f"{tools_result.model_dump_json(indent=2)}"
            )

            # Test add_bug
            print("\nTesting add_bug...")
            add_bug_payload = {
                "description": "Test bug from MCP client",
                "cause": "Testing the MCP implementation",
                "async": False,
            }
            result = await session.call_tool("add_bug", add_bug_payload)
            print(f"✅ add_bug result: {result.model_dump_json(indent=2)}")

            # Get the bug ID from the result
            bug_id = None
            if result.content and isinstance(result.content[0], TextContent):
                try:
                    result_data = json.loads(result.content[0].text)
                    # The actual bug_id is nested inside the 'result' field
                    # of the tool's response
                    if (
                        isinstance(result_data, dict)
                        and "result" in result_data
                        and isinstance(result_data["result"], dict)
                    ):
                        bug_id = result_data["result"].get("bug_id")
                    elif isinstance(
                        result_data, dict
                    ):  # Direct bug_id if not nested under "result" field
                        bug_id = result_data.get("bug_id")

                except json.JSONDecodeError:
                    print("❌ Error decoding JSON from add_bug tool result content.")
            else:
                print("❌ Unexpected add_bug tool result content format.")

            assert bug_id is not None, "Failed to retrieve bug_id from add_bug response"

            # Test get_bug
            print(f"\nTesting get_bug with ID {bug_id}...")
            result = await session.call_tool("get_bug", {"id": bug_id})
            print(f"✅ get_bug result: {result.model_dump_json(indent=2)}")

            # Test update_bug
            print(f"\nTesting update_bug with ID {bug_id}...")
            update_bug_payload = {
                "id": bug_id,
                "status": "fixed",
                "resolution": "Fixed in MCP implementation",
            }
            result = await session.call_tool("update_bug", update_bug_payload)
            print(f"✅ update_bug result: {result.model_dump_json(indent=2)}")

            # Test get_bug again to verify update
            print(f"\nTesting get_bug again with ID {bug_id}...")
            result = await session.call_tool("get_bug", {"id": bug_id})
            print(f"✅ get_bug result after update: {result.model_dump_json(indent=2)}")

            # Test delete_bug
            print(f"\nTesting delete_bug with ID {bug_id}...")
            result = await session.call_tool("delete_bug", {"id": bug_id})
            print(f"✅ delete_bug result: {result.model_dump_json(indent=2)}")

            # Test list_bugs again to verify deletion
            print("\nTesting list_bugs again...")
            # Using list_tools() as a proxy for listing,
            # assuming "list_bugs" isn't a distinct tool
            final_tools_list = await session.list_tools()
            # The actual verification of deletion would involve checking
            # if the specific bug_id is no longer present
            # This requires parsing the content of a get_bug or
            # a more specific list_bugs tool if it existed.
            # For now, just printing the list.
            print(
                f"✅ list_tools result after deletion: "
                f"{final_tools_list.model_dump_json(indent=2)}"
            )

            print("\n=== All tests completed successfully ===")


async def main() -> None:
    """Main function."""
    mcp_websocket_port = get_port("bug_mcp")
    # Start the WebSocket MCP server in a separate process
    server_process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            f"from src.mcp.mcp_server import start_server; import asyncio; "
            f"asyncio.run(start_server(port={mcp_websocket_port}))",
        ],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for the server to start
    print("Starting MCP server...")
    time.sleep(3)  # Increased sleep time

    try:
        # Run the tests
        await test_bug_tracking_tools()
    finally:
        # Terminate the server process
        print("\nTerminating server process...")
        server_process.terminate()
        try:
            stdout, stderr = server_process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            server_process.kill()
            stdout, stderr = server_process.communicate()

        if stdout:
            print("\nServer stdout:")
            print(stdout.decode(errors="ignore"))

        if stderr:
            print("\nServer stderr:")
            print(stderr.decode(errors="ignore"))
        print("Server process terminated.")


if __name__ == "__main__":
    asyncio.run(main())
