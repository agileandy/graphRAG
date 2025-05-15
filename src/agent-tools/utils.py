#!/usr/bin/env python3
"""
Utility functions for GraphRAG agent tools.

This module provides common functionality used by all agent tools:
- Configuration loading from environment variables
- MPC server connection handling
- Error handling
"""

from src.config import get_port, load_config

# Get ports from centralized configuration
mpc_port = get_port('mpc')
docker_neo4j_port = get_port('docker_neo4j_bolt')

# Default configuration that can be overridden by environment variables
DEFAULT_CONFIG = {
    "MPC_HOST": "localhost",
    "MPC_PORT": str(mpc_port),
    "NEO4J_URI": f"bolt://localhost:{docker_neo4j_port}",  # Default port for Docker mapping
    "NEO4J_USERNAME": "neo4j",
    "NEO4J_PASSWORD": "graphrag"
}

def get_mpc_url() -> str:
    """
    Get the MPC server URL from configuration.

    Returns:
        MPC server URL
    """
    config = load_config()
    return f"ws://{config['MPC_HOST']}:{config['MPC_PORT']}"

def connect_to_mpc(url: Optional[str] = None) -> ws.ClientConnection:
    """
    Connect to the MPC server.

    Args:
        url: MPC server URL (optional, will use configuration if not provided)

    Returns:
        WebSocket connection to MPC server

    Raises:
        SystemExit: If connection fails
    """
    if url is None:
        url = get_mpc_url()

    try:
        return ws.connect(url)
    except Exception as e:
        print(f"Error connecting to MPC server at {url}: {e}", file=sys.stderr)
        print("\nPossible solutions:")
        print("1. Check if the GraphRAG MPC server is running")
        print("2. Verify the MPC_HOST and MPC_PORT environment variables")
        print("3. Check Docker port mappings if using Docker")
        sys.exit(1)

def send_request(conn: ws.ClientConnection, action: str, **kwargs) -> Dict[str, Any]:
    """
    Send a request to the MPC server and return the response.

    Args:
        conn: WebSocket connection
        action: Action to perform
        **kwargs: Additional parameters for the action

    Returns:
        Response from the MPC server

    Raises:
        SystemExit: If communication fails
    """
    # Create the message
    message = {"action": action, **kwargs}

    # Send the message
    try:
        conn.send(json.dumps(message))

        # Receive the response
        response = conn.recv()
        return json.loads(response)
    except Exception as e:
        print(f"Error communicating with MPC server: {e}", file=sys.stderr)
        sys.exit(1)

def format_json(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Format JSON data for display.

    Args:
        data: JSON data
        indent: Indentation level

    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=indent)

def check_chromadb_version():
    """
    Checks and prints the installed ChromaDB version.
    """
    try:
        import chromadb
        print(f"ChromaDB version: {chromadb.__version__}")
    except ImportError:
        print("ChromaDB is not installed.")

if __name__ == "__main__":
    # Example usage (optional, for testing the utility script directly)
    check_chromadb_version()
