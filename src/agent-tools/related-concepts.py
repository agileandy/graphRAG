#!/usr/bin/env python3
"""
GraphRAG Agent Tool: related-concepts

This tool lists concepts related to a given concept.

Usage:
    python related-concepts.py --name CONCEPT_NAME [--limit LIMIT] [--url URL]

Arguments:
    --name CONCEPT_NAME   Name of the concept
    --limit LIMIT         Maximum number of related concepts to return (default: 10)
    --url URL             MPC server URL (overrides environment variables)

Environment Variables:
    MPC_HOST     MPC server host (default: localhost)
    MPC_PORT     MPC server port (default: 8766)
"""

import sys
import argparse
from utils import connect_to_mpc, send_request, get_mpc_url, format_json
from typing import Dict, Any

def display_related_concepts(result: Dict[str, Any]) -> None:
    """Display related concepts in a readable format."""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    if result.get("status") != "success":
        print(f"❌ Error: {result.get('message', 'Unknown error')}")
        return
    
    concept_name = result.get("concept_name", "Unknown concept")
    related_concepts = result.get("related_concepts", [])
    total_count = result.get("total_count", len(related_concepts))
    
    print(f"\n=== Concepts related to '{concept_name}' ({len(related_concepts)} of {total_count} total) ===")
    
    for i, concept in enumerate(related_concepts):
        print(f"\n[{i+1}] {concept.get('name', 'Unnamed')}")
        
        # Display concept ID
        concept_id = concept.get("id", "Unknown")
        print(f"  ID: {concept_id}")
        
        # Display relationship type if available
        if "relationship" in concept:
            print(f"  Relationship: {concept['relationship']}")
        
        # Display relationship strength if available
        if "strength" in concept:
            print(f"  Strength: {concept['strength']:.2f}")
        
        # Display co-occurrence count if available
        if "co_occurrences" in concept:
            print(f"  Co-occurrences: {concept['co_occurrences']}")
        
        # Display properties if available
        if "properties" in concept:
            print("  Properties:")
            for key, value in concept["properties"].items():
                if key != "name":  # Skip name as it's already displayed
                    print(f"    {key}: {value}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="List concepts related to a given concept")
    parser.add_argument("--name", required=True, help="Name of the concept")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of related concepts to return")
    parser.add_argument("--url", default=None, help="MPC server URL (overrides environment variables)")
    parser.add_argument("--raw", action="store_true", help="Display raw JSON response")
    args = parser.parse_args()
    
    # Get the MPC URL
    url = args.url or get_mpc_url()
    
    # Connect to the MPC server
    conn = connect_to_mpc(url)
    
    try:
        # Get related concepts
        print(f"Finding concepts related to: '{args.name}' (limit: {args.limit})...")
        
        response = send_request(conn, "related-concepts", 
                               concept_name=args.name, 
                               limit=args.limit)
        
        # Display results
        if args.raw:
            print("\nRaw response:")
            print(format_json(response))
        else:
            display_related_concepts(response)
        
        return 0
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    sys.exit(main())