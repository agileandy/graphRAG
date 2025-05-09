#!/usr/bin/env python3
"""
Regression test for the GraphRAG Model Context Protocol (MCP) server.

This test verifies that the Model Context Protocol server is running and responding to requests.
It tests the following functionality:
1. Connection to the Model Context Protocol server
2. Getting available tools
3. Invoking the search tool
4. Invoking the ping tool
5. Invoking the concept tool
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
    test_mcp_connection,
    mcp_get_tools,
    mcp_invoke_tool
)

async def test_model_context_tools():
    """Test Model Context Protocol tools."""
    print_section("Testing Model Context Protocol Tools")

    # Test ping tool
    print("\nTesting ping tool...")
    success, result = await mcp_invoke_tool(tool_name="ping", parameters={})
    print(f"Success: {success}")
    print(f"Result: {json.dumps(result, indent=2)}")

    # Test search tool
    print("\nTesting search tool...")
    success, result = await mcp_invoke_tool(
        tool_name="search",
        parameters={
            "query": "What is GraphRAG?",
            "n_results": 3
        }
    )
    print(f"Success: {success}")
    print(f"Result: {json.dumps(result, indent=2)}")

    # Test concept tool
    print("\nTesting concept tool...")
    success, result = await mcp_invoke_tool(
        tool_name="concept",
        parameters={
            "concept_name": "GraphRAG"
        }
    )
    print(f"Success: {success}")
    print(f"Result: {json.dumps(result, indent=2)}")

    return success

def run_test():
    """Run the Model Context Protocol server test."""
    print_test_header("Model Context Protocol Server Test")

    # Test connection to Model Context Protocol server
    success, message = test_mcp_connection()
    print(f"Model Context Protocol Server Connection: {message}")

    if not success:
        print_test_result("Model Context Protocol Server Test", False, "Failed to connect to Model Context Protocol server")
        return False

    # Test getting tools
    success, tools = asyncio.run(mcp_get_tools())

    if not success:
        print_test_result("Model Context Protocol Server Test", False, "Failed to get tools from Model Context Protocol server")
        return False

    print(f"Available tools: {len(tools)}")
    for i, tool in enumerate(tools):
        print(f"{i+1}. {tool['name']} - {tool['description']}")

    # Test tools
    success = asyncio.run(test_model_context_tools())

    print_test_result("Model Context Protocol Server Test", success, "All tests passed" if success else "Some tests failed")
    return success

if __name__ == "__main__":
    run_test()
