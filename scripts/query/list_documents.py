#!/usr/bin/env python3
"""Script to list all documents in the GraphRAG system using the MPC server."""

import json
import sys

import websockets.sync.client as ws

# Default MPC server URL (matching the Docker port mapping)
DEFAULT_MPC_URL = "ws://localhost:8766"


def list_documents(limit=100, url=DEFAULT_MPC_URL) -> bool | None:
    """List all documents in the GraphRAG system."""
    print(f"Connecting to MPC server at {url}...")

    try:
        # Connect to the server
        conn = ws.connect(url)
        print("✅ Connected to MPC server")

        # Create documents message
        message = {"action": "documents", "limit": limit}

        # Send the message
        print(f"Requesting document list (limit: {limit})...")
        conn.send(json.dumps(message))

        # Receive response
        response = conn.recv()
        result = json.loads(response)

        # Pretty print the result
        print("\nDocuments in GraphRAG:")
        print(json.dumps(result, indent=2))

        # Close the connection
        conn.close()
        print("\nConnection closed.")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    # Get limit from command line or use default
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    success = list_documents(limit)
    sys.exit(0 if success else 1)
