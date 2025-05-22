"""Tests for MCP server error handling."""

import pytest
import json
from typing import Any

from mcp.client.session import ClientSession # Assuming ClientSession is used via a fixture
from mcp.types import TextContent # Import TextContent
from mcp.shared.exceptions import McpError # Import McpError for more specific exception checking

@pytest.mark.asyncio
async def test_call_nonexistent_tool(mcp_session: ClientSession):
    """Test calling a tool that does not exist."""
    with pytest.raises(McpError) as exc_info:
        await mcp_session.call_tool("this_tool_does_not_exist", {})

    # The McpError should contain the JSON-RPC error details
    assert exc_info.value.error is not None
    assert exc_info.value.error.code == -32601  # Method not found
    assert "Tool not found" in exc_info.value.error.message

@pytest.mark.asyncio
async def test_call_tool_with_missing_required_params(mcp_session: ClientSession):
    """Test calling a tool with missing required parameters."""
    # Assuming 'add_bug' requires 'description' and 'cause'
    with pytest.raises(McpError) as exc_info:
        await mcp_session.call_tool("add_bug", {"description": "A bug without a cause"})

    assert exc_info.value.error is not None
    # The exact error code and message might depend on the server's validation logic
    # For the current mcp_server.py, it might be a generic error if not handled specifically
    # or a more specific one if validation is added to handle_add_bug.
    # Let's assume the server returns an error indicating missing parameters.
    # The current `bugMCP_mcp.py` server's `add_bug` tool would raise a TypeError if params are missing
    # which the `FastMCP` layer would then convert into an McpError.
    # The `src/mcp/mcp_server.py`'s `handle_add_document` (if used for `add_bug`) returns an error dict.
    assert exc_info.value.error.code != 0 # Not a success code
    assert "missing" in exc_info.value.error.message.lower() or \
           "required" in exc_info.value.error.message.lower()


@pytest.mark.asyncio
async def test_call_tool_with_invalid_param_type(mcp_session: ClientSession):
    """Test calling a tool with parameters of an incorrect type."""
    # Assuming 'get_bug' expects 'id' as an integer (or string that can be int)
    # The bugMCP_mcp.py server's get_bug tool expects an int.
    # The src/mcp/mcp_server.py's handle_invoke_tool would pass params to tool handlers.
    # If the tool handler (e.g., handle_get_bug if it existed) tried to use a non-int ID,
    # it might raise a TypeError or ValueError.
    with pytest.raises(McpError) as exc_info:
        await mcp_session.call_tool("get_bug", {"id": {"not_an_id": True}})

    assert exc_info.value.error is not None
    # Expecting an error related to invalid parameters or type mismatch
    assert exc_info.value.error.code == -32602 or exc_info.value.error.code == -32603 # Invalid params or Internal Error

@pytest.mark.asyncio
async def test_get_nonexistent_bug_error(mcp_session: ClientSession):
    """Test retrieving a non-existent bug by ID."""
    # Using a very unlikely ID
    result = await mcp_session.call_tool("get_bug", {"id": 999999999})
    assert result.content and len(result.content) > 0
    content_item = result.content[0]
    assert isinstance(content_item, TextContent)

    data = json.loads(content_item.text)
    assert data.get("status") == "error"
    assert "not found" in data.get("message", "").lower()

@pytest.mark.asyncio
async def test_update_nonexistent_bug(mcp_session: ClientSession):
    """Test updating a non-existent bug."""
    update_payload = {
        "id": 999999999, # Non-existent ID
        "status": "fixed",
        "resolution": "Attempting to resolve a ghost"
    }
    result = await mcp_session.call_tool("update_bug", update_payload)
    assert result.content and len(result.content) > 0
    content_item = result.content[0]
    assert isinstance(content_item, TextContent)

    data = json.loads(content_item.text)
    assert data.get("status") == "error"
    assert "not found" in data.get("message", "").lower()

@pytest.mark.asyncio
async def test_delete_nonexistent_bug(mcp_session: ClientSession):
    """Test deleting a non-existent bug."""
    result = await mcp_session.call_tool("delete_bug", {"id": 999999999}) # Non-existent ID
    assert result.content and len(result.content) > 0
    content_item = result.content[0]
    assert isinstance(content_item, TextContent)

    data = json.loads(content_item.text)
    assert data.get("status") == "error" # Or success with a message indicating nothing was deleted
                                         # The current bugMCP_mcp.py returns error for not found.
    assert "not found" in data.get("message", "").lower()
