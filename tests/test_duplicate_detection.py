"""Tests for duplicate detection functionality.

This module tests the duplicate detection functionality in the GraphRAG system,
particularly focusing on the ChromaDB duplicate detection with proper query formatting.
"""

import os

import pytest

from src.database.vector_db import VectorDatabase


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


def test_duplicate_detection_by_metadata(vector_db) -> None:
    """Test duplicate detection using metadata."""
    # Create test documents
    documents = ["Test document 1", "Test document 2", "Test document 3"]

    metadatas = [
        {"title": "Test 1", "author": "Author 1"},
        {"title": "Test 2", "author": "Author 2"},
        {"title": "Test 1", "author": "Author 1"},  # Duplicate of first document
    ]

    ids = ["doc1", "doc2", "doc3"]

    # Add documents
    vector_db.add_documents(
        documents=documents, metadatas=metadatas, ids=ids, check_duplicates=True
    )

    # Verify only non-duplicates were added
    results = vector_db.get()
    assert (
        len(results["ids"]) == 2
    )  # Should only have 2 documents (duplicate filtered out)

    # Verify the correct documents were kept
    kept_ids = set(results["ids"])
    assert "doc1" in kept_ids
    assert "doc2" in kept_ids
    assert "doc3" not in kept_ids  # Duplicate should be filtered out


def test_duplicate_detection_by_path(vector_db) -> None:
    """Test duplicate detection using file path."""
    # Create test documents
    documents = ["Test document 1", "Test document 2", "Test document 3"]

    metadatas = [
        {"file_path": "/path/to/doc1.txt"},
        {"file_path": "/path/to/doc2.txt"},
        {"file_path": "/path/to/doc1.txt"},  # Duplicate path
    ]

    ids = ["doc1", "doc2", "doc3"]

    # Add documents
    vector_db.add_documents(
        documents=documents, metadatas=metadatas, ids=ids, check_duplicates=True
    )

    # Verify only non-duplicates were added
    results = vector_db.get()
    assert (
        len(results["ids"]) == 2
    )  # Should only have 2 documents (duplicate filtered out)

    # Verify the correct documents were kept
    kept_ids = set(results["ids"])
    assert "doc1" in kept_ids
    assert "doc2" in kept_ids
    assert "doc3" not in kept_ids  # Duplicate should be filtered out


def test_multiple_field_duplicate_detection(vector_db) -> None:
    """Test duplicate detection with multiple fields."""
    # Create test documents
    documents = ["Test document 1", "Test document 2", "Test document 3"]

    metadatas = [
        {"title": "Test 1", "author": "Author 1", "category": "Cat1"},
        {"title": "Test 2", "author": "Author 2", "category": "Cat2"},
        {"title": "Test 1", "author": "Author 1", "category": "Cat1"},  # Duplicate
    ]

    ids = ["doc1", "doc2", "doc3"]

    # Add documents
    vector_db.add_documents(
        documents=documents, metadatas=metadatas, ids=ids, check_duplicates=True
    )

    # Verify only non-duplicates were added
    results = vector_db.get()
    assert (
        len(results["ids"]) == 2
    )  # Should only have 2 documents (duplicate filtered out)

    # Verify the correct documents were kept
    kept_ids = set(results["ids"])
    assert "doc1" in kept_ids
    assert "doc2" in kept_ids
    assert "doc3" not in kept_ids  # Duplicate should be filtered out


def test_case_insensitive_path_detection(vector_db) -> None:
    """Test case-insensitive file path duplicate detection."""
    # Create test documents
    documents = ["Test document 1", "Test document 2", "Test document 3"]

    metadatas = [
        {"file_path": "/path/to/doc1.txt"},
        {"file_path": "/path/to/doc2.txt"},
        {"file_path": "/PATH/TO/DOC1.TXT"},  # Same path, different case
    ]

    ids = ["doc1", "doc2", "doc3"]

    # Add documents
    vector_db.add_documents(
        documents=documents, metadatas=metadatas, ids=ids, check_duplicates=True
    )

    # Verify only non-duplicates were added
    results = vector_db.get()
    assert (
        len(results["ids"]) == 2
    )  # Should only have 2 documents (duplicate filtered out)

    # Verify the correct documents were kept
    kept_ids = set(results["ids"])
    assert "doc1" in kept_ids
    assert "doc2" in kept_ids
    assert "doc3" not in kept_ids  # Duplicate should be filtered out
