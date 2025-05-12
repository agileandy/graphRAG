#!/usr/bin/env python3
"""
Script to test document deduplication functionality.

This script tests:
1. Document hashing
2. Metadata-based deduplication
3. Content-based deduplication
4. Title similarity detection
"""
import sys
import os
import logging
import uuid
from typing import Dict, Any

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.vector_db import VectorDatabase
from src.processing.document_hash import (
    generate_document_hash,
    generate_metadata_hash,
    enrich_metadata_with_hashes,
    calculate_title_similarity,
    is_likely_duplicate
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_document_hashing():
    """Test document hashing functionality."""
    print("\nTesting document hashing...")
    
    # Test document
    doc1 = "This is a test document for hashing."
    doc2 = "This is a test document for hashing."
    doc3 = "This is a slightly different test document for hashing."
    
    # Generate hashes
    hash1 = generate_document_hash(doc1)
    hash2 = generate_document_hash(doc2)
    hash3 = generate_document_hash(doc3)
    
    print(f"Hash 1: {hash1}")
    print(f"Hash 2: {hash2}")
    print(f"Hash 3: {hash3}")
    
    # Check if identical documents have the same hash
    if hash1 == hash2:
        print("✅ Identical documents have the same hash")
    else:
        print("❌ Identical documents have different hashes")
    
    # Check if different documents have different hashes
    if hash1 != hash3:
        print("✅ Different documents have different hashes")
    else:
        print("❌ Different documents have the same hash")
    
    # Test with whitespace and case variations
    doc4 = "  This  is a TEST document for hashing.  "
    hash4 = generate_document_hash(doc4)
    
    if hash1 == hash4:
        print("✅ Normalization works correctly")
    else:
        print("❌ Normalization failed")
    
    return hash1 == hash2 and hash1 != hash3 and hash1 == hash4

def test_metadata_hashing():
    """Test metadata hashing functionality."""
    print("\nTesting metadata hashing...")
    
    # Test metadata
    meta1 = {
        "title": "Test Document",
        "author": "Test Author",
        "file_path": "/path/to/test.pdf"
    }
    
    meta2 = {
        "title": "Test Document",
        "author": "Test Author",
        "file_path": "/path/to/test.pdf"
    }
    
    meta3 = {
        "title": "Different Document",
        "author": "Test Author",
        "file_path": "/path/to/different.pdf"
    }
    
    # Generate hashes
    hash1 = generate_metadata_hash(meta1)
    hash2 = generate_metadata_hash(meta2)
    hash3 = generate_metadata_hash(meta3)
    
    print(f"Metadata Hash 1: {hash1}")
    print(f"Metadata Hash 2: {hash2}")
    print(f"Metadata Hash 3: {hash3}")
    
    # Check if identical metadata have the same hash
    if hash1 == hash2:
        print("✅ Identical metadata have the same hash")
    else:
        print("❌ Identical metadata have different hashes")
    
    # Check if different metadata have different hashes
    if hash1 != hash3:
        print("✅ Different metadata have different hashes")
    else:
        print("❌ Different metadata have the same hash")
    
    # Test with case variations
    meta4 = {
        "title": "TEST DOCUMENT",
        "author": "test author",
        "file_path": "/path/to/test.pdf"
    }
    
    hash4 = generate_metadata_hash(meta4)
    
    if hash1 == hash4:
        print("✅ Case normalization works correctly")
    else:
        print("❌ Case normalization failed")
    
    return hash1 == hash2 and hash1 != hash3 and hash1 == hash4

def test_title_similarity():
    """Test title similarity calculation."""
    print("\nTesting title similarity calculation...")
    
    # Test titles
    title1 = "Introduction to Machine Learning"
    title2 = "Introduction to Machine Learning"
    title3 = "Introduction to Deep Learning"
    title4 = "Intro to Machine Learning"
    title5 = "Something Completely Different"
    
    # Calculate similarities
    sim1_2 = calculate_title_similarity(title1, title2)
    sim1_3 = calculate_title_similarity(title1, title3)
    sim1_4 = calculate_title_similarity(title1, title4)
    sim1_5 = calculate_title_similarity(title1, title5)
    
    print(f"Similarity between '{title1}' and '{title2}': {sim1_2}%")
    print(f"Similarity between '{title1}' and '{title3}': {sim1_3}%")
    print(f"Similarity between '{title1}' and '{title4}': {sim1_4}%")
    print(f"Similarity between '{title1}' and '{title5}': {sim1_5}%")
    
    # Check if identical titles have 100% similarity
    if sim1_2 == 100:
        print("✅ Identical titles have 100% similarity")
    else:
        print("❌ Identical titles don't have 100% similarity")
    
    # Check if similar titles have high similarity
    if sim1_4 > 80:
        print("✅ Similar titles have high similarity")
    else:
        print("❌ Similar titles don't have high similarity")
    
    # Check if different titles have low similarity
    if sim1_5 < 50:
        print("✅ Different titles have low similarity")
    else:
        print("❌ Different titles have high similarity")
    
    return sim1_2 == 100 and sim1_4 > 80 and sim1_5 < 50

def test_deduplication_with_db():
    """Test deduplication with the vector database."""
    print("\nTesting deduplication with vector database...")
    
    # Connect to vector database
    vector_db = VectorDatabase()
    vector_db.connect()
    
    # Create test documents
    doc1_text = "This is a test document for deduplication testing."
    doc1_metadata = {
        "title": "Test Document",
        "author": "Test Author",
        "file_path": f"/path/to/test_{uuid.uuid4()}.pdf"
    }
    
    doc2_text = "This is a test document for deduplication testing."
    doc2_metadata = {
        "title": "Test Document",
        "author": "Test Author",
        "file_path": doc1_metadata["file_path"]  # Same file path
    }
    
    doc3_text = "This is a completely different document."
    doc3_metadata = {
        "title": "Different Document",
        "author": "Another Author",
        "file_path": f"/path/to/different_{uuid.uuid4()}.pdf"
    }
    
    # Enrich metadata with hashes
    doc1_metadata = enrich_metadata_with_hashes(doc1_metadata, doc1_text)
    doc2_metadata = enrich_metadata_with_hashes(doc2_metadata, doc2_text)
    doc3_metadata = enrich_metadata_with_hashes(doc3_metadata, doc3_text)
    
    # Add first document
    doc1_id = f"test-dedup-{uuid.uuid4()}"
    vector_db.add_documents(
        documents=[doc1_text],
        metadatas=[doc1_metadata],
        ids=[doc1_id]
    )
    print(f"✅ Added first document with ID: {doc1_id}")
    
    # Check if second document is detected as duplicate
    is_dup, dup_id, method = is_likely_duplicate(doc2_text, doc2_metadata, vector_db.collection)
    
    if is_dup:
        print(f"✅ Duplicate detected correctly (method: {method})")
        print(f"  Original document ID: {dup_id}")
    else:
        print("❌ Failed to detect duplicate")
    
    # Check if third document is not detected as duplicate
    is_dup, dup_id, method = is_likely_duplicate(doc3_text, doc3_metadata, vector_db.collection)
    
    if not is_dup:
        print("✅ Non-duplicate correctly identified as unique")
    else:
        print(f"❌ Non-duplicate incorrectly identified as duplicate (method: {method})")
    
    return is_dup == False

def main():
    """Main function."""
    print("Testing document deduplication functionality...")
    
    # Run tests
    hashing_ok = test_document_hashing()
    metadata_ok = test_metadata_hashing()
    similarity_ok = test_title_similarity()
    dedup_ok = test_deduplication_with_db()
    
    # Print summary
    print("\nTest Summary:")
    print(f"Document Hashing: {'✅ Passed' if hashing_ok else '❌ Failed'}")
    print(f"Metadata Hashing: {'✅ Passed' if metadata_ok else '❌ Failed'}")
    print(f"Title Similarity: {'✅ Passed' if similarity_ok else '❌ Failed'}")
    print(f"Deduplication with DB: {'✅ Passed' if dedup_ok else '❌ Failed'}")
    
    if hashing_ok and metadata_ok and similarity_ok and dedup_ok:
        print("\n✅ All deduplication tests passed!")
        return True
    else:
        print("\n❌ Some deduplication tests failed.")
        return False

if __name__ == "__main__":
    main()
