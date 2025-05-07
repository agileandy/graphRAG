"""
Document processing utilities for GraphRAG project.

This module provides optimized document processing functions for:
1. Smart chunking strategies
2. Batch processing
3. Metadata optimization
"""
import os
import re
import uuid
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

# Default chunking parameters
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_OVERLAP = 200
DEFAULT_BATCH_SIZE = 100

def smart_chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    semantic_boundaries: bool = True
) -> List[str]:
    """
    Split text into overlapping chunks using semantic boundaries.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters
        semantic_boundaries: Whether to use semantic boundaries (paragraphs, sentences)
        
    Returns:
        List of text chunks
    """
    chunks = []
    
    # Clean text: normalize whitespace and line breaks
    text = re.sub(r'\s+', ' ', text)
    
    if semantic_boundaries:
        # First try to split by paragraphs (double line breaks)
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = ""
        current_paragraphs = []
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk size, save current chunk and start a new one
            if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                
                # Start new chunk with overlap from the end of the previous chunk
                if len(current_chunk) > overlap:
                    # Find a good paragraph boundary for the overlap
                    overlap_size = 0
                    overlap_paragraphs = []
                    
                    # Work backwards through paragraphs to find a good overlap point
                    for p in reversed(current_paragraphs):
                        if overlap_size + len(p) <= overlap:
                            overlap_paragraphs.insert(0, p)
                            overlap_size += len(p)
                        else:
                            break
                    
                    current_chunk = " ".join(overlap_paragraphs) + " "
                    current_paragraphs = overlap_paragraphs.copy()
                else:
                    current_chunk = ""
                    current_paragraphs = []
            
            current_chunk += paragraph + " "
            current_paragraphs.append(paragraph)
        
        # Add the last chunk if it's not empty
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
    else:
        # Simple chunking by character count
        for i in range(0, len(text), chunk_size - overlap):
            # Don't start a new chunk if we're near the end
            if i + chunk_size >= len(text):
                if i > 0:  # Only add the last chunk if it's not the only chunk
                    chunks.append(text[i:].strip())
                break
            
            chunks.append(text[i:i + chunk_size].strip())
    
    return chunks

def batch_process_documents(
    documents: List[str],
    metadatas: List[Dict[str, Any]],
    ids: Optional[List[str]] = None,
    batch_size: int = DEFAULT_BATCH_SIZE
) -> List[Tuple[List[str], List[Dict[str, Any]], List[str]]]:
    """
    Split documents into batches for efficient processing.
    
    Args:
        documents: List of document texts
        metadatas: List of document metadata
        ids: List of document IDs (optional)
        batch_size: Number of documents per batch
        
    Returns:
        List of batches, each containing (documents, metadatas, ids)
    """
    # Generate IDs if not provided
    if ids is None:
        ids = [f"doc-{uuid.uuid4()}" for _ in range(len(documents))]
    
    # Split into batches
    batches = []
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i + batch_size]
        batch_meta = metadatas[i:i + batch_size]
        batch_ids = ids[i:i + batch_size]
        
        batches.append((batch_docs, batch_meta, batch_ids))
    
    return batches

def optimize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimize metadata for efficient filtering in vector database.
    
    Args:
        metadata: Original metadata
        
    Returns:
        Optimized metadata
    """
    optimized = {}
    
    # Copy all original metadata
    for key, value in metadata.items():
        # Convert lists to comma-separated strings (ChromaDB limitation)
        if isinstance(value, list):
            optimized[key] = ",".join(str(v) for v in value)
        # Convert nested dictionaries to flattened keys
        elif isinstance(value, dict):
            for nested_key, nested_value in value.items():
                flat_key = f"{key}_{nested_key}"
                if isinstance(nested_value, list):
                    optimized[flat_key] = ",".join(str(v) for v in nested_value)
                else:
                    optimized[flat_key] = nested_value
        else:
            optimized[key] = value
    
    # Add searchable lowercase versions of key text fields
    for key in ['title', 'name', 'category', 'author']:
        if key in optimized and isinstance(optimized[key], str):
            optimized[f"{key}_lower"] = optimized[key].lower()
    
    return optimized

def process_document_with_metadata(
    text: str,
    metadata: Dict[str, Any],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP
) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
    """
    Process a document with metadata into optimized chunks.
    
    Args:
        text: Document text
        metadata: Document metadata
        chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters
        
    Returns:
        Tuple of (chunks, chunk_metadatas, chunk_ids)
    """
    # Create a unique ID for the document if not provided
    doc_id = metadata.get('doc_id', f"doc-{uuid.uuid4()}")
    
    # Smart chunk the text
    chunks = smart_chunk_text(text, chunk_size, overlap)
    
    # Create metadata and IDs for each chunk
    chunk_metadatas = []
    chunk_ids = []
    
    for i, chunk in enumerate(chunks):
        # Create a unique ID for the chunk
        chunk_id = f"{doc_id}-chunk-{i}"
        
        # Create metadata for the chunk
        chunk_metadata = metadata.copy()
        chunk_metadata.update({
            'doc_id': doc_id,
            'chunk_id': chunk_id,
            'chunk_index': i,
            'total_chunks': len(chunks)
        })
        
        # Optimize metadata
        optimized_metadata = optimize_metadata(chunk_metadata)
        
        chunk_metadatas.append(optimized_metadata)
        chunk_ids.append(chunk_id)
    
    return chunks, chunk_metadatas, chunk_ids
