#!/usr/bin/env python3
"""Script to clear the Neo4j database."""

import logging
import os
import sys

# Add the project root to the Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from neo4j import GraphDatabase

from src.config import get_port


def clear_neo4j() -> int:
    """Clear the Neo4j database."""
    logging.basicConfig(level=logging.INFO)

    try:
        # Get Neo4j port from centralized configuration
        neo4j_port = get_port("neo4j_bolt")

        # Connect to Neo4j
        uri = f"bolt://localhost:{neo4j_port}"
        username = "neo4j"
        password = "graphrag"

        print(f"Connecting to Neo4j at {uri}...")
        driver = GraphDatabase.driver(uri, auth=(username, password))

        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            test_value = result.single()["test"]
            if test_value != 1:
                print("❌ Neo4j connection test failed")
                return 1
            print("✅ Neo4j connection successful")

            # Get node count
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()["count"]
            print(f"Found {node_count} nodes in Neo4j")

            # Clear all data
            print("Clearing all data from Neo4j...")
            session.run("MATCH (n) DETACH DELETE n")

            # Verify deletion
            result = session.run("MATCH (n) RETURN count(n) as count")
            new_count = result.single()["count"]

            if new_count == 0:
                print("✅ Successfully cleared all data from Neo4j")
            else:
                print(f"❌ Failed to clear all data. {new_count} nodes remain.")
                return 1

    except Exception as e:
        print(f"❌ Error clearing Neo4j database: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(clear_neo4j())
