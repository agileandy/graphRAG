#!/usr/bin/env python3
"""
Test script to demonstrate the document pipeline with verbose output.
This script will process a PDF file and show the detailed output for:
- Reading the PDF
- Converting content (text, tables, images)
- Chunking the document
- Embedding the chunks
"""

import os
import sys
import argparse
import time
from typing import Dict, Any, List, Tuple
import uuid
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import required modules
from src.loaders.pdf_loader import PDFLoader
from src.processing.document_processor import smart_chunk_text, optimize_chunk_size, DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP
from src.llm.llm_provider import create_llm_provider
from src.utils.config import load_config

def main():
    """Main function to process a PDF file and show verbose output."""
    parser = argparse.ArgumentParser(description="Test the document pipeline with verbose output")
    parser.add_argument("pdf_path", help="Path to the PDF file to process")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE,
                        help=f"Maximum chunk size in characters (default: {DEFAULT_CHUNK_SIZE})")
    parser.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP,
                        help=f"Overlap between chunks in characters (default: {DEFAULT_OVERLAP})")

    args = parser.parse_args()

    # Check if the file exists
    if not os.path.exists(args.pdf_path):
        print(f"Error: File {args.pdf_path} not found")
        sys.exit(1)

    # Process the PDF file
    process_pdf_with_verbose_output(args.pdf_path, args.chunk_size, args.overlap)

def process_pdf_with_verbose_output(pdf_path: str, chunk_size: int, overlap: int):
    """
    Process a PDF file with verbose output for each step.

    Args:
        pdf_path: Path to the PDF file
        chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters
    """
    print("\n" + "="*80)
    print(f"PROCESSING PDF: {pdf_path}")
    print("="*80)

    # Step 1: Load the PDF file
    print("\n\n" + "="*40)
    print("STEP 1: LOADING PDF FILE")
    print("="*40)

    start_time = time.time()
    print(f"Loading PDF file: {pdf_path}")

    text, metadata = PDFLoader.load(pdf_path)

    load_time = time.time() - start_time
    print(f"PDF loaded in {load_time:.2f} seconds")
    print(f"Metadata: {metadata}")
    print(f"Text length: {len(text)} characters")
    print(f"First 500 characters of text:\n{text[:500]}...")

    # Step 2: Extract tables and images
    print("\n\n" + "="*40)
    print("STEP 2: EXTRACTING TABLES AND IMAGES")
    print("="*40)

    start_time = time.time()
    print("Extracting tables...")
    tables_text = PDFLoader._extract_tables(pdf_path)

    tables_time = time.time() - start_time
    print(f"Tables extracted in {tables_time:.2f} seconds")

    if tables_text:
        print(f"Tables found: {tables_text[:500]}...")
    else:
        print("No tables found in the document")

    start_time = time.time()
    print("\nDetecting diagrams and images...")
    diagrams = PDFLoader._detect_diagrams(pdf_path)

    diagrams_time = time.time() - start_time
    print(f"Diagrams detected in {diagrams_time:.2f} seconds")
    print(f"Diagrams found: {len(diagrams)}")
    for i, diagram in enumerate(diagrams[:5]):  # Show first 5 diagrams
        print(f"  Diagram {i+1}: {diagram}")

    # Step 3: Chunk the document
    print("\n\n" + "="*40)
    print("STEP 3: CHUNKING THE DOCUMENT")
    print("="*40)

    start_time = time.time()
    print(f"Determining optimal chunk size for document of length {len(text)} characters...")

    optimized_chunk_size = optimize_chunk_size(text, chunk_size)
    print(f"Optimized chunk size: {optimized_chunk_size} characters (original: {chunk_size})")

    print(f"Chunking text with chunk_size={optimized_chunk_size}, overlap={overlap}...")
    chunks = smart_chunk_text(text, optimized_chunk_size, overlap, semantic_boundaries=True)

    chunk_time = time.time() - start_time
    print(f"Text chunked in {chunk_time:.2f} seconds")
    print(f"Created {len(chunks)} chunks")

    # Print some statistics about the chunks
    chunk_lengths = [len(chunk) for chunk in chunks]
    avg_chunk_length = sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0

    print(f"Average chunk length: {avg_chunk_length:.2f} characters")
    print(f"Shortest chunk: {min(chunk_lengths)} characters")
    print(f"Longest chunk: {max(chunk_lengths)} characters")

    # Print the first few chunks
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        print(f"\nChunk {i+1} ({len(chunk)} chars):")
        print(f"{chunk[:200]}...")

    # Step 4: Generate embeddings
    print("\n\n" + "="*40)
    print("STEP 4: GENERATING EMBEDDINGS")
    print("="*40)

    # Load configuration
    config = load_config()

    # Create a specific configuration for Ollama embeddings
    embedding_config = {
        "embedding_provider": {
            "type": "ollama",
            "api_base": "http://localhost:11434",
            "model": "snowflake-arctic-embed2:latest",
            "embedding_model": "snowflake-arctic-embed2:latest",
            "timeout": 60
        }
    }

    # Create LLM provider for embeddings
    print("Creating LLM provider for embeddings using Ollama...")
    llm_provider = create_llm_provider(embedding_config.get("embedding_provider", {}))

    # Generate embeddings for the first few chunks
    sample_chunks = chunks[:3]  # Use first 3 chunks for demonstration

    start_time = time.time()
    print(f"Generating embeddings for {len(sample_chunks)} sample chunks...")

    try:
        embeddings = llm_provider.get_embeddings(sample_chunks)

        embed_time = time.time() - start_time
        print(f"Embeddings generated in {embed_time:.2f} seconds")

        # Print embedding statistics
        for i, embedding in enumerate(embeddings):
            print(f"Chunk {i+1} embedding: {len(embedding)} dimensions")
            print(f"  First 5 values: {embedding[:5]}")
            print(f"  Min: {min(embedding) if embedding and len(embedding) > 1 else 0.0}, Max: {max(embedding) if embedding and len(embedding) > 1 else 0.0}")
    except Exception as e:
        print(f"Error generating embeddings: {e}")

    # Summary
    print("\n\n" + "="*40)
    print("DOCUMENT PROCESSING SUMMARY")
    print("="*40)

    print(f"PDF file: {pdf_path}")
    print(f"Document length: {len(text)} characters")
    print(f"Tables found: {'Yes' if tables_text else 'No'}")
    print(f"Diagrams/images found: {len(diagrams)}")
    print(f"Chunks created: {len(chunks)}")
    print(f"Average chunk size: {avg_chunk_length:.2f} characters")

    total_time = load_time + tables_time + diagrams_time + chunk_time
    print(f"Total processing time: {total_time:.2f} seconds (excluding embeddings)")

if __name__ == "__main__":
    main()
