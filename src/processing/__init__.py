"""
Processing module for GraphRAG project.

This module provides utilities for processing documents, extracting entities,
and optimizing data for the GraphRAG system.
"""

from src.processing.document_processor import (
    smart_chunk_text,
    batch_process_documents,
    optimize_metadata,
    process_document_with_metadata,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_OVERLAP,
    DEFAULT_BATCH_SIZE
)

__all__ = [
    'smart_chunk_text',
    'batch_process_documents',
    'optimize_metadata',
    'process_document_with_metadata',
    'DEFAULT_CHUNK_SIZE',
    'DEFAULT_OVERLAP',
    'DEFAULT_BATCH_SIZE'
]
