"""
Processing module for GraphRAG project.

This module provides utilities for processing documents, extracting entities,
optimizing data, managing background jobs, and detecting duplicates for the GraphRAG system.
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

from src.processing.job_manager import (
    JobManager,
    JobStatus,
    Job
)

from src.processing.duplicate_detector import (
    DuplicateDetector
)

__all__ = [
    # Document processing
    'smart_chunk_text',
    'batch_process_documents',
    'optimize_metadata',
    'process_document_with_metadata',
    'DEFAULT_CHUNK_SIZE',
    'DEFAULT_OVERLAP',
    'DEFAULT_BATCH_SIZE',

    # Job management
    'JobManager',
    'JobStatus',
    'Job',

    # Duplicate detection
    'DuplicateDetector'
]
