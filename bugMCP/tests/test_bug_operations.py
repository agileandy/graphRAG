"""Tests for bug operations using the MCP server."""

import pytest
import json
from typing import Any

from mcp.client.session import (
    ClientSession,
)  # Assuming ClientSession is used via a fixture
from mcp.types import TextContent  # Import TextContent


@pytest.mark.asyncio
async def test_add_bug_operation(
    mcp_session: ClientSession, test_bug_data: dict[str, Any]
):
    """Test adding a new bug via MCP."""
    result = await mcp_session.call_tool("add_bug", test_bug_data)
    assert result.content and len(result.content) > 0
    content_item = result.content[0]
    assert isinstance(content_item, TextContent)

    data = json.loads(content_item.text)
    assert data.get("status") == "success"
    assert "bug_id" in data
    return data["bug_id"]  # Return bug_id for subsequent tests


@pytest.mark.asyncio
async def test_get_bug_operation(
    mcp_session: ClientSession, test_bug_data: dict[str, Any]
):
    """Test retrieving a bug by ID via MCP."""
    # First, add a bug to retrieve
    add_result = await mcp_session.call_tool("add_bug", test_bug_data)
    assert add_result.content and len(add_result.content) > 0
    add_content_item = add_result.content[0]
    assert isinstance(add_content_item, TextContent)
    bug_id = json.loads(add_content_item.text).get("bug_id")
    assert bug_id is not None

    # Retrieve the bug
    get_result = await mcp_session.call_tool("get_bug", {"id": bug_id})
    assert get_result.content and len(get_result.content) > 0
    get_content_item = get_result.content[0]
    assert isinstance(get_content_item, TextContent)

    retrieved_bug = json.loads(get_content_item.text).get("bug")
    assert retrieved_bug is not None
    assert retrieved_bug["id"] == bug_id
    assert retrieved_bug["description"] == test_bug_data["description"]
    assert retrieved_bug["cause"] == test_bug_data["cause"]
    # MCP server might set default status to 'open'
    # assert retrieved_bug["status"] == test_bug_data["status"]


@pytest.mark.asyncio
async def test_update_bug_operation(
    mcp_session: ClientSession, test_bug_data: dict[str, Any]
):
    """Test updating an existing bug via MCP."""
    # Add a bug first
    add_result = await mcp_session.call_tool("add_bug", test_bug_data)
    assert add_result.content and len(add_result.content) > 0
    add_content_item = add_result.content[0]
    assert isinstance(add_content_item, TextContent)
    bug_id = json.loads(add_content_item.text).get("bug_id")
    assert bug_id is not None

    # Update the bug
    update_payload = {
        "id": bug_id,
        "status": "fixed",
        "resolution": "Resolved by test case",
    }
    update_result = await mcp_session.call_tool("update_bug", update_payload)
    assert update_result.content and len(update_result.content) > 0
    update_content_item = update_result.content[0]
    assert isinstance(update_content_item, TextContent)

    update_data = json.loads(update_content_item.text)
    assert update_data.get("status") == "success"

    # Verify the update
    get_result = await mcp_session.call_tool("get_bug", {"id": bug_id})
    assert get_result.content and len(get_result.content) > 0
    get_content_item = get_result.content[0]
    assert isinstance(get_content_item, TextContent)

    updated_bug = json.loads(get_content_item.text).get("bug")
    assert updated_bug is not None
    assert updated_bug["status"] == "fixed"
    assert updated_bug["resolution"] == "Resolved by test case"


@pytest.mark.asyncio
async def test_delete_bug_operation(
    mcp_session: ClientSession, test_bug_data: dict[str, Any]
):
    """Test deleting a bug via MCP."""
    # Add a bug
    add_result = await mcp_session.call_tool("add_bug", test_bug_data)
    assert add_result.content and len(add_result.content) > 0
    add_content_item = add_result.content[0]
    assert isinstance(add_content_item, TextContent)
    bug_id = json.loads(add_content_item.text).get("bug_id")
    assert bug_id is not None

    # Delete the bug
    delete_result = await mcp_session.call_tool("delete_bug", {"id": bug_id})
    assert delete_result.content and len(delete_result.content) > 0
    delete_content_item = delete_result.content[0]
    assert isinstance(delete_content_item, TextContent)

    delete_data = json.loads(delete_content_item.text)
    assert delete_data.get("status") == "success"

    # Verify deletion by trying to get the bug (should fail or return error)
    get_result = await mcp_session.call_tool("get_bug", {"id": bug_id})
    assert get_result.content and len(get_result.content) > 0
    get_content_item = get_result.content[0]
    assert isinstance(get_content_item, TextContent)

    get_data = json.loads(get_content_item.text)
    assert (
        get_data.get("status") == "error"
    )  # Expecting an error as bug should not be found
    assert "not found" in get_data.get("message", "").lower()


@pytest.mark.asyncio
async def test_list_bugs_operation(
    mcp_session: ClientSession, test_bug_data: dict[str, Any]
):
    """Test listing bugs via MCP."""
    # Ensure no bugs initially (or handle existing ones if tests run in shared env)
    # The cleanup_bugs fixture in conftest.py should handle this.

    # Add a couple of bugs
    bug_data1 = test_bug_data.copy()
    bug_data1["description"] = "Bug 1 for listing"
    add_result1 = await mcp_session.call_tool("add_bug", bug_data1)
    assert add_result1.content and len(add_result1.content) > 0
    add_content_item1 = add_result1.content[0]
    assert isinstance(add_content_item1, TextContent)
    bug_id1 = json.loads(add_content_item1.text).get("bug_id")

    bug_data2 = test_bug_data.copy()
    bug_data2["description"] = "Bug 2 for listing"
    add_result2 = await mcp_session.call_tool("add_bug", bug_data2)
    assert add_result2.content and len(add_result2.content) > 0
    add_content_item2 = add_result2.content[0]
    assert isinstance(add_content_item2, TextContent)
    bug_id2 = json.loads(add_content_item2.text).get("bug_id")

    # List bugs
    list_result = await mcp_session.call_tool("list_bugs", {})
    assert list_result.content and len(list_result.content) > 0
    list_content_item = list_result.content[0]
    assert isinstance(list_content_item, TextContent)

    listed_bugs_data = json.loads(list_content_item.text)
    assert "bugs" in listed_bugs_data
    bugs_list = listed_bugs_data["bugs"]
    assert isinstance(bugs_list, list)

    # Check if the added bugs are in the list
    found_bug1 = any(bug["id"] == bug_id1 for bug in bugs_list)
    found_bug2 = any(bug["id"] == bug_id2 for bug in bugs_list)
    assert found_bug1
    assert found_bug2
