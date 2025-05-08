#!/usr/bin/env python3
"""
Script to add prompting ebooks to the GraphRAG system.
"""

import os
import sys
import json
import argparse
import websockets.sync.client as ws
from typing import Dict, Any

# Default MPC server URL (matching the Docker port mapping)
DEFAULT_MPC_URL = "ws://localhost:8766"

def connect_to_mpc(url=DEFAULT_MPC_URL):
    """Connect to the MPC server."""
    print(f"Connecting to MPC server at {url}...")
    try:
        return ws.connect(url)
    except Exception as e:
        print(f"❌ Error connecting to MPC server: {e}")
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
        print(f"❌ Error communicating with MPC server: {e}")
        sys.exit(1)

def add_folder(conn, folder_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Add all documents in a folder to the GraphRAG system."""
    print(f"Adding folder: {folder_path}")
    return send_request(conn, "add-folder", folder_path=folder_path, metadata=metadata)

def add_document(conn, file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Add a single document to the GraphRAG system."""
    print(f"Adding document: {file_path}")

    # For PDF files, we'll need to extract the text
    # This is a simplified version - in a real scenario, you'd use a PDF parser
    # Here we're just sending the file path and letting the server handle it
    return send_request(conn, "add-document", file_path=file_path, metadata=metadata)

def search(conn, query: str, limit: int = 5) -> Dict[str, Any]:
    """Search for documents in the GraphRAG system."""
    print(f"Searching for: {query}")
    return send_request(conn, "search", query=query, limit=limit)

def get_concept(conn, concept_name: str) -> Dict[str, Any]:
    """Get information about a concept."""
    print(f"Getting information about concept: {concept_name}")
    return send_request(conn, "concept", concept_name=concept_name)

def get_related_concepts(conn, concept_name: str) -> Dict[str, Any]:
    """Get concepts related to a given concept."""
    print(f"Getting concepts related to: {concept_name}")
    return send_request(conn, "related-concepts", concept_name=concept_name)

def main():
    parser = argparse.ArgumentParser(description="Add prompting ebooks to the GraphRAG system")
    parser.add_argument("--url", default=DEFAULT_MPC_URL, help="MPC server URL")
    parser.add_argument("--folder", default="/Users/andyspamer/ebooks/prompting", help="Folder containing ebooks")
    parser.add_argument("--method", choices=["folder", "individual"], default="individual",
                        help="Method to add documents: 'folder' to add entire folder at once, 'individual' to add each document separately")
    parser.add_argument("--verify", action="store_true", help="Verify documents were added by performing a search")
    parser.add_argument("--search-only", action="store_true", help="Only perform search without adding documents")
    parser.add_argument("--query", type=str, default="prompt engineering", help="Search query to use")
    parser.add_argument("--concept", type=str, help="Get information about a specific concept")
    parser.add_argument("--related", type=str, help="Get concepts related to a specific concept")
    args = parser.parse_args()

    # Connect to the MPC server
    conn = connect_to_mpc(args.url)

    try:
        # Handle concept information request
        if args.concept:
            print(f"\nGetting information about concept: '{args.concept}'")
            concept_info = get_concept(conn, args.concept)
            print("\nConcept Information:")
            print(json.dumps(concept_info, indent=2))
            return

        # Handle related concepts request
        if args.related:
            print(f"\nGetting concepts related to: '{args.related}'")
            related_concepts = get_related_concepts(conn, args.related)
            print("\nRelated Concepts:")
            print(json.dumps(related_concepts, indent=2))
            return

        if args.search_only:
            # Just perform a search to verify documents are in the system
            search_query = args.query
            print(f"\nPerforming search for: '{search_query}'")
            search_results = search(conn, search_query, limit=10)
            print("\nSearch Results:")
            print(json.dumps(search_results, indent=2))
            return

        if args.method == "folder":
            # Add the entire folder at once
            metadata = {
                "category": "AI",
                "subcategory": "Prompt Engineering",
                "source": "ebooks"
            }
            response = add_folder(conn, args.folder, metadata)
            print("\nServer response:")
            print(json.dumps(response, indent=2))

        else:  # individual method
            # Get list of PDF files in the folder
            files = [f for f in os.listdir(args.folder) if f.endswith('.pdf')]

            if not files:
                print(f"No PDF files found in {args.folder}")
                return

            print(f"Found {len(files)} PDF files to add")

            # Add each file individually
            for i, filename in enumerate(files, 1):
                file_path = os.path.join(args.folder, filename)

                # Extract title from filename (remove extension and clean up)
                title = os.path.splitext(filename)[0]

                # Try to extract author information if in parentheses
                author = "Unknown"
                if "(" in title and ")" in title:
                    parts = title.split("(")
                    for part in parts[1:]:
                        if ")" in part:
                            potential_author = part.split(")")[0].strip()
                            if potential_author and "Z-Library" not in potential_author:
                                author = potential_author
                                break

                # Clean up title
                title = title.split("(")[0].strip()

                # Create metadata
                metadata = {
                    "title": title,
                    "author": author,
                    "category": "AI",
                    "subcategory": "Prompt Engineering",
                    "source": "ebooks",
                    "format": "PDF"
                }

                print(f"\n[{i}/{len(files)}] Adding: {title} by {author}")

                # Add the document
                response = add_document(conn, file_path, metadata)

                # Print response summary
                status = response.get("status", "unknown")
                message = response.get("message", "No message provided")
                print(f"Status: {status}")
                print(f"Message: {message}")

                # If there are errors, print them
                if "errors" in response:
                    print("Errors:")
                    for error in response["errors"]:
                        print(f"  - {error}")

            print("\nAll documents processed.")

        # Verify documents were added by performing a search
        if args.verify:
            search_query = "prompt engineering"
            print(f"\nVerifying documents were added by searching for: '{search_query}'")
            search_results = search(conn, search_query, limit=10)
            print("\nSearch Results:")
            print(json.dumps(search_results, indent=2))

    finally:
        # Close the connection
        conn.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
