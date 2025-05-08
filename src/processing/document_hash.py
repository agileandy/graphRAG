"""
Document hashing and fingerprinting utilities for deduplication.
"""
import hashlib
import re
import logging
from typing import Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def generate_document_hash(document_text: str) -> str:
    """
    Generate a hash based on document content.
    
    Args:
        document_text: The text content of the document
        
    Returns:
        SHA-256 hash of the normalized document text
    """
    # Normalize text (remove whitespace, convert to lowercase)
    normalized_text = re.sub(r'\s+', ' ', document_text).lower().strip()
    
    # Generate SHA-256 hash
    return hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()

def generate_metadata_hash(metadata: Dict[str, Any]) -> str:
    """
    Generate a hash based on document metadata.
    
    Args:
        metadata: Document metadata
        
    Returns:
        SHA-256 hash of the normalized metadata
    """
    # Extract key fields for hashing
    hash_fields = {}
    
    # Include title if available
    if 'title' in metadata and metadata['title']:
        hash_fields['title'] = str(metadata['title']).lower().strip()
    
    # Include author if available
    if 'author' in metadata and metadata['author']:
        hash_fields['author'] = str(metadata['author']).lower().strip()
    
    # Include ISBN if available
    if 'isbn' in metadata and metadata['isbn']:
        hash_fields['isbn'] = str(metadata['isbn']).strip().replace('-', '')
    
    # Include file path if available
    if 'file_path' in metadata and metadata['file_path']:
        hash_fields['file_path'] = str(metadata['file_path']).strip()
    
    # If we have no fields to hash, return None
    if not hash_fields:
        return None
    
    # Create a string representation of the hash fields
    hash_str = '|'.join([f"{k}:{v}" for k, v in sorted(hash_fields.items())])
    
    # Generate SHA-256 hash
    return hashlib.sha256(hash_str.encode('utf-8')).hexdigest()

def enrich_metadata_with_hashes(
    metadata: Dict[str, Any], 
    document_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Enrich document metadata with hash values for deduplication.
    
    Args:
        metadata: Document metadata
        document_text: Document text (optional)
        
    Returns:
        Enriched metadata with hash values
    """
    # Create a copy of the metadata
    enriched = metadata.copy()
    
    # Add metadata hash
    metadata_hash = generate_metadata_hash(metadata)
    if metadata_hash:
        enriched['metadata_hash'] = metadata_hash
    
    # Add content hash if document text is provided
    if document_text:
        enriched['content_hash'] = generate_document_hash(document_text)
    
    return enriched

def calculate_title_similarity(title1: str, title2: str) -> float:
    """
    Calculate similarity between two document titles.
    
    Args:
        title1: First title
        title2: Second title
        
    Returns:
        Similarity score between 0 and 100
    """
    from fuzzywuzzy import fuzz
    
    # Normalize titles
    t1 = title1.lower().strip()
    t2 = title2.lower().strip()
    
    # Calculate similarity
    return fuzz.ratio(t1, t2)

def is_likely_duplicate(
    text: str, 
    metadata: Dict[str, Any],
    collection,
    title_similarity_threshold: float = 90
) -> Tuple[bool, Optional[str], str]:
    """
    Check if a document is likely a duplicate using multiple methods.
    
    Args:
        text: Document text
        metadata: Document metadata
        collection: ChromaDB collection
        title_similarity_threshold: Threshold for title similarity (0-100)
        
    Returns:
        Tuple of (is_duplicate, existing_doc_id, method)
    """
    # Enrich metadata with hashes
    enriched_metadata = enrich_metadata_with_hashes(metadata, text)
    
    # Check by content hash
    if 'content_hash' in enriched_metadata:
        try:
            results = collection.get(
                where={"content_hash": enriched_metadata['content_hash']},
                limit=1
            )
            
            if results and results["ids"] and len(results["ids"]) > 0:
                logger.info(f"Duplicate detected by content hash: {enriched_metadata.get('title', 'Untitled')}")
                return True, results["ids"][0], "content_hash"
        except Exception as e:
            logger.warning(f"Error checking content hash: {e}")
    
    # Check by metadata hash
    if 'metadata_hash' in enriched_metadata:
        try:
            results = collection.get(
                where={"metadata_hash": enriched_metadata['metadata_hash']},
                limit=1
            )
            
            if results and results["ids"] and len(results["ids"]) > 0:
                logger.info(f"Duplicate detected by metadata hash: {enriched_metadata.get('title', 'Untitled')}")
                return True, results["ids"][0], "metadata_hash"
        except Exception as e:
            logger.warning(f"Error checking metadata hash: {e}")
    
    # Check by file path
    if 'file_path' in metadata and metadata['file_path']:
        file_path = metadata['file_path']
        try:
            results = collection.get(
                where={"file_path": file_path},
                limit=1
            )
            
            if results and results["ids"] and len(results["ids"]) > 0:
                logger.info(f"Duplicate detected by file path: {file_path}")
                return True, results["ids"][0], "file_path"
        except Exception as e:
            logger.warning(f"Error checking file path: {e}")
    
    # Check by title similarity
    if 'title' in metadata and metadata['title']:
        title = metadata['title']
        try:
            # Get all documents (this could be optimized for large collections)
            all_docs = collection.get(include=['metadatas'])
            
            if all_docs and all_docs["metadatas"]:
                for i, doc_metadata in enumerate(all_docs["metadatas"]):
                    if 'title' in doc_metadata and doc_metadata['title']:
                        similarity = calculate_title_similarity(title, doc_metadata['title'])
                        if similarity >= title_similarity_threshold:
                            logger.info(
                                f"Potential duplicate detected by title similarity ({similarity}%): "
                                f"{title} vs {doc_metadata['title']}"
                            )
                            return True, all_docs["ids"][i], "title_similarity"
        except Exception as e:
            logger.warning(f"Error checking title similarity: {e}")
    
    # No duplicate found
    return False, None, "none"

if __name__ == "__main__":
    # Example usage
    text = "This is a sample document for testing the hashing functions."
    metadata = {
        "title": "Sample Document",
        "author": "Test Author",
        "file_path": "/path/to/sample.pdf"
    }
    
    content_hash = generate_document_hash(text)
    metadata_hash = generate_metadata_hash(metadata)
    
    print(f"Content hash: {content_hash}")
    print(f"Metadata hash: {metadata_hash}")
    
    enriched = enrich_metadata_with_hashes(metadata, text)
    print(f"Enriched metadata: {enriched}")
