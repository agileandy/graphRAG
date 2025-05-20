#!/usr/bin/env python3
"""Script to test the GraphRAG system end-to-end.

This script:
1. Resets the databases (Neo4j and ChromaDB)
2. Verifies database connections
3. Adds a test document
4. Performs a search query
5. Displays the results

Usage:
    uv run scripts/test_end_to_end.py
"""

import argparse
import os
import shutil
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from scripts.document_processing.add_document_core import add_document_to_graphrag
    from src.database.db_linkage import DatabaseLinkage
    from src.database.neo4j_db import Neo4jDatabase
    from src.database.vector_db import VectorDatabase
    from src.processing.duplicate_detector import (
        DuplicateDetector,
    )  # Import DuplicateDetector
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Make sure all dependencies are installed:")
    print("  uv pip install neo4j chromadb websockets")
    sys.exit(1)


def reset_chromadb() -> bool | None:
    """Reset the ChromaDB vector database by deleting and recreating the directory."""
    print("\n=== Resetting ChromaDB ===")

    # Initialize vector database to get the persist directory
    vector_db = VectorDatabase()
    persist_dir = vector_db.persist_directory

    # Check if directory exists
    if not os.path.exists(persist_dir):
        print(f"ChromaDB directory not found: {persist_dir}")
        os.makedirs(persist_dir, exist_ok=True)
        print(f"Created new ChromaDB directory: {persist_dir}")
        return True

    # Delete the directory
    print(f"Deleting ChromaDB directory: {persist_dir}")
    try:
        shutil.rmtree(persist_dir)
        print("✅ Successfully deleted ChromaDB directory")

        # Recreate the directory
        os.makedirs(persist_dir, exist_ok=True)
        print("✅ Recreated empty ChromaDB directory")

        return True
    except Exception as e:
        print(f"❌ Failed to delete ChromaDB directory: {e}")
        return False


def reset_neo4j() -> bool:
    """Reset the Neo4j database by deleting all nodes and relationships."""
    print("\n=== Resetting Neo4j ===")

    # Initialize Neo4j database
    neo4j_db = Neo4jDatabase()

    # Verify connection
    if not neo4j_db.verify_connection():
        print("❌ Neo4j connection failed!")
        return False

    # Get node count
    query = "MATCH (n) RETURN count(n) as count"
    result = neo4j_db.run_query_and_return_single(query)
    node_count = result.get("count", 0)

    # Get relationship count
    query = "MATCH ()-[r]->() RETURN count(r) as count"
    result = neo4j_db.run_query_and_return_single(query)
    rel_count = result.get("count", 0)

    print(f"Found {node_count} nodes and {rel_count} relationships in Neo4j")

    # Clear all data
    print("Clearing all data from Neo4j...")
    neo4j_db.run_query("MATCH (n) DETACH DELETE n")

    # Verify deletion
    query = "MATCH (n) RETURN count(n) as count"
    result = neo4j_db.run_query_and_return_single(query)
    new_count = result.get("count", 0)

    if new_count == 0:
        print("✅ Successfully cleared all data from Neo4j")
        neo4j_db.close()
        return True
    else:
        print(f"❌ Failed to clear all data. {new_count} nodes remain.")
        neo4j_db.close()
        return False


def verify_connections() -> bool:
    """Verify database connections."""
    print("\n=== Verifying Database Connections ===")

    # Initialize databases
    neo4j_db = Neo4jDatabase()
    vector_db = VectorDatabase()

    # Verify Neo4j connection
    print("Verifying Neo4j connection...")
    if neo4j_db.verify_connection():
        print("✅ Neo4j connection successful!")
    else:
        print("❌ Neo4j connection failed!")
        return False

    # Verify vector database connection
    print("Verifying vector database connection...")
    if vector_db.verify_connection():
        print("✅ Vector database connection successful!")
    else:
        print("❌ Vector database connection failed!")
        return False

    # Close Neo4j connection
    neo4j_db.close()

    return True


def add_test_document() -> bool | None:
    """Add a test document to the GraphRAG system."""
    print("\n=== Adding Test Document ===")

    # Initialize databases
    neo4j_db = Neo4jDatabase()
    vector_db = VectorDatabase()
    DatabaseLinkage(neo4j_db, vector_db)

    # Verify connections
    if not neo4j_db.verify_connection() or not vector_db.verify_connection():
        print("❌ Database connections failed!")
        return False

    # Test document
    document_text = """
    GraphRAG: Enhancing Large Language Models with Knowledge Graphs

    GraphRAG is an innovative approach that combines Retrieval-Augmented Generation (RAG)
    with knowledge graphs to enhance the capabilities of Large Language Models (LLMs).

    Traditional RAG systems use vector databases to retrieve relevant information based on
    semantic similarity. While effective, this approach lacks the ability to capture
    relationships between concepts.

    GraphRAG addresses this limitation by integrating a knowledge graph (Neo4j) with a
    vector database (ChromaDB). This hybrid approach enables:

    1. Semantic search through vector embeddings
    2. Relationship-aware retrieval through graph traversal
    3. Enhanced context by combining both retrieval methods

    The system extracts entities and relationships from documents, stores them in both
    databases, and provides a unified query interface that leverages the strengths of both
    approaches.

    GraphRAG can significantly improve the accuracy and relevance of LLM responses by
    providing both textual context and structural knowledge about the relationships
    between concepts.
    """

    # Document metadata
    document_metadata = {
        "title": "GraphRAG: Enhancing LLMs with Knowledge Graphs",
        "author": "Test Script",
        "category": "AI",
        "source": "End-to-End Test",
    }

    # Add document to GraphRAG system
    print("Adding document to GraphRAG system...")
    try:
        # Initialize DuplicateDetector
        duplicate_detector = DuplicateDetector(vector_db)

        result = add_document_to_graphrag(
            text=document_text,
            metadata=document_metadata,
            neo4j_db=neo4j_db,
            vector_db=vector_db,
            duplicate_detector=duplicate_detector,  # Add the duplicate_detector argument
        )

        print("\nDocument added successfully!")
        # Check if result is not None before accessing its attributes
        if result:
            print(f"Document ID: {result.get('document_id', 'Unknown')}")
            print(
                f"Extracted entities: {', '.join(entity['name'] for entity in result.get('entities', []))}"
            )
            print(f"Created relationships: {len(result.get('relationships', []))}")

            return True
        else:
            print("❌ Failed to add document or document was a duplicate.")
            return False
    except Exception as e:
        print(f"❌ Failed to add document: {e}")
        return False
    finally:
        # Close Neo4j connection
        neo4j_db.close()


def perform_search() -> bool | None:
    """Perform a search query."""
    print("\n=== Performing Search Query ===")

    # Initialize databases
    neo4j_db = Neo4jDatabase()
    vector_db = VectorDatabase()
    db_linkage = DatabaseLinkage(neo4j_db, vector_db)

    # Verify connections
    if not neo4j_db.verify_connection() or not vector_db.verify_connection():
        print("❌ Database connections failed!")
        return False

    # Perform a hybrid search
    search_query = "How does GraphRAG improve on traditional RAG systems?"
    print(f"Search query: '{search_query}'")

    try:
        search_results = db_linkage.hybrid_search(
            query_text=search_query, n_vector_results=2, max_graph_hops=2
        )

        # Display vector results
        print("\nVector results:")
        for i, doc in enumerate(search_results["vector_results"]["documents"]):
            print(f"  {i + 1}. {doc[:100]}...")

        # Display graph results
        print("\nGraph results:")
        for i, (node, score) in enumerate(search_results["graph_results"]):
            print(f"  {i + 1}. {node} (Score: {score})")

        return True
    except Exception as e:
        print(f"❌ Failed to perform search: {e}")
        return False
    finally:
        # Close Neo4j connection
        neo4j_db.close()


def main() -> int:
    """Main function to test the GraphRAG system end-to-end."""
    parser = argparse.ArgumentParser(description="Test the GraphRAG system end-to-end")
    parser.add_argument("--skip-reset", action="store_true", help="Skip database reset")
    args = parser.parse_args()

    # Track success of each step
    steps_success = {}

    # Step 1: Reset databases
    if not args.skip_reset:
        steps_success["reset_chromadb"] = reset_chromadb()
        steps_success["reset_neo4j"] = reset_neo4j()
    else:
        print("Skipping database reset...")
        steps_success["reset_chromadb"] = True
        steps_success["reset_neo4j"] = True

    # Step 2: Verify connections
    steps_success["verify_connections"] = verify_connections()

    # Step 3: Add test document
    if steps_success["verify_connections"]:
        steps_success["add_test_document"] = add_test_document()
    else:
        steps_success["add_test_document"] = False

    # Step 4: Perform search
    if steps_success["add_test_document"]:
        steps_success["perform_search"] = perform_search()
    else:
        steps_success["perform_search"] = False

    # Print summary
    print("\n=== Test Summary ===")
    for step, success in steps_success.items():
        print(f"{step}: {'✅ Success' if success else '❌ Failed'}")

    # Overall result
    if all(steps_success.values()):
        print("\n✅ End-to-end test completed successfully!")
        print("\nNext steps:")
        print(
            "1. Query the system interactively with 'uv run scripts/query_graphrag.py'"
        )
        print("2. Add your own documents with 'uv run scripts/add_document.py'")
        print("3. Explore the knowledge graph in Neo4j Browser")
        return 0
    else:
        print("\n❌ End-to-end test failed!")
        print("Please check the error messages above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
