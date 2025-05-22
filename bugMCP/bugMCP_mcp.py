#!/usr/bin/env python3
"""Bug Tracking MCP Server.

This module implements a Model Context Protocol (MCP) server for bug tracking.
It provides tools for adding, updating, deleting, and retrieving bugs.
"""

import json
import logging
import os
from typing import Any

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("bugMCP")

# File to store bugs
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bugs.json")

# Global storage
bugs = []
next_id = 1
VALID_STATUSES = {"open", "fixed"}


def save_bugs() -> None:
    """Save bugs to a JSON file."""
    try:
        with open(DATA_FILE, "w") as f:
            json.dump({"bugs": bugs, "next_id": next_id}, f, indent=2)
        logger.info(f"Bugs saved to {DATA_FILE}")
    except Exception as e:
        logger.error(f"Error saving bugs: {e}")


def load_bugs() -> None:
    """Load bugs from a JSON file."""
    global bugs, next_id
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE) as f:
                data = json.load(f)
                bugs = data.get("bugs", [])
                next_id = data.get("next_id", 1)
            logger.info(f"Loaded {len(bugs)} bugs from {DATA_FILE}")
        else:
            logger.info(
                f"No data file found at {DATA_FILE}, starting with empty bug list"
            )
    except Exception as e:
        logger.error(f"Error loading bugs: {e}")


# Create an MCP server
mcp = FastMCP(
    name="BugTracker", description="A bug tracking system for the GraphRAG project"
)


@mcp.tool(
    description="Add a new bug to the system"
)
def add_bug(description: str, cause: str) -> dict[str, Any]:
    """Add a new bug to the system.

    Args:
        description: A description of the bug
        cause: The perceived cause of the bug

    Returns:
        A dictionary with the status, message, and bug ID

    """
    global next_id

    new_bug = {
        "id": next_id,
        "description": description,
        "cause": cause,
        "status": "open",
        "resolution": "",
    }

    bugs.append(new_bug)
    next_id += 1
    save_bugs()

    return {
        "status": "success",
        "message": "Bug added successfully",
        "bug_id": new_bug["id"],
    }


@mcp.tool(
    description="Update an existing bug"
)
def update_bug(
    id: int, status: str | None = None, resolution: str | None = None
) -> dict[str, Any]:
    """Update an existing bug.

    Args:
        id: The ID of the bug to update
        status: The new status of the bug (optional)
        resolution: The resolution details for the bug (optional)

    Returns:
        A dictionary with the status, message, and updated fields

    """
    bug = next((b for b in bugs if b["id"] == id), None)
    if not bug:
        return {"status": "error", "message": f"Bug not found with ID: {id}"}

    updated_fields = []

    if status is not None:
        if status not in VALID_STATUSES:
            return {
                "status": "error",
                "message": f"Invalid status. Allowed values: {VALID_STATUSES}",
            }
        bug["status"] = status
        updated_fields.append("status")

    if resolution is not None:
        bug["resolution"] = resolution
        updated_fields.append("resolution")

    if updated_fields:
        save_bugs()
        return {
            "status": "success",
            "message": f"Updated bug {id}",
            "updated_fields": updated_fields,
        }
    else:
        return {"status": "success", "message": "No changes made"}


@mcp.tool(
    description="Delete a bug from the system"
)
def delete_bug(id: int) -> dict[str, Any]:
    """Delete a bug from the system.

    Args:
        id: The ID of the bug to delete

    Returns:
        A dictionary with the status and message

    """
    global bugs
    original_length = len(bugs)
    bugs = [b for b in bugs if b["id"] != id]

    if original_length > len(bugs):
        save_bugs()
        return {"status": "success", "message": f"Deleted bug {id}"}
    else:
        return {"status": "error", "message": f"No bug found with ID: {id}"}


@mcp.tool(
    description="Get a specific bug by ID"
)
def get_bug(id: int) -> dict[str, Any]:
    """Get a specific bug by ID.

    Args:
        id: The ID of the bug to retrieve

    Returns:
        A dictionary with the bug details or an error message

    """
    bug = next((b for b in bugs if b["id"] == id), None)

    if bug:
        return {"status": "success", "bug": bug}
    else:
        return {"status": "error", "message": f"Bug not found with ID: {id}"}


@mcp.tool(
    description="List all bugs in the system"
)
def list_bugs() -> dict[str, Any]:
    """List all bugs in the system.

    Returns:
        A dictionary with the list of bugs

    """
    return {"status": "success", "total_records": len(bugs), "bugs": bugs}


# Load bugs from file when starting
load_bugs()


def main() -> None:
    """Main function to start the MCP server."""
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Start the Bug Tracking MCP server")
    parser.add_argument("--port", type=int, default=5005, help="Server port")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    args = parser.parse_args()

    # Set logging level
    logger.setLevel(getattr(logging, args.log_level))

    # Register save_bugs to be called when the program exits
    import atexit

    atexit.register(save_bugs)

    # Start the server using the MCP run method
    logger.info(f"Starting Bug Tracking MCP server on {args.host}:{args.port}")
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
