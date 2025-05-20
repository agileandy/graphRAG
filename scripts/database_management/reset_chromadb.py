#!/usr/bin/env python3
"""
Script to reset ChromaDB database.

This script:
1. Deletes the ChromaDB database directory
2. Recreates the directory
3. Initializes a new ChromaDB database
"""
import sys
import os
import shutil
import logging

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.utils.db_utils import check_chromadb_version
from src.database.vector_db import VectorDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def reset_chromadb():
    """Reset ChromaDB database."""
    # Get ChromaDB directory
    chroma_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chromadb")

    # Check if directory exists
    if os.path.exists(chroma_dir):
        print(f"Deleting ChromaDB directory: {chroma_dir}")
        try:
            # Delete directory
            shutil.rmtree(chroma_dir)
            print("✅ Successfully deleted ChromaDB directory")
        except Exception as e:
            print(f"❌ Error deleting ChromaDB directory: {e}")
            return False

    # Create directory
    try:
        os.makedirs(chroma_dir, exist_ok=True)
        print(f"✅ Created new ChromaDB directory: {chroma_dir}")
    except Exception as e:
        print(f"❌ Error creating ChromaDB directory: {e}")
        return False

    # Initialize ChromaDB
    try:
        print("Initializing new ChromaDB database...")
        vector_db = VectorDatabase()
        vector_db.connect()
        print("✅ Successfully initialized new ChromaDB database")

        # Create dummy data
        print("Creating dummy data...")
        vector_db.create_dummy_data()
        print("✅ Successfully created dummy data")

        return True
    except Exception as e:
        print(f"❌ Error initializing ChromaDB: {e}")
        return False

def main():
    """Main function."""
    print("Resetting ChromaDB database...")

    # Check ChromaDB version
    print("\nChecking ChromaDB version...")
    version_ok = check_chromadb_version()
    if not version_ok:
        print("⚠️ ChromaDB version check failed. Proceeding anyway...")

    # Reset ChromaDB
    success = reset_chromadb()

    if success:
        print("\n✅ ChromaDB reset completed successfully!")
    else:
        print("\n❌ ChromaDB reset failed.")

if __name__ == "__main__":
    main()
