#!/usr/bin/env python3
"""Script to check relationship types in Neo4j."""

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
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.info("Make sure you're running this script from the project root directory")
    sys.exit(1)


def check_relationship_types() -> None:
    """Check relationship types in Neo4j."""
    # Initialize Neo4j database
    neo4j_db = Neo4jDatabase()

    # Check connection
    if not neo4j_db.verify_connection():
        logger.error("Failed to connect to Neo4j database")
        return

    logger.info(f"Successfully connected to Neo4j at {neo4j_db.uri}")

    try:
        # Get relationship counts by type
        query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(*) as count
        ORDER BY count DESC
        """

        results = neo4j_db.run_query(query)

        logger.info("Relationship counts by type:")
        for row in results:
            rel_type = row["type"]
            count = row["count"]
            logger.info(f"  - {rel_type}: {count}")

        # Get relationship strength distribution
        query = """
        MATCH ()-[r]->()
        WHERE r.strength IS NOT NULL
        RETURN
            CASE
                WHEN r.strength <= 0.3 THEN 'Low (0.0-0.3)'
                WHEN r.strength <= 0.6 THEN 'Medium (0.3-0.6)'
                WHEN r.strength <= 0.9 THEN 'High (0.6-0.9)'
                ELSE 'Very High (0.9-1.0)'
            END as strength_range,
            count(*) as count
        ORDER BY
            CASE strength_range
                WHEN 'Low (0.0-0.3)' THEN 1
                WHEN 'Medium (0.3-0.6)' THEN 2
                WHEN 'High (0.6-0.9)' THEN 3
                WHEN 'Very High (0.9-1.0)' THEN 4
            END
        """

        results = neo4j_db.run_query(query)

        logger.info("\nRelationship strength distribution:")
        for row in results:
            strength_range = row["strength_range"]
            count = row["count"]
            logger.info(f"  - {strength_range}: {count}")

        # Get sample relationships for each type
        query = """
        MATCH (c1:Concept)-[r]->(c2:Concept)
        RETURN type(r) as type, c1.name as source, c2.name as target, r.strength as strength
        ORDER BY type, r.strength DESC
        LIMIT 20
        """

        results = neo4j_db.run_query(query)

        logger.info("\nSample relationships:")
        current_type = None
        for row in results:
            rel_type = row["type"]
            source = row["source"]
            target = row["target"]
            strength = row["strength"]

            if rel_type != current_type:
                logger.info(f"\n  {rel_type}:")
                current_type = rel_type

            logger.info(f"    - {source} -> {target} (Strength: {strength:.2f})")

        # Check for concept reuse across documents
        query = """
        MATCH (d1:Document)-[:MENTIONS]->(c:Concept)<-[:MENTIONS]-(d2:Document)
        WHERE d1.id < d2.id
        RETURN c.name as concept, count(DISTINCT d1) as document_count
        ORDER BY document_count DESC
        LIMIT 10
        """

        results = neo4j_db.run_query(query)

        logger.info("\nConcepts shared across documents:")
        for row in results:
            concept = row["concept"]
            doc_count = row["document_count"]
            logger.info(f"  - {concept}: mentioned in {doc_count} documents")

    finally:
        # Close Neo4j connection
        neo4j_db.close()


if __name__ == "__main__":
    check_relationship_types()
