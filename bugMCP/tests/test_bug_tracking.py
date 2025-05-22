"""Tests for the bug tracking functionality."""

import json
import pytest
import asyncio
from typing import Any, Dict

from mcp.types import TextContent


class TestBugTracking:
    """Test suite for bug tracking functionality."""

    @pytest.mark.asyncio
    async def test_list_bugs_empty(self, websocket_session):
        """Test listing bugs when none exist."""
        result = await websocket_session.call_tool("list_bugs", {})
        assert result.content
        assert isinstance(result.content[0], TextContent)
        bugs = json.loads(result.content[0].text)
        assert isinstance(bugs, list)
        assert len(bugs) == 0

    @pytest.mark.asyncio
    async def test_add_bug_success(self, websocket_session):
        """Test adding a bug successfully."""
        result = await websocket_session.call_tool(
            "add_bug",
            {
                "description": "Test bug",
                "cause": "Testing",
            },
        )
        assert result.content
        assert isinstance(result.content[0], TextContent)
        data = json.loads(result.content[0].text)
        assert "bug_id" in data
        return data["bug_id"]

    @pytest.mark.asyncio
    async def test_get_bug_success(self, websocket_session):
        """Test getting a bug by ID."""
        # First add a bug
        bug_id = await self.test_add_bug_success(websocket_session)

        # Then retrieve it
        result = await websocket_session.call_tool("get_bug", {"id": bug_id})
        assert result.content
        assert isinstance(result.content[0], TextContent)
        data = json.loads(result.content[0].text)
        assert data["description"] == "Test bug"
        assert data["cause"] == "Testing"

    @pytest.mark.asyncio
    async def test_update_bug_success(self, websocket_session):
        """Test updating a bug."""
        # First add a bug
        bug_id = await self.test_add_bug_success(websocket_session)

        # Then update it
        result = await websocket_session.call_tool(
            "update_bug",
            {
                "id": bug_id,
                "status": "fixed",
                "resolution": "Fixed in test",
            },
        )
        assert result.content
        assert isinstance(result.content[0], TextContent)

        # Verify the update
        result = await websocket_session.call_tool("get_bug", {"id": bug_id})
        data = json.loads(result.content[0].text)
        assert data["status"] == "fixed"
        assert data["resolution"] == "Fixed in test"

    @pytest.mark.asyncio
    async def test_delete_bug_success(self, websocket_session):
        """Test deleting a bug."""
        # First add a bug
        bug_id = await self.test_add_bug_success(websocket_session)

        # Then delete it
        result = await websocket_session.call_tool("delete_bug", {"id": bug_id})
        assert result.content

        # Verify it's gone
        result = await websocket_session.call_tool("list_bugs", {})
        bugs = json.loads(result.content[0].text)
        assert all(bug["id"] != bug_id for bug in bugs)

    @pytest.mark.asyncio
    async def test_get_nonexistent_bug(self, websocket_session):
        """Test getting a bug that doesn't exist."""
        with pytest.raises(Exception) as exc_info:
            await websocket_session.call_tool("get_bug", {"id": "nonexistent"})
        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_invalid_bug_data(self, websocket_session):
        """Test adding a bug with invalid data."""
        with pytest.raises(Exception):
            await websocket_session.call_tool(
                "add_bug",
                {
                    "invalid_field": "This should fail",
                },
            )

    @pytest.mark.asyncio
    async def test_concurrent_updates(self, websocket_session):
        """Test concurrent updates to the same bug."""
        bug_id = await self.test_add_bug_success(websocket_session)

        # Create multiple update coroutines
        async def update_bug(status: str) -> None:
            await websocket_session.call_tool(
                "update_bug",
                {
                    "id": bug_id,
                    "status": status,
                },
            )

        # Run updates concurrently
        await asyncio.gather(
            update_bug("in-progress"),
            update_bug("fixed"),
            update_bug("won't fix"),
        )

        # Verify final state is consistent
        result = await websocket_session.call_tool("get_bug", {"id": bug_id})
        data = json.loads(result.content[0].text)
        assert data["status"] in ["in-progress", "fixed", "won't fix"]
