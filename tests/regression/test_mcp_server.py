#!/usr/bin/env python3
"""
Regression test for the GraphRAG MCP server.

This test verifies that the MCP server is running and responding to requests.
It tests the following functionality:
1. Connection to the MCP server
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

async def test_mcp_tools():
    """Test MCP tools."""
    print_section("Testing MCP Tools")
    
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
    """Run the MCP server test."""
    print_test_header("MCP Server Test")
    
    # Test connection to MCP server
    success, message = test_mcp_connection()
    print(f"MCP Server Connection: {message}")
    
    if not success:
        print_test_result("MCP Server Test", False, "Failed to connect to MCP server")
        return False
    
    # Test getting tools
    success, tools = asyncio.run(mcp_get_tools())
    
    if not success:
        print_test_result("MCP Server Test", False, "Failed to get tools from MCP server")
        return False
    
    print(f"Available tools: {len(tools)}")
    for i, tool in enumerate(tools):
        print(f"{i+1}. {tool['name']} - {tool['description']}")
    
    # Test tools
    success = asyncio.run(test_mcp_tools())
    
    print_test_result("MCP Server Test", success, "All tests passed" if success else "Some tests failed")
    return success

if __name__ == "__main__":
    run_test()
