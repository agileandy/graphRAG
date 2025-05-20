"""Simple demonstration of adding a document to the GraphRAG system and querying it."""

import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.add_document import add_document_to_graphrag
from src.database.db_linkage import DatabaseLinkage
from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase


def main() -> None:
    """Main function to demonstrate adding a document and querying it."""
    print("Initializing databases...")

    # Initialize databases
    neo4j_db = Neo4jDatabase()
    vector_db = VectorDatabase()
    db_linkage = DatabaseLinkage(neo4j_db, vector_db)

    # Verify connections
    if not neo4j_db.verify_connection():
        print("❌ Neo4j connection failed!")
        return

    if not vector_db.verify_connection():
        print("❌ Vector database connection failed!")
        return

    print("✅ Database connections verified!")

    # Example document
    document_text = """
    GraphRAG: Enhancing Large Language Models with Knowledge Graphs

    GraphRAG is an innovative approach that combines Retrieval-Augmented Generation (RAG)
    with knowledge graphs to enhance the capabilities of Large Language Models (LLMs).
    Traditional RAG systems rely solely on vector embeddings to retrieve relevant information,
    which can miss important semantic relationships between concepts.

    By incorporating knowledge graphs, GraphRAG explicitly represents the relationships
    between entities and concepts, enabling more sophisticated retrieval that considers
    the semantic structure of the information. This approach is particularly valuable for
    complex domains where understanding the relationships between concepts is crucial.

    The key components of a GraphRAG system include:

    1. Vector Database: Stores text embeddings for efficient similarity search
    2. Knowledge Graph: Represents entities and their relationships
    3. Hybrid Retrieval: Combines vector similarity with graph traversal
    4. Large Language Model: Generates responses based on retrieved context

    GraphRAG can significantly improve the accuracy and relevance of LLM responses by
    providing both textual context and structural knowledge about the relationships
    between concepts.
    """

    # Document metadata
    document_metadata = {
        "title": "GraphRAG: Enhancing LLMs with Knowledge Graphs",
        "author": "AI Researcher",
        "category": "AI",
        "source": "Example",
    }

    # Add document to GraphRAG system
    print("\nAdding document to GraphRAG system...")
    result = add_document_to_graphrag(
        text=document_text,
        metadata=document_metadata,
        neo4j_db=neo4j_db,
        vector_db=vector_db,
    )

    print("\nDocument added successfully!")
    print(f"Document ID: {result['doc_id']}")
    print(
        f"Extracted entities: {', '.join(entity['name'] for entity in result['entities'])}"
    )
    print(f"Created relationships: {len(result['relationships'])}")

    # Perform a hybrid search
    print("\nPerforming hybrid search...")
    search_query = "How does GraphRAG improve on traditional RAG systems?"
    search_results = db_linkage.hybrid_search(
        query_text=search_query, n_vector_results=2, max_graph_hops=2
    )

    # Display search results
    print(f"\nSearch query: '{search_query}'")
    print("\nVector results:")
    for i, doc in enumerate(search_results["vector_results"]["documents"]):
        print(f"  {i + 1}. {doc[:200]}...")

    print("\nGraph results:")
    for i, result in enumerate(search_results["graph_results"]):
        print(f"  {i + 1}. {result['name']} (Score: {result['relevance_score']})")

    # Close Neo4j connection
    neo4j_db.close()

    print("\n✅ Demo completed successfully!")
    print("\nNext steps:")
    print(
        "1. Try adding more documents with 'python scripts/batch_process.py --create-examples'"
    )
    print(
        "2. Process the example documents with 'python scripts/batch_process.py --dir ./example_docs'"
    )
    print("3. Query the system interactively with 'python scripts/query_graphrag.py'")


if __name__ == "__main__":
    main()
