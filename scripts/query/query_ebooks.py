"""Script to query and explore the ebook graph.

This script provides specialized queries for exploring the ebook knowledge graph:
1. Find books mentioning a specific concept
2. Find related concepts
3. Find passages about a concept
4. Perform hybrid search across the ebook collection
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


def find_books_by_concept(
    concept_name: str, neo4j_db: Neo4jDatabase
) -> list[dict[str, Any]]:
    """Find books that mention a specific concept.

    Args:
        concept_name: Name of the concept
        neo4j_db: Neo4j database instance

    Returns:
        List of books

    """
    print(f"Finding books mentioning concept: '{concept_name}'")

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

    # Find books mentioning this concept
    query = """
    MATCH (b:Book)-[:MENTIONS]->(c:Concept {id: $concept_id})
    RETURN b.id AS id, b.title AS title, b.filename AS filename
    """
    books = neo4j_db.run_query(query, {"concept_id": concept_id})

    # Display books
    print(f"\nBooks mentioning '{concept_name}':")
    print("=" * 50)

    if not books:
        print("No books found.")
        return []

    for i, book in enumerate(books):
        print(f"{i + 1}. {book['title']}")
        print(f"   Filename: {book['filename']}")
        print()

    return books


def find_related_concepts(
    concept_name: str, neo4j_db: Neo4jDatabase, max_hops: int = 2
) -> list[dict[str, Any]]:
    """Find concepts related to a specific concept.

    Args:
        concept_name: Name of the concept
        neo4j_db: Neo4j database instance
        max_hops: Maximum number of hops in the graph

    Returns:
        List of related concepts

    """
    print(f"Finding concepts related to: '{concept_name}'")

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

    # Find related concepts within max_hops with deduplication in the query
    query = f"""
    MATCH path = (c:Concept {{id: $concept_id}})-[r:RELATED_TO*1..{max_hops}]-(related:Concept)
    WITH related, min(length(path) - 1) as distance,
         max(reduce(s = 0, rel IN relationships(path) | s + coalesce(rel.strength, 0.5))) as relevance_score
    RETURN related.id AS id, related.name AS name,
           distance,
           relevance_score
    ORDER BY distance ASC, relevance_score DESC
    """

    related = neo4j_db.run_query(query, {"concept_id": concept_id})

    # Display related concepts
    print(f"\nConcepts related to '{concept_name}':")
    print("=" * 50)

    if not related:
        print("No related concepts found.")
        return []

    # Group by distance (results are already deduplicated by the query)
    by_distance = {}
    for result in related:
        distance = result["distance"]
        if distance not in by_distance:
            by_distance[distance] = []
        by_distance[distance].append(result)

    # Display by distance
    for distance in sorted(by_distance.keys()):
        print(f"\nDistance {distance}:")
        for i, result in enumerate(by_distance[distance]):
            print(f"{i + 1}. {result['name']} (Score: {result['relevance_score']:.2f})")

    return related


def find_passages_about_concept(
    concept_name: str,
    neo4j_db: Neo4jDatabase,
    vector_db: VectorDatabase,
    limit: int = 5,
) -> dict[str, Any]:
    """Find passages about a specific concept.

    Args:
        concept_name: Name of the concept
        neo4j_db: Neo4j database instance
        vector_db: Vector database instance
        limit: Maximum number of passages to return

    Returns:
        Dictionary with passages information

    """
    print(f"Finding passages about concept: '{concept_name}'")

    # Find the concept by name (case-insensitive)
    query = """
    MATCH (c:Concept)
    WHERE toLower(c.name) CONTAINS toLower($name)
    RETURN c.id AS id, c.name AS name
    """
    results = neo4j_db.run_query(query, {"name": concept_name})

    if not results:
        print(f"No concept found with name containing '{concept_name}'")
        return {"ids": [], "documents": [], "metadatas": []}

    # Display found concepts
    print("\nFound concepts:")
    for i, result in enumerate(results):
        print(f"{i + 1}. {result['name']} (ID: {result['id']})")

    # If multiple concepts found, use the first one
    concept_id = results[0]["id"]
    concept_name = results[0]["name"]

    # Query vector database for chunks mentioning this concept
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
    combined_ids = results_primary.get("ids", []) + filtered_ids
    combined_docs = results_primary.get("documents", []) + filtered_docs
    combined_metadatas = results_primary.get("metadatas", []) + filtered_metadatas

    # Limit the number of results
    combined_ids = combined_ids[:limit]
    combined_docs = combined_docs[:limit]
    combined_metadatas = combined_metadatas[:limit]

    # Display passages
    print(f"\nPassages about '{concept_name}':")
    print("=" * 50)

    if not combined_ids:
        print("No passages found.")
        return {"ids": [], "documents": [], "metadatas": []}

    for i, doc_id in enumerate(combined_ids):
        doc = combined_docs[i]
        metadata = combined_metadatas[i]

        print(f"\nPassage {i + 1}:")
        print(f"Book: {metadata.get('book_title', 'Unknown')}")
        print(f"Chunk: {metadata.get('chunk_index', 'Unknown')}")
        print("-" * 50)

        # Print a snippet of the passage (first 300 characters)
        snippet = doc[:300] + "..." if len(doc) > 300 else doc
        print(snippet)
        print()

    return {
        "ids": combined_ids,
        "documents": combined_docs,
        "metadatas": combined_metadatas,
    }


def hybrid_search_ebooks(
    query: str, db_linkage: DatabaseLinkage, n_results: int = 5, max_hops: int = 2
) -> dict[str, Any]:
    """Perform hybrid search across the ebook collection.

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
    print("=" * 50)

    if not results["vector_results"]["documents"]:
        print("No vector results found.")
    else:
        for i, doc in enumerate(results["vector_results"]["documents"]):
            metadata = results["vector_results"]["metadatas"][i]

            print(f"\nResult {i + 1}:")
            print(f"Book: {metadata.get('book_title', 'Unknown')}")
            print(f"Chunk: {metadata.get('chunk_index', 'Unknown')}")
            print("-" * 50)

            # Print a snippet of the passage (first 300 characters)
            snippet = doc[:300] + "..." if len(doc) > 300 else doc
            print(snippet)
            print()

    # Display graph results
    print("\nRelated Concepts:")
    print("=" * 50)

    if not results["graph_results"]:
        print("No related concepts found.")
    else:
        # The graph_results should already be de-duplicated by the hybrid_search method
        # But we'll display them in order of relevance score
        for i, result in enumerate(results["graph_results"]):
            print(f"{i + 1}. {result['name']} (Score: {result['relevance_score']:.2f})")

    return results


def main() -> None:
    """Main function to query and explore the ebook graph."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Query and explore the ebook graph")
    parser.add_argument(
        "--books", "-b", type=str, help="Find books mentioning a concept"
    )
    parser.add_argument(
        "--related", "-r", type=str, help="Find concepts related to a concept"
    )
    parser.add_argument(
        "--passages", "-p", type=str, help="Find passages about a concept"
    )
    parser.add_argument("--search", "-s", type=str, help="Perform hybrid search")
    parser.add_argument(
        "--limit", "-l", type=int, default=5, help="Maximum number of results to return"
    )
    parser.add_argument(
        "--hops", type=int, default=2, help="Maximum number of hops in the graph"
    )
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
    if args.books:
        find_books_by_concept(args.books, neo4j_db)
    elif args.related:
        find_related_concepts(args.related, neo4j_db, args.hops)
    elif args.passages:
        find_passages_about_concept(args.passages, neo4j_db, vector_db, args.limit)
    elif args.search:
        hybrid_search_ebooks(args.search, db_linkage, args.limit, args.hops)
    else:
        # If no arguments provided, run an interactive demo
        while True:
            print("\nEbook Graph Explorer")
            print("=" * 50)
            print("1. Find books mentioning a concept")
            print("2. Find related concepts")
            print("3. Find passages about a concept")
            print("4. Perform hybrid search")
            print("5. Exit")

            choice = input("\nEnter your choice (1-5): ")

            if choice == "1":
                concept = input("Enter concept name: ")
                find_books_by_concept(concept, neo4j_db)
            elif choice == "2":
                concept = input("Enter concept name: ")
                hops = int(input("Maximum hops (default: 2): ") or "2")
                find_related_concepts(concept, neo4j_db, hops)
            elif choice == "3":
                concept = input("Enter concept name: ")
                limit = int(input("Maximum passages (default: 5): ") or "5")
                find_passages_about_concept(concept, neo4j_db, vector_db, limit)
            elif choice == "4":
                query = input("Enter search query: ")
                limit = int(input("Maximum results (default: 5): ") or "5")
                hops = int(input("Maximum hops (default: 2): ") or "2")
                hybrid_search_ebooks(query, db_linkage, limit, hops)
            elif choice == "5":
                break
            else:
                print("Invalid choice. Please try again.")

    # Close Neo4j connection
    neo4j_db.close()


if __name__ == "__main__":
    main()
