"""Test configuration and fixtures for bug tracking tests."""

import asyncio
import json
import os
import pytest
import subprocess
import sys
import time
import websockets
from collections.abc import AsyncGenerator, Generator
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.websocket import websocket_client
from mcp.types import TextContent
from src.config import get_port

@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def mcp_server(
    event_loop: asyncio.AbstractEventLoop
) -> AsyncGenerator[subprocess.Popen, None]:
    """Start the MCP server as a fixture."""
    port = get_port("bug_mcp")
    server_process = subprocess.Popen(
        [
            sys.executable,
            "bugMCP/standalone_server.py",
            "--port",
            str(port),
            "--log-level",
            "DEBUG",
        ],
        cwd=os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server to start with timeout
    start_time = time.time()
    max_wait = 10  # seconds
    while time.time() - start_time < max_wait:
        try:
            async with websockets.connect(f"ws://localhost:{port}"):
                break
        except Exception as e:
            await asyncio.sleep(0.1)
            if server_process.poll() is not None:
                stdout, stderr = server_process.communicate()
                raise RuntimeError(
                    f"Server failed to start. Error: {e}\n"
                    f"stdout: {stdout.decode()}\n"
                    f"stderr: {stderr.decode()}"
                )
    else:
        stdout, stderr = server_process.communicate()
        raise TimeoutError(
            f"Server failed to start within {max_wait} seconds.\n"
            f"stdout: {stdout.decode()}\n"
            f"stderr: {stderr.decode()}"
        )

    yield server_process

    # Cleanup
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_process.kill()
        server_process.wait()

@pytest.fixture
async def mcp_session(
    mcp_server: subprocess.Popen
) -> AsyncGenerator[ClientSession, None]:
    """Create a connected MCP client session."""
    port = get_port("bug_mcp")
    async with websocket_client(
        f"ws://localhost:{port}"
    ) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            yield session

@pytest.fixture
def test_bug_data() -> dict[str, Any]:
    """Return test bug data."""
    return {
        "description": "Test bug from automated test",
        "cause": "Testing the MCP implementation",
        "status": "pending",
        "priority": "medium",
        "tags": ["test", "automated"],
    }

@pytest.fixture(autouse=True)
async def cleanup_bugs(
    mcp_session: ClientSession
) -> AsyncGenerator[None, None]:
    """Clean up any bugs created during tests."""
    yield
    # After each test, list all bugs and delete them
    result = await mcp_session.call_tool("list_bugs", {})
    if result.content:
        content = result.content[0]
        if isinstance(content, TextContent) and content.text:
            bugs = json.loads(content.text)
            for bug in bugs:
                await mcp_session.call_tool("delete_bug", {"id": bug["id"]})
