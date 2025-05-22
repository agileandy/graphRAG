"""Test script to search for GraphRAG content we just added."""

import asyncio
import json
import os
import sys

import websockets

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import port configuration
from src.config.ports import get_port


async def test_search(uri, query="GraphRAG", n_results=3, max_hops=2) -> bool | None:
    """Test search functionality for GraphRAG content."""
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")

            # Prepare search message
            message = {
                "action": "search",
                "query": query,
                "n_results": n_results,
                "max_hops": max_hops,
            }

            print(f"Sending search query: '{query}'...")
            await websocket.send(json.dumps(message))

            print("Waiting for response...")
            response = await websocket.recv()

            print("\nSearch results:")
            response_data = json.loads(response)
            print(json.dumps(response_data, indent=2))

            return True
    except Exception as e:
        print(f"Search failed: {e}")
        return False


async def main() -> None:
    mpc_port = get_port("mpc")
    host = os.getenv(
        "MPC_HOST", "localhost"
    )  # Use MPC_HOST or default to localhost for client connection
    uri = f"ws://{host}:{mpc_port}"

    # Search for GraphRAG content
    query = "GraphRAG hybrid approach"

    success = await test_search(uri, query)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
