#!/usr/bin/env python3
"""
Script to reset the GraphRAG databases (Neo4j and Vector DB).
"""

import sys
import os
import argparse
import time

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from src.database.neo4j_db import Neo4jDatabase
    from src.database.vector_db import VectorDatabase
except ImportError:
    print("Error: Could not import database modules. Make sure you're running this script from the project root directory.")
    sys.exit(1)

def reset_neo4j(neo4j_db, confirm=True):
    """Reset the Neo4j database by deleting all nodes and relationships."""
    if confirm:
        response = input("Are you sure you want to reset the Neo4j database? This will delete all nodes and relationships. (y/n): ")
        if response.lower() != 'y':
            print("Neo4j reset cancelled.")
            return False

    print("Resetting Neo4j database...")

    try:
        # Delete all nodes and relationships
        neo4j_db.run_query("MATCH (n) DETACH DELETE n")
        print("✅ All nodes and relationships deleted.")

        # Verify that the database is empty
        result = neo4j_db.run_query("MATCH (n) RETURN count(n) AS count")
        count = result[0]["count"]
        print(f"Node count after reset: {count}")

        return True
    except Exception as e:
        print(f"❌ Error resetting Neo4j database: {e}")
        return False

def reset_vector_db(vector_db, confirm=True):
    """Reset the vector database by deleting all collections."""
    if confirm:
        response = input("Are you sure you want to reset the vector database? This will delete all documents. (y/n): ")
        if response.lower() != 'y':
            print("Vector database reset cancelled.")
            return False

    print("Resetting vector database...")

    try:
        # Get the collection name
        collection_name = "ebook_chunks"  # Default collection name

        # Connect to the database
        if vector_db.client is None:
            vector_db.connect()

        # Get all collections
        collections = vector_db.client.list_collections()
        print(f"Found {len(collections)} collections")

        # Delete the collection if it exists
        for collection in collections:
            if collection.name == collection_name:
                print(f"Deleting collection: {collection_name}")
                vector_db.client.delete_collection(collection_name)
                print(f"✅ Collection {collection_name} deleted.")
                break

        # Recreate the collection
        vector_db.connect(collection_name)
        print(f"✅ Collection {collection_name} recreated.")

        return True
    except Exception as e:
        print(f"❌ Error resetting vector database: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Reset the GraphRAG databases")
    parser.add_argument("--neo4j", action="store_true", help="Reset only the Neo4j database")
    parser.add_argument("--vector", action="store_true", help="Reset only the vector database")
    parser.add_argument("--all", action="store_true", help="Reset both databases")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompts")
    args = parser.parse_args()

    # Check if at least one database is selected
    if not (args.neo4j or args.vector or args.all):
        print("Error: Please specify which database to reset (--neo4j, --vector, or --all).")
        parser.print_help()
        return 1

    # Initialize database connections
    neo4j_db = Neo4jDatabase()
    vector_db = VectorDatabase()

    # Reset Neo4j if selected
    if args.neo4j or args.all:
        neo4j_success = reset_neo4j(neo4j_db, not args.yes)
    else:
        neo4j_success = True

    # Reset vector database if selected
    if args.vector or args.all:
        vector_success = reset_vector_db(vector_db, not args.yes)
    else:
        vector_success = True

    # Close Neo4j connection
    neo4j_db.close()

    # Print summary
    print("\nReset Summary:")
    if args.neo4j or args.all:
        print(f"Neo4j Database: {'✅ Success' if neo4j_success else '❌ Failed'}")
    if args.vector or args.all:
        print(f"Vector Database: {'✅ Success' if vector_success else '❌ Failed'}")

    if (args.neo4j or args.all) and (args.vector or args.all):
        if neo4j_success and vector_success:
            print("\n✅ Database reset completed successfully!")
            return 0
        else:
            print("\n❌ Database reset failed.")
            return 1
    elif args.neo4j and neo4j_success:
        print("\n✅ Neo4j database reset completed successfully!")
        return 0
    elif args.vector and vector_success:
        print("\n✅ Vector database reset completed successfully!")
        return 0
    else:
        print("\n❌ Database reset failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
