"""Document processing utilities for GraphRAG project.

This module provides optimized document processing functions for:
1. Smart chunking strategies
2. Batch processing
3. Metadata optimization
4. Adaptive chunk sizing
5. Document hashing for deduplication
"""

import logging
import re
import uuid
from typing import Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default chunking parameters
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_OVERLAP = 200
DEFAULT_BATCH_SIZE = 100
# Adaptive chunking parameters
VERY_LARGE_DOC_THRESHOLD = 1000000  # > 1MB
LARGE_DOC_THRESHOLD = 500000  # > 0.5MB
SMALL_CHUNK_SIZE = 500
MEDIUM_CHUNK_SIZE = 750


def smart_chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    semantic_boundaries: bool = True,
) -> list[str]:
    """Split text into overlapping chunks using semantic boundaries.

    Args:
        text: Text to chunk
        chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters
        semantic_boundaries: Whether to use semantic boundaries (paragraphs, sentences)

    Returns:
        List of text chunks

    """
    chunks = []

    # Clean text: normalize whitespace while preserving paragraph breaks
    # First, ensure consistent line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace multiple spaces with a single space, but preserve paragraph breaks
    text = re.sub(r"([^\n])\s+([^\n])", r"\1 \2", text)

    # Normalize paragraph breaks (multiple newlines become exactly two newlines)
    text = re.sub(r"\n\s*\n\s*", "\n\n", text)

    # Ensure text doesn't start or end with excessive whitespace
    text = text.strip()

    if semantic_boundaries:
        # First try to split by paragraphs (double line breaks)
        paragraphs = re.split(r"\n\s*\n", text)

        # Handle very large paragraphs by splitting them further
        processed_paragraphs = []
        for paragraph in paragraphs:
            # If paragraph is too large, split it into sentences
            if len(paragraph) > chunk_size:
                logger.info(
                    f"Splitting large paragraph of size {len(paragraph)} into sentences"
                )
                # Split by sentence boundaries
                sentences = re.split(r"(?<=[.!?])\s+", paragraph)
                processed_paragraphs.extend(sentences)
            else:
                processed_paragraphs.append(paragraph)

        # Now process the paragraphs/sentences
        current_chunk = ""
        current_paragraphs = []

        for paragraph in processed_paragraphs:
            # If this paragraph alone exceeds chunk size, we need to split it
            if len(paragraph) > chunk_size:
                # If we have content in the current chunk, save it first
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                    current_paragraphs = []

                # Split the large paragraph by character
                logger.info(
                    f"Paragraph of size {len(paragraph)} exceeds chunk size {chunk_size}, splitting by character"
                )
                for i in range(0, len(paragraph), chunk_size - overlap):
                    if i + chunk_size >= len(paragraph):
                        chunks.append(paragraph[i:].strip())
                    else:
                        chunks.append(paragraph[i : i + chunk_size].strip())
                continue

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

            chunks.append(text[i : i + chunk_size].strip())

    return chunks


def batch_process_documents(
    documents: list[str],
    metadatas: list[dict[str, Any]],
    ids: list[str] | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> list[tuple[list[str], list[dict[str, Any]], list[str]]]:
    """Split documents into batches for efficient processing.

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
        batch_docs = documents[i : i + batch_size]
        batch_meta = metadatas[i : i + batch_size]
        batch_ids = ids[i : i + batch_size]

        batches.append((batch_docs, batch_meta, batch_ids))

    return batches


def optimize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Optimize metadata for efficient filtering in vector database.

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
    for key in ["title", "name", "category", "author"]:
        if key in optimized and isinstance(optimized[key], str):
            optimized[f"{key}_lower"] = optimized[key].lower()

    return optimized


def optimize_chunk_size(
    document_text: str,
    default_size: int = DEFAULT_CHUNK_SIZE,
    very_large_doc_threshold: int = VERY_LARGE_DOC_THRESHOLD,
    large_doc_threshold: int = LARGE_DOC_THRESHOLD,
    small_chunk_size: int = SMALL_CHUNK_SIZE,
    medium_chunk_size: int = MEDIUM_CHUNK_SIZE,
) -> int:
    """Determine optimal chunk size based on document characteristics.

    This function implements adaptive chunk sizing based on:
    1. Document length - longer documents get smaller chunks
    2. Content complexity - more complex content gets smaller chunks

    Args:
        document_text: The text content of the document
        default_size: Default chunk size for normal documents
        very_large_doc_threshold: Threshold for very large documents (chars)
        large_doc_threshold: Threshold for large documents (chars)
        small_chunk_size: Chunk size for very large documents
        medium_chunk_size: Chunk size for large documents

    Returns:
        Optimized chunk size in characters

    """
    # Get document length
    doc_length = len(document_text)

    # Base size adjustment on document length
    if doc_length > very_large_doc_threshold:
        base_size = small_chunk_size  # Smaller chunks for very large documents
    elif doc_length > large_doc_threshold:
        base_size = medium_chunk_size  # Medium chunks for large documents
    else:
        base_size = default_size  # Use default for smaller documents

    # Further adjust based on content complexity
    # Check for complex content indicators
    has_tables = bool(re.search(r"\|\s*-+\s*\|", document_text))  # Markdown tables
    has_code_blocks = bool(re.search(r"```[\s\S]*?```", document_text))  # Code blocks
    has_lists = bool(re.search(r"^\s*[*\-+]\s+", document_text, re.MULTILINE))  # Lists

    # Adjust size based on content complexity
    complexity_factor = 1.0
    if has_tables:
        complexity_factor *= 0.8  # Reduce size for documents with tables
    if has_code_blocks:
        complexity_factor *= 0.9  # Reduce size for documents with code blocks
    if has_lists:
        complexity_factor *= 0.95  # Slight reduction for documents with lists

    # Apply complexity factor
    adjusted_size = int(base_size * complexity_factor)

    # Ensure size is within reasonable bounds
    min_size = 250
    max_size = 2000
    final_size = max(min_size, min(adjusted_size, max_size))

    return final_size


def process_document_with_metadata(
    text: str,
    metadata: dict[str, Any],
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    """Process a document with metadata into optimized chunks.

    Args:
        text: Document text
        metadata: Document metadata
        chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters

    Returns:
        Tuple of (chunks, chunk_metadatas, chunk_ids)

    """
    # Create a unique ID for the document if not provided
    doc_id = metadata.get("doc_id", f"doc-{uuid.uuid4()}")

    # Determine the optimal chunk size based on document text length
    optimized_chunk_size = optimize_chunk_size(text, chunk_size)

    # Smart chunk the text using the optimized size
    chunks = smart_chunk_text(text, optimized_chunk_size, overlap)

    # Create metadata and IDs for each chunk
    chunk_metadatas = []
    chunk_ids = []

    # Add content hash to metadata if not already present
    from src.processing.document_hash import (
        enrich_metadata_with_hashes,
        generate_document_hash,
    )

    # Enrich the document metadata with hashes for deduplication
    enriched_metadata = enrich_metadata_with_hashes(metadata, text)

    for i, chunk in enumerate(chunks):
        # Create a unique ID for the chunk
        chunk_id = f"{doc_id}-chunk-{i}"

        # Create metadata for the chunk
        chunk_metadata = enriched_metadata.copy()
        chunk_metadata.update(
            {
                "doc_id": doc_id,
                "chunk_id": chunk_id,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "chunk_size": len(chunk),
                "chunk_hash": generate_document_hash(chunk),
            }
        )

        # Optimize metadata
        optimized_metadata = optimize_metadata(chunk_metadata)

        chunk_metadatas.append(optimized_metadata)
        chunk_ids.append(chunk_id)

    return chunks, chunk_metadatas, chunk_ids
