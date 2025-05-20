#!/usr/bin/env python3
"""Test script for file handlers."""

import os

from src.loaders.markdown_loader import MarkdownLoader
from src.loaders.pdf_loader import PDFLoader
from src.processing.file_handler import FileHandler


def test_markdown_loader() -> None:
    """Test the Markdown loader."""
    print("\n=== Testing Markdown Loader ===")

    # Path to test Markdown file
    file_path = "test_files/test_markdown.md"

    if not os.path.exists(file_path):
        print(f"Error: Test file {file_path} not found")
        return

    print(f"Loading Markdown file: {file_path}")

    try:
        text, metadata = MarkdownLoader.load(file_path)

        print(f"Metadata: {metadata}")
        print(f"Text (first 200 chars): {text[:200]}...")
        print("Markdown loader test successful!")
    except Exception as e:
        print(f"Error loading Markdown file: {e}")
        import traceback

        traceback.print_exc()


def test_pdf_loader() -> None:
    """Test the PDF loader."""
    print("\n=== Testing PDF Loader ===")

    # Path to test PDF file
    file_path = "test_files/test_pdf.pdf"

    if not os.path.exists(file_path):
        print(f"Error: Test file {file_path} not found")
        return

    print(f"Loading PDF file: {file_path}")

    try:
        text, metadata = PDFLoader.load(file_path)

        print(f"Metadata: {metadata}")
        print(f"Text (first 200 chars): {text[:200]}...")
        print("PDF loader test successful!")
    except Exception as e:
        print(f"Error loading PDF file: {e}")
        import traceback

        traceback.print_exc()


def test_file_handler() -> None:
    """Test the file handler."""
    print("\n=== Testing File Handler ===")

    print(f"Supported extensions: {FileHandler.get_supported_extensions()}")

    # Test with Markdown file
    md_path = "test_files/test_markdown.md"
    if os.path.exists(md_path):
        print(f"\nTesting with Markdown file: {md_path}")
        print(f"Can handle: {FileHandler.can_handle_file(md_path)}")

        try:
            text, metadata = FileHandler.process_file(md_path)
            print(f"Metadata: {metadata}")
            print(f"Text (first 200 chars): {text[:200]}...")
        except Exception as e:
            print(f"Error processing Markdown file: {e}")
            import traceback

            traceback.print_exc()

    # Test with PDF file
    pdf_path = "test_files/test_pdf.pdf"
    if os.path.exists(pdf_path):
        print(f"\nTesting with PDF file: {pdf_path}")
        print(f"Can handle: {FileHandler.can_handle_file(pdf_path)}")

        try:
            text, metadata = FileHandler.process_file(pdf_path)
            print(f"Metadata: {metadata}")
            print(f"Text (first 200 chars): {text[:200]}...")
        except Exception as e:
            print(f"Error processing PDF file: {e}")
            import traceback

            traceback.print_exc()


def main() -> None:
    """Main function."""
    test_markdown_loader()
    test_pdf_loader()
    test_file_handler()


if __name__ == "__main__":
    main()
