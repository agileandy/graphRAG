#!/usr/bin/env python3
"""GraphRAG Agent Tool: books-by-concept.

This tool lists books that cover a specific concept.

Usage:
    python books-by-concept.py --name CONCEPT_NAME [--limit LIMIT] [--url URL]

Arguments:
    --name CONCEPT_NAME   Name of the concept
    --limit LIMIT         Maximum number of books to return (default: 10)
    --url URL             MCP server URL (overrides environment variables)

Environment Variables:
    MCP_HOST     MCP server host (default: localhost)
    MCP_PORT     MCP server port (default: 8767)

"""

import argparse
import sys
from typing import Any

from utils import connect_to_mcp, format_json, get_mcp_url, send_request


def display_books(result: dict[str, Any]) -> None:
    """Display books in a readable format."""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return

    if result.get("status") != "success":
        print(f"❌ Error: {result.get('message', 'Unknown error')}")
        return

    concept_name = result.get("concept_name", "Unknown concept")
    books = result.get("books", [])
    total_count = result.get("total_count", len(books))

    print(
        f"\n=== Books covering '{concept_name}' ({len(books)} of {total_count} total) ==="
    )

    for i, book in enumerate(books):
        print(f"\n[{i + 1}] {book.get('title', 'Untitled')}")

        # Display book ID
        book_id = book.get("id", "Unknown")
        print(f"  ID: {book_id}")

        # Display metadata
        if "metadata" in book:
            print("  Metadata:")
            for key, value in book["metadata"].items():
                if key != "title":  # Skip title as it's already displayed
                    print(f"    {key}: {value}")

        # Display relevance score if available
        if "score" in book:
            print(f"  Relevance: {book['score']:.2f}")

        # Display mention count if available
        if "mention_count" in book:
            print(f"  Mentions: {book['mention_count']}")


def main() -> int | None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="List books covering a specific concept"
    )
    parser.add_argument("--name", required=True, help="Name of the concept")
    parser.add_argument(
        "--limit", type=int, default=10, help="Maximum number of books to return"
    )
    parser.add_argument(
        "--url", default=None, help="MCP server URL (overrides environment variables)"
    )
    parser.add_argument("--raw", action="store_true", help="Display raw JSON response")
    args = parser.parse_args()

    # Get the MCP URL
    url = args.url or get_mcp_url()

    # Connect to the MCP server
    conn = connect_to_mcp(url)

    try:
        # Get books by concept
        print(f"Finding books covering concept: '{args.name}' (limit: {args.limit})...")

        response = send_request(
            conn, "books-by-concept", concept_name=args.name, limit=args.limit
        )

        # Display results
        if args.raw:
            print("\nRaw response:")
            print(format_json(response))
        else:
            display_books(response)

        return 0
    finally:
        # Close the connection
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
