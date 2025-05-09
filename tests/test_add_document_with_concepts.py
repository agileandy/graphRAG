"""
Test script for the modified add_document_with_concepts.py
"""
import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase
from scripts.add_document_with_concepts import add_document_to_graphrag

def main():
    """
    Main function to test adding a document with concepts.
    """
    print("Initializing databases...")

    # Initialize databases with Docker container connection details
    neo4j_db = Neo4jDatabase(
        uri="bolt://localhost:7688",
        username="neo4j",
        password="graphrag"
    )
    vector_db = VectorDatabase()

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
    GraphRAG: Enhancing Retrieval-Augmented Generation with Knowledge Graphs

    Retrieval-Augmented Generation (RAG) is a technique that enhances Large Language Models (LLMs)
    by retrieving relevant information from external knowledge sources before generating responses.

    GraphRAG extends traditional RAG by incorporating graph databases like Neo4j alongside vector
    databases such as ChromaDB. This hybrid approach allows for more contextual understanding by
    capturing relationships between concepts, not just semantic similarity.

    Key concepts in GraphRAG include:
    1. Knowledge Graphs - Storing relationships between entities
    2. Vector Embeddings - Numerical representations of text for semantic search
    3. Hybrid Search - Combining graph traversal with vector similarity
    4. Deduplication - Ensuring unique concepts despite different references

    GraphRAG provides more comprehensive and accurate responses by leveraging both the structured
    relationships in graphs and the semantic understanding from vector embeddings.
    """

    # Document metadata with explicit concepts
    document_metadata = {
        "title": "GraphRAG and RAG Concepts",
        "author": "Test Script",
        "source": "Test Document",
        "concepts": "RAG,GraphRAG,Knowledge Graphs,Vector Embeddings,Hybrid Search,Deduplication,LLM"
    }

    # Add document to GraphRAG system
    print("\nAdding document to GraphRAG system...")
    result = add_document_to_graphrag(
        text=document_text,
        metadata=document_metadata,
        neo4j_db=neo4j_db,
        vector_db=vector_db
    )

    # Display results
    print("\nDocument added with ID:", result["document_id"])
    print("\nExtracted entities:")
    for entity in result["entities"]:
        print(f"  - {entity['name']} (ID: {entity['id']})")

    print("\nExtracted relationships:")
    for source_id, target_id, strength in result["relationships"]:
        print(f"  - {source_id} -> {target_id} (Strength: {strength})")

    # Query Neo4j for all concepts
    print("\nVerifying concepts in Neo4j:")
    query = """
    MATCH (c:Concept)
    RETURN c.id AS id, c.name AS name
    """
    concepts = neo4j_db.run_query(query)

    for concept in concepts:
        print(f"  - {concept['name']} (ID: {concept['id']})")

    # Close Neo4j connection
    neo4j_db.close()

    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
