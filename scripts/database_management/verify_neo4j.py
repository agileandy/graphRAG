"""Script to verify Neo4j database connection and setup."""

import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.database.neo4j_db import Neo4jDatabase


def main() -> bool:
    """Verify Neo4j database connection and setup."""
    print("Verifying Neo4j database connection...")

    # Create Neo4j database instance
    neo4j_db = Neo4jDatabase()

    # Verify connection
    if neo4j_db.verify_connection():
        print("✅ Neo4j connection successful!")
    else:
        print("❌ Neo4j connection failed!")
        print(
            "Please make sure Neo4j is running and the connection details are correct."
        )
        return False

    # Create schema
    print("\nCreating Neo4j schema...")
    try:
        neo4j_db.create_schema()
        print("✅ Neo4j schema created successfully!")
    except Exception as e:
        print(f"❌ Failed to create Neo4j schema: {e}")
        return False

    # Create dummy data
    print("\nChecking for existing data...")
    try:
        result = neo4j_db.run_query_and_return_single(
            "MATCH (b:Book) RETURN count(b) as count"
        )
        book_count = result.get("count", 0)

        if book_count > 0:
            print(f"✅ Data already exists! Found {book_count} books in the database.")
        else:
            print("Creating dummy data...")
            neo4j_db.create_dummy_data()
            print("✅ Dummy data created successfully!")
    except Exception as e:
        print(f"❌ Failed to check/create dummy data: {e}")
        return False

    # Run a test query
    print("\nRunning test query...")
    try:
        result = neo4j_db.run_query_and_return_single(
            "MATCH (n) RETURN count(n) as count"
        )
        count = result.get("count", 0)
        print(f"✅ Test query successful! Found {count} nodes in the database.")
    except Exception as e:
        print(f"❌ Failed to run test query: {e}")
        return False

    # Close connection
    neo4j_db.close()

    print("\n✅ Neo4j verification completed successfully!")
    return True


if __name__ == "__main__":
    main()
