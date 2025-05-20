#!/usr/bin/env python3
"""Utility functions for GraphRAG agent tools.

This module provides common functionality used by all agent tools:
- Configuration loading from environment variables
- MCP server connection handling
- Error handling
- Logging
"""

import json
import logging
import os
import sys
import traceback
from typing import Any

import websockets.sync.client as ws

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger("graphrag-utils")

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.config import get_port

# Get ports from centralized configuration
mcp_port = get_port("mcp")
docker_neo4j_port = get_port("docker_neo4j_bolt")

# Default configuration that can be overridden by environment variables
DEFAULT_CONFIG = {
    "MCP_HOST": "localhost",
    "MCP_PORT": str(mcp_port),  # Use MCP port by default
    "MCP_SERVER_TYPE": "mcp",  # Use MCP server by default (JSON-RPC 2.0)
    "NEO4J_URI": f"bolt://localhost:{docker_neo4j_port}",  # Default port for Docker mapping
    "NEO4J_USERNAME": "neo4j",
    "NEO4J_PASSWORD": "graphrag",
}


def load_config() -> dict[str, str]:
    """Load configuration from environment variables with defaults.

    Returns:
        Dictionary with configuration values

    """
    logger.debug("Loading configuration with defaults and environment variables")
    config = DEFAULT_CONFIG.copy()
    logger.debug(f"Default configuration: {config}")

    # Override defaults with environment variables if they exist
    env_overrides = {}
    for key in config:
        if key in os.environ:
            env_overrides[key] = os.environ[key]
            config[key] = os.environ[key]

    if env_overrides:
        logger.debug(f"Environment variable overrides: {env_overrides}")
    else:
        logger.debug("No environment variable overrides found")

    logger.debug(f"Final configuration: {config}")
    return config


def get_mcp_url() -> str:
    """Get the MCP server URL from configuration.

    Returns:
        MCP server URL

    """
    logger.debug("Getting MCP server URL from configuration")
    config = load_config()
    server_type = config.get("MCP_SERVER_TYPE", "mcp").lower()
    logger.debug(f"Server type from config: {server_type}")

    # Use the correct port based on server type
    if server_type == "mcp":
        port = get_port("mcp")  # MCP server port (8767)
        logger.debug(f"Using MCP server port: {port}")
    else:
        port = get_port("mcp")  # MCP server port (8767)
        logger.debug(f"Using MCP server port: {port}")

    # Override with environment variable if set
    if "MCP_PORT" in os.environ:
        port = os.environ["MCP_PORT"]
        logger.debug(f"Overriding port with environment variable: {port}")

    host = config["MCP_HOST"]
    url = f"ws://{host}:{port}"
    logger.debug(f"Constructed MCP URL: {url}")

    return url


def connect_to_mcp(url: str | None = None) -> ws.ClientConnection:
    """Connect to the MCP server.

    Args:
        url: MCP server URL (optional, will use configuration if not provided)

    Returns:
        WebSocket connection to MCP server

    Raises:
        SystemExit: If connection fails

    """
    if url is None:
        url = get_mcp_url()
        logger.debug(f"No URL provided, using configured URL: {url}")
    else:
        logger.debug(f"Using provided URL: {url}")

    try:
        logger.info(f"Connecting to MCP server at {url}")
        connection = ws.connect(url)
        logger.info("Successfully connected to MCP server")
        return connection
    except Exception as e:
        error_msg = f"Error connecting to MCP server at {url}: {e}"
        logger.error(error_msg)
        logger.debug(f"Exception details: {traceback.format_exc()}")

        print(error_msg, file=sys.stderr)
        print("\nPossible solutions:")
        print("1. Check if the GraphRAG MCP server is running")
        print("2. Verify the MCP_HOST and MCP_PORT environment variables")
        print("3. Check Docker port mappings if using Docker")

        logger.debug("Exiting with status code 1")
        sys.exit(1)


def send_request(conn: ws.ClientConnection, action: str, **kwargs) -> dict[str, Any]:
    """Send a request to the MCP server and return the response.

    Args:
        conn: WebSocket connection
        action: Action to perform
        **kwargs: Additional parameters for the action

    Returns:
        Response from the MCP server

    Raises:
        SystemExit: If communication fails

    """
    logger.debug(f"Preparing to send request: action={action}, params={kwargs}")

    # Check if we're connecting to the MCP server (JSON-RPC 2.0)
    config = load_config()
    server_type = config.get("MCP_SERVER_TYPE", "mcp").lower()
    logger.debug(f"Server type: {server_type}")

    if server_type == "mcp":
        # Using JSON-RPC 2.0 for MCP server
        message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "invokeTool",
            "params": {"name": action, "parameters": kwargs},
        }
        logger.debug("Using JSON-RPC 2.0 format for MCP server")
    else:
        # Legacy format for backward compatibility
        message = {"action": action, **kwargs}
        logger.debug("Using legacy format for backward compatibility")

    # Send the message
    try:
        message_json = json.dumps(message)
        logger.debug(
            f"Sending message: {message_json[:200]}..."
            if len(message_json) > 200
            else message_json
        )
        conn.send(message_json)
        logger.debug("Message sent successfully")

        # Receive the response
        logger.debug("Waiting for response...")
        response = conn.recv()
        logger.debug(
            f"Received raw response: {response[:200]}..."
            if len(response) > 200
            else response
        )

        response_data = json.loads(response)
        logger.debug("Response parsed successfully")

        # Handle JSON-RPC 2.0 response format
        if "jsonrpc" in response_data and response_data.get("jsonrpc") == "2.0":
            logger.debug("Processing JSON-RPC 2.0 response")

            if "error" in response_data:
                error = response_data["error"]
                error_msg = error.get("message", "Unknown error")
                logger.error(f"Error from server: {error_msg}")
                print(f"Error from server: {error_msg}", file=sys.stderr)
                return {"error": error_msg}
            elif "result" in response_data:
                logger.debug("Extracted result from JSON-RPC 2.0 response")
                return response_data["result"]
            else:
                logger.warning(
                    "JSON-RPC 2.0 response missing both 'error' and 'result' fields"
                )
                return response_data

        # Return legacy response format
        logger.debug("Returning legacy response format")
        return response_data
    except Exception as e:
        error_msg = f"Error communicating with MCP server: {e}"
        logger.error(error_msg)
        logger.debug(f"Exception details: {traceback.format_exc()}")
        print(error_msg, file=sys.stderr)
        sys.exit(1)


def format_json(data: dict[str, Any], indent: int = 2) -> str:
    """Format JSON data for display.

    Args:
        data: JSON data
        indent: Indentation level

    Returns:
        Formatted JSON string

    """
    return json.dumps(data, indent=indent)


def check_chromadb_version() -> None:
    """Checks and prints the installed ChromaDB version."""
    try:
        import chromadb

        print(f"ChromaDB version: {chromadb.__version__}")
    except ImportError:
        print("ChromaDB is not installed.")


if __name__ == "__main__":
    # Example usage (optional, for testing the utility script directly)
    check_chromadb_version()
