#!/usr/bin/env python3
"""
Script to perform a hybrid search in the GraphRAG system.
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
    from src.database.vector_db import VectorDatabase
    from src.database.db_linkage import DatabaseLinkage
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.info("Make sure you're running this script from the project root directory")
    sys.exit(1)

def hybrid_search(query: str, n_results: int = 5, max_hops: int = 2):
    """
    Perform a hybrid search using both vector and graph databases.
    
    Args:
        query: Search query
        n_results: Number of vector results to return
        max_hops: Maximum number of hops in the graph
    """
    # Initialize databases
    neo4j_db = Neo4jDatabase()
    vector_db = VectorDatabase()
    db_linkage = DatabaseLinkage(neo4j_db, vector_db)
    
    # Check connections
    if not neo4j_db.verify_connection():
        logger.error("Failed to connect to Neo4j database")
        return
    
    if not vector_db.verify_connection():
        logger.error("Failed to connect to ChromaDB")
        return
    
    logger.info(f"Performing hybrid search for: '{query}'")
    
    try:
        # Perform hybrid search
        results = db_linkage.hybrid_search(
            query_text=query,
            n_vector_results=n_results,
            max_graph_hops=max_hops
        )
        
        # Display vector results
        logger.info("\nVector Search Results:")
        vector_results = results.get("vector_results", {})
        
        ids = vector_results.get("ids", [])
        documents = vector_results.get("documents", [])
        metadatas = vector_results.get("metadatas", [])
        distances = vector_results.get("distances", [])
        
        for i in range(min(len(ids), n_results)):
            doc_id = ids[i]
            metadata = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else None
            
            title = metadata.get("title", "Untitled")
            author = metadata.get("author", "Unknown")
            
            logger.info(f"Document {i+1}: {title} by {author}")
            logger.info(f"  ID: {doc_id}")
            logger.info(f"  Relevance: {1 - distance if distance is not None else 'N/A'}")
            
            # Display a snippet of the document
            document = documents[i] if i < len(documents) else ""
            snippet = document[:200] + "..." if len(document) > 200 else document
            logger.info(f"  Snippet: {snippet}")
            logger.info("")
        
        # Display graph results
        logger.info("\nGraph Search Results:")
        graph_results = results.get("graph_results", [])
        
        for i, result in enumerate(graph_results[:n_results]):
            name = result.get("name", "Unknown")
            relevance = result.get("relevance_score", 0)
            
            logger.info(f"Concept {i+1}: {name}")
            logger.info(f"  Relevance: {relevance}")
            
            # Display related concepts
            related_concepts = result.get("related_concepts", [])
            if related_concepts:
                logger.info("  Related concepts:")
                for j, related in enumerate(related_concepts[:5]):
                    related_name = related.get("name", "Unknown")
                    related_strength = related.get("strength", 0)
                    logger.info(f"    - {related_name} (Strength: {related_strength:.2f})")
            
            logger.info("")
    
    finally:
        # Close Neo4j connection
        neo4j_db.close()

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Perform a hybrid search in the GraphRAG system")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument("--results", "-n", type=int, default=5, help="Number of results to return")
    parser.add_argument("--hops", type=int, default=2, help="Maximum number of hops in the graph")
    args = parser.parse_args()
    
    hybrid_search(args.query, args.results, args.hops)

if __name__ == "__main__":
    main()
