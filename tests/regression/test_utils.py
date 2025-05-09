"""
Utility functions for GraphRAG regression tests.
"""
import os
import sys
import time
import json
import requests
import subprocess
import asyncio
import websockets
from typing import Dict, Any, Tuple, List, Optional

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# API endpoints
API_BASE_URL = "http://localhost:5001"
HEALTH_ENDPOINT = f"{API_BASE_URL}/health"
SEARCH_ENDPOINT = f"{API_BASE_URL}/search"
DOCUMENTS_ENDPOINT = f"{API_BASE_URL}/documents"
CONCEPTS_ENDPOINT = f"{API_BASE_URL}/concepts"
BOOKS_ENDPOINT = f"{API_BASE_URL}/books"

def wait_for_api_ready(max_retries: int = 30, retry_interval: int = 2) -> bool:
    """
    Wait for the API to be ready by checking the health endpoint.

    Args:
        max_retries: Maximum number of retries
        retry_interval: Interval between retries in seconds

    Returns:
        True if the API is ready, False otherwise
    """
    print(f"Waiting for API to be ready at {HEALTH_ENDPOINT}...")

    for i in range(max_retries):
        try:
            response = requests.get(HEALTH_ENDPOINT, timeout=5)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get('status') in ['ok', 'degraded']:
                    print(f"API is ready! Status: {health_data.get('status')}")
                    return True
        except requests.RequestException:
            pass

        print(f"API not ready yet. Retrying in {retry_interval} seconds... ({i+1}/{max_retries})")
        time.sleep(retry_interval)

    print("Failed to connect to API after maximum retries.")
    return False

def check_api_health() -> Tuple[bool, Dict[str, Any]]:
    """
    Check the health of the API.

    Returns:
        Tuple of (success, health_data)
    """
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            is_healthy = health_data.get('status') == 'ok'
            return is_healthy, health_data
        return False, {"error": f"Unexpected status code: {response.status_code}"}
    except requests.RequestException as e:
        return False, {"error": str(e)}

def add_test_document(document_text: str, metadata: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Add a test document to the GraphRAG system via the API.

    Args:
        document_text: Document text
        metadata: Document metadata

    Returns:
        Tuple of (success, response_data)
    """
    document = {
        "text": document_text,
        "metadata": metadata
    }

    try:
        response = requests.post(DOCUMENTS_ENDPOINT, json=document, timeout=30)
        if response.status_code in [200, 201]:
            return True, response.json()
        return False, {"error": f"Unexpected status code: {response.status_code}", "response": response.text}
    except requests.RequestException as e:
        return False, {"error": str(e)}

def search_documents(query: str, n_results: int = 5, max_hops: int = 2) -> Tuple[bool, Dict[str, Any]]:
    """
    Search for documents using the GraphRAG API.

    Args:
        query: Search query
        n_results: Number of vector results to return
        max_hops: Maximum number of hops in the graph

    Returns:
        Tuple of (success, response_data)
    """
    search_data = {
        "query": query,
        "n_results": n_results,
        "max_hops": max_hops
    }

    try:
        response = requests.post(SEARCH_ENDPOINT, json=search_data, timeout=30)
        if response.status_code == 200:
            return True, response.json()
        return False, {"error": f"Unexpected status code: {response.status_code}", "response": response.text}
    except requests.RequestException as e:
        return False, {"error": str(e)}

def get_concept(concept_name: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Get information about a specific concept.

    Args:
        concept_name: Name of the concept

    Returns:
        Tuple of (success, response_data)
    """
    try:
        response = requests.get(f"{CONCEPTS_ENDPOINT}/{concept_name}", timeout=10)
        if response.status_code == 200:
            return True, response.json()
        return False, {"error": f"Unexpected status code: {response.status_code}", "response": response.text}
    except requests.RequestException as e:
        return False, {"error": str(e)}

def get_all_concepts() -> Tuple[bool, Dict[str, Any]]:
    """
    Get all concepts in the system.

    Returns:
        Tuple of (success, response_data)
    """
    try:
        response = requests.get(CONCEPTS_ENDPOINT, timeout=10)
        if response.status_code == 200:
            return True, response.json()
        return False, {"error": f"Unexpected status code: {response.status_code}", "response": response.text}
    except requests.RequestException as e:
        return False, {"error": str(e)}

def get_documents_for_concept(concept_name: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Get documents related to a specific concept.

    Args:
        concept_name: Name of the concept

    Returns:
        Tuple of (success, response_data)
    """
    try:
        response = requests.get(f"{DOCUMENTS_ENDPOINT}/{concept_name}", timeout=10)
        if response.status_code == 200:
            return True, response.json()
        return False, {"error": f"Unexpected status code: {response.status_code}", "response": response.text}
    except requests.RequestException as e:
        return False, {"error": str(e)}

def start_services() -> Tuple[bool, Optional[subprocess.Popen]]:
    """
    Start the GraphRAG services.

    Returns:
        Tuple of (success, process)
    """
    try:
        # Use the start script to start the services
        process = subprocess.Popen(
            ["./start-graphrag-local.sh"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=True
        )

        # Wait for the API to be ready
        if wait_for_api_ready():
            return True, process

        # If the API is not ready, kill the process
        process.terminate()
        return False, None
    except Exception as e:
        print(f"Error starting services: {e}")
        return False, None

def stop_services(process: Optional[subprocess.Popen] = None) -> bool:
    """
    Stop the GraphRAG services.

    Args:
        process: Process object returned by start_services

    Returns:
        True if successful, False otherwise
    """
    try:
        if process:
            # Try to terminate the process gracefully
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                process.kill()

        # Use the stop script to ensure all services are stopped
        result = subprocess.run(
            ["./tools/graphrag-service.sh", "stop"],
            capture_output=True,
            text=True
        )
        print(f"Stop script output: {result.stdout}")

        # Additional cleanup to make sure all processes are stopped
        subprocess.run(["pkill", "-f", "gunicorn"], check=False)
        subprocess.run(["pkill", "-f", "src.mpc.server"], check=False)
        subprocess.run(["pkill", "-f", "python.*server.py"], check=False)

        # Check if any GraphRAG processes are still running
        ps_result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )

        # Look for any remaining GraphRAG processes
        if "gunicorn" in ps_result.stdout or "src.mpc.server" in ps_result.stdout:
            print("Warning: Some GraphRAG processes are still running. Attempting to force kill...")
            subprocess.run(["pkill", "-9", "-f", "gunicorn"], check=False)
            subprocess.run(["pkill", "-9", "-f", "src.mpc.server"], check=False)

        # Wait a moment for processes to terminate
        time.sleep(2)

        # Verify that services are actually stopped by checking if the API is accessible
        try:
            requests.get(HEALTH_ENDPOINT, timeout=1)
            print("Warning: API is still accessible after stopping services")
            # One last attempt to kill everything
            subprocess.run(["pkill", "-9", "-f", "gunicorn"], check=False)
            subprocess.run(["pkill", "-9", "-f", "python"], check=False)
            time.sleep(2)
        except requests.RequestException:
            # This is actually good - it means the API is not accessible
            pass

        return True
    except Exception as e:
        print(f"Error stopping services: {e}")
        return False

def get_test_document_text() -> str:
    """
    Get the text for a test document.

    Returns:
        Document text
    """
    return """
    GraphRAG: Enhancing Large Language Models with Knowledge Graphs

    GraphRAG is an innovative approach that combines Retrieval-Augmented Generation (RAG)
    with knowledge graphs to enhance the capabilities of Large Language Models (LLMs).

    Traditional RAG systems use vector databases to retrieve relevant information based on
    semantic similarity. While effective, this approach lacks the ability to capture
    relationships between concepts.

    GraphRAG addresses this limitation by integrating a knowledge graph (Neo4j) with a
    vector database (ChromaDB). This hybrid approach enables:

    1. Semantic search through vector embeddings
    2. Relationship-aware retrieval through graph traversal
    3. Enhanced context by combining both retrieval methods

    The system extracts entities and relationships from documents, stores them in both
    databases, and provides a unified query interface that leverages the strengths of both
    approaches.

    GraphRAG can significantly improve the accuracy and relevance of LLM responses by
    providing both textual context and structural knowledge about the relationships
    between concepts.
    """

def get_test_document_metadata() -> Dict[str, Any]:
    """
    Get the metadata for a test document.

    Returns:
        Document metadata
    """
    return {
        "title": "GraphRAG: Enhancing LLMs with Knowledge Graphs",
        "author": "Regression Test",
        "category": "AI",
        "source": "Regression Test"
    }

# MPC server functions
def test_mpc_connection(host="localhost", port=8766, timeout=5) -> Tuple[bool, str]:
    """
    Test connection to the MPC server.

    Args:
        host: MPC server host
        port: MPC server port
        timeout: Connection timeout in seconds

    Returns:
        Tuple of (success, message)
    """
    try:
        async def test_connection():
            uri = f"ws://{host}:{port}"
            try:
                async with websockets.connect(uri, timeout=timeout) as websocket:
                    # Send a ping message
                    await websocket.send(json.dumps({"action": "ping"}))
                    response = await websocket.recv()
                    response_data = json.loads(response)
                    return True, f"Connected to MPC server at {uri}. Response: {response_data}"
            except Exception as e:
                return False, f"Failed to connect to MPC server at {uri}: {e}"

        return asyncio.run(test_connection())
    except ImportError as e:
        return False, f"Failed to import required modules: {e}"
    except Exception as e:
        return False, f"Unexpected error testing MPC connection: {e}"

async def mpc_search(host="localhost", port=8766, query="What is RAG?", n_results=3, max_hops=2) -> Tuple[bool, Dict[str, Any]]:
    """
    Perform a search using the MPC server.

    Args:
        host: MPC server host
        port: MPC server port
        query: Search query
        n_results: Number of results to return
        max_hops: Maximum number of hops in the graph

    Returns:
        Tuple of (success, response)
    """
    uri = f"ws://{host}:{port}"
    try:
        async with websockets.connect(uri) as websocket:
            # Prepare search message
            message = {
                'action': 'search',
                'query': query,
                'n_results': n_results,
                'max_hops': max_hops
            }

            # Send search query
            await websocket.send(json.dumps(message))

            # Receive response
            response = await websocket.recv()
            response_data = json.loads(response)

            return True, response_data
    except Exception as e:
        return False, {"error": str(e)}

# MCP server functions
def test_mcp_connection(host="localhost", port=8767, timeout=5) -> Tuple[bool, str]:
    """
    Test connection to the MCP server.

    Args:
        host: MCP server host
        port: MCP server port
        timeout: Connection timeout in seconds

    Returns:
        Tuple of (success, message)
    """
    try:
        async def test_connection():
            uri = f"ws://{host}:{port}"
            try:
                async with websockets.connect(uri, timeout=timeout) as websocket:
                    # Send initialize request
                    await websocket.send(json.dumps({
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {
                                "name": "test-client",
                                "version": "0.1.0"
                            }
                        },
                        "id": 0
                    }))

                    # Receive response
                    response = await websocket.recv()
                    response_data = json.loads(response)

                    if "result" in response_data:
                        return True, f"Connected to MCP server at {uri}. Server info: {response_data['result'].get('serverInfo', {})}"
                    else:
                        return False, f"Failed to initialize MCP server at {uri}: {response_data.get('error', {})}"
            except Exception as e:
                return False, f"Failed to connect to MCP server at {uri}: {e}"

        return asyncio.run(test_connection())
    except ImportError as e:
        return False, f"Failed to import required modules: {e}"
    except Exception as e:
        return False, f"Unexpected error testing MCP connection: {e}"

async def mcp_get_tools(host="localhost", port=8767) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Get available tools from the MCP server.

    Args:
        host: MCP server host
        port: MCP server port

    Returns:
        Tuple of (success, tools)
    """
    uri = f"ws://{host}:{port}"
    try:
        async with websockets.connect(uri) as websocket:
            # Initialize connection
            await websocket.send(json.dumps({
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "0.1.0"
                    }
                },
                "id": 0
            }))

            # Receive initialize response
            await websocket.recv()

            # Get tools
            await websocket.send(json.dumps({
                "jsonrpc": "2.0",
                "method": "getTools",
                "params": {},
                "id": 1
            }))

            # Receive getTools response
            response = await websocket.recv()
            response_data = json.loads(response)

            if "result" in response_data and "tools" in response_data["result"]:
                return True, response_data["result"]["tools"]
            else:
                return False, []
    except Exception as e:
        return False, []

async def mcp_invoke_tool(host="localhost", port=8767, tool_name="search", parameters=None) -> Tuple[bool, Dict[str, Any]]:
    """
    Invoke a tool on the MCP server.

    Args:
        host: MCP server host
        port: MCP server port
        tool_name: Tool name
        parameters: Tool parameters

    Returns:
        Tuple of (success, response)
    """
    if parameters is None:
        parameters = {}

    uri = f"ws://{host}:{port}"
    try:
        async with websockets.connect(uri) as websocket:
            # Initialize connection
            await websocket.send(json.dumps({
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "0.1.0"
                    }
                },
                "id": 0
            }))

            # Receive initialize response
            await websocket.recv()

            # Invoke tool
            await websocket.send(json.dumps({
                "jsonrpc": "2.0",
                "method": "invokeTool",
                "params": {
                    "name": tool_name,
                    "parameters": parameters
                },
                "id": 1
            }))

            # Receive invokeTool response
            response = await websocket.recv()
            response_data = json.loads(response)

            if "result" in response_data:
                return True, response_data["result"]
            else:
                return False, {"error": response_data.get("error", {})}
    except Exception as e:
        return False, {"error": str(e)}