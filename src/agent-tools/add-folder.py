#!/usr/bin/env python3
"""GraphRAG Agent Tool: add-folder.

This tool adds a folder of documents to the GraphRAG system.

Usage:
    python add-folder.py --path FOLDER_PATH [--recursive] [--file-types EXT1,EXT2,...] [--metadata KEY=VALUE...] [--sync] [--url URL]

Arguments:
    --path FOLDER_PATH    Path to the folder containing documents
    --recursive           Process subfolders recursively
    --file-types EXT      Comma-separated list of file extensions to process (default: .txt,.json,.pdf,.md)
    --metadata KEY=VALUE  Document metadata (can be specified multiple times)
    --sync                Process documents synchronously (default is async)
    --url URL             MCP server URL (overrides environment variables)

Environment Variables:
    MCP_HOST     MCP server host (default: localhost)
    MCP_PORT     MCP server port (default: 8767)

"""

import argparse
import os
import sys
from typing import Any

from utils import connect_to_mcp, format_json, get_mcp_url, send_request


def parse_metadata(metadata_args):
    """Parse metadata arguments into a dictionary."""
    metadata = {}

    for item in metadata_args:
        if "=" in item:
            key, value = item.split("=", 1)
            metadata[key.strip()] = value.strip()

    return metadata


def parse_file_types(file_types_arg):
    """Parse file types argument into a list."""
    if not file_types_arg:
        return [".txt", ".json", ".pdf", ".md"]

    return [
        ext.strip() if ext.strip().startswith(".") else f".{ext.strip()}"
        for ext in file_types_arg.split(",")
    ]


def display_result(result: dict[str, Any], async_mode: bool) -> None:
    """Display the result of adding a folder."""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return

    if async_mode:
        # Asynchronous mode
        if result.get("status") == "accepted":
            print("✅ Folder accepted for processing")
            print(f"Job ID: {result.get('job_id', 'Unknown')}")
            print(f"Total files to process: {result.get('total_files', 'Unknown')}")
            print("\nYou can check the job status with:")
            print(f"python job-status.py --job-id {result.get('job_id', 'Unknown')}")
        else:
            print(f"❌ Error: {result.get('message', 'Unknown error')}")
    else:
        # Synchronous mode
        if result.get("status") == "success":
            print("✅ Folder processed successfully")

            # Display statistics
            processed = result.get("processed_files", 0)
            skipped = result.get("skipped_files", 0)
            duplicates = result.get("duplicate_files", 0)
            total = processed + skipped + duplicates

            print(f"\nProcessed {processed} files")
            print(f"Skipped {skipped} files")
            print(f"Detected {duplicates} duplicates")
            print(f"Total: {total} files")

            # Display entities
            entities = result.get("entities", [])
            print(f"\nExtracted {len(entities)} entities")

            # Display relationships
            relationships = result.get("relationships", [])
            print(f"Created {len(relationships)} relationships")
        else:
            print(f"❌ Error: {result.get('message', 'Unknown error')}")


def main() -> int | None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Add a folder of documents to the GraphRAG system"
    )
    parser.add_argument(
        "--path", required=True, help="Path to the folder containing documents"
    )
    parser.add_argument(
        "--recursive", action="store_true", help="Process subfolders recursively"
    )
    parser.add_argument(
        "--file-types",
        default=None,
        help="Comma-separated list of file extensions to process",
    )
    parser.add_argument(
        "--metadata", action="append", default=[], help="Document metadata (KEY=VALUE)"
    )
    parser.add_argument(
        "--sync",
        dest="sync_mode",
        action="store_true",
        help="Process documents synchronously",
    )
    parser.add_argument(
        "--url", default=None, help="MCP server URL (overrides environment variables)"
    )
    parser.add_argument("--raw", action="store_true", help="Display raw JSON response")
    args = parser.parse_args()

    # Check that the folder exists
    if not os.path.isdir(args.path):
        print(f"❌ Error: Folder not found: {args.path}", file=sys.stderr)
        return 1

    # Parse metadata
    metadata = parse_metadata(args.metadata)

    # Parse file types
    file_types = parse_file_types(args.file_types)

    # Get the MCP URL
    url = args.url or get_mcp_url()

    # Connect to the MCP server
    conn = connect_to_mcp(url)

    try:
        # Add folder
        print(f"Adding folder to GraphRAG system: {args.path}")
        print(f"Recursive: {args.recursive}")
        print(f"File types: {', '.join(file_types)}")
        print(f"Metadata: {metadata}")
        print(f"Sync mode: {args.sync_mode}")

        response = send_request(
            conn,
            "add-folder",
            folder_path=os.path.abspath(args.path),
            recursive=args.recursive,
            file_types=file_types,
            metadata=metadata,
            async_processing=not args.sync_mode,
        )  # Default is async

        # Display results
        if args.raw:
            print("\nRaw response:")
            print(format_json(response))
        else:
            display_result(response, not args.sync_mode)

        return 0
    finally:
        # Close the connection
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
