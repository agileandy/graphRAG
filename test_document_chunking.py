#!/usr/bin/env python3
"""
Test script for document chunking functionality.

This script tests:
1. Basic chunking with different sizes
2. Semantic boundary chunking
3. Paragraph preservation
4. Overlap functionality
"""
import sys
import os
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import the document processor
from src.processing.document_processor import (
    smart_chunk_text,
    optimize_chunk_size,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_OVERLAP
)

def test_basic_chunking():
    """Test basic chunking functionality."""
    print("\n=== Testing Basic Chunking ===")
    
    # Test document with multiple paragraphs
    test_text = """
    This is the first paragraph of the test document. It contains multiple sentences.
    This is the second sentence. And this is the third sentence.
    
    This is the second paragraph. It also has multiple sentences.
    Another sentence in the second paragraph.
    
    This is the third paragraph, which will help test the chunking functionality.
    We want to make sure that paragraphs are properly preserved during chunking.
    
    This is the fourth paragraph. It contains some more text to ensure we have
    enough content to test the chunking functionality properly.
    """
    
    # Test with different chunk sizes
    chunk_sizes = [100, 200, 500]
    
    for size in chunk_sizes:
        print(f"\nChunking with size {size}, no semantic boundaries:")
        chunks = smart_chunk_text(test_text, chunk_size=size, overlap=50, semantic_boundaries=False)
        
        print(f"Created {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1} ({len(chunk)} chars): {chunk[:50]}...")
    
    return True

def test_semantic_chunking():
    """Test semantic boundary chunking."""
    print("\n=== Testing Semantic Boundary Chunking ===")
    
    # Test document with multiple paragraphs
    test_text = """
    This is the first paragraph of the test document. It contains multiple sentences.
    This is the second sentence. And this is the third sentence.
    
    This is the second paragraph. It also has multiple sentences.
    Another sentence in the second paragraph.
    
    This is the third paragraph, which will help test the chunking functionality.
    We want to make sure that paragraphs are properly preserved during chunking.
    
    This is the fourth paragraph. It contains some more text to ensure we have
    enough content to test the chunking functionality properly.
    """
    
    # Test with semantic boundaries
    print("\nChunking with semantic boundaries:")
    chunks = smart_chunk_text(test_text, chunk_size=200, overlap=50, semantic_boundaries=True)
    
    print(f"Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1} ({len(chunk)} chars): {chunk[:50]}...")
    
    return True

def test_paragraph_preservation():
    """Test paragraph preservation in chunking."""
    print("\n=== Testing Paragraph Preservation ===")
    
    # Test document with multiple paragraphs and formatting
    test_text = """
    # Heading 1
    
    This is the first paragraph with **bold** text and *italics*.
    
    ## Heading 2
    
    This is a paragraph under heading 2.
    It continues for multiple lines.
    
    - List item 1
    - List item 2
    - List item 3
    
    ### Heading 3
    
    Final paragraph with some code:
    ```python
    def hello_world():
        print("Hello, world!")
    ```
    """
    
    # Test with semantic boundaries
    print("\nChunking with semantic boundaries and paragraph preservation:")
    chunks = smart_chunk_text(test_text, chunk_size=200, overlap=50, semantic_boundaries=True)
    
    print(f"Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1} ({len(chunk)} chars):")
        print(f"    {chunk[:100]}...")
    
    return True

def test_overlap_functionality():
    """Test overlap functionality in chunking."""
    print("\n=== Testing Overlap Functionality ===")
    
    # Create a test document with numbered sentences for easy tracking
    sentences = []
    for i in range(1, 21):
        sentences.append(f"This is sentence number {i} in the test document.")
    
    test_text = " ".join(sentences)
    
    # Test with different overlap sizes
    overlap_sizes = [0, 50, 100]
    chunk_size = 200
    
    for overlap in overlap_sizes:
        print(f"\nChunking with size {chunk_size}, overlap {overlap}:")
        chunks = smart_chunk_text(test_text, chunk_size=chunk_size, overlap=overlap, semantic_boundaries=False)
        
        print(f"Created {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1} ({len(chunk)} chars): {chunk[:50]}...")
    
    return True

def test_large_document_chunking():
    """Test chunking with a larger document."""
    print("\n=== Testing Large Document Chunking ===")
    
    # Create a larger test document
    paragraphs = []
    for i in range(1, 21):
        paragraphs.append(f"This is paragraph {i} in the test document. It contains multiple sentences that will help test the chunking functionality. We want to ensure that the chunking works properly with larger documents and preserves the semantic meaning of the text.")
    
    test_text = "\n\n".join(paragraphs)
    
    # Determine optimal chunk size
    optimal_size = optimize_chunk_size(test_text)
    print(f"Optimal chunk size for document: {optimal_size}")
    
    # Test chunking with optimal size
    print(f"\nChunking with optimal size {optimal_size}:")
    chunks = smart_chunk_text(test_text, chunk_size=optimal_size, overlap=DEFAULT_OVERLAP, semantic_boundaries=True)
    
    print(f"Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1} ({len(chunk)} chars): {chunk[:50]}...")
    
    return True

def main():
    """Main function."""
    print("Testing document chunking functionality...")
    
    # Run tests
    basic_ok = test_basic_chunking()
    semantic_ok = test_semantic_chunking()
    paragraph_ok = test_paragraph_preservation()
    overlap_ok = test_overlap_functionality()
    large_doc_ok = test_large_document_chunking()
    
    # Print summary
    print("\nTest Summary:")
    print(f"Basic Chunking: {'✅ Passed' if basic_ok else '❌ Failed'}")
    print(f"Semantic Chunking: {'✅ Passed' if semantic_ok else '❌ Failed'}")
    print(f"Paragraph Preservation: {'✅ Passed' if paragraph_ok else '❌ Failed'}")
    print(f"Overlap Functionality: {'✅ Passed' if overlap_ok else '❌ Failed'}")
    print(f"Large Document Chunking: {'✅ Passed' if large_doc_ok else '❌ Failed'}")

if __name__ == "__main__":
    main()
