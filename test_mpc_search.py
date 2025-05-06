"""
Test script for MPC server search functionality.
"""
import asyncio
import websockets
import json
import sys

async def test_search(uri, query="What is RAG?", n_results=3, max_hops=2):
    """Test search functionality."""
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")
            
            # Prepare search message
            message = {
                'action': 'search',
                'query': query,
                'n_results': n_results,
                'max_hops': max_hops
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

async def main():
    uri = "ws://localhost:8766"
    
    # You can change the search query here
    query = "What is RAG?"
    
    success = await test_search(uri, query)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
