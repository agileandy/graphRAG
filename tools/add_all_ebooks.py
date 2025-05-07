#!/usr/bin/env python3
"""
Script to add all ebooks to the GraphRAG system.

This script recursively processes all ebook directories and adds the PDFs to the
GraphRAG MPC server running in a Docker container.
"""

import os
import sys
import json
import argparse
import websockets.sync.client as ws
from typing import Dict, Any, List, Optional
import time
import glob

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

def send_request(conn, action: str, verbose=False, **kwargs) -> Dict[str, Any]:
    """Send a request to the MPC server and return the response."""
    # Create the message
    message = {"action": action, **kwargs}

    if verbose:
        print(f"\n=== REQUEST ===")
        print(f"Action: {action}")
        print(f"Parameters: {json.dumps(kwargs, indent=2)}")

    # Send the message
    try:
        conn.send(json.dumps(message))

        # Receive the response
        response = conn.recv()
        response_data = json.loads(response)
        
        if verbose:
            print(f"\n=== RESPONSE ===")
            print(json.dumps(response_data, indent=2))
            
        return response_data
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

def add_document(conn, text: str, metadata: Dict[str, Any], verbose=False) -> Dict[str, Any]:
    """Add a document to the GraphRAG system."""
    print(f"Adding document: {metadata.get('title', 'Untitled')}")

    return send_request(conn, "add-document", verbose=verbose, text=text, metadata=metadata)

def chunk_text(text: str, max_chunk_size: int = 500000) -> List[str]:
    """
    Split text into chunks of maximum size.
    
    Args:
        text: Text to split
        max_chunk_size: Maximum chunk size in characters
        
    Returns:
        List of text chunks
    """
    # If text is smaller than max_chunk_size, return it as is
    if len(text) <= max_chunk_size:
        return [text]
    
    # Split text into chunks
    chunks = []
    
    # Try to split at paragraph boundaries
    paragraphs = text.split("\n\n")
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed the max chunk size,
        # save the current chunk and start a new one
        if len(current_chunk) + len(paragraph) + 2 > max_chunk_size:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = paragraph
        else:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    # If any chunk is still too large, split it further
    final_chunks = []
    for chunk in chunks:
        if len(chunk) <= max_chunk_size:
            final_chunks.append(chunk)
        else:
            # Split at sentence boundaries
            sentences = chunk.replace(". ", ".\n").split("\n")
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 1 > max_chunk_size:
                    if current_chunk:
                        final_chunks.append(current_chunk)
                    current_chunk = sentence
                else:
                    if current_chunk:
                        current_chunk += " " + sentence
                    else:
                        current_chunk = sentence
            
            # Add the last chunk if it's not empty
            if current_chunk:
                final_chunks.append(current_chunk)
    
    return final_chunks

def process_pdf_file(conn, file_path: str, category: str = None, verbose=False) -> Dict[str, Any]:
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

    # Determine category from directory name if not provided
    if not category:
        # Get the directory name from the file path
        dir_name = os.path.basename(os.path.dirname(file_path))
        category = dir_name.capitalize()

    # Create metadata
    metadata = {
        "title": title,
        "author": author,
        "category": category,
        "source": "ebooks",
        "format": "PDF",
        "file_path": file_path
    }

    # Check if the text is too large for a single message (WebSocket limit is 1MB)
    # If so, split it into chunks and add each chunk separately
    MAX_MESSAGE_SIZE = 500000  # 500KB to be safe
    
    if len(text) > MAX_MESSAGE_SIZE:
        print(f"Text is too large ({len(text)} bytes), splitting into chunks...")
        chunks = chunk_text(text, MAX_MESSAGE_SIZE)
        print(f"Split into {len(chunks)} chunks")
        
        # Add each chunk as a separate document
        results = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = metadata.copy()
            chunk_metadata["title"] = f"{title} - Part {i+1}/{len(chunks)}"
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(chunks)
            
            print(f"Adding chunk {i+1}/{len(chunks)} ({len(chunk)} bytes)")
            result = add_document(conn, chunk, chunk_metadata, verbose=verbose)
            results.append(result)
        
        # Return success if at least one chunk was added successfully
        if any(result.get("status") == "success" for result in results):
            return {
                "status": "success",
                "message": f"Document added successfully in {len(chunks)} chunks",
                "chunks_added": len([r for r in results if r.get("status") == "success"]),
                "total_chunks": len(chunks)
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to add any chunks of the document"
            }
    else:
        # Add the document as a single chunk
        return add_document(conn, text, metadata, verbose=verbose)

def process_directory(conn, directory_path: str, recursive: bool = False, verbose=False) -> Dict[str, Any]:
    """Process all PDF files in a directory."""
    if not os.path.isdir(directory_path):
        return {
            "status": "error",
            "message": f"Directory not found: {directory_path}"
        }

    # Get the category from the directory name
    category = os.path.basename(directory_path).capitalize()
    print(f"\n=== Processing {category} ebooks from {directory_path} ===")

    # Find all PDF files
    if recursive:
        pdf_files = glob.glob(os.path.join(directory_path, "**", "*.pdf"), recursive=True)
    else:
        pdf_files = glob.glob(os.path.join(directory_path, "*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {directory_path}")
        return {
            "status": "warning",
            "message": f"No PDF files found in {directory_path}",
            "processed_files": 0
        }

    print(f"Found {len(pdf_files)} PDF files to process")

    # Process each file
    processed_files = 0
    failed_files = 0

    for i, file_path in enumerate(pdf_files, 1):
        filename = os.path.basename(file_path)
        print(f"\n[{i}/{len(pdf_files)}] Processing: {filename}")

        # Process the file
        result = process_pdf_file(conn, file_path, category, verbose=verbose)

        # Print response summary
        status = result.get("status", "unknown")
        message = result.get("message", "No message provided")
        print(f"Status: {status}")
        print(f"Message: {message}")

        # Count successes and failures
        if status == "success":
            processed_files += 1
        else:
            failed_files += 1

        # Sleep briefly to avoid overwhelming the server
        if i < len(pdf_files):
            time.sleep(1)

    return {
        "status": "success",
        "message": f"Processed {processed_files} files from {directory_path}",
        "processed_files": processed_files,
        "failed_files": failed_files,
        "total_files": len(pdf_files)
    }

def main():
    parser = argparse.ArgumentParser(description="Add all ebooks to the GraphRAG system")
    parser.add_argument("--url", default=DEFAULT_MPC_URL, help="MPC server URL")
    parser.add_argument("--root", default="/Users/andyspamer/ebooks", help="Root directory containing ebook folders")
    parser.add_argument("--recursive", action="store_true", help="Process subdirectories recursively")
    parser.add_argument("--directory", help="Process a specific directory instead of all directories")
    parser.add_argument("--file", help="Process a single PDF file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    # Connect to the MPC server
    conn = connect_to_mpc(args.url)
    
    # Send a ping to make sure the server is ready
    try:
        ping_response = send_request(conn, "ping", verbose=args.verbose)
        if args.verbose:
            print(f"Ping response: {ping_response}")
    except Exception as e:
        print(f"Warning: Ping failed, but continuing anyway: {e}")

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
            result = process_pdf_file(conn, args.file, verbose=args.verbose)

            # Print response summary
            status = result.get("status", "unknown")
            message = result.get("message", "No message provided")
            print(f"Status: {status}")
            print(f"Message: {message}")

        elif args.directory:
            # Process a specific directory
            process_directory(conn, args.directory, args.recursive, verbose=args.verbose)

        else:
            # Process all directories in the root directory
            if not os.path.isdir(args.root):
                print(f"❌ Root directory not found: {args.root}")
                sys.exit(1)

            # Get all subdirectories
            subdirs = [d for d in os.listdir(args.root) if os.path.isdir(os.path.join(args.root, d))]
            
            # Filter out hidden directories and other non-ebook directories
            subdirs = [d for d in subdirs if not d.startswith('.') and d not in ['Notes', '.roo']]

            if not subdirs:
                print(f"No subdirectories found in {args.root}")
                return

            print(f"Found {len(subdirs)} ebook categories to process")

            # Process each directory
            total_processed = 0
            total_failed = 0
            total_files = 0

            for i, subdir in enumerate(subdirs, 1):
                dir_path = os.path.join(args.root, subdir)
                print(f"\n[{i}/{len(subdirs)}] Processing directory: {subdir}")

                # Process the directory
                result = process_directory(conn, dir_path, args.recursive, verbose=args.verbose)

                # Update totals
                total_processed += result.get("processed_files", 0)
                total_failed += result.get("failed_files", 0)
                total_files += result.get("total_files", 0)

            # Print summary
            print("\n=== Summary ===")
            print(f"Total directories processed: {len(subdirs)}")
            print(f"Total files found: {total_files}")
            print(f"Total files processed successfully: {total_processed}")
            print(f"Total files failed: {total_failed}")

    finally:
        # Close the connection
        conn.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
