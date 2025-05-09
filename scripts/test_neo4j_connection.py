#!/usr/bin/env python3
"""
Script to test Neo4j database connection.

This script:
1. Connects to the Neo4j database
2. Verifies the connection
3. Creates the schema
4. Creates dummy data
5. Runs some test queries
"""
import sys
import os
import logging
import argparse
from typing import Dict, Any

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.neo4j_db import Neo4jDatabase
from src.database.graph_db import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_neo4j_connection(uri: str = None, username: str = None, password: str = None) -> bool:
    """
    Test Neo4j database connection.
    
    Args:
        uri: Neo4j URI
        username: Neo4j username
        password: Neo4j password
        
    Returns:
        True if connection is successful, False otherwise
    """
    # Create Neo4j database instance
    neo4j_db = Neo4jDatabase(uri, username, password)
    
    # Connect to database
    try:
        neo4j_db.connect()
        logger.info("Connected to Neo4j database")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j database: {e}")
        return False
    
    # Verify connection
    if neo4j_db.verify_connection():
        logger.info("Neo4j connection verified")
    else:
        logger.error("Failed to verify Neo4j connection")
        return False
    
    # Close connection
    neo4j_db.close()
    logger.info("Neo4j connection closed")
    
    return True

def test_graph_database(uri: str = None, username: str = None, password: str = None) -> bool:
    """
    Test GraphDatabase wrapper.
    
    Args:
        uri: Neo4j URI
        username: Neo4j username
        password: Neo4j password
        
    Returns:
        True if tests pass, False otherwise
    """
    # Create GraphDatabase instance
    graph_db = GraphDatabase(uri, username, password)
    
    # Connect to database
    try:
        graph_db.connect()
        logger.info("Connected to graph database")
    except Exception as e:
        logger.error(f"Failed to connect to graph database: {e}")
        return False
    
    # Verify connection
    if graph_db.verify_connection():
        logger.info("Graph database connection verified")
    else:
        logger.error("Failed to verify graph database connection")
        return False
    
    # Create schema
    try:
        graph_db.create_schema()
        logger.info("Created graph database schema")
    except Exception as e:
        logger.error(f"Failed to create graph database schema: {e}")
        return False
    
    # Clear database
    try:
        graph_db.clear_database()
        logger.info("Cleared graph database")
    except Exception as e:
        logger.error(f"Failed to clear graph database: {e}")
        return False
    
    # Create dummy data
    try:
        graph_db.neo4j_db.create_dummy_data()
        logger.info("Created dummy data")
    except Exception as e:
        logger.error(f"Failed to create dummy data: {e}")
        return False
    
    # Test adding a concept
    try:
        concept = graph_db.add_concept("Machine Learning", {
            "type": "TECHNOLOGY",
            "description": "A field of AI that enables systems to learn from data"
        })
        logger.info(f"Added concept: {concept}")
    except Exception as e:
        logger.error(f"Failed to add concept: {e}")
        return False
    
    # Test adding a document
    try:
        document = graph_db.add_document("doc-test", {
            "title": "Test Document",
            "author": "Test Author",
            "source": "Test Source"
        })
        logger.info(f"Added document: {document}")
    except Exception as e:
        logger.error(f"Failed to add document: {e}")
        return False
    
    # Test adding a relationship
    try:
        relationship = graph_db.add_document_concept_relationship(
            document["id"],
            concept["id"],
            "MENTIONS",
            {"weight": 0.8}
        )
        logger.info(f"Added relationship: {relationship}")
    except Exception as e:
        logger.error(f"Failed to add relationship: {e}")
        return False
    
    # Test getting concepts by name
    try:
        concepts = graph_db.get_concept_by_name("Machine")
        logger.info(f"Found {len(concepts)} concepts by name")
        for c in concepts:
            logger.info(f"  - {c.get('name')}")
    except Exception as e:
        logger.error(f"Failed to get concepts by name: {e}")
        return False
    
    # Test getting related concepts
    try:
        related_concepts = graph_db.get_related_concepts(concept["id"])
        logger.info(f"Found {len(related_concepts)} related concepts")
        for c in related_concepts:
            logger.info(f"  - {c.get('name')}")
    except Exception as e:
        logger.error(f"Failed to get related concepts: {e}")
        return False
    
    # Test getting documents by concept
    try:
        documents = graph_db.get_documents_by_concept(concept["id"])
        logger.info(f"Found {len(documents)} documents by concept")
        for d in documents:
            logger.info(f"  - {d.get('title')}")
    except Exception as e:
        logger.error(f"Failed to get documents by concept: {e}")
        return False
    
    # Get counts
    try:
        concept_count = graph_db.get_concept_count()
        document_count = graph_db.get_document_count()
        relationship_count = graph_db.get_relationship_count()
        logger.info(f"Counts: {concept_count} concepts, {document_count} documents, {relationship_count} relationships")
    except Exception as e:
        logger.error(f"Failed to get counts: {e}")
        return False
    
    # Close connection
    graph_db.close()
    logger.info("Graph database connection closed")
    
    return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test Neo4j database connection")
    parser.add_argument("--uri", type=str, help="Neo4j URI")
    parser.add_argument("--username", type=str, help="Neo4j username")
    parser.add_argument("--password", type=str, help="Neo4j password")
    parser.add_argument("--test-type", type=str, choices=["connection", "graph", "all"], default="all", help="Test type")
    
    args = parser.parse_args()
    
    if args.test_type in ["connection", "all"]:
        print("\nTesting Neo4j connection...")
        if test_neo4j_connection(args.uri, args.username, args.password):
            print("✅ Neo4j connection test passed")
        else:
            print("❌ Neo4j connection test failed")
    
    if args.test_type in ["graph", "all"]:
        print("\nTesting GraphDatabase wrapper...")
        if test_graph_database(args.uri, args.username, args.password):
            print("✅ GraphDatabase test passed")
        else:
            print("❌ GraphDatabase test failed")

if __name__ == "__main__":
    main()
