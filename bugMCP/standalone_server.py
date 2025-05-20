#!/usr/bin/env python3
"""Standalone Bug Tracking MCP Server.

This script runs a standalone MCP server for bug tracking using FastAPI and Uvicorn.
"""

import argparse
import logging
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the MCP server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bugMCP_mcp import load_bugs, mcp, save_bugs

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("standalone_server")


def main() -> None:
    """Main function to start the standalone server."""
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

    # Load bugs from file
    load_bugs()

    # Start the server
    logger.info(f"Starting Bug Tracking MCP server on {args.host}:{args.port}")

    # Create a FastAPI app with the MCP server
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI()
    app.mount("/", mcp.streamable_http_app())

    # Run the server
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
