#!/usr/bin/env python3
"""
Simple test script to verify connection to the GraphRAG MPC server.
"""

import sys
import json
import websockets.sync.client as ws

# Default MPC server URL (matching the Docker port mapping)
DEFAULT_MPC_URL = "ws://localhost:8766"

def test_connection(url=DEFAULT_MPC_URL):
    """Test connection to the MPC server."""
    print(f"Attempting to connect to MPC server at {url}...")
    
    try:
        # Connect to the server
        conn = ws.connect(url)
        print("✅ Successfully connected to MPC server!")
        
        # Try a simple ping message
        print("Sending ping message...")
        conn.send(json.dumps({"action": "ping"}))
        
        # Receive response
        response = conn.recv()
        print(f"Received response: {response}")
        
        # Close the connection
        conn.close()
        print("Connection closed.")
        return True
    except Exception as e:
        print(f"❌ Error connecting to MPC server: {e}")
        return False

if __name__ == "__main__":
    # Use command-line argument for URL if provided
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MPC_URL
    success = test_connection(url)
    sys.exit(0 if success else 1)
