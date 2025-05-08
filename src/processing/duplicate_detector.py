"""
Duplicate detection for GraphRAG project.

This module provides utilities for detecting duplicate documents
in the GraphRAG system, particularly for PDFs and other document types.
"""
import os
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
import re
from fuzzywuzzy import fuzz
from fuzzywuzzy import process # Import process for potential future use or if needed by fuzz.ratio internally

from src.database.vector_db import VectorDatabase

class DuplicateDetector:
    """
    Duplicate detector for documents in the GraphRAG system.
    """
    def __init__(self, vector_db: VectorDatabase):
        """
        Initialize duplicate detector.

        Args:
            vector_db: Vector database instance
        """
        self.vector_db = vector_db

    def is_duplicate_by_path(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a document is a duplicate by file path.

        Args:
            file_path: Path to the file

        Returns:
            Tuple of (is_duplicate, existing_doc_id)
        """
        # Ensure vector database is connected
        if self.vector_db.collection is None:
            self.vector_db.connect()

        collection = self.vector_db.collection
        if collection is None:
            print("Error: Vector database collection is not connected.")
            return False, None

        # Normalize file path for consistent comparison
        normalized_path = os.path.normpath(file_path)

        # Query for documents with the same file path
        try:
            results = collection.get(
                where={"file_path": normalized_path}
            )

            if results and results["ids"]:
                return True, results["ids"][0]

            # Try with case-insensitive comparison (for case-insensitive filesystems)
            # ChromaDB doesn't support case-insensitive search directly, so we need to
            # get all documents and filter manually
            all_docs = collection.get(include=['metadatas'])

            if all_docs and all_docs["metadatas"]:
                for i, metadata in enumerate(all_docs["metadatas"]):
                    if "file_path" in metadata:
                        db_file_path = metadata.get("file_path")
                        if isinstance(db_file_path, str):
                            db_path = os.path.normpath(db_file_path)
                            if db_path.lower() == normalized_path.lower():
                                return True, all_docs["ids"][i]

            return False, None
        except Exception as e:
            print(f"Error checking for duplicate by path: {e}")
            return False, None

    def is_duplicate_by_metadata(
        self,
        metadata: Dict[str, Any],
        title_similarity_threshold: float = 90
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a document is a duplicate by metadata, including fuzzy title matching.

        Args:
            metadata: Document metadata
            title_similarity_threshold: Threshold for fuzzy title matching (0-100)

        Returns:
            Tuple of (is_duplicate, existing_doc_id)
        """
        # Ensure vector database is connected
        if self.vector_db.collection is None:
            self.vector_db.connect()

        collection = self.vector_db.collection
        if collection is None:
            print("Error: Vector database collection is not connected.")
            return False, None

        # Check for key metadata fields that would indicate a duplicate
        title = metadata.get("title")
        author = metadata.get("author")

        if not title or not isinstance(title, str):
            return False, None

        # Query for documents with the same title and author
        try:
            # First try exact match on title and author if available
            if author and isinstance(author, str):
                results = collection.get(
                    where={"title": title, "author": author}
                )

                if results and results["ids"]:
                    return True, results["ids"][0]

            # Try with just title
            results = collection.get(
                where={"title": title}
            )

            if results and results["ids"]:
                return True, results["ids"][0]

            # Try with lowercase title (ChromaDB doesn't support case-insensitive search directly)
            # We'll use the lowercase fields we added in optimize_metadata
            title_lower = metadata.get("title_lower")
            if title_lower and isinstance(title_lower, str):
                 results = collection.get(
                    where={"title_lower": title_lower}
                )

                 if results and results["ids"]:
                    return True, results["ids"][0]


            # Implement fuzzy matching on titles for existing documents
            # Retrieve a limited number of documents to check for fuzzy title matches
            # In a large database, this might need optimization (e.g., indexing titles)
            all_docs = collection.get(
                 include=['metadatas']
            )

            if all_docs and all_docs["metadatas"]:
                for i, existing_metadata in enumerate(all_docs["metadatas"]):
                    existing_title = existing_metadata.get("title")
                    if isinstance(existing_title, str):
                        similarity = fuzz.ratio(title.lower(), existing_title.lower())
                        if similarity >= title_similarity_threshold:
                            print(f"Potential duplicate (fuzzy title match): '{title}' similar to '{existing_title}' with score {similarity}")
                            return True, all_docs["ids"][i]

            return False, None
        except Exception as e:
            print(f"Error checking for duplicate by metadata: {e}")
            return False, None

    def generate_document_hash(self, text: str) -> str:
        """
        Generate a hash based on document content.

        Args:
            text: Document text

        Returns:
            Hash of the text
        """
        # Normalize text by removing whitespace and converting to lowercase
        normalized_text = re.sub(r'\s+', ' ', text).strip().lower()

        # Compute SHA-256 hash
        return hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()

    def is_duplicate_by_content(
        self,
        doc_hash: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a document is a duplicate by content hash stored in metadata.

        Args:
            doc_hash: The SHA-256 hash of the document content.

        Returns:
            Tuple of (is_duplicate, existing_doc_id)
        """
        # Ensure vector database is connected
        if self.vector_db.collection is None:
            self.vector_db.connect()

        collection = self.vector_db.collection
        if collection is None:
            print("Error: Vector database collection is not connected.")
            return False, None

        # Query for existing documents with the same hash in metadata
        try:
            results = collection.get(
                where={"hash": doc_hash},
                include=['metadatas']
            )

            if results and results["ids"]:
                # Found a document with the same hash
                return True, results["ids"][0]

            return False, None
        except Exception as e:
            print(f"Error checking for duplicate by content hash: {e}")
            return False, None

    def is_duplicate(
        self,
        text: str,
        metadata: Dict[str, Any],
        title_similarity_threshold: float = 90
    ) -> Tuple[bool, Optional[str], str]:
        """
        Check if a document is a duplicate using multiple methods:
        1. File path (exact match)
        2. Metadata (exact title/author, exact title, lowercase title, fuzzy title)
        3. Content hash

        Args:
            text: Document text
            metadata: Document metadata

        Returns:
            Tuple of (is_duplicate, existing_doc_id, method)
        """
        # Check by file path first (fastest)
        if "file_path" in metadata:
            file_path = metadata.get("file_path")
            if isinstance(file_path, str):
                is_dup, doc_id = self.is_duplicate_by_path(file_path)
                if is_dup:
                    return True, doc_id, "file_path"

        # Then check by metadata
        is_dup, doc_id = self.is_duplicate_by_metadata(metadata, title_similarity_threshold)
        if is_dup:
            return True, doc_id, "metadata"

        # Finally, check by content hash
        doc_hash = self.generate_document_hash(text)
        is_dup, doc_id = self.is_duplicate_by_content(doc_hash)
        if is_dup:
            return True, doc_id, "content_hash"

        return False, None, "none"
