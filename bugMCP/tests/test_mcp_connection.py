"""Tests for MCP server connection and basic protocol adherence."""

import pytest
import json
from typing import Any

from mcp.types import Tool, ListToolsResult, TextContent # Import TextContent

@pytest.mark.asyncio
async def test_mcp_server_connection(mcp_session):
    """Test basic connection and initialization with the MCP server."""
    # The mcp_session fixture already handles connection and initialization
    # If it fails, the test will fail there.
    # We can add a simple assertion to confirm the session is active if needed,
    # but session.initialize() being successful is the main check.
    assert mcp_session is not None
    # assert mcp_session.initialized -> This attribute doesn't exist, initialization is confirmed by initialize() success

@pytest.mark.asyncio
async def test_list_tools_protocol(mcp_session):
    """Test the tools/list method for protocol compliance."""
    result = await mcp_session.list_tools()
    assert isinstance(result, ListToolsResult)
    assert hasattr(result, 'tools')
    assert isinstance(result.tools, list)

    for tool in result.tools:
        assert isinstance(tool, Tool)
        assert hasattr(tool, 'name')
        assert isinstance(tool.name, str)
        assert hasattr(tool, 'description')
        # description can be None
        assert isinstance(tool.description, (str, type(None)))
        assert hasattr(tool, 'inputSchema')
        # inputSchema can be None if no parameters
        assert isinstance(tool.inputSchema, (dict, type(None)))

@pytest.mark.asyncio
async def test_ping_tool_exists(mcp_session):
    """Test that the 'ping' tool is listed."""
    tools_list = await mcp_session.list_tools()
    assert any(tool.name == "ping" for tool in tools_list.tools)

@pytest.mark.asyncio
async def test_ping_tool_execution(mcp_session):
    """Test executing the 'ping' tool."""
    result = await mcp_session.call_tool("ping", {})
    assert result.content
    assert len(result.content) > 0
    content_item = result.content[0]
    assert isinstance(content_item, TextContent)

    data = json.loads(content_item.text)
    assert "message" in data
    assert data["message"] == "Pong!"
    assert "status" in data
    assert data["status"] == "success"

@pytest.mark.asyncio
async def test_get_tool_schemas(mcp_session):
    """Test retrieving and verifying tool schemas."""
    tools_list = await mcp_session.list_tools()
    assert tools_list.tools

    tool_schemas = {tool.name: tool.inputSchema for tool in tools_list.tools}

    # Example: Verify schema for 'search' tool
    assert "search" in tool_schemas
    search_schema = tool_schemas["search"]
    assert isinstance(search_schema, dict)
    assert search_schema.get("type") == "object"
    assert "properties" in search_schema
    assert "query" in search_schema["properties"]
    assert search_schema["properties"]["query"]["type"] == "string"
    assert "required" in search_schema
    assert "query" in search_schema["required"]

@pytest.mark.asyncio
async def test_unknown_tool_call(mcp_session):
    """Test calling a non-existent tool."""
    with pytest.raises(Exception) as exc_info: # MCPError specifically if defined and imported
        await mcp_session.call_tool("non_existent_tool", {})
    # Check for a specific error message if the MCP library provides one
    # For now, just check that an exception is raised.
    # Example: assert "Tool not found" in str(exc_info.value)
    # This depends on the exact error returned by the mcp_server for unknown tools.
    # The current mcp_server returns: {"error": {"code": -32601, "message": f"Tool not found: {tool_name}"}}
    # The mcp.shared.exceptions.McpError wraps this.
    assert "Tool not found" in str(exc_info.value)

@pytest.mark.asyncio
async def test_tool_call_with_invalid_params(mcp_session):
    """Test calling a tool with invalid parameters."""
    # Assuming 'search' tool requires 'query' parameter
    with pytest.raises(Exception) as exc_info:
         # The mcp_server's handle_search returns an error dict, which McpError wraps
        await mcp_session.call_tool("search", {"wrong_param": "test"})
    assert "Missing required parameter: query" in str(exc_info.value)
