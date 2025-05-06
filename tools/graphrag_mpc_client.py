#!/usr/bin/env python3
"""
GraphRAG MPC Client Tool

This script provides a command-line interface to interact with the GraphRAG MPC server.
It can be used to add documents, search for documents, and get information about concepts.
"""

import argparse
import json
import sys
import websockets.sync.client as ws
from typing import Dict, Any, List, Optional

# Default MPC server URL
DEFAULT_MPC_URL = "ws://localhost:8766"

def connect_to_mpc(url: str = DEFAULT_MPC_URL):
    """Connect to the MPC server."""
    try:
        return ws.connect(url)
    except Exception as e:
        print(f"Error connecting to MPC server at {url}: {e}", file=sys.stderr)
        sys.exit(1)

def send_request(conn, action: str, **kwargs) -> Dict[str, Any]:
    """Send a request to the MPC server and return the response."""
    # Create the message
    message = {"action": action, **kwargs}
    
    # Send the message
    try:
        conn.send(json.dumps(message))
        
        # Receive the response
        response = conn.recv()
        return json.loads(response)
    except Exception as e:
        print(f"Error communicating with MPC server: {e}", file=sys.stderr)
        sys.exit(1)

def add_document(conn, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Add a document to the GraphRAG system."""
    return send_request(conn, "add-document", text=text, metadata=metadata)

def add_folder(conn, folder_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Add all documents in a folder to the GraphRAG system."""
    return send_request(conn, "add-folder", folder_path=folder_path, metadata=metadata)

def search(conn, query: str, limit: int = 5) -> Dict[str, Any]:
    """Search for documents in the GraphRAG system."""
    return send_request(conn, "search", query=query, limit=limit)

def get_concept(conn, concept_name: str) -> Dict[str, Any]:
    """Get information about a concept."""
    return send_request(conn, "concept", concept_name=concept_name)

def get_related_concepts(conn, concept_name: str) -> Dict[str, Any]:
    """Get concepts related to a given concept."""
    return send_request(conn, "related-concepts", concept_name=concept_name)

def get_passages_about_concept(conn, concept_name: str) -> Dict[str, Any]:
    """Get passages that mention a given concept."""
    return send_request(conn, "passages-about-concept", concept_name=concept_name)

def get_books_by_concept(conn, concept_name: str) -> Dict[str, Any]:
    """Get books that mention a given concept."""
    return send_request(conn, "books-by-concept", concept_name=concept_name)

def get_documents(conn, limit: int = 10) -> Dict[str, Any]:
    """Get a list of documents in the GraphRAG system."""
    return send_request(conn, "documents", limit=limit)

def parse_metadata(metadata_str: str) -> Dict[str, Any]:
    """Parse metadata from a string in the format 'key1=value1,key2=value2'."""
    if not metadata_str:
        return {}
    
    metadata = {}
    pairs = metadata_str.split(",")
    for pair in pairs:
        if "=" in pair:
            key, value = pair.split("=", 1)
            metadata[key.strip()] = value.strip()
    
    return metadata

def main():
    parser = argparse.ArgumentParser(description="GraphRAG MPC Client Tool")
    parser.add_argument("--url", default=DEFAULT_MPC_URL, help="MPC server URL")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Add document command
    add_doc_parser = subparsers.add_parser("add-document", help="Add a document to the GraphRAG system")
    add_doc_parser.add_argument("--text", required=True, help="Document text")
    add_doc_parser.add_argument("--metadata", default="", help="Document metadata in the format 'key1=value1,key2=value2'")
    add_doc_parser.add_argument("--file", help="Read document text from a file")
    
    # Add folder command
    add_folder_parser = subparsers.add_parser("add-folder", help="Add all documents in a folder to the GraphRAG system")
    add_folder_parser.add_argument("--path", required=True, help="Folder path")
    add_folder_parser.add_argument("--metadata", default="", help="Document metadata in the format 'key1=value1,key2=value2'")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for documents in the GraphRAG system")
    search_parser.add_argument("--query", required=True, help="Search query")
    search_parser.add_argument("--limit", type=int, default=5, help="Maximum number of results to return")
    
    # Get concept command
    concept_parser = subparsers.add_parser("concept", help="Get information about a concept")
    concept_parser.add_argument("--name", required=True, help="Concept name")
    
    # Get related concepts command
    related_parser = subparsers.add_parser("related-concepts", help="Get concepts related to a given concept")
    related_parser.add_argument("--name", required=True, help="Concept name")
    
    # Get passages about concept command
    passages_parser = subparsers.add_parser("passages-about-concept", help="Get passages that mention a given concept")
    passages_parser.add_argument("--name", required=True, help="Concept name")
    
    # Get books by concept command
    books_parser = subparsers.add_parser("books-by-concept", help="Get books that mention a given concept")
    books_parser.add_argument("--name", required=True, help="Concept name")
    
    # Get documents command
    docs_parser = subparsers.add_parser("documents", help="Get a list of documents in the GraphRAG system")
    docs_parser.add_argument("--limit", type=int, default=10, help="Maximum number of documents to return")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Connect to the MPC server
    conn = connect_to_mpc(args.url)
    
    try:
        # Execute the command
        if args.command == "add-document":
            text = args.text
            if args.file:
                with open(args.file, "r") as f:
                    text = f.read()
            
            metadata = parse_metadata(args.metadata)
            response = add_document(conn, text, metadata)
            
        elif args.command == "add-folder":
            metadata = parse_metadata(args.metadata)
            response = add_folder(conn, args.path, metadata)
            
        elif args.command == "search":
            response = search(conn, args.query, args.limit)
            
        elif args.command == "concept":
            response = get_concept(conn, args.name)
            
        elif args.command == "related-concepts":
            response = get_related_concepts(conn, args.name)
            
        elif args.command == "passages-about-concept":
            response = get_passages_about_concept(conn, args.name)
            
        elif args.command == "books-by-concept":
            response = get_books_by_concept(conn, args.name)
            
        elif args.command == "documents":
            response = get_documents(conn, args.limit)
        
        # Print the response
        print(json.dumps(response, indent=2))
        
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    main()
