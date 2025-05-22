"""Common utility functions for GraphRAG tests."""

import asyncio
import json
import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
import websockets
from websockets.exceptions import ConnectionClosed

# Type aliases
MCPResponse = Dict[str, Any]
WebResponse = Dict[str, Any]

# Terminal colors
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.config import get_port

# Get ports from centralized configuration
api_port = get_port("api")
mcp_port = get_port("mcp")

# API endpoints
API_BASE_URL = f"http://localhost:{api_port}"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
SEARCH_ENDPOINT = f"{API_BASE_URL}/search"
DOCUMENTS_ENDPOINT = f"{API_BASE_URL}/documents"
CONCEPTS_ENDPOINT = f"{API_BASE_URL}/concepts"
BOOKS_ENDPOINT = f"{API_BASE_URL}/books"
JOBS_ENDPOINT = f"{API_BASE_URL}/jobs"

# Event loop management
def get_or_create_eventloop() -> asyncio.AbstractEventLoop:
    """Get the current event loop or create a new one."""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

def run_async(coro: Any) -> Any:
    """Run an async coroutine in a sync context."""
    loop = get_or_create_eventloop()
    return loop.run_until_complete(coro)

# Test formatting utilities
def print_test_result(test_name: str, success: bool, message: str = "") -> None:
    """Print a test result with color coding."""
    if success:
        print(f"{GREEN}✓ {test_name} passed{RESET}")
        if message:
            print(f"  {message}")
    else:
        print(f"{RED}✗ {test_name} failed{RESET}")
        if message:
            print(f"  {message}")

def print_section(title: str) -> None:
    """Print a section header."""
    print("\n" + "-" * 80)
    print(f"{BOLD}{title}{RESET}")
    print("-" * 80)

def print_header(title: str) -> None:
    """Print a main header."""
    print("\n" + "=" * 80)
    print(f"{BOLD}{title.center(80)}{RESET}")
    print("=" * 80)

# Test data utilities
def get_test_document_text() -> str:
    """Get sample text for test documents."""
    return """
    GraphRAG: Enhancing Large Language Models with Knowledge Graphs

    GraphRAG is an innovative system that combines Retrieval-Augmented Generation (RAG)
    with knowledge graphs to enhance the capabilities of Large Language Models (LLMs).
    """

def get_test_document_metadata() -> Dict[str, str]:
    """Get sample metadata for test documents."""
    return {
        "title": "GraphRAG System Overview",
        "author": "Test Author",
        "category": "AI Systems",
        "source": "Test Suite",
        "type": "documentation"
    }

# Web API utilities
def wait_for_api_ready(max_retries: int = 30, retry_interval: int = 2) -> bool:
    """Wait for the API to be ready."""
    print(f"Waiting for API to be ready at {HEALTH_ENDPOINT}...")
    for i in range(max_retries):
        try:
            response = requests.get(HEALTH_ENDPOINT, timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") in ["ok", "degraded"]:
                    print(f"API is ready! Status: {health_data.get('status')}")
                    return True
        except requests.RequestException:
            pass
        print(f"API not ready yet. Retrying in {retry_interval} seconds... ({i + 1}/{max_retries})")
        time.sleep(retry_interval)
    print("Failed to connect to API after maximum retries.")
    return False

def check_database_initialization(verify_indexes: bool = False) -> Tuple[bool, WebResponse]:
    """Check database initialization status via Web API."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/admin/database/check",
            params={"verify_indexes": verify_indexes},
            timeout=10
        )
        return response.ok, response.json()
    except requests.RequestException as e:
        return False, {"error": str(e)}

def add_test_document(text: str, metadata: Dict[str, Any]) -> Tuple[bool, WebResponse]:
    """Add a document via Web API."""
    try:
        response = requests.post(
            DOCUMENTS_ENDPOINT,
            json={"text": text, "metadata": metadata},
            timeout=10
        )
        return response.ok, response.json()
    except requests.RequestException as e:
        return False, {"error": str(e)}

def search_documents(query: str, n_results: int = 5) -> Tuple[bool, WebResponse]:
    """Search documents via Web API."""
    try:
        response = requests.post(
            SEARCH_ENDPOINT,
            json={"query": query, "n_results": n_results},
            timeout=10
        )
        return response.ok, response.json()
    except requests.RequestException as e:
        return False, {"error": str(e)}

def get_job_status(job_id: str) -> Tuple[bool, WebResponse]:
    """Get job status via Web API."""
    try:
        response = requests.get(f"{JOBS_ENDPOINT}/{job_id}", timeout=10)
        return response.ok, response.json()
    except requests.RequestException as e:
        return False, {"error": str(e)}

def cancel_job(job_id: str) -> Tuple[bool, WebResponse]:
    """Cancel a job via Web API."""
    try:
        response = requests.post(f"{JOBS_ENDPOINT}/{job_id}/cancel", timeout=10)
        return response.ok, response.json()
    except requests.RequestException as e:
        return False, {"error": str(e)}

# MCP utilities
async def test_mcp_connection(
    host: str = "localhost",
    port: Optional[int] = None,
    timeout: float = 5.0
) -> Tuple[bool, str]:
    """Test connection to the MCP server."""
    if port is None:
        port = mcp_port

    uri = f"ws://{host}:{port}"
    try:
        async with websockets.connect(uri, timeout=timeout) as websocket:
            await websocket.send(json.dumps({"type": "ping"}))
            response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            response_data = json.loads(response)
            if response_data.get("type") == "pong":
                return True, "Connection successful"
            return False, f"Unexpected response: {response_data}"
    except (ConnectionClosed, asyncio.TimeoutError) as e:
        return False, f"Connection failed: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

async def mcp_invoke_tool(
    tool_name: str,
    parameters: Dict[str, Any] = {},
    timeout: float = 10.0
) -> Tuple[bool, MCPResponse]:
    """Invoke a tool on the MCP server."""
    try:
        async with websockets.connect(f"ws://localhost:{mcp_port}", timeout=timeout) as websocket:
            request = {
                "type": "invoke_tool",
                "tool": tool_name,
                "parameters": parameters
            }
            await websocket.send(json.dumps(request))
            response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            response_data = json.loads(response)

            if response_data.get("type") == "tool_result":
                return True, response_data
            return False, {"error": f"Unexpected response type: {response_data.get('type')}"}
    except (ConnectionClosed, asyncio.TimeoutError) as e:
        return False, {"error": f"Connection failed: {str(e)}"}
    except Exception as e:
        return False, {"error": f"Unexpected error: {str(e)}"}

async def mcp_search(
    query: str,
    max_results: int = 5,
    timeout: float = 10.0
) -> Tuple[bool, MCPResponse]:
    """Perform a search using the MCP server."""
    try:
        async with websockets.connect(f"ws://localhost:{mcp_port}", timeout=timeout) as websocket:
            request = {
                "type": "search",
                "query": query,
                "max_results": max_results
            }
            await websocket.send(json.dumps(request))
            response = await asyncio.wait_for(websocket.recv(), timeout=timeout)
            response_data = json.loads(response)

            if response_data.get("type") == "search_results":
                return True, response_data
            return False, {"error": f"Unexpected response type: {response_data.get('type')}"}
    except (ConnectionClosed, asyncio.TimeoutError) as e:
        return False, {"error": f"Connection failed: {str(e)}"}
    except Exception as e:
        return False, {"error": f"Unexpected error: {str(e)}"}

# Synchronous wrappers
def sync_mcp_connection(host: str = "localhost", port: Optional[int] = None, timeout: float = 5.0) -> Tuple[bool, str]:
    """Synchronous wrapper for test_mcp_connection."""
    return run_async(test_mcp_connection(host, port, timeout))

def sync_mcp_invoke_tool(tool_name: str, parameters: Dict[str, Any] = {}, timeout: float = 10.0) -> Tuple[bool, MCPResponse]:
    """Synchronous wrapper for mcp_invoke_tool."""
    return run_async(mcp_invoke_tool(tool_name, parameters, timeout))

def sync_mcp_search(query: str, max_results: int = 5, timeout: float = 10.0) -> Tuple[bool, MCPResponse]:
    """Synchronous wrapper for mcp_search."""
    return run_async(mcp_search(query, max_results, timeout))

def run_pytest_async(module_file: str) -> None:
    """Run pytest with async support."""
    import pytest
    pytest.main([module_file, "-v", "--asyncio-mode=auto"])