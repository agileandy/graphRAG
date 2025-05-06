"""
Script to clean the GraphRAG database.

This script:
1. Clears all data from Neo4j
2. Resets the ChromaDB vector database
"""
import sys
import os
import shutil
import argparse

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase
from dotenv import load_dotenv

def clean_neo4j(neo4j_db: Neo4jDatabase, confirm: bool = False) -> bool:
    """
    Clear all data from Neo4j.
    
    Args:
        neo4j_db: Neo4j database instance
        confirm: Whether to skip confirmation prompt
        
    Returns:
        True if successful, False otherwise
    """
    print("Preparing to clear all data from Neo4j...")
    
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
    
    # Confirm deletion
    if not confirm:
        response = input("Are you sure you want to delete all data from Neo4j? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return False
    
    # Clear all data
    print("Clearing all data from Neo4j...")
    neo4j_db.run_query("MATCH (n) DETACH DELETE n")
    
    # Verify deletion
    query = "MATCH (n) RETURN count(n) as count"
    result = neo4j_db.run_query_and_return_single(query)
    new_count = result.get("count", 0)
    
    if new_count == 0:
        print("✅ Successfully cleared all data from Neo4j")
        return True
    else:
        print(f"❌ Failed to clear all data. {new_count} nodes remain.")
        return False

def clean_chromadb(vector_db: VectorDatabase, confirm: bool = False) -> bool:
    """
    Reset the ChromaDB vector database.
    
    Args:
        vector_db: Vector database instance
        confirm: Whether to skip confirmation prompt
        
    Returns:
        True if successful, False otherwise
    """
    print("Preparing to reset ChromaDB...")
    
    # Get the persist directory
    persist_dir = vector_db.persist_directory
    
    # Check if directory exists
    if not os.path.exists(persist_dir):
        print(f"ChromaDB directory not found: {persist_dir}")
        return False
    
    # Confirm deletion
    if not confirm:
        response = input(f"Are you sure you want to delete ChromaDB directory: {persist_dir}? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return False
    
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

def main():
    """
    Main function to clean the GraphRAG database.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Clean the GraphRAG database")
    parser.add_argument("--neo4j", action="store_true", help="Clean only Neo4j")
    parser.add_argument("--chromadb", action="store_true", help="Clean only ChromaDB")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompts")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize databases
    neo4j_db = Neo4jDatabase()
    vector_db = VectorDatabase()
    
    # Clean databases based on arguments
    if args.neo4j or not (args.neo4j or args.chromadb):
        clean_neo4j(neo4j_db, args.yes)
    
    if args.chromadb or not (args.neo4j or args.chromadb):
        clean_chromadb(vector_db, args.yes)
    
    # Close Neo4j connection
    neo4j_db.close()
    
    print("\n✅ Database cleaning completed")

if __name__ == "__main__":
    main()