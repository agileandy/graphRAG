"""
Processing module for GraphRAG project.

This module provides utilities for processing documents, extracting entities,
optimizing data, managing background jobs, and detecting duplicates for the GraphRAG system.
"""

from src.processing.document_processor import (
    smart_chunk_text,
    batch_process_documents,
    optimize_metadata,
    optimize_chunk_size,
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

from src.processing.document_hash import (
    generate_document_hash,
    generate_metadata_hash,
    enrich_metadata_with_hashes,
    calculate_title_similarity,
    is_likely_duplicate
)

from src.processing.concept_extractor import (
    ConceptExtractor
)

__all__ = [
    # Document processing
    'smart_chunk_text',
    'batch_process_documents',
    'optimize_metadata',
    'optimize_chunk_size',
    'process_document_with_metadata',
    'DEFAULT_CHUNK_SIZE',
    'DEFAULT_OVERLAP',
    'DEFAULT_BATCH_SIZE',

    # Job management
    'JobManager',
    'JobStatus',
    'Job',

    # Duplicate detection
    'DuplicateDetector',
    
    # Document hashing
    'generate_document_hash',
    'generate_metadata_hash',
    'enrich_metadata_with_hashes',
    'calculate_title_similarity',
    'is_likely_duplicate',
    
    # Concept extraction
    'ConceptExtractor'
]
