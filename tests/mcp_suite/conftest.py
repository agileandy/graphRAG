"""Pytest configuration for MCP test suite."""

import pytest
import asyncio
from typing import AsyncGenerator, Generator

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def setup_test_environment() -> AsyncGenerator[None, None]:
    """Set up test environment before each test.

    This includes:
    - Ensuring clean database state
    - Starting MCP server
    - Establishing WebSocket connection
    - Setting up test data if needed
    """
    # Add setup code here
    yield
    # Add cleanup code here

@pytest.fixture
def pytest_configure(config):
    """Configure pytest for the test suite."""
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as requiring asyncio"
    )

pytest_plugins = ["pytest_asyncio"]