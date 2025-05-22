"""Performance tests for bug tracking system."""

import asyncio
import json
import pytest
import time
from typing import List


class TestBugTrackingPerformance:
    """Performance test suite for bug tracking."""

    async def _create_test_bugs(self, websocket_session, count: int) -> List[str]:
        """Create multiple test bugs for performance testing."""
        bug_ids = []
        for i in range(count):
            result = await websocket_session.call_tool(
                "add_bug",
                {
                    "description": f"Performance test bug {i}",
                    "cause": "Performance testing",
                },
            )
            data = json.loads(result.content[0].text)
            bug_ids.append(data["bug_id"])
        return bug_ids

    @pytest.mark.asyncio
    async def test_bulk_creation_performance(self, websocket_session):
        """Test performance of creating multiple bugs."""
        start_time = time.time()
        bug_ids = await self._create_test_bugs(websocket_session, 100)
        elapsed = time.time() - start_time

        assert len(bug_ids) == 100
        assert elapsed < 5.0  # Should create 100 bugs in under 5 seconds

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, websocket_session):
        """Test performance of concurrent operations."""
        # Create some test bugs first
        bug_ids = await self._create_test_bugs(websocket_session, 10)

        # Define concurrent operations
        async def update_operation(bug_id: str) -> float:
            start = time.time()
            await websocket_session.call_tool(
                "update_bug",
                {
                    "id": bug_id,
                    "status": "in-progress",
                },
            )
            return time.time() - start

        # Run concurrent updates
        start_time = time.time()
        update_times = await asyncio.gather(
            *[update_operation(bug_id) for bug_id in bug_ids]
        )
        total_elapsed = time.time() - start_time

        # Verify performance
        assert total_elapsed < 2.0  # All updates should complete in under 2 seconds
        assert max(update_times) < 0.5  # Individual updates should be fast

    @pytest.mark.asyncio
    async def test_search_performance(self, websocket_session):
        """Test performance of searching/listing bugs."""
        # Create test data
        await self._create_test_bugs(websocket_session, 50)

        # Test list_bugs performance
        start_time = time.time()
        result = await websocket_session.call_tool("list_bugs", {})
        elapsed = time.time() - start_time

        assert elapsed < 0.5  # Should return results in under 500ms

    @pytest.mark.asyncio
    async def test_concurrent_reads(self, websocket_session):
        """Test performance of concurrent read operations."""
        # Create test data
        bug_ids = await self._create_test_bugs(websocket_session, 10)

        async def read_operation(bug_id: str) -> float:
            start = time.time()
            await websocket_session.call_tool("get_bug", {"id": bug_id})
            return time.time() - start

        # Run concurrent reads
        start_time = time.time()
        read_times = await asyncio.gather(
            *[read_operation(bug_id) for bug_id in bug_ids * 10]  # 100 total reads
        )
        total_elapsed = time.time() - start_time

        assert total_elapsed < 3.0  # All reads should complete in under 3 seconds
        assert sum(read_times) / len(read_times) < 0.1  # Average read time under 100ms
