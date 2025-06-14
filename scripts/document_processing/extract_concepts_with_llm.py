#!/usr/bin/env python3
"""Script to extract concepts from documents using LLM.

This script:
1. Retrieves documents from the vector database
2. Extracts concepts using LLM
3. Analyzes relationships between concepts
4. Adds concepts and relationships to the graph database
"""

import argparse
import json
import logging
import os
import sys
from typing import Any

from tqdm import tqdm

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.graph_db import GraphDatabase
from src.database.vector_db import VectorDatabase
from src.llm.concept_extraction import (
    analyze_concept_relationships,
    extract_concepts_two_pass,
    summarize_text_with_llm,
)
from src.llm.llm_provider import LLMManager, create_llm_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_llm_config(config_path: str = None) -> dict[str, Any]:
    """Load LLM configuration from file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    """
    # Default config path
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config", "llm_config.json"
        )

    try:
        with open(config_path) as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading LLM config: {e}")
        # Return default config
        return {
            "primary_provider": {
                "type": "openai-compatible",
                "api_base": "http://192.168.1.21:1234/v1",
                "api_key": "dummy-key",
                "model": "lmstudio-community/Phi-4-mini-reasoning-MLX-4bit",
                "temperature": 0.1,
                "max_tokens": 1000,
                "timeout": 60,
            }
        }


def setup_llm_manager(config: dict[str, Any]) -> LLMManager:
    """Set up LLM manager from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        LLM manager instance

    """
    # Create primary provider
    primary_config = config.get("primary_provider", {})
    try:
        primary_provider = create_llm_provider(primary_config)
        logger.info(
            f"Created primary provider: {primary_config.get('type')} with model {primary_config.get('model')}"
        )
    except Exception as e:
        logger.error(f"Error creating primary provider: {e}")
        primary_provider = None

    # Create fallback provider if configured
    fallback_provider = None
    if "fallback_provider" in config:
        fallback_config = config.get("fallback_provider", {})
        try:
            fallback_provider = create_llm_provider(fallback_config)
            logger.info(
                f"Created fallback provider: {fallback_config.get('type')} with model {fallback_config.get('model')}"
            )
        except Exception as e:
            logger.error(f"Error creating fallback provider: {e}")

    # Create LLM manager
    return LLMManager(primary_provider, fallback_provider)


def process_documents_with_llm(
    collection_name: str,
    limit: int,
    llm_manager: LLMManager,
    batch_size: int = 10,
    min_text_length: int = 100,
    chunk_size: int = 3000,
    chunk_overlap: int = 500,
) -> dict[str, Any]:
    """Process documents with LLM for concept extraction.

    Args:
        collection_name: Name of the collection to process
        limit: Maximum number of documents to process
        llm_manager: LLM manager instance
        batch_size: Number of documents to process in each batch
        min_text_length: Minimum text length to process

    Returns:
        Dictionary with statistics

    """
    # Initialize databases
    vector_db = VectorDatabase()
    graph_db = GraphDatabase()

    # Connect to databases
    vector_db.connect()
    graph_db.connect()

    # Get documents from vector database
    logger.info(f"Retrieving documents from collection '{collection_name}'...")

    # Connect to the collection
    vector_db.connect(collection_name)

    # For simplicity, we'll use a dummy query to get documents
    # This approach should work with most vector database implementations
    logger.info(f"Querying up to {limit} documents from collection '{collection_name}'")

    try:
        # Use a dummy query to get documents
        documents = vector_db.query(
            query_texts=[""],  # Empty query to get random documents
            n_results=limit,
        )
    except Exception as e:
        logger.error(f"Error querying documents: {e}")
        documents = []

    if not documents:
        logger.warning(f"No documents found in collection '{collection_name}'")
        return {
            "documents_processed": 0,
            "concepts_extracted": 0,
            "relationships_added": 0,
        }

    logger.info(f"Retrieved {len(documents)} documents")

    # Statistics
    stats = {
        "documents_processed": 0,
        "concepts_extracted": 0,
        "relationships_added": 0,
        "concepts_per_document": {},
        "concept_frequencies": {},
    }

    # Process documents in batches
    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        logger.info(
            f"Processing batch {i // batch_size + 1}/{(len(documents) + batch_size - 1) // batch_size}"
        )

        for doc in tqdm(batch, desc=f"Batch {i // batch_size + 1}"):
            doc_id = doc.get("id")
            doc.get("metadata", {}).get("title", "Unknown")
            doc_text = doc.get("text", "")

            if not doc_text or len(doc_text) < min_text_length:
                logger.warning(
                    f"Document {doc_id} has insufficient text ({len(doc_text)} chars), skipping"
                )
                continue

            # Extract concepts from document using two-pass approach
            try:
                # Get existing concepts from the graph database to provide context
                existing_concepts = []
                try:
                    # Get top concepts from the database to provide context
                    concept_count = graph_db.get_concept_count()
                    if concept_count > 0:
                        # Query for some existing concepts to provide context
                        query = """
                        MATCH (c:Concept)
                        RETURN c.id AS id, c.name AS name, c.type AS type, c.description AS description
                        ORDER BY rand()
                        LIMIT 20
                        """
                        existing_concepts = graph_db.neo4j_db.run_query(query)
                        logger.info(
                            f"Retrieved {len(existing_concepts)} existing concepts for context"
                        )
                except Exception as e:
                    logger.warning(f"Error retrieving existing concepts: {e}")

                # Use the two-pass approach for concept extraction with configurable chunk size and overlap
                concepts = extract_concepts_two_pass(
                    document_text=doc_text,
                    llm_manager=llm_manager,
                    chunk_size=chunk_size,
                    overlap=chunk_overlap,
                )

                if not concepts:
                    logger.warning(f"No concepts extracted from document {doc_id}")
                    continue

                logger.info(
                    f"Extracted {len(concepts)} concepts from document {doc_id}"
                )

                # Add concepts to graph database
                for concept in concepts:
                    concept_name = concept.get("name", "")
                    concept_type = concept.get("type", "CONCEPT")
                    concept_description = concept.get("description", "")

                    if not concept_name:
                        continue

                    # Update statistics
                    stats["concepts_extracted"] += 1
                    stats["concept_frequencies"][concept_name] = (
                        stats["concept_frequencies"].get(concept_name, 0) + 1
                    )

                    # Add concept to graph database
                    concept_node = graph_db.add_concept(
                        concept_name,
                        properties={
                            "type": concept_type,
                            "description": concept_description,
                        },
                    )

                    if concept_node:
                        # Add relationship between concept and document
                        graph_db.add_document_concept_relationship(
                            doc_id, concept_node["id"]
                        )

                # Process relationships from the two-pass extraction
                relationships = []
                for concept in concepts:
                    if "relationships" in concept:
                        for rel in concept.get("relationships", []):
                            relationships.append(
                                {
                                    "source": concept["name"],
                                    "target": rel["target"],
                                    "type": rel["type"],
                                    "strength": rel["strength"],
                                    "description": rel["description"],
                                }
                            )

                # If no relationships were found in the concepts, analyze them separately
                if not relationships:
                    relationships = analyze_concept_relationships(
                        concepts, llm_manager, existing_concepts
                    )

                if relationships:
                    logger.info(
                        f"Adding {len(relationships)} relationships for document {doc_id}"
                    )

                    # Add relationships to graph database
                    for rel in relationships:
                        source = rel.get("source", "")
                        target = rel.get("target", "")
                        rel_type = rel.get("type", "RELATED_TO")
                        strength = rel.get("strength", 0.5)
                        description = rel.get("description", "")

                        if not source or not target:
                            continue

                        # Add relationship to graph database
                        graph_db.add_concept_relationship(
                            source,
                            target,
                            rel_type,
                            properties={
                                "strength": strength,
                                "description": description,
                            },
                        )

                        stats["relationships_added"] += 1

                # Generate summary if needed
                if len(doc_text) > 1000:
                    try:
                        summary = summarize_text_with_llm(doc_text, llm_manager)

                        if summary:
                            # Log the summary but don't try to update the document
                            # This avoids compatibility issues with different vector database implementations
                            logger.info(
                                f"Generated summary for document {doc_id}: {summary[:100]}..."
                            )

                            # Store the summary in the graph database instead
                            # This is more reliable than trying to update the vector database
                            try:
                                # Update document properties in Neo4j
                                query = """
                                MATCH (d:Document {id: $doc_id})
                                SET d.summary = $summary
                                RETURN d.id
                                """
                                graph_db.neo4j_db.run_query(
                                    query, {"doc_id": doc_id, "summary": summary}
                                )
                                logger.info(
                                    f"Stored summary in graph database for document {doc_id}"
                                )
                            except Exception as e:
                                logger.warning(
                                    f"Could not store summary in graph database: {e}"
                                )
                    except Exception as e:
                        logger.warning(
                            f"Error generating summary for document {doc_id}: {e}"
                        )

                # Update statistics
                stats["documents_processed"] += 1
                stats["concepts_per_document"][doc_id] = len(concepts)

            except Exception as e:
                logger.error(f"Error processing document {doc_id}: {e}")

    # Calculate average concepts per document
    if stats["documents_processed"] > 0:
        stats["avg_concepts_per_document"] = (
            sum(stats["concepts_per_document"].values()) / stats["documents_processed"]
        )
    else:
        stats["avg_concepts_per_document"] = 0

    # Get top concepts
    stats["top_concepts"] = sorted(
        stats["concept_frequencies"].items(), key=lambda x: x[1], reverse=True
    )[:20]

    return stats


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Extract concepts from documents using LLM with enhanced relationship identification"
    )
    parser.add_argument(
        "--collection", type=str, default="documents", help="Collection name"
    )
    parser.add_argument(
        "--limit", type=int, default=10, help="Maximum number of documents to process"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="Number of documents to process in each batch",
    )
    parser.add_argument("--config", type=str, help="Path to LLM configuration file")
    parser.add_argument(
        "--min-text-length",
        type=int,
        default=100,
        help="Minimum text length to process",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=3000,
        help="Size of each chunk in characters for two-pass extraction",
    )
    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=500,
        help="Overlap between chunks in characters for two-pass extraction",
    )

    args = parser.parse_args()

    print(
        f"Extracting concepts with enhanced semantic relationships from documents in collection '{args.collection}'..."
    )
    print(f"Processing up to {args.limit} documents in batches of {args.batch_size}")
    print(
        f"Using two-pass approach with chunk size {args.chunk_size} and overlap {args.chunk_overlap}"
    )

    # Load configuration
    config = load_llm_config(args.config)

    # Set up LLM manager
    llm_manager = setup_llm_manager(config)

    # Process documents
    stats = process_documents_with_llm(
        collection_name=args.collection,
        limit=args.limit,
        llm_manager=llm_manager,
        batch_size=args.batch_size,
        min_text_length=args.min_text_length,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
    )

    # Print statistics
    print("\nExtraction Statistics:")
    print(f"Documents processed: {stats['documents_processed']}")
    print(f"Concepts extracted: {stats['concepts_extracted']}")
    print(f"Relationships added: {stats['relationships_added']}")
    print(
        f"Average concepts per document: {stats.get('avg_concepts_per_document', 0):.2f}"
    )

    print("\nTop 20 Concepts:")
    for concept, frequency in stats.get("top_concepts", []):
        print(f"  - {concept}: {frequency}")


if __name__ == "__main__":
    main()
