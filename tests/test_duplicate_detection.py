"""
Tests for duplicate detection functionality.

This module tests the duplicate detection functionality in the GraphRAG system,
particularly focusing on the ChromaDB duplicate detection with proper query formatting.
"""
import os
import pytest
from typing import Dict, Any
from unittest.mock import MagicMock, patch

from src.database.vector_db import VectorDatabase
from src.processing.duplicate_detector import ChromaDuplicateDetector, DuplicateDetector

@pytest.fixture
def vector_db():
    """Create a test vector database instance."""
    # Use a test-specific directory
    test_dir = "./data/test_chromadb"
    os.makedirs(test_dir, exist_ok=True)

    # Create and connect to the database
    db = VectorDatabase(persist_directory=test_dir)
    db.connect(collection_name="test_collection")

    yield db

    # Cleanup
    try:
        import shutil
        shutil.rmtree(test_dir)
    except Exception as e:
        print(f"Error cleaning up test directory: {e}")

def test_duplicate_detection_by_metadata(vector_db):
    """Test duplicate detection using metadata."""
    # Create test documents
    documents = [
        "Test document 1",
        "Test document 2",
        "Test document 3"
    ]

    metadatas = [
        {"title": "Test 1", "author": "Author 1"},
        {"title": "Test 2", "author": "Author 2"},
        {"title": "Test 1", "author": "Author 1"}  # Duplicate of first document
    ]

    ids = ["doc1", "doc2", "doc3"]

    # Add documents
    vector_db.add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        check_duplicates=True
    )

    # Verify only non-duplicates were added
    results = vector_db.get()
    assert len(results["ids"]) == 2  # Should only have 2 documents (duplicate filtered out)

    # Verify the correct documents were kept
    kept_ids = set(results["ids"])
    assert "doc1" in kept_ids
    assert "doc2" in kept_ids
    assert "doc3" not in kept_ids  # Duplicate should be filtered out

def test_duplicate_detection_by_path(vector_db):
    """Test duplicate detection using file path."""
    # Create test documents
    documents = [
        "Test document 1",
        "Test document 2",
        "Test document 3"
    ]

    metadatas = [
        {"file_path": "/path/to/doc1.txt"},
        {"file_path": "/path/to/doc2.txt"},
        {"file_path": "/path/to/doc1.txt"}  # Duplicate path
    ]

    ids = ["doc1", "doc2", "doc3"]

    # Add documents
    vector_db.add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        check_duplicates=True
    )

    # Verify only non-duplicates were added
    results = vector_db.get()
    assert len(results["ids"]) == 2  # Should only have 2 documents (duplicate filtered out)

    # Verify the correct documents were kept
    kept_ids = set(results["ids"])
    assert "doc1" in kept_ids
    assert "doc2" in kept_ids
    assert "doc3" not in kept_ids  # Duplicate should be filtered out

def test_multiple_field_duplicate_detection(vector_db):
    """Test duplicate detection with multiple fields."""
    # Create test documents
    documents = [
        "Test document 1",
        "Test document 2",
        "Test document 3"
    ]

    metadatas = [
        {"title": "Test 1", "author": "Author 1", "category": "Cat1"},
        {"title": "Test 2", "author": "Author 2", "category": "Cat2"},
        {"title": "Test 1", "author": "Author 1", "category": "Cat1"}  # Duplicate
    ]

    ids = ["doc1", "doc2", "doc3"]

    # Add documents
    vector_db.add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        check_duplicates=True
    )

    # Verify only non-duplicates were added
    results = vector_db.get()
    assert len(results["ids"]) == 2  # Should only have 2 documents (duplicate filtered out)

    # Verify the correct documents were kept
    kept_ids = set(results["ids"])
    assert "doc1" in kept_ids
    assert "doc2" in kept_ids
    assert "doc3" not in kept_ids  # Duplicate should be filtered out

def test_case_insensitive_path_detection(vector_db):
    """Test case-insensitive file path duplicate detection."""
    # Create test documents
    documents = [
        "Test document 1",
        "Test document 2",
        "Test document 3"
    ]

    metadatas = [
        {"file_path": "/path/to/doc1.txt"},
        {"file_path": "/path/to/doc2.txt"},
        {"file_path": "/PATH/TO/DOC1.TXT"}  # Same path, different case
    ]

    ids = ["doc1", "doc2", "doc3"]

    # Add documents
    vector_db.add_documents(
        documents=documents,
        metadatas=metadatas,
        ids=ids,
        check_duplicates=True
    )

    # Verify only non-duplicates were added
    results = vector_db.get()
    assert len(results["ids"]) == 2  # Should only have 2 documents (duplicate filtered out)

    # Verify the correct documents were kept
    kept_ids = set(results["ids"])
    assert "doc1" in kept_ids
    assert "doc2" in kept_ids
    assert "doc3" not in kept_ids  # Duplicate should be filtered out

def test_chroma_duplicate_detector_query_building():
    """Test ChromaDuplicateDetector query building with proper ChromaDB syntax."""
    # Create a mock collection
    mock_collection = MagicMock()
    detector = ChromaDuplicateDetector(mock_collection)

    # Test with a single field
    single_field_metadata = {"title": "Test Document"}
    single_field_query = detector._build_duplicate_query(single_field_metadata)

    # For a single field, we expect a simple equality query
    expected_single_query = {"title": {"$eq": "Test Document"}}
    assert single_field_query == expected_single_query

    # Test with multiple fields
    multi_field_metadata = {
        "title": "Neural Networks and Deep Learning: A Comprehensive Guide",
        "author": "AI Researcher"
    }
    multi_field_query = detector._build_duplicate_query(multi_field_metadata)

    # For multiple fields, we expect an $and query with proper operators
    expected_multi_query = {
        "$and": [
            {"title": {"$eq": "Neural Networks and Deep Learning: A Comprehensive Guide"}},
            {"author": {"$eq": "AI Researcher"}}
        ]
    }
    assert multi_field_query == expected_multi_query

def test_chroma_duplicate_detector_is_duplicate():
    """Test ChromaDuplicateDetector is_duplicate method with proper query format."""
    # Create a mock collection
    mock_collection = MagicMock()
    # Configure the mock to return a result for the first call and empty for the second
    mock_collection.get.side_effect = [
        {"ids": ["doc1"], "metadatas": [{"title": "Test", "author": "Author"}]},  # First call returns a match
        {"ids": [], "metadatas": []}  # Second call returns no match
    ]

    detector = ChromaDuplicateDetector(mock_collection)

    # Test with multiple fields that should match
    metadata = {
        "title": "Neural Networks and Deep Learning: A Comprehensive Guide",
        "author": "AI Researcher"
    }
    is_dup, doc_id = detector.is_duplicate(metadata)

    # Verify the query was built correctly with $and operator
    expected_where = {
        "$and": [
            {"title": {"$eq": "Neural Networks and Deep Learning: A Comprehensive Guide"}},
            {"author": {"$eq": "AI Researcher"}}
        ]
    }
    mock_collection.get.assert_called_with(where=expected_where)

    # Verify the result
    assert is_dup is True
    assert doc_id == "doc1"

    # Test with metadata that should not match
    metadata = {"title": "Non-existent Document"}
    is_dup, doc_id = detector.is_duplicate(metadata)

    # Verify the result
    assert is_dup is False
    assert doc_id is None