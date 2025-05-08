#!/usr/bin/env python3
"""
GraphRAG Agent Tool: ping

This tool tests if the GraphRAG MPC server is alive and responding.

Usage:
    python ping.py [--url URL]

Arguments:
    --url URL    MPC server URL (default: from environment or ws://localhost:8766)

Environment Variables:
    MPC_HOST     MPC server host (default: localhost)
    MPC_PORT     MPC server port (default: 8766)
"""

import sys
import argparse
from utils import connect_to_mpc, send_request, get_mpc_url

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test if the GraphRAG MPC server is alive")
    parser.add_argument("--url", default=None, help="MPC server URL (overrides environment variables)")
    args = parser.parse_args()
    
    # Get the MPC URL
    url = args.url or get_mpc_url()
    
    # Connect to the MPC server
    conn = connect_to_mpc(url)
    
    try:
        # Send ping request
        print(f"Pinging MPC server at {url}...")
        response = send_request(conn, "ping")
        
        # Check response
        if response.get("status") == "success":
            print("✅ MPC server is alive and responding!")
            print(f"Server message: {response.get('message', 'No message')}")
            return 0
        else:
            print(f"❌ MPC server returned an error: {response.get('error', 'Unknown error')}")
            return 1
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    sys.exit(main())