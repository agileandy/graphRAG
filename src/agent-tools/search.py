#!/usr/bin/env python3
"""
GraphRAG Agent Tool: search

This tool performs a hybrid search using both vector and graph databases.

Usage:
    python search.py --query QUERY [--n-results N] [--max-hops HOPS] [--url URL]

Arguments:
    --query QUERY       Search query
    --n-results N       Number of vector results to return (default: 5)
    --max-hops HOPS     Maximum number of hops in the graph (default: 2)
    --url URL           MPC server URL (overrides environment variables)

Environment Variables:
    MPC_HOST     MPC server host (default: localhost)
    MPC_PORT     MPC server port (default: 8766)
"""

import sys
import argparse
from utils import connect_to_mpc, send_request, get_mpc_url, format_json
from typing import Dict, Any

def display_search_results(results: Dict[str, Any]) -> None:
    """Display search results in a readable format."""
    if "error" in results:
        print(f"❌ Error: {results['error']}")
        return
    
    # Display vector results
    if "vector_results" in results:
        print("\n=== Vector Results ===")
        vector_results = results["vector_results"]
        
        if "documents" in vector_results:
            for i, doc in enumerate(vector_results["documents"]):
                print(f"\n[{i+1}] Document:")
                # Truncate long documents for display
                if len(doc) > 300:
                    print(f"{doc[:300]}...")
                else:
                    print(doc)
                
                # Display metadata if available
                if "metadatas" in vector_results and i < len(vector_results["metadatas"]):
                    metadata = vector_results["metadatas"][i]
                    print("\nMetadata:")
                    for key, value in metadata.items():
                        print(f"  {key}: {value}")
    
    # Display graph results
    if "graph_results" in results:
        print("\n=== Graph Results ===")
        graph_results = results["graph_results"]
        
        for i, (node, score) in enumerate(graph_results):
            print(f"\n[{i+1}] {node.get('name', 'Unnamed')} (Score: {score:.2f})")
            print(f"  Type: {node.get('type', 'Unknown')}")
            if "properties" in node:
                print("  Properties:")
                for key, value in node["properties"].items():
                    if key != "name":  # Skip name as it's already displayed
                        print(f"    {key}: {value}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Perform a hybrid search in the GraphRAG system")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--n-results", type=int, default=5, help="Number of vector results to return")
    parser.add_argument("--max-hops", type=int, default=2, help="Maximum number of hops in the graph")
    parser.add_argument("--url", default=None, help="MPC server URL (overrides environment variables)")
    parser.add_argument("--raw", action="store_true", help="Display raw JSON response")
    args = parser.parse_args()
    
    # Get the MPC URL
    url = args.url or get_mpc_url()
    
    # Connect to the MPC server
    conn = connect_to_mpc(url)
    
    try:
        # Perform search
        print(f"Searching for: '{args.query}'")
        print(f"Parameters: n_results={args.n_results}, max_hops={args.max_hops}")
        
        response = send_request(conn, "search", 
                               query=args.query, 
                               n_results=args.n_results, 
                               max_hops=args.max_hops)
        
        # Display results
        if args.raw:
            print("\nRaw response:")
            print(format_json(response))
        else:
            display_search_results(response)
        
        return 0
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    sys.exit(main())