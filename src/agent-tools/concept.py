#!/usr/bin/env python3
"""
GraphRAG Agent Tool: concept

This tool retrieves information about a specific concept in the knowledge graph.

Usage:
    python concept.py --name CONCEPT_NAME [--url URL]

Arguments:
    --name CONCEPT_NAME   Name of the concept to retrieve
    --url URL             MPC server URL (overrides environment variables)

Environment Variables:
    MPC_HOST     MPC server host (default: localhost)
    MPC_PORT     MPC server port (default: 8766)
"""

import sys
import argparse
from utils import connect_to_mpc, send_request, get_mpc_url, format_json
from typing import Dict, Any

def display_concept_info(result: Dict[str, Any]) -> None:
    """Display concept information in a readable format."""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    if result.get("status") != "success":
        print(f"❌ Error: {result.get('message', 'Unknown error')}")
        return
    
    concept = result.get("concept", {})
    
    print("\n=== Concept Information ===")
    print(f"Name: {concept.get('name', 'Unknown')}")
    
    # Display properties
    if "properties" in concept:
        print("\nProperties:")
        for key, value in concept["properties"].items():
            if key != "name":  # Skip name as it's already displayed
                print(f"  {key}: {value}")
    
    # Display related concepts count
    related_count = result.get("related_count", 0)
    print(f"\nRelated concepts: {related_count}")
    
    # Display document count
    document_count = result.get("document_count", 0)
    print(f"Referenced in {document_count} documents")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Get information about a concept in the GraphRAG system")
    parser.add_argument("--name", required=True, help="Name of the concept")
    parser.add_argument("--url", default=None, help="MPC server URL (overrides environment variables)")
    parser.add_argument("--raw", action="store_true", help="Display raw JSON response")
    args = parser.parse_args()
    
    # Get the MPC URL
    url = args.url or get_mpc_url()
    
    # Connect to the MPC server
    conn = connect_to_mpc(url)
    
    try:
        # Get concept information
        print(f"Getting information for concept: '{args.name}'")
        
        response = send_request(conn, "concept", concept_name=args.name)
        
        # Display results
        if args.raw:
            print("\nRaw response:")
            print(format_json(response))
        else:
            display_concept_info(response)
        
        return 0
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    sys.exit(main())