#!/usr/bin/env python3
"""
Script to repair the ChromaDB vector index.

This script:
1. Checks the health of the ChromaDB index
2. Attempts to repair the index if it's unhealthy
3. Verifies the repair was successful
"""
import sys
import os
import logging
import argparse

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.vector_db import VectorDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Repair ChromaDB vector index")
    parser.add_argument("--force", action="store_true", help="Force repair even if index appears healthy")
    parser.add_argument("--verify", action="store_true", help="Verify index health after repair")
    args = parser.parse_args()
    
    print("Checking ChromaDB vector index health...")
    
    # Initialize vector database
    vector_db = VectorDatabase()
    
    # Check index health
    is_healthy, health_message = vector_db.check_index_health()
    
    if is_healthy and not args.force:
        print(f"✅ Vector index is healthy: {health_message}")
        return True
    
    if not is_healthy:
        print(f"❌ Vector index is unhealthy: {health_message}")
    elif args.force:
        print("Force repair requested even though index appears healthy")
    
    # Attempt to repair the index
    print("\nAttempting to repair the vector index...")
    success, repair_message = vector_db.repair_index()
    
    if success:
        print(f"✅ Vector index repair successful: {repair_message}")
    else:
        print(f"❌ Vector index repair failed: {repair_message}")
        return False
    
    # Verify the repair if requested
    if args.verify:
        print("\nVerifying vector index health after repair...")
        is_healthy, health_message = vector_db.check_index_health()
        
        if is_healthy:
            print(f"✅ Vector index is now healthy: {health_message}")
        else:
            print(f"❌ Vector index is still unhealthy: {health_message}")
            return False
    
    # Test a simple query
    print("\nTesting vector search...")
    try:
        result = vector_db.query(
            query_texts=["test query after index repair"],
            n_results=1
        )
        
        if result and "documents" in result and len(result["documents"]) > 0:
            print("✅ Vector search test successful!")
        else:
            print("⚠️ Vector search returned no results (this might be normal for an empty database)")
    except Exception as e:
        print(f"❌ Vector search test failed: {e}")
        return False
    
    print("\n✅ Vector index repair and verification completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
