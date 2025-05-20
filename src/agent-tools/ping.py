#!/usr/bin/env python3
"""GraphRAG Agent Tool: ping.

This tool tests if the GraphRAG MCP server is alive and responding.

Usage:
    python ping.py [--url URL]

Arguments:
    --url URL    MCP server URL (default: from environment or ws://localhost:8767)

Environment Variables:
    MCP_HOST     MCP server host (default: localhost)
    MCP_PORT     MCP server port (default: 8767)

"""

import argparse
import sys

from utils import connect_to_mcp, get_mcp_url, send_request


def main() -> int | None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test if the GraphRAG MCP server is alive"
    )
    parser.add_argument(
        "--url", default=None, help="MCP server URL (overrides environment variables)"
    )
    args = parser.parse_args()

    # Get the MCP URL
    url = args.url or get_mcp_url()

    # Connect to the MCP server
    conn = connect_to_mcp(url)

    try:
        # Send ping request
        print(f"Pinging MCP server at {url}...")
        response = send_request(conn, "ping")

        # Check response
        if response.get("status") == "success":
            print("✅ MCP server is alive and responding!")
            print(f"Server message: {response.get('message', 'No message')}")
            return 0
        else:
            print(
                f"❌ MCP server returned an error: {response.get('error', 'Unknown error')}"
            )
            return 1
    finally:
        # Close the connection
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
