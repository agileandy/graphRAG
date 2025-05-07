"""
Duplicate detection for GraphRAG project.

This module provides utilities for detecting duplicate documents
in the GraphRAG system, particularly for PDFs and other document types.
"""
import os
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
import re

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
        
        # Normalize file path for consistent comparison
        normalized_path = os.path.normpath(file_path)
        
        # Query for documents with the same file path
        try:
            results = self.vector_db.collection.get(
                where={"file_path": normalized_path}
            )
            
            if results and results["ids"]:
                return True, results["ids"][0]
            
            # Try with case-insensitive comparison (for case-insensitive filesystems)
            # ChromaDB doesn't support case-insensitive search directly, so we need to
            # get all documents and filter manually
            all_docs = self.vector_db.collection.get()
            
            if all_docs and all_docs["metadatas"]:
                for i, metadata in enumerate(all_docs["metadatas"]):
                    if "file_path" in metadata:
                        db_path = os.path.normpath(metadata["file_path"])
                        if db_path.lower() == normalized_path.lower():
                            return True, all_docs["ids"][i]
            
            return False, None
        except Exception as e:
            print(f"Error checking for duplicate by path: {e}")
            return False, None

    def is_duplicate_by_metadata(
        self, 
        metadata: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a document is a duplicate by metadata.

        Args:
            metadata: Document metadata

        Returns:
            Tuple of (is_duplicate, existing_doc_id)
        """
        # Ensure vector database is connected
        if self.vector_db.collection is None:
            self.vector_db.connect()
        
        # Check for key metadata fields that would indicate a duplicate
        title = metadata.get("title")
        author = metadata.get("author")
        
        if not title:
            return False, None
        
        # Query for documents with the same title and author
        try:
            # First try exact match on title and author if available
            if author:
                results = self.vector_db.collection.get(
                    where={"title": title, "author": author}
                )
                
                if results and results["ids"]:
                    return True, results["ids"][0]
            
            # Try with just title
            results = self.vector_db.collection.get(
                where={"title": title}
            )
            
            if results and results["ids"]:
                return True, results["ids"][0]
            
            # Try with lowercase title (ChromaDB doesn't support case-insensitive search directly)
            # We'll use the lowercase fields we added in optimize_metadata
            if "title_lower" in metadata:
                results = self.vector_db.collection.get(
                    where={"title_lower": metadata["title_lower"]}
                )
                
                if results and results["ids"]:
                    return True, results["ids"][0]
            
            return False, None
        except Exception as e:
            print(f"Error checking for duplicate by metadata: {e}")
            return False, None

    def compute_text_hash(self, text: str) -> str:
        """
        Compute a hash of the text content.

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
        text: str,
        threshold: float = 0.9
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a document is a duplicate by content.

        Args:
            text: Document text
            threshold: Similarity threshold (0.0 to 1.0)

        Returns:
            Tuple of (is_duplicate, existing_doc_id)
        """
        # Ensure vector database is connected
        if self.vector_db.collection is None:
            self.vector_db.connect()
        
        # Compute hash of the text
        text_hash = self.compute_text_hash(text)
        
        # For exact content matching, we would need to store the hash in metadata
        # This is a limitation of the current implementation
        # Instead, we'll use vector similarity search
        
        # Query for similar documents
        try:
            results = self.vector_db.collection.query(
                query_texts=[text],
                n_results=5
            )
            
            if results and results["documents"] and results["documents"][0]:
                # Check similarity of the top result
                # This is a simple approach - in a production system, you might
                # want to use more sophisticated similarity metrics
                top_doc = results["documents"][0][0]
                
                # Compute similarity based on the hash
                top_doc_hash = self.compute_text_hash(top_doc)
                
                # Simple similarity metric: ratio of matching characters in the hash
                # This is just an approximation - real systems would use better metrics
                matching_chars = sum(1 for a, b in zip(text_hash, top_doc_hash) if a == b)
                similarity = matching_chars / len(text_hash)
                
                if similarity >= threshold:
                    return True, results["ids"][0][0]
            
            return False, None
        except Exception as e:
            print(f"Error checking for duplicate by content: {e}")
            return False, None

    def is_duplicate(
        self, 
        text: str, 
        metadata: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], str]:
        """
        Check if a document is a duplicate using multiple methods.

        Args:
            text: Document text
            metadata: Document metadata

        Returns:
            Tuple of (is_duplicate, existing_doc_id, method)
        """
        # Check by file path first (fastest)
        if "file_path" in metadata:
            is_dup, doc_id = self.is_duplicate_by_path(metadata["file_path"])
            if is_dup:
                return True, doc_id, "file_path"
        
        # Then check by metadata
        is_dup, doc_id = self.is_duplicate_by_metadata(metadata)
        if is_dup:
            return True, doc_id, "metadata"
        
        # Finally, check by content (slowest)
        is_dup, doc_id = self.is_duplicate_by_content(text)
        if is_dup:
            return True, doc_id, "content"
        
        return False, None, "none"
