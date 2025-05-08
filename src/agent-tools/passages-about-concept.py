#!/usr/bin/env python3
"""
GraphRAG Agent Tool: passages-about-concept

This tool retrieves passages of text that mention a specific concept.

Usage:
    python passages-about-concept.py --name CONCEPT_NAME [--limit LIMIT] [--url URL]

Arguments:
    --name CONCEPT_NAME   Name of the concept
    --limit LIMIT         Maximum number of passages to return (default: 5)
    --url URL             MPC server URL (overrides environment variables)

Environment Variables:
    MPC_HOST     MPC server host (default: localhost)
    MPC_PORT     MPC server port (default: 8766)
"""

import sys
import argparse
from utils import connect_to_mpc, send_request, get_mpc_url, format_json
from typing import Dict, Any

def display_passages(result: Dict[str, Any]) -> None:
    """Display passages in a readable format."""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    if result.get("status") != "success":
        print(f"❌ Error: {result.get('message', 'Unknown error')}")
        return
    
    concept_name = result.get("concept_name", "Unknown concept")
    passages = result.get("passages", [])
    
    print(f"\n=== Passages about '{concept_name}' ({len(passages)} passages) ===")
    
    for i, passage in enumerate(passages):
        print(f"\n[{i+1}] From: {passage.get('source', 'Unknown source')}")
        
        # Display passage text
        text = passage.get("text", "No text available")
        print("\nText:")
        print(text)
        
        # Display metadata if available
        if "metadata" in passage:
            print("\nMetadata:")
            for key, value in passage["metadata"].items():
                if key != "source":  # Skip source as it's already displayed
                    print(f"  {key}: {value}")
        
        # Display relevance score if available
        if "score" in passage:
            print(f"\nRelevance: {passage['score']:.2f}")
        
        print("\n" + "-" * 80)  # Separator between passages

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Retrieve passages about a specific concept")
    parser.add_argument("--name", required=True, help="Name of the concept")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of passages to return")
    parser.add_argument("--url", default=None, help="MPC server URL (overrides environment variables)")
    parser.add_argument("--raw", action="store_true", help="Display raw JSON response")
    args = parser.parse_args()
    
    # Get the MPC URL
    url = args.url or get_mpc_url()
    
    # Connect to the MPC server
    conn = connect_to_mpc(url)
    
    try:
        # Get passages about concept
        print(f"Finding passages about concept: '{args.name}' (limit: {args.limit})...")
        
        response = send_request(conn, "passages-about-concept", 
                               concept_name=args.name, 
                               limit=args.limit)
        
        # Display results
        if args.raw:
            print("\nRaw response:")
            print(format_json(response))
        else:
            display_passages(response)
        
        return 0
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    sys.exit(main())