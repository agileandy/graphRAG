#!/usr/bin/env python3
"""
Script to check database indexes and optimizations.
"""
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase

def check_neo4j_indexes():
    """Check Neo4j indexes and constraints."""
    print("\n=== Neo4j Indexes and Constraints ===")
    
    db = Neo4jDatabase()
    
    # Check connection
    if not db.verify_connection():
        print("❌ Failed to connect to Neo4j")
        return False
    
    # Check indexes
    print("\nIndexes:")
    result = db.run_query("SHOW INDEXES")
    
    if not result:
        print("No indexes found")
    else:
        for idx in result:
            name = idx.get("name", "Unknown")
            idx_type = idx.get("type", "Unknown")
            labels = idx.get("labelsOrTypes", [])
            properties = idx.get("properties", [])
            
            print(f"- {name} ({idx_type}): {labels} {properties}")
    
    # Check constraints
    print("\nConstraints:")
    result = db.run_query("SHOW CONSTRAINTS")
    
    if not result:
        print("No constraints found")
    else:
        for constraint in result:
            name = constraint.get("name", "Unknown")
            constraint_type = constraint.get("type", "Unknown")
            labels = constraint.get("labelsOrTypes", [])
            properties = constraint.get("properties", [])
            
            print(f"- {name} ({constraint_type}): {labels} {properties}")
    
    # Close connection
    db.close()
    
    return True

def check_chromadb_settings():
    """Check ChromaDB settings and optimizations."""
    print("\n=== ChromaDB Settings ===")
    
    db = VectorDatabase()
    
    # Check connection
    if not db.verify_connection():
        print("❌ Failed to connect to ChromaDB")
        return False
    
    # Check collection settings
    if db.collection is None:
        print("❌ ChromaDB collection is None")
        return False
    
    print("\nCollection Information:")
    print(f"- Name: {db.collection.name}")
    print(f"- Count: {db.collection.count()}")
    
    # Try to get collection metadata
    try:
        metadata = db.collection.metadata
        print("\nCollection Metadata:")
        if metadata:
            for key, value in metadata.items():
                print(f"- {key}: {value}")
        else:
            print("No metadata found")
    except Exception as e:
        print(f"❌ Error getting collection metadata: {e}")
    
    return True

def main():
    """Main function."""
    print("Checking database indexes and optimizations...")
    
    # Check Neo4j indexes
    neo4j_success = check_neo4j_indexes()
    
    # Check ChromaDB settings
    chromadb_success = check_chromadb_settings()
    
    # Print summary
    print("\n=== Summary ===")
    print(f"Neo4j Indexes: {'✅ Checked' if neo4j_success else '❌ Failed'}")
    print(f"ChromaDB Settings: {'✅ Checked' if chromadb_success else '❌ Failed'}")
    
    return 0 if neo4j_success and chromadb_success else 1

if __name__ == "__main__":
    sys.exit(main())
