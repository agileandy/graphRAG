#!/usr/bin/env python3
"""
Test script to perform a search using the GraphRAG MPC server.
"""

import sys
import json
import websockets.sync.client as ws

# Default MPC server URL (matching the Docker port mapping)
DEFAULT_MPC_URL = "ws://localhost:8766"

def search_graphrag(query, limit=5, url=DEFAULT_MPC_URL):
    """Search the GraphRAG system."""
    print(f"Connecting to MPC server at {url}...")
    
    try:
        # Connect to the server
        conn = ws.connect(url)
        print("✅ Connected to MPC server")
        
        # Create search message
        message = {
            "action": "search",
            "query": query,
            "limit": limit
        }
        
        # Send the message
        print(f"Sending search query: '{query}'")
        conn.send(json.dumps(message))
        
        # Receive response
        response = conn.recv()
        result = json.loads(response)
        
        # Pretty print the result
        print("\nSearch Results:")
        print(json.dumps(result, indent=2))
        
        # Close the connection
        conn.close()
        print("\nConnection closed.")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    # Get query from command line or use default
    query = sys.argv[1] if len(sys.argv) > 1 else "GraphRAG"
    success = search_graphrag(query)
    sys.exit(0 if success else 1)
