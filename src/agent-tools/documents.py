#!/usr/bin/env python3
"""
GraphRAG Agent Tool: documents

This tool lists documents in the GraphRAG system.

Usage:
    python documents.py [--limit LIMIT] [--url URL]

Arguments:
    --limit LIMIT    Maximum number of documents to return (default: 10)
    --url URL        MPC server URL (overrides environment variables)

Environment Variables:
    MPC_HOST     MPC server host (default: localhost)
    MPC_PORT     MPC server port (default: 8766)
"""

import sys
import argparse
from utils import connect_to_mpc, send_request, get_mcp_url, format_json
from typing import Dict, Any

def display_documents(result: Dict[str, Any]) -> None:
    """Display document list in a readable format."""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    if result.get("status") != "success":
        print(f"❌ Error: {result.get('message', 'Unknown error')}")
        return
    
    documents = result.get("documents", [])
    total_count = result.get("total_count", len(documents))
    
    print(f"\n=== Documents ({len(documents)} of {total_count} total) ===")
    
    for i, doc in enumerate(documents):
        print(f"\n[{i+1}] {doc.get('title', 'Untitled')}")
        
        # Display document ID
        doc_id = doc.get("id", "Unknown")
        print(f"  ID: {doc_id}")
        
        # Display metadata
        if "metadata" in doc:
            print("  Metadata:")
            for key, value in doc["metadata"].items():
                if key != "title":  # Skip title as it's already displayed
                    print(f"    {key}: {value}")
        
        # Display concepts count
        concepts = doc.get("concepts", [])
        print(f"  Concepts: {len(concepts)}")
        
        # Display chunk count
        chunk_count = doc.get("chunk_count", 0)
        print(f"  Chunks: {chunk_count}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="List documents in the GraphRAG system")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of documents to return")
    parser.add_argument("--url", default=None, help="MPC server URL (overrides environment variables)")
    parser.add_argument("--raw", action="store_true", help="Display raw JSON response")
    args = parser.parse_args()
    
    # Get the MPC URL
    url = args.url or get_mcp_url()
    
    # Connect to the MPC server
    conn = connect_to_mpc(url)
    
    try:
        # Get documents
        print(f"Getting document list (limit: {args.limit})...")
        
        response = send_request(conn, "documents", limit=args.limit)
        
        # Display results
        if args.raw:
            print("\nRaw response:")
            print(format_json(response))
        else:
            display_documents(response)
        
        return 0
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    sys.exit(main())