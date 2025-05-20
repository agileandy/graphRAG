#!/usr/bin/env python3
"""Script to query the Neo4j and ChromaDB databases in the GraphRAG system."""

import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the current directory to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    # Import required modules
    from src.database.neo4j_db import Neo4jDatabase
    from src.database.vector_db import VectorDatabase
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.info("Make sure you're running this script from the project root directory")
    sys.exit(1)


def query_neo4j() -> None:
    """Query Neo4j database for node and relationship counts."""
    neo4j_db = Neo4jDatabase()

    # Check connection
    if not neo4j_db.verify_connection():
        logger.error("Failed to connect to Neo4j database")
        return

    logger.info(f"Successfully connected to Neo4j at {neo4j_db.uri}")

    try:
        # Get node count
        result = neo4j_db.run_query("MATCH (n) RETURN count(n) as count")
        node_count = result[0]["count"]
        logger.info(f"Total nodes in Neo4j: {node_count}")

        # Get node counts by label
        result = neo4j_db.run_query(
            "MATCH (n) RETURN labels(n) as label, count(*) as count"
        )
        logger.info("Node counts by label:")
        for row in result:
            label = row["label"][0] if row["label"] else "No Label"
            count = row["count"]
            logger.info(f"  - {label}: {count}")

        # Get relationship count
        result = neo4j_db.run_query("MATCH ()-[r]->() RETURN count(r) as count")
        rel_count = result[0]["count"]
        logger.info(f"Total relationships in Neo4j: {rel_count}")

        # Get relationship counts by type
        result = neo4j_db.run_query(
            "MATCH ()-[r]->() RETURN type(r) as type, count(*) as count"
        )
        logger.info("Relationship counts by type:")
        for row in result:
            rel_type = row["type"]
            count = row["count"]
            logger.info(f"  - {rel_type}: {count}")

        # Get sample concepts
        result = neo4j_db.run_query("MATCH (c:Concept) RETURN c.name as name LIMIT 10")
        logger.info("Sample concepts:")
        for row in result:
            logger.info(f"  - {row['name']}")

    finally:
        # Close connection
        neo4j_db.close()


def query_chromadb() -> None:
    """Query ChromaDB for document counts and sample documents."""
    vector_db = VectorDatabase()

    # Check connection
    if not vector_db.verify_connection():
        logger.error("Failed to connect to ChromaDB")
        return

    logger.info(f"Successfully connected to ChromaDB at {vector_db.persist_directory}")

    try:
        # Get document count
        count = vector_db.count()
        logger.info(f"Total documents in ChromaDB: {count}")

        # Get sample documents
        if count > 0:
            results = vector_db.get(limit=5)

            logger.info("Sample documents:")
            for i, doc_id in enumerate(results.get("ids", [])):
                metadata = results.get("metadatas", [])[i]
                title = metadata.get("title", "Untitled")
                author = metadata.get("author", "Unknown")
                logger.info(f"  - {title} by {author} (ID: {doc_id})")

    except Exception as e:
        logger.error(f"Error querying ChromaDB: {e}")


def main() -> None:
    """Main function."""
    logger.info("Querying Neo4j database...")
    query_neo4j()

    logger.info("\nQuerying ChromaDB database...")
    query_chromadb()


if __name__ == "__main__":
    main()
