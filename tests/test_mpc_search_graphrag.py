"""Test script to search for GraphRAG content we just added."""

import asyncio
import json
import sys

import websockets


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
    uri = "ws://localhost:8766"

    # Search for GraphRAG content
    query = "GraphRAG hybrid approach"

    success = await test_search(uri, query)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
