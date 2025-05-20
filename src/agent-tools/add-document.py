#!/usr/bin/env python3
"""GraphRAG Agent Tool: add-document.

This tool adds a document to the GraphRAG system.

Usage:
    python add-document.py --text TEXT [--file FILE] [--metadata KEY=VALUE...] [--async] [--url URL]

Arguments:
    --text TEXT           Document text (required if --file not provided)
    --file FILE           File containing document text (required if --text not provided)
    --metadata KEY=VALUE  Document metadata (can be specified multiple times)
    --async               Process document asynchronously
    --url URL             MPC server URL (overrides environment variables)

Environment Variables:
    MPC_HOST     MPC server host (default: localhost)
    MPC_PORT     MPC server port (default: 8766)

"""

import argparse
import os
import sys
from typing import Any

from utils import connect_to_mpc, format_json, get_mcp_url, send_request


def parse_metadata(metadata_args):
    """Parse metadata arguments into a dictionary."""
    metadata = {}

    for item in metadata_args:
        if "=" in item:
            key, value = item.split("=", 1)
            metadata[key.strip()] = value.strip()

    return metadata


def display_result(result: dict[str, Any], async_mode: bool) -> None:
    """Display the result of adding a document."""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return

    if async_mode:
        # Asynchronous mode
        if result.get("status") == "accepted":
            print("✅ Document accepted for processing")
            print(f"Job ID: {result.get('job_id', 'Unknown')}")
            print("\nYou can check the job status with:")
            print(f"python job-status.py --job-id {result.get('job_id', 'Unknown')}")
        else:
            print(f"❌ Error: {result.get('message', 'Unknown error')}")
    else:
        # Synchronous mode
        if result.get("status") == "success":
            print("✅ Document added successfully")
            print(f"Document ID: {result.get('document_id', 'Unknown')}")

            # Display entities
            entities = result.get("entities", [])
            print(f"\nExtracted {len(entities)} entities:")
            for entity in entities[:10]:  # Show first 10 entities
                print(f"  - {entity.get('name', 'Unnamed')}")

            if len(entities) > 10:
                print(f"  ... and {len(entities) - 10} more")

            # Display relationships
            relationships = result.get("relationships", [])
            print(f"\nCreated {len(relationships)} relationships")
        else:
            print(f"❌ Error: {result.get('message', 'Unknown error')}")


def main() -> int | None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Add a document to the GraphRAG system"
    )
    parser.add_argument("--text", help="Document text")
    parser.add_argument("--file", help="File containing document text")
    parser.add_argument(
        "--metadata", action="append", default=[], help="Document metadata (KEY=VALUE)"
    )
    parser.add_argument(
        "--async",
        dest="async_mode",
        action="store_true",
        help="Process document asynchronously",
    )
    parser.add_argument(
        "--url", default=None, help="MPC server URL (overrides environment variables)"
    )
    parser.add_argument("--raw", action="store_true", help="Display raw JSON response")
    args = parser.parse_args()

    # Check that either text or file is provided
    if not args.text and not args.file:
        parser.error("Either --text or --file must be provided")

    # Get document text
    text = args.text
    if args.file:
        try:
            with open(args.file, encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print(f"❌ Error reading file: {e}", file=sys.stderr)
            return 1

    # Parse metadata
    metadata = parse_metadata(args.metadata)

    # Add file metadata if using a file
    if args.file and "title" not in metadata:
        metadata["title"] = os.path.basename(args.file)

    # Get the MPC URL
    url = args.url or get_mcp_url()

    # Connect to the MPC server
    conn = connect_to_mpc(url)

    try:
        # Add document
        print("Adding document to GraphRAG system...")
        print(f"Text length: {len(text)} characters")
        print(f"Metadata: {metadata}")
        print(f"Async mode: {args.async_mode}")

        response = send_request(
            conn,
            "add-document",
            text=text,
            metadata=metadata,
            async_processing=args.async_mode,
        )

        # Display results
        if args.raw:
            print("\nRaw response:")
            print(format_json(response))
        else:
            display_result(response, args.async_mode)

        return 0
    finally:
        # Close the connection
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
