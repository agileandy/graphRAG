#!/usr/bin/env python3
"""Script to select 50 random ebooks from a directory and add them to the GraphRAG system.

This script uses the functionality from add_ebooks_batch.py to process individual files.
It requires the project's Python virtual environment to be activated.
"""

import glob
import os
import random
import sys
import time

import websockets.sync.client as ws

# Assuming add_ebooks_batch is in the same directory or accessible in the path
try:
    from add_ebooks_batch import DEFAULT_MPC_URL, process_pdf_file
except ImportError:
    print("❌ Could not import necessary functions from add_ebooks_batch.py.")
    print(
        "Please ensure add_ebooks_batch.py is in the same directory or accessible in the Python path."
    )
    sys.exit(1)


def connect_to_mpc(url=DEFAULT_MPC_URL):
    """Connect to the MPC server."""
    print(f"Connecting to MPC server at {url}...")
    try:
        return ws.connect(url)
    except Exception as e:
        print(f"❌ Error connecting to MPC server: {e}")
        sys.exit(1)


def main() -> None:
    ebooks_directory = "/Users/andyspamer/ebooks"
    num_books_to_process = 50

    if not os.path.isdir(ebooks_directory):
        print(f"❌ Ebooks directory not found: {ebooks_directory}")
        sys.exit(1)

    # Find all PDF files in the directory (non-recursive)
    # To make it recursive, change the glob pattern to os.path.join(ebooks_directory, "**", "*.pdf")
    # and set recursive=True in glob.glob
    pdf_files = glob.glob(os.path.join(ebooks_directory, "**", "*.pdf"), recursive=True)

    if not pdf_files:
        print(f"No PDF files found in {ebooks_directory}")
        sys.exit(0)

    print(f"Found {len(pdf_files)} PDF files in {ebooks_directory}")

    if len(pdf_files) <= num_books_to_process:
        print(
            f"Processing all {len(pdf_files)} found files as it's less than or equal to the requested {num_books_to_process}."
        )
        selected_files = pdf_files
    else:
        print(
            f"Selecting {num_books_to_process} random files out of {len(pdf_files)} found."
        )
        selected_files = random.sample(pdf_files, num_books_to_process)

    # Connect to the MPC server
    conn = connect_to_mpc()

    try:
        print(f"\n=== Processing {len(selected_files)} randomly selected ebooks ===")
        processed_count = 0
        failed_count = 0

        for i, file_path in enumerate(selected_files, 1):
            filename = os.path.basename(file_path)
            print(f"\n[{i}/{len(selected_files)}] Processing: {filename}")

            # Process the file using the function from add_ebooks_batch.py
            result = process_pdf_file(
                conn, file_path, verbose=False
            )  # Set verbose to True for more output

            # Print response summary
            status = result.get("status", "unknown")
            message = result.get("message", "No message provided")
            print(f"Status: {status}")
            print(f"Message: {message}")

            # Count successes and failures
            if status == "success":
                processed_count += 1
            else:
                failed_count += 1

            # Sleep briefly to avoid overwhelming the server
            if i < len(selected_files):
                time.sleep(1)

        print("\n=== Summary ===")
        print(f"Total files selected: {len(selected_files)}")
        print(f"Total files processed successfully: {processed_count}")
        print(f"Total files failed: {failed_count}")

    finally:
        # Close the connection
        conn.close()
        print("Connection closed.")


if __name__ == "__main__":
    # Note: This script needs to be run within the project's Python virtual environment.
    # Ensure the environment is activated before executing this script.
    main()
