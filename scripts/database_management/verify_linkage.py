"""Script to verify database linkage between Neo4j and vector database."""

import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.db_linkage import DatabaseLinkage
from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase


def main() -> bool:
    """Verify database linkage between Neo4j and vector database."""
    print("Verifying database linkage...")

    # Create database instances
    neo4j_db = Neo4jDatabase()
    vector_db = VectorDatabase()

    # Verify connections
    print("\nVerifying Neo4j connection...")
    if not neo4j_db.verify_connection():
        print("❌ Neo4j connection failed!")
        return False

    print("\nVerifying vector database connection...")
    if not vector_db.verify_connection():
        print("❌ Vector database connection failed!")
        return False

    # Create database linkage
    db_linkage = DatabaseLinkage(neo4j_db, vector_db)

    # Test hybrid search
    print("\nTesting hybrid search...")
    try:
        results = db_linkage.hybrid_search(
            "neural networks", n_vector_results=2, max_graph_hops=2
        )

        print("\nVector results:")
        for i, doc in enumerate(results["vector_results"]["documents"]):
            print(f"  {i + 1}. {doc[:100]}...")

        print("\nGraph results:")
        for i, result in enumerate(results["graph_results"]):
            print(f"  {i + 1}. {result['name']} (Score: {result['relevance_score']})")

        print("\n✅ Hybrid search successful!")
    except Exception as e:
        print(f"❌ Failed to run hybrid search: {e}")
        return False

    # Test getting node chunks
    print("\nTesting get_node_chunks...")
    try:
        chunks = db_linkage.get_node_chunks("concept-001", "Concept")

        print(f"\nFound {len(chunks['ids'])} chunks for Concept 'concept-001':")
        for i, doc in enumerate(chunks["documents"]):
            print(f"  {i + 1}. {doc[:100]}...")

        print("\n✅ get_node_chunks successful!")
    except Exception as e:
        print(f"❌ Failed to get node chunks: {e}")
        return False

    # Test getting related nodes
    print("\nTesting get_related_nodes...")
    try:
        nodes = db_linkage.get_related_nodes("chunk-concept-001")

        print(f"\nFound {len(nodes)} nodes related to chunk 'chunk-concept-001':")
        for i, node in enumerate(nodes):
            print(f"  {i + 1}. {node['type']}: {node['id']} - {node['name']}")

        print("\n✅ get_related_nodes successful!")
    except Exception as e:
        print(f"❌ Failed to get related nodes: {e}")
        return False

    # Close Neo4j connection
    neo4j_db.close()

    print("\n✅ Database linkage verification completed successfully!")
    return True


if __name__ == "__main__":
    main()
