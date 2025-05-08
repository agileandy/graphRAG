#!/usr/bin/env python3
"""
Script to verify ChromaDB installation and configuration.

This script checks:
1. ChromaDB version
2. Database directories
3. Connection to the database
4. Basic operations
"""
import sys
import os
import logging

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.db_utils import check_chromadb_version, check_database_directories, get_chromadb_info
from src.database.vector_db import VectorDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function."""
    print("Verifying ChromaDB installation and configuration...")
    
    # Check ChromaDB version
    print("\nChecking ChromaDB version...")
    version_ok = check_chromadb_version()
    if version_ok:
        print("✅ ChromaDB version check passed")
    else:
        print("⚠️ ChromaDB version check failed")
    
    # Get ChromaDB info
    chromadb_info = get_chromadb_info()
    if chromadb_info:
        print("\nChromaDB Information:")
        print(f"  Version: {chromadb_info['version']}")
        print(f"  Python Version: {chromadb_info['python_version']}")
        print(f"  Platform: {chromadb_info['platform']}")
        print(f"  64-bit: {chromadb_info['is_64bit']}")
    
    # Check database directories
    print("\nChecking database directories...")
    dirs_ok = check_database_directories()
    if dirs_ok:
        print("✅ Database directories check passed")
    else:
        print("❌ Database directories check failed")
    
    # Test vector database connection
    print("\nTesting vector database connection...")
    vector_db = VectorDatabase()
    
    try:
        vector_db.connect()
        print("✅ Successfully connected to vector database")
        
        # Test basic operations
        print("\nTesting basic operations...")
        
        # Count documents
        count = vector_db.count()
        print(f"  Document count: {count}")
        
        # Create a test document
        test_doc = "This is a test document for ChromaDB verification."
        test_metadata = {"title": "Test Document", "source": "verify_chromadb.py"}
        test_id = "test-doc-verification"
        
        # Add the test document
        vector_db.add_documents(
            documents=[test_doc],
            metadatas=[test_metadata],
            ids=[test_id]
        )
        print("✅ Successfully added test document")
        
        # Query for the test document
        results = vector_db.query(
            query_texts=["test document verification"],
            n_results=1
        )
        
        if results and len(results["ids"][0]) > 0:
            print("✅ Successfully queried for test document")
            print(f"  Result: {results['documents'][0][0]}")
        else:
            print("❌ Failed to query for test document")
        
        # Get the test document by ID
        get_results = vector_db.get(ids=[test_id])
        
        if get_results and len(get_results["ids"]) > 0:
            print("✅ Successfully retrieved test document by ID")
        else:
            print("❌ Failed to retrieve test document by ID")
        
        print("\n✅ ChromaDB verification completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Error testing vector database: {e}")
        return False

if __name__ == "__main__":
    main()
