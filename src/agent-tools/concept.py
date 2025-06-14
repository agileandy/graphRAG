#!/usr/bin/env python3
"""GraphRAG Agent Tool: concept.

This tool retrieves information about a specific concept in the knowledge graph.

Usage:
    python concept.py --name CONCEPT_NAME [--url URL]

Arguments:
    --name CONCEPT_NAME   Name of the concept to retrieve
    --url URL             MCP server URL (overrides environment variables)

Environment Variables:
    MCP_HOST     MCP server host (default: localhost)
    MCP_PORT     MCP server port (default: 8767)

"""

import argparse
import sys
from typing import Any

from utils import connect_to_mcp, format_json, get_mcp_url, send_request


def display_concept_info(result: dict[str, Any]) -> None:
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


def main() -> int | None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Get information about a concept in the GraphRAG system"
    )
    parser.add_argument("--name", required=True, help="Name of the concept")
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
