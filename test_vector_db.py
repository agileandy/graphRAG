#!/usr/bin/env python3
"""
Test script to verify ChromaDB connection.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from src.database.vector_db import VectorDatabase

def main():
    """
    Main function to test ChromaDB connection.
    """
    # Print environment variables
    config_env_path = os.path.expanduser("~/.graphrag/config.env")
    logger.info(f"Config file path: {config_env_path}")
    logger.info(f"Config file exists: {os.path.exists(config_env_path)}")
    
    if os.path.exists(config_env_path):
        load_dotenv(config_env_path)
        logger.info(f"Loaded environment variables from {config_env_path}")
    
    chroma_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chromadb")
    logger.info(f"CHROMA_PERSIST_DIRECTORY from environment: {chroma_dir}")
    
    # Convert to absolute path if it's a relative path
    if not os.path.isabs(chroma_dir):
        chroma_dir = os.path.abspath(chroma_dir)
        logger.info(f"Converted to absolute path: {chroma_dir}")
    
    logger.info(f"Directory exists: {os.path.exists(chroma_dir)}")
    logger.info(f"Directory is writable: {os.access(chroma_dir, os.W_OK)}")
    
    # Initialize VectorDatabase
    logger.info("Initializing VectorDatabase...")
    vector_db = VectorDatabase()
    
    # Verify connection
    logger.info("Verifying connection...")
    connection_status = vector_db.verify_connection()
    logger.info(f"Connection status: {connection_status}")
    
    # Print database info
    if connection_status:
        logger.info(f"ChromaDB directory: {vector_db.persist_directory}")
        logger.info(f"Document count: {vector_db.count()}")
    
    return connection_status

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
