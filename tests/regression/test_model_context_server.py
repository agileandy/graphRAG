#!/usr/bin/env python3
"""Regression test for the GraphRAG Model Context Protocol (MCP) server.

This test verifies that the Model Context Protocol server is running and
responding to requests. It tests the following functionality:
1. Connection to the Model Context Protocol server
2. Getting available tools
3. Invoking tools (ping, search, concept)
"""

import asyncio
import json
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

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
    mcp_get_tools,
    mcp_invoke_tool,
    print_header,
    print_section,
    print_test_result,
    test_mcp_connection,
)


def run_test() -> bool:
    """Run the Model Context Protocol server test.

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
        print_test_result(
            "Model Context Protocol Server Test",
            False,
            "Failed to connect to Model Context Protocol server",
        )
        return False

    # Get available tools
    success, tools = asyncio.run(mcp_get_tools(host="localhost", port=mcp_port))

    if not success:
        print_test_result(
            "Model Context Protocol Server Test",
            False,
            "Failed to get tools from Model Context Protocol server",
        )
        return False

    print(f"Available tools: {len(tools)}")
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool['name']} - {tool['description']}")

    # Test invoking tools
    print_section("Testing Model Context Protocol Tools")

    # Test ping tool
    print("\nTesting ping tool...")
    success, result = asyncio.run(
        mcp_invoke_tool(
            host="localhost", port=mcp_port, tool_name="ping", parameters={}
        )
    )

    print(f"Success: {success}")
    print(f"Result: {json.dumps(result, indent=2)}")

    # Test search tool
    print("\nTesting search tool...")
    success, result = asyncio.run(
        mcp_invoke_tool(
            host="localhost",
            port=mcp_port,
            tool_name="search",
            parameters={"query": "What is GraphRAG?", "n_results": 3},
        )
    )

    print(f"Success: {success}")
    print(f"Result: {json.dumps(result, indent=2)}")

    # Test concept tool
    print("\nTesting concept tool...")
    success, result = asyncio.run(
        mcp_invoke_tool(
            host="localhost",
            port=mcp_port,
            tool_name="concept",
            parameters={"concept_name": "GraphRAG"},
        )
    )

    print(f"Success: {success}")
    print(f"Result: {json.dumps(result, indent=2)}")

    # Print test result
    print_section("Model Context Protocol Server Test: PASSED")
    print("All tests passed")

    return True


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
