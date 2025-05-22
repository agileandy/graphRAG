"""Script to query the GraphRAG system.

This script demonstrates how to:
1. Perform a hybrid search using both vector and graph databases
2. Explore the knowledge graph
3. Retrieve related documents
"""

import argparse
import os
import sys
from typing import Any

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.db_linkage import DatabaseLinkage
from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase


def hybrid_search(
    query: str, db_linkage: DatabaseLinkage, n_results: int = 3, max_hops: int = 2
) -> dict[str, Any]:
    """Perform a hybrid search using both vector and graph databases.

    Args:
        query: Search query
        db_linkage: Database linkage instance
        n_results: Number of vector results to return
        max_hops: Maximum number of hops in the graph

    Returns:
        Search results

    """
    print(f"Searching for: '{query}'")

    # Perform hybrid search
    results = db_linkage.hybrid_search(
        query_text=query, n_vector_results=n_results, max_graph_hops=max_hops
    )

    # Display vector results
    print("\nVector Results:")
    print("---------------")
    for i, doc in enumerate(results["vector_results"]["documents"]):
        metadata = results["vector_results"]["metadatas"][i]
        print(f"{i + 1}. {metadata.get('title', 'Untitled')}")
        print(f"   Source: {metadata.get('source', 'Unknown')}")

        # Display concepts if available
        if "concept_ids" in metadata:
            concept_ids = metadata["concept_ids"].split(",")
            print(f"   Concepts: {', '.join(concept_ids)}")
        elif "concept_id" in metadata:
            print(f"   Primary Concept: {metadata['concept_id']}")

        print(f"   {doc[:200]}...")
        print()

    # Display graph results
    print("\nGraph Results (Related Concepts):")
    print("--------------------------------")
    for i, result in enumerate(results["graph_results"]):
        print(f"{i + 1}. {result['name']} (Relevance: {result['relevance_score']:.2f})")

    return results


def explore_concept(concept_name: str, neo4j_db: Neo4jDatabase) -> list[dict[str, Any]]:
    """Explore a concept in the knowledge graph.

    Args:
        concept_name: Name of the concept to explore
        neo4j_db: Neo4j database instance

    Returns:
        List of related concepts

    """
    print(f"Exploring concept: '{concept_name}'")

    # Find the concept by name (case-insensitive)
    query = """
    MATCH (c:Concept)
    WHERE toLower(c.name) CONTAINS toLower($name)
    RETURN c.id AS id, c.name AS name
    """
    results = neo4j_db.run_query(query, {"name": concept_name})

    if not results:
        print(f"No concept found with name containing '{concept_name}'")
        return []

    # Display found concepts
    print("\nFound concepts:")
    for i, result in enumerate(results):
        print(f"{i + 1}. {result['name']} (ID: {result['id']})")

    # If multiple concepts found, use the first one
    concept_id = results[0]["id"]
    concept_name = results[0]["name"]

    # Find related concepts
    query = """
    MATCH (c:Concept {id: $concept_id})-[r:RELATED_TO]-(related:Concept)
    RETURN related.id AS id, related.name AS name, r.strength AS strength
    ORDER BY r.strength DESC
    """
    related = neo4j_db.run_query(query, {"concept_id": concept_id})

    # Display related concepts
    print(f"\nConcepts related to '{concept_name}':")
    print("----------------------------------")
    for i, result in enumerate(related):
        print(f"{i + 1}. {result['name']} (Strength: {result['strength']:.2f})")

    return related


def get_documents_for_concept(
    concept_name: str, neo4j_db: Neo4jDatabase, vector_db: VectorDatabase
) -> list[dict[str, Any]]:
    """Get documents related to a concept.

    Args:
        concept_name: Name of the concept
        neo4j_db: Neo4j database instance
        vector_db: Vector database instance

    Returns:
        List of related documents

    """
    print(f"Finding documents related to concept: '{concept_name}'")

    # Find the concept by name (case-insensitive)
    query = """
    MATCH (c:Concept)
    WHERE toLower(c.name) CONTAINS toLower($name)
    RETURN c.id AS id, c.name AS name
    """
    results = neo4j_db.run_query(query, {"name": concept_name})

    if not results:
        print(f"No concept found with name containing '{concept_name}'")
        return []

    # If multiple concepts found, use the first one
    concept_id = results[0]["id"]
    concept_name = results[0]["name"]

    # Query vector database for documents related to this concept
    # We need to search in both concept_id and concept_ids fields
    # First, try the primary concept_id field
    results_primary = vector_db.get(where={"concept_id": concept_id})

    # Then, try to find in the comma-separated concept_ids field
    # ChromaDB doesn't support substring search in metadata, so we'll use a workaround
    # by getting all documents and filtering them in Python
    all_docs = vector_db.get()

    # Filter documents that have the concept_id in their concept_ids field
    filtered_ids = []
    filtered_docs = []
    filtered_metadatas = []

    if all_docs.get("ids"):
        for i, doc_id in enumerate(all_docs["ids"]):
            metadata = all_docs["metadatas"][i]
            if "concept_ids" in metadata:
                concept_ids = metadata["concept_ids"].split(",")
                if concept_id in concept_ids:
                    filtered_ids.append(doc_id)
                    filtered_docs.append(all_docs["documents"][i])
                    filtered_metadatas.append(metadata)

    # Combine results
    results = {
        "ids": results_primary.get("ids", []) + filtered_ids,
        "documents": results_primary.get("documents", []) + filtered_docs,
        "metadatas": results_primary.get("metadatas", []) + filtered_metadatas,
    }

    # Display related documents
    print(f"\nDocuments related to '{concept_name}':")
    print("----------------------------------")

    if not results.get("ids"):
        print("No documents found.")
        return []

    for i, doc_id in enumerate(results["ids"]):
        doc = results["documents"][i]
        metadata = results["metadatas"][i]
        print(f"{i + 1}. {metadata.get('title', 'Untitled')} (ID: {doc_id})")
        print(f"   Source: {metadata.get('source', 'Unknown')}")
        print(f"   {doc[:200]}...")
        print()

    return results


def main() -> None:
    """Main function to demonstrate querying the GraphRAG system."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Query the GraphRAG system")
    parser.add_argument("--query", "-q", type=str, help="Search query")
    parser.add_argument("--concept", "-c", type=str, help="Concept to explore")
    parser.add_argument("--documents", "-d", type=str, help="Get documents for concept")
    args = parser.parse_args()

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

    # Perform the requested operation
    if args.query:
        hybrid_search(args.query, db_linkage)
    elif args.concept:
        explore_concept(args.concept, neo4j_db)
    elif args.documents:
        get_documents_for_concept(args.documents, neo4j_db, vector_db)
    else:
        # If no arguments provided, run an interactive demo
        while True:
            print("\nGraphRAG Query System")
            print("--------------------")
            print("1. Perform a hybrid search")
            print("2. Explore a concept")
            print("3. Find documents for a concept")
            print("4. Exit")

            choice = input("\nEnter your choice (1-4): ")

            if choice == "1":
                query = input("Enter your search query: ")
                hybrid_search(query, db_linkage)
            elif choice == "2":
                concept = input("Enter concept name: ")
                explore_concept(concept, neo4j_db)
            elif choice == "3":
                concept = input("Enter concept name: ")
                get_documents_for_concept(concept, neo4j_db, vector_db)
            elif choice == "4":
                break
            else:
                print("Invalid choice. Please try again.")

    # Close Neo4j connection
    neo4j_db.close()


if __name__ == "__main__":
    main()
