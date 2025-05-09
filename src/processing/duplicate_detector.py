"""
Duplicate detection for GraphRAG documents.

This module provides functionality to detect duplicate documents in the GraphRAG system.
"""
import hashlib
from typing import Dict, Any, Tuple, Optional

from src.database.vector_db import VectorDatabase

class DuplicateDetector:
    """
    Class for detecting duplicate documents in the GraphRAG system.
    """
    
    def __init__(self, vector_db: VectorDatabase):
        """
        Initialize the DuplicateDetector.
        
        Args:
            vector_db: Vector database instance
        """
        self.vector_db = vector_db
    
    def generate_document_hash(self, text: str) -> str:
        """
        Generate a hash for a document text.
        
        Args:
            text: Document text
            
        Returns:
            Document hash
        """
        # Normalize the text by removing whitespace and converting to lowercase
        normalized_text = "".join(text.lower().split())
        
        # Generate a SHA-256 hash
        return hashlib.sha256(normalized_text.encode()).hexdigest()
    
    def is_duplicate(self, text: str, metadata: Dict[str, Any]) -> Tuple[bool, Optional[str], str]:
        """
        Check if a document is a duplicate.
        
        Args:
            text: Document text
            metadata: Document metadata
            
        Returns:
            Tuple of (is_duplicate, existing_doc_id, method)
        """
        # Check by hash if provided in metadata
        doc_hash = metadata.get("hash")
        if not doc_hash:
            doc_hash = self.generate_document_hash(text)
        
        # Query the vector database for documents with the same hash
        results = self.vector_db.get(
            where={"hash": doc_hash}
        )
        
        if results and results.get("ids") and len(results["ids"]) > 0:
            return True, results["ids"][0], "hash"
        
        # If no hash match, check by title if available
        title = metadata.get("title")
        if title:
            results = self.vector_db.get(
                where={"title": title}
            )
            
            if results and results.get("ids") and len(results["ids"]) > 0:
                return True, results["ids"][0], "title"
        
        # No duplicates found
        return False, None, "none"