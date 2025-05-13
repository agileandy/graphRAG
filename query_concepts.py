#!/usr/bin/env python3
"""
Script to query concepts in the Neo4j database.
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

def find_concepts(query: str, limit: int = 10):
    """
    Find concepts in Neo4j that match the query.
    
    Args:
        query: Search query
        limit: Maximum number of results to return
    """
    # Initialize Neo4j database
    neo4j_db = Neo4jDatabase()
    
    # Check connection
    if not neo4j_db.verify_connection():
        logger.error("Failed to connect to Neo4j database")
        return
    
    logger.info(f"Searching for concepts matching: '{query}'")
    
    try:
        # Find concepts by name (case-insensitive)
        cypher_query = """
        MATCH (c:Concept)
        WHERE toLower(c.name) CONTAINS toLower($query)
        RETURN c.id AS id, c.name AS name, c.type AS type, c.description AS description
        ORDER BY size(c.name) ASC
        LIMIT $limit
        """
        
        results = neo4j_db.run_query(cypher_query, {"query": query, "limit": limit})
        
        if not results:
            logger.info(f"No concepts found matching '{query}'")
            return
        
        logger.info(f"Found {len(results)} concepts matching '{query}':")
        
        for i, result in enumerate(results):
            concept_id = result.get("id", "Unknown")
            name = result.get("name", "Unknown")
            concept_type = result.get("type", "Concept")
            description = result.get("description", "")
            
            logger.info(f"\nConcept {i+1}: {name}")
            logger.info(f"  ID: {concept_id}")
            logger.info(f"  Type: {concept_type}")
            
            if description:
                logger.info(f"  Description: {description}")
            
            # Find related concepts
            related_query = """
            MATCH (c:Concept {id: $concept_id})-[r:RELATED_TO]-(related:Concept)
            RETURN related.id AS id, related.name AS name, r.strength AS strength
            ORDER BY r.strength DESC
            LIMIT 5
            """
            
            related_results = neo4j_db.run_query(related_query, {"concept_id": concept_id})
            
            if related_results:
                logger.info("  Related concepts:")
                
                for j, related in enumerate(related_results):
                    related_name = related.get("name", "Unknown")
                    strength = related.get("strength", 0)
                    
                    logger.info(f"    - {related_name} (Strength: {strength:.2f})")
    
    finally:
        # Close Neo4j connection
        neo4j_db.close()

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Query concepts in the Neo4j database")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument("--limit", "-n", type=int, default=10, help="Maximum number of results to return")
    args = parser.parse_args()
    
    find_concepts(args.query, args.limit)

if __name__ == "__main__":
    main()
