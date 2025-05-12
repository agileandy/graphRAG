#!/usr/bin/env python3
"""
Script to add PDF documents to the GraphRAG system.

This script extracts text from PDF files on the local machine and sends it to the
GraphRAG MPC server running in a Docker container.
"""

import os
import sys
import json
import argparse
import websockets.sync.client as ws
from typing import Dict, Any
import time

try:
    import PyPDF2
except ImportError:
    print("❌ PyPDF2 is not installed. Please install it with 'pip install PyPDF2'.")
    print("You can create a virtual environment with:")
    print("  python3 -m venv .venv")
    print("  source .venv/bin/activate")
    print("  pip install PyPDF2 websockets")
    sys.exit(1)

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

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    print(f"Extracting text from PDF: {file_path}")

    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""

            # Extract text from each page
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n\n"

            return text
    except Exception as e:
        print(f"❌ Error extracting text from PDF: {e}")
        return ""

def add_document(conn, text: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Add a document to the GraphRAG system."""
    print(f"Adding document: {metadata.get('title', 'Untitled')}")

    return send_request(conn, "add-document", text=text, metadata=metadata)

def process_pdf_file(conn, file_path: str) -> Dict[str, Any]:
    """Process a PDF file and add it to the GraphRAG system."""
    # Extract text from PDF
    text = extract_text_from_pdf(file_path)

    if not text:
        return {
            "status": "error",
            "message": f"Failed to extract text from {file_path}"
        }

    # Extract metadata from filename
    filename = os.path.basename(file_path)
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
        "format": "PDF",
        "file_path": file_path,
        "concepts": "Prompt Engineering, LLM, AI, Natural Language Processing"
    }

    # Add the document
    return add_document(conn, text, metadata)

def main():
    parser = argparse.ArgumentParser(description="Add PDF documents to the GraphRAG system")
    parser.add_argument("--url", default=DEFAULT_MPC_URL, help="MPC server URL")
    parser.add_argument("--folder", default="/Users/andyspamer/ebooks/prompting", help="Folder containing PDF files")
    parser.add_argument("--file", help="Single PDF file to process")
    args = parser.parse_args()

    # Connect to the MPC server
    conn = connect_to_mpc(args.url)

    try:
        if args.file:
            # Process a single file
            if not os.path.isfile(args.file):
                print(f"❌ File not found: {args.file}")
                sys.exit(1)

            if not args.file.lower().endswith('.pdf'):
                print(f"❌ Not a PDF file: {args.file}")
                sys.exit(1)

            print(f"Processing file: {args.file}")
            result = process_pdf_file(conn, args.file)

            # Print response summary
            status = result.get("status", "unknown")
            message = result.get("message", "No message provided")
            print(f"Status: {status}")
            print(f"Message: {message}")

            # If there are errors, print them
            if "error" in result:
                print(f"Error: {result['error']}")

        else:
            # Process all PDF files in the folder
            if not os.path.isdir(args.folder):
                print(f"❌ Folder not found: {args.folder}")
                sys.exit(1)

            # Get list of PDF files in the folder
            files = [f for f in os.listdir(args.folder) if f.lower().endswith('.pdf')]

            if not files:
                print(f"No PDF files found in {args.folder}")
                return

            print(f"Found {len(files)} PDF files to add")

            # Add each file individually
            for i, filename in enumerate(files, 1):
                file_path = os.path.join(args.folder, filename)

                print(f"\n[{i}/{len(files)}] Processing: {filename}")

                # Process the file
                result = process_pdf_file(conn, file_path)

                # Print response summary
                status = result.get("status", "unknown")
                message = result.get("message", "No message provided")
                print(f"Status: {status}")
                print(f"Message: {message}")

                # If there are errors, print them
                if "error" in result:
                    print(f"Error: {result['error']}")

                # Sleep briefly to avoid overwhelming the server
                if i < len(files):
                    time.sleep(1)

            print("\nAll documents processed.")

    finally:
        # Close the connection
        conn.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
