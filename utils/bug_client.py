#!/usr/bin/env python3
"""Bug tracking client for GraphRAG.

This module provides a robust client for interacting with the bug tracking MCP server.
It includes error handling, retries, and fallback mechanisms.
"""

import argparse
import json
import logging
import os
import socket
import sys
import time
from typing import Any

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import port configuration
try:
    from src.config.ports import get_port

    BUG_MCP_PORT = get_port("bug_mcp")
except (ImportError, ValueError):
    # Fallback if config module is not available
    BUG_MCP_PORT = 5005

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("bug_client")

# Fallback file for storing bugs when server is unavailable
FALLBACK_FILE = os.path.join(
    os.path.dirname(__file__), "..", "bugMCP", "pending_bugs.json"
)


def ensure_fallback_file() -> None:
    """Ensure the fallback file exists."""
    os.makedirs(os.path.dirname(FALLBACK_FILE), exist_ok=True)
    if not os.path.exists(FALLBACK_FILE):
        with open(FALLBACK_FILE, "w") as f:
            json.dump([], f)


def add_bug_to_fallback(bug_data: dict[str, Any]) -> None:
    """Add a bug to the fallback file."""
    ensure_fallback_file()

    try:
        with open(FALLBACK_FILE) as f:
            bugs = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        bugs = []

    bugs.append({"data": bug_data, "timestamp": time.time(), "status": "pending"})

    with open(FALLBACK_FILE, "w") as f:
        json.dump(bugs, f, indent=2)

    logger.info(f"Bug added to fallback file: {FALLBACK_FILE}")


def send_to_bug_server(
    data: dict[str, Any],
    host: str = "localhost",
    port: int = BUG_MCP_PORT,
    timeout: int = 5,
    retries: int = 3,
) -> dict[str, Any] | None:
    """Send data to the bug tracking server with retries.

    Args:
        data: Data to send
        host: Server host
        port: Server port
        timeout: Connection timeout in seconds
        retries: Number of retry attempts

    Returns:
        Server response or None if failed

    """
    for attempt in range(retries):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            s.connect((host, port))

            # Send data
            s.sendall(json.dumps(data).encode())

            # Receive response
            chunks = []
            while True:
                chunk = s.recv(1024)
                if not chunk:
                    break
                chunks.append(chunk)

            s.close()

            # Parse response
            response_data = b"".join(chunks).decode()
            try:
                return json.loads(response_data)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON response: {response_data}")
                return {"status": "error", "message": "Invalid JSON response"}

        except TimeoutError:
            logger.warning(f"Connection timeout (attempt {attempt + 1}/{retries})")
        except ConnectionRefusedError:
            logger.warning(f"Connection refused (attempt {attempt + 1}/{retries})")
        except Exception as e:
            logger.warning(
                f"Error connecting to bug server: {e} (attempt {attempt + 1}/{retries})"
            )

        # Wait before retrying
        if attempt < retries - 1:
            time.sleep(1)

    return None


def add_bug(description: str, cause: str, critical: bool = False) -> dict[str, Any]:
    """Add a bug to the tracking system.

    Args:
        description: Bug description
        cause: Bug cause
        critical: Whether the bug is critical

    Returns:
        Result of the operation

    """
    bug_data = {
        "action": "add",
        "description": description,
        "cause": cause,
        "critical": critical,
        "timestamp": time.time(),
    }

    # Try to send to server
    response = send_to_bug_server(bug_data)

    if response:
        logger.info(f"Bug reported successfully: {response}")
        return response

    # Fallback to file
    logger.warning("Could not connect to bug server, using fallback file")
    add_bug_to_fallback(bug_data)
    return {"status": "fallback", "message": "Bug saved to fallback file"}


def list_bugs() -> dict[str, Any]:
    """List all bugs.

    Returns:
        List of bugs

    """
    data = {"action": "list"}

    response = send_to_bug_server(data)

    if response:
        return response

    # Fallback to file
    logger.warning("Could not connect to bug server, using fallback file")

    try:
        with open(FALLBACK_FILE) as f:
            bugs = json.load(f)
        return {"status": "fallback", "message": "Using fallback file", "bugs": bugs}
    except (json.JSONDecodeError, FileNotFoundError):
        return {"status": "error", "message": "No bugs found in fallback file"}


def sync_pending_bugs() -> None:
    """Sync pending bugs from fallback file to server."""
    try:
        with open(FALLBACK_FILE) as f:
            bugs = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        logger.info("No pending bugs to sync")
        return

    if not bugs:
        logger.info("No pending bugs to sync")
        return

    logger.info(f"Syncing {len(bugs)} pending bugs")

    synced_bugs = []

    for bug in bugs:
        if bug["status"] == "pending":
            response = send_to_bug_server(bug["data"])
            if response:
                bug["status"] = "synced"
                bug["sync_timestamp"] = time.time()
                synced_bugs.append(bug)

    # Update fallback file
    with open(FALLBACK_FILE, "w") as f:
        json.dump(bugs, f, indent=2)

    logger.info(f"Synced {len(synced_bugs)} bugs")


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Bug tracking client for GraphRAG")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Add bug command
    add_parser = subparsers.add_parser("add", help="Add a bug")
    add_parser.add_argument("description", help="Bug description")
    add_parser.add_argument("cause", help="Bug cause")
    add_parser.add_argument("--critical", action="store_true", help="Mark as critical")

    # List bugs command
    subparsers.add_parser("list", help="List all bugs")

    # Sync command
    subparsers.add_parser("sync", help="Sync pending bugs")

    args = parser.parse_args()

    if args.command == "add":
        result = add_bug(args.description, args.cause, args.critical)
        print(json.dumps(result, indent=2))
    elif args.command == "list":
        result = list_bugs()
        print(json.dumps(result, indent=2))
    elif args.command == "sync":
        sync_pending_bugs()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
