#!/usr/bin/env python3
"""Consolidated script to add documents (primarily PDFs) to the GraphRAG system
via an MPC (Message Passing Component/Controller) server.

This script combines functionalities from older scripts:
- add_ebooks_batch.py
- add_pdf_documents.py
- add_prompting_ebooks.py

It supports:
- Client-side PDF text extraction (using PyPDF2) and chunking ('auto' mode).
- Server-side processing by sending file paths to the MPC ('server-file' mode).
- Server-side processing by sending folder paths to the MPC ('server-folder' mode, less common).
- Configurable metadata.
- Recursive directory processing.
"""

import argparse
import glob
import json
import os
import sys
import time
from typing import Any

import websockets.sync.client as ws

try:
    import PyPDF2
except ImportError:
    print(
        "WARNING: PyPDF2 is not installed. Client-side PDF processing ('auto' mode) will not be available."
    )
    print(
        "To enable client-side PDF processing, please install it with 'pip install PyPDF2'."
    )
    PyPDF2 = None  # Set to None if not available

# Default MPC server URL
DEFAULT_MPC_URL = "ws://localhost:8766"
DEFAULT_MAX_CHUNK_SIZE = 500000  # Characters, approx 0.5MB


def connect_to_mpc(url: str = DEFAULT_MPC_URL, verbose: bool = False):
    """Connect to the MPC server."""
    if verbose:
        print(f"Connecting to MPC server at {url}...")
    try:
        conn = ws.connect(url)
        if verbose:
            print("Successfully connected to MPC server.")
        # Send a ping to verify connection
        ping_response = send_request(conn, "ping", verbose=verbose, suppress_exit=True)
        if ping_response.get("status") != "success":
            print(
                f"⚠️ Warning: MPC ping failed or returned non-success: {ping_response.get('message', 'No message')}"
            )
            if verbose:
                print(f"Ping response details: {ping_response}")
        elif verbose:
            print(f"MPC Ping successful: {ping_response.get('message', 'OK')}")
        return conn
    except Exception as e:
        print(f"❌ Error connecting to MPC server: {e}")
        sys.exit(1)


def send_request(
    conn, action: str, verbose: bool = False, suppress_exit: bool = False, **kwargs
) -> dict[str, Any]:
    """Send a request to the MPC server and return the response."""
    message = {"action": action, **kwargs}

    if verbose:
        print("\n=== REQUEST ===")
        print(f"Action: {action}")
        preview_kwargs = {}
        for k, v in kwargs.items():
            if (
                isinstance(v, str) and len(v) > 200
            ):  # Avoid printing very large text content
                preview_kwargs[k] = v[:200] + "... (truncated)"
            else:
                preview_kwargs[k] = v
        print(f"Parameters: {json.dumps(preview_kwargs, indent=2)}")

    try:
        conn.send(json.dumps(message))
        response_raw = conn.recv(timeout=60)  # Added timeout
        response_data = json.loads(response_raw)

        if verbose:
            print("\n=== RESPONSE ===")
            print(json.dumps(response_data, indent=2))

        return response_data
    except TimeoutError:
        print(f"❌ Timeout waiting for response from MPC server for action: {action}")
        if suppress_exit:
            return {
                "status": "error",
                "message": "Timeout waiting for MPC server response",
            }
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error communicating with MPC server: {e}")
        if not suppress_exit:
            try:
                conn.close()
            except Exception:
                pass
            sys.exit(1)
        return {"status": "error", "message": str(e)}


def extract_text_from_pdf(file_path: str, verbose: bool = False) -> str:
    """Extract text from a PDF file using PyPDF2."""
    if not PyPDF2:
        print(
            "❌ PyPDF2 is not available. Cannot extract text from PDF for client-side processing."
        )
        return ""

    if verbose:
        print(f"Extracting text from PDF: {file_path}")
    try:
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text_parts = []
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            full_text = "\n\n".join(text_parts)
            if verbose:
                print(f"Extracted ~{len(full_text)} characters from {file_path}")
            return full_text
    except Exception as e:
        print(f"❌ Error extracting text from PDF {file_path}: {e}")
        return ""


def chunk_text(text: str, max_chunk_size: int, verbose: bool = False) -> list[str]:
    """Split text into chunks of maximum size, trying to respect paragraph/sentence boundaries."""
    if len(text) <= max_chunk_size:
        return [text]

    if verbose:
        print(
            f"Text length ({len(text)}) exceeds max_chunk_size ({max_chunk_size}). Splitting into chunks..."
        )

    chunks = []
    current_pos = 0
    while current_pos < len(text):
        end_pos = current_pos + max_chunk_size

        if end_pos >= len(text):  # Last chunk
            chunks.append(text[current_pos:])
            break

        # Try to find a good split point (paragraph or sentence end) backwards from end_pos
        # Prefer paragraph breaks
        split_pos = text.rfind("\n\n", current_pos, end_pos)
        if split_pos != -1 and split_pos > current_pos:  # Found a paragraph break
            split_pos += 2  # Include the newline characters in the current chunk
        else:  # Try sentence breaks
            split_pos = text.rfind(". ", current_pos, end_pos)
            if split_pos != -1 and split_pos > current_pos:
                split_pos += 2  # Include the period and space
            else:  # If no good break, force split at max_chunk_size
                split_pos = end_pos

        chunks.append(text[current_pos:split_pos].strip())
        current_pos = split_pos

    # Filter out any empty chunks that might have been created
    chunks = [c for c in chunks if c]

    if verbose:
        print(f"Split text into {len(chunks)} chunks.")
    return chunks


def generate_metadata(file_path: str, args: argparse.Namespace) -> dict[str, Any]:
    """Generate metadata for a document."""
    filename = os.path.basename(file_path)
    title = os.path.splitext(filename)[0]

    author = args.author or "Unknown"
    # Basic author extraction if not provided and pattern matches
    if author == "Unknown" and "(" in title and ")" in title:
        try:
            potential_author = title.split("(")[-1].split(")")[0].strip()
            # Basic sanity check for common non-author patterns
            if (
                potential_author
                and "Z-Library" not in potential_author
                and len(potential_author) < 70
                and not potential_author.isdigit()
            ):
                author = potential_author
                title = title.split("(")[
                    0
                ].strip()  # Clean title if author was extracted
        except IndexError:
            pass  # Ignore if parsing fails

    category = args.category
    if (
        not category and args.input_path and os.path.isdir(args.input_path)
    ):  # Try to infer from parent directory if input is a dir
        parent_dir_name = os.path.basename(os.path.normpath(os.path.dirname(file_path)))
        input_base = os.path.basename(os.path.normpath(args.input_path))
        # Only use parent_dir_name if it's not the same as the input_path directory itself (for files in root of input_path)
        # and not some generic name
        if (
            parent_dir_name
            and parent_dir_name != input_base
            and parent_dir_name != "."
            and len(parent_dir_name) > 1
        ):
            category = parent_dir_name.replace("_", " ").replace("-", " ").capitalize()
        else:
            category = "General"  # Default if no better category found
    elif not category:
        category = "General"

    metadata = {
        "title": title,
        "author": author,
        "category": category,
        "source": args.source or "local_import_script",
        "format": "PDF",  # Assuming PDF for now
        "original_file_path": os.path.abspath(
            file_path
        ),  # Store absolute path of original file
    }
    if args.subcategory:
        metadata["subcategory"] = args.subcategory
    if args.concepts:
        # Split concepts by comma, strip whitespace
        metadata["concepts"] = [
            c.strip() for c in args.concepts.split(",") if c.strip()
        ]
    if args.custom_metadata:
        try:
            custom_data = json.loads(args.custom_metadata)
            metadata.update(custom_data)
        except json.JSONDecodeError:
            print(
                f"⚠️ Warning: Could not parse custom_metadata JSON: {args.custom_metadata}"
            )

    return metadata


def process_single_file_client_side(
    conn, file_path: str, args: argparse.Namespace
) -> dict[str, Any]:
    """Process a single file using client-side extraction and chunking."""
    if args.verbose:
        print(f"Processing file (client-side 'auto' mode): {file_path}")

    text = extract_text_from_pdf(file_path, verbose=args.verbose)
    if not text:
        return {
            "status": "error",
            "message": f"Failed to extract text from {file_path}",
        }

    doc_metadata = generate_metadata(file_path, args)

    text_chunks = [text]  # Default to one chunk
    if not args.no_chunking:
        text_chunks = chunk_text(text, args.max_chunk_size, verbose=args.verbose)

    results = []
    for i, chunk_content in enumerate(text_chunks):
        chunk_metadata = doc_metadata.copy()
        if len(text_chunks) > 1:
            chunk_metadata["title"] = (
                f"{doc_metadata['title']} - Part {i + 1}/{len(text_chunks)}"
            )
            chunk_metadata["chunk_index"] = i
            chunk_metadata["total_chunks"] = len(text_chunks)

        if args.verbose:
            print(
                f"Adding chunk {i + 1}/{len(text_chunks)} for '{doc_metadata['title']}' ({len(chunk_content)} chars)"
            )

        if args.dry_run:
            print(
                f"[DRY RUN] Would send 'add-document' for chunk {i + 1} of {doc_metadata['title']}"
            )
            if args.verbose:
                print(f"[DRY RUN] Metadata: {json.dumps(chunk_metadata, indent=1)}")
            results.append(
                {
                    "status": "dry_run_success",
                    "message": "Dry run: document chunk not sent.",
                }
            )
            continue

        result = send_request(
            conn,
            "add-document",
            verbose=args.verbose,
            text=chunk_content,
            metadata=chunk_metadata,
        )
        results.append(result)
        if result.get("status") != "success" and args.verbose:
            print(
                f"⚠️ Warning: Failed to add chunk {i + 1}: {result.get('message', 'Unknown error')}"
            )
        if i < len(text_chunks) - 1:
            time.sleep(0.1)  # Small delay between chunks

    successful_chunks = sum(
        1
        for r in results
        if r.get("status") == "success" or r.get("status") == "dry_run_success"
    )
    if successful_chunks == len(text_chunks):
        return {
            "status": "success",
            "message": f"Document '{doc_metadata['title']}' (client-side) added successfully in {len(text_chunks)} chunk(s).",
        }
    else:
        return {
            "status": "error",
            "message": f"Document '{doc_metadata['title']}' (client-side) partially added. {successful_chunks}/{len(text_chunks)} chunks successful.",
        }


def process_input_path(conn, args: argparse.Namespace) -> None:
    """Processes the input path (file or directory) based on arguments."""
    input_path = args.input_path

    if not os.path.exists(input_path):
        print(f"❌ Error: Input path does not exist: {input_path}")
        sys.exit(1)

    files_to_process = []
    if os.path.isfile(input_path):
        if input_path.lower().endswith(".pdf"):
            files_to_process.append(input_path)
        else:
            print(f"❌ Error: Input file is not a PDF: {input_path}")
            sys.exit(1)  # Exit if single file is not PDF
    elif os.path.isdir(input_path):
        if (
            args.mode == "server-folder"
        ):  # Special mode to send whole folder path to server
            if args.dry_run:
                print(f"[DRY RUN] Would send 'add-folder' for directory: {input_path}")
                doc_metadata = generate_metadata(
                    input_path, args
                )  # Use dir path for generic metadata
                if args.verbose:
                    print(f"[DRY RUN] Metadata: {json.dumps(doc_metadata, indent=1)}")
                print("\n=== Processing Summary ===")
                print("Total folders found: 1")
                print("Folders attempted: 1 (dry run)")
                print("Successfully processed: 1 (dry run)")
                return
            else:
                print(f"Processing directory (server-folder mode): {input_path}")
                doc_metadata = generate_metadata(
                    input_path, args
                )  # Use dir path for generic metadata
                result = send_request(
                    conn,
                    "add-folder",
                    verbose=args.verbose,
                    folder_path=os.path.abspath(input_path),
                    metadata=doc_metadata,
                )
                print("\n=== Processing Summary ===")
                print("Total folders found: 1")
                print("Folders attempted: 1")
                if result.get("status") == "success":
                    print(
                        f"Successfully processed: 1. Server message: {result.get('message', 'OK')}"
                    )
                else:
                    print(
                        f"Failed: 1. Server message: {result.get('message', 'Error')}"
                    )
                return  # Exit after server-folder mode

        # For 'auto' and 'server-file' modes, find individual PDFs
        glob_pattern = (
            os.path.join(input_path, "**", "*.pdf")
            if args.recursive
            else os.path.join(input_path, "*.pdf")
        )
        files_to_process = glob.glob(glob_pattern, recursive=args.recursive)
        if not files_to_process:
            print(f"No PDF files found in {input_path} (recursive={args.recursive}).")
            return
    else:
        print(f"❌ Error: Input path is not a valid file or directory: {input_path}")
        sys.exit(1)

    total_files = len(files_to_process)
    print(f"Found {total_files} PDF file(s) to process using mode '{args.mode}'.")

    processed_count = 0
    success_count = 0
    error_count = 0

    for i, file_path in enumerate(files_to_process):
        print(
            f"\n--- Processing file {i + 1}/{total_files}: {os.path.basename(file_path)} ---"
        )
        result = None
        if args.mode == "auto":
            if not PyPDF2:
                print(
                    f"⚠️ Skipping {file_path}: PyPDF2 not available for client-side processing and mode is 'auto'. Consider '--mode server-file'."
                )
                error_count += 1
                continue
            result = process_single_file_client_side(conn, file_path, args)
        elif args.mode == "server-file":
            doc_metadata = generate_metadata(file_path, args)
            if args.dry_run:
                print(
                    f"[DRY RUN] Would send 'add-document' (server-file mode) for file: {file_path}"
                )
                if args.verbose:
                    print(f"[DRY RUN] Metadata: {json.dumps(doc_metadata, indent=1)}")
                result = {
                    "status": "dry_run_success",
                    "message": "Dry run: document not sent.",
                }
            else:
                if args.verbose:
                    print(f"Processing file (server-file mode): {file_path}")
                result = send_request(
                    conn,
                    "add-document",
                    verbose=args.verbose,
                    file_path=os.path.abspath(file_path),
                    metadata=doc_metadata,
                )
        else:  # Should not happen if arg choices are enforced
            print(f"❌ Internal Error: Unknown processing mode: {args.mode}")
            error_count += 1
            continue

        processed_count += 1
        if result and (
            result.get("status") == "success"
            or result.get("status") == "dry_run_success"
        ):
            success_count += 1
            print(f"✅ {result.get('message', 'Successfully processed.')}")
        else:
            error_count += 1
            print(f"❌ {result.get('message', 'Failed to process.')}")
            if args.verbose and result:
                print(f"Full error response: {result}")

        if i < total_files - 1 and not args.dry_run:
            time.sleep(args.delay)

    print("\n=== Processing Summary ===")
    print(f"Total files found: {total_files}")
    print(f"Files attempted: {processed_count}")
    print(f"Successfully processed: {success_count}")
    print(f"Failed/Skipped: {error_count}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Consolidated script to add PDF documents to GraphRAG via MPC.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  # Add a single PDF using client-side processing (text extraction, chunking)
  python %(prog)s --input-path /path/to/document.pdf --mode auto

  # Add all PDFs in a directory (non-recursive) using server-side file processing
  python %(prog)s --input-path /path/to/docs/ --mode server-file

  # Add all PDFs in a directory (recursive) using client-side processing with custom category
  python %(prog)s --input-path /path/to/ebooks/ --recursive --mode auto --category "Technical Books"

  # Add a single PDF, let server handle processing, and provide concepts
  python %(prog)s --input-path doc.pdf --mode server-file --concepts "AI,LLM,Python"

  # Dry run: show what would be done for client-side processing of a folder
  python %(prog)s --input-path /path/to/data/ --recursive --mode auto --dry-run --verbose
""",
    )

    # Connection arguments
    parser.add_argument(
        "--url",
        default=DEFAULT_MPC_URL,
        help=f"MPC server URL (default: {DEFAULT_MPC_URL})",
    )

    # Input arguments
    parser.add_argument(
        "--input-path",
        required=True,
        help="Path to a PDF file or a directory containing PDFs.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="If input-path is a directory, process subdirectories recursively.",
    )

    # Processing mode
    parser.add_argument(
        "--mode",
        choices=["auto", "server-file", "server-folder"],
        default="auto",
        help=(
            "Processing mode:\n"
            "  auto: Client-side PDF text extraction and chunking. Requires PyPDF2.\n"
            "        Sends text content to MPC 'add-document' action.\n"
            "  server-file: Server-side processing for individual files.\n"
            "               Sends file path to MPC 'add-document' action. MPC must have access to the path.\n"
            "  server-folder: Server-side processing for an entire folder.\n"
            "                 Sends folder path to MPC 'add-folder' action. MPC must have access to the path.\n"
            "(default: auto)"
        ),
    )

    # Metadata arguments
    parser.add_argument(
        "--category",
        type=str,
        help="Category for the document(s). If not provided, inferred from parent directory or 'General'.",
    )
    parser.add_argument(
        "--subcategory", type=str, help="Subcategory for the document(s)."
    )
    parser.add_argument(
        "--author",
        type=str,
        help="Author for the document(s). If not provided, 'Unknown' or inferred from filename.",
    )
    parser.add_argument(
        "--source",
        type=str,
        help="Source of the document(s) (e.g., 'project_docs', 'research_papers'). Default 'local_import_script'.",
    )
    parser.add_argument(
        "--concepts",
        type=str,
        help="Comma-separated list of concepts related to the document(s).",
    )
    parser.add_argument(
        "--custom-metadata",
        type=str,
        help='JSON string for additional custom metadata fields (e.g., \'{"project_id": "X123", "status": "draft"}\')',
    )

    # Client-side processing arguments (for 'auto' mode)
    parser.add_argument(
        "--no-chunking",
        action="store_true",
        help="Disable client-side text chunking (sends entire document text as one piece).",
    )
    parser.add_argument(
        "--max-chunk-size",
        type=int,
        default=DEFAULT_MAX_CHUNK_SIZE,
        help=f"Maximum chunk size in characters for client-side chunking (default: {DEFAULT_MAX_CHUNK_SIZE}).",
    )

    # General arguments
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay in seconds between processing files (default: 0.5s).",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output, including request/response details.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate processing without actually sending data to MPC or writing files.",
    )

    args = parser.parse_args()

    if args.mode == "auto" and not PyPDF2:
        print(
            "❌ Error: Mode 'auto' (client-side processing) selected, but PyPDF2 is not installed."
        )
        print(
            "Please install PyPDF2 ('pip install PyPDF2') or choose '--mode server-file' or '--mode server-folder'."
        )
        sys.exit(1)

    if args.dry_run:
        print("💧 DRY RUN MODE ENABLED: No actual data will be sent to the MPC server.")

    conn = None
    try:
        if (
            not args.dry_run
        ):  # No need to connect for dry run if all processing is client-side preview
            conn = connect_to_mpc(args.url, verbose=args.verbose)

        process_input_path(conn, args)

    except KeyboardInterrupt:
        print("\n🚫 Process interrupted by user.")
    finally:
        if conn:
            if args.verbose:
                print("Closing MPC connection...")
            conn.close()
            if args.verbose:
                print("MPC connection closed.")
        print("Script finished.")


if __name__ == "__main__":
    main()
