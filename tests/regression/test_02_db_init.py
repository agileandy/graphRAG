#!/usr/bin/env python3
"""Regression Test 2: Check database initialization.

This test:
1. Completely deletes datastores (ChromaDB and Neo4j)
2. Starts the services
3. Verifies the databases are initialized correctly
4. Stops the services

Usage:
    python -m tests.regression.test_02_db_init
"""

import os
import shutil
import sys
import time

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from tests.regression.test_utils import check_api_health, start_services, stop_services


def delete_chromadb() -> bool:
    """Delete the ChromaDB datastore."""
    print("Deleting ChromaDB datastore...")

    # Get the ChromaDB directory from environment or use default
    chroma_dir = os.environ.get(
        "CHROMADB_DIR", os.path.expanduser("~/.graphrag/chromadb")
    )

    if os.path.exists(chroma_dir):
        try:
            shutil.rmtree(chroma_dir)
            print(f"✅ Successfully deleted ChromaDB directory: {chroma_dir}")
            return True
        except Exception as e:
            print(f"❌ Failed to delete ChromaDB directory: {e}")
            return False
    else:
        print(f"ChromaDB directory not found: {chroma_dir}")
        # Create the directory to ensure it exists
        os.makedirs(chroma_dir, exist_ok=True)
        print(f"Created new ChromaDB directory: {chroma_dir}")
        return True


def delete_neo4j() -> bool:
    """Delete the Neo4j datastore."""
    print("Deleting Neo4j datastore...")

    # Get the Neo4j directory from environment or use default
    neo4j_dir = os.environ.get("NEO4J_DIR", os.path.expanduser("~/.graphrag/neo4j"))

    if os.path.exists(neo4j_dir):
        try:
            # Use a safer approach than deleting the entire directory
            # Delete only the database files, not the configuration
            for subdir in ["data", "transactions"]:
                path = os.path.join(neo4j_dir, subdir)
                if os.path.exists(path):
                    shutil.rmtree(path)
                    print(f"✅ Successfully deleted Neo4j {subdir} directory")

            # Delete specific files that store database state
            for file in [
                "neostore",
                "neostore.counts.db",
                "neostore.id",
                "neostore.labelscanstore.db",
            ]:
                path = os.path.join(neo4j_dir, "data", "databases", "neo4j", file)
                if os.path.exists(path):
                    os.remove(path)
                    print(f"✅ Successfully deleted Neo4j file: {file}")

            print(f"✅ Successfully reset Neo4j database: {neo4j_dir}")
            return True
        except Exception as e:
            print(f"❌ Failed to reset Neo4j database: {e}")
            return False
    else:
        print(f"Neo4j directory not found: {neo4j_dir}")
        # Create the directory to ensure it exists
        os.makedirs(neo4j_dir, exist_ok=True)
        print(f"Created new Neo4j directory: {neo4j_dir}")
        return True


def test_db_initialization() -> bool:
    """Test database initialization."""
    print("\n=== Test 2: Database Initialization ===\n")

    # Step 1: Delete datastores
    print("Step 1: Deleting datastores...")
    chroma_success = delete_chromadb()
    neo4j_success = delete_neo4j()

    if not chroma_success or not neo4j_success:
        print("❌ Failed to delete datastores")
        return False

    print("✅ Datastores deleted successfully")

    # Step 2: Start services
    print("\nStep 2: Starting services...")
    success, process = start_services()

    if not success:
        print("❌ Failed to start services")
        return False

    print("✅ Services started successfully")

    # Step 3: Verify databases are initialized
    print("\nStep 3: Verifying databases are initialized...")
    time.sleep(5)  # Give databases time to initialize

    is_healthy, health_data = check_api_health()

    if is_healthy:
        print("✅ API health check passed")
        print(f"Health data: {health_data}")

        # Check Neo4j connection
        if health_data.get("neo4j_connected"):
            print("✅ Neo4j connection successful")
        else:
            print("❌ Neo4j connection failed")
            stop_services(process)
            return False

        # Check vector database connection
        if health_data.get("vector_db_connected"):
            print("✅ Vector database connection successful")
        else:
            print("❌ Vector database connection failed")
            stop_services(process)
            return False
    else:
        print("❌ API health check failed")
        print(f"Health data: {health_data}")
        stop_services(process)
        return False

    # Step 4: Stop services
    print("\nStep 4: Stopping services...")
    if stop_services(process):
        print("✅ Services stopped successfully")
    else:
        print("❌ Failed to stop services")
        return False

    print("\n=== Test 2 Completed Successfully ===")
    return True


def main() -> int:
    """Main function to run the test."""
    success = test_db_initialization()

    if success:
        print("\n✅ Test 2 passed: Database initialization")
        return 0
    else:
        print("\n❌ Test 2 failed: Database initialization")
        return 1


if __name__ == "__main__":
    sys.exit(main())
