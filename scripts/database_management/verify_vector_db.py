"""Script to verify vector database connection and setup."""

import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.vector_db import VectorDatabase


def main() -> bool:
    """Verify vector database connection and setup."""
    print("Verifying vector database connection...")

    # Create vector database instance
    vector_db = VectorDatabase()

    # Verify connection
    if vector_db.verify_connection():
        print("✅ Vector database connection successful!")
    else:
        print("❌ Vector database connection failed!")
        print("Please check the vector database configuration.")
        return False

    # Create dummy data
    print("\nCreating dummy data...")
    try:
        vector_db.create_dummy_data()
        print("✅ Dummy data created successfully!")
    except Exception as e:
        print(f"❌ Failed to create dummy data: {e}")
        return False

    # Run a test query
    print("\nRunning test query...")
    try:
        count = vector_db.count()
        print(f"✅ Test query successful! Found {count} documents in the database.")

        # Query for a specific document
        results = vector_db.query(query_texts=["neural networks"], n_results=1)

        if results and results.get("ids") and results["ids"][0]:
            print("✅ Successfully queried for 'neural networks'!")
            print(f"   Top result: {results['documents'][0][0]}")
        else:
            print("❌ Query returned no results.")
    except Exception as e:
        print(f"❌ Failed to run test query: {e}")
        return False

    print("\n✅ Vector database verification completed successfully!")
    return True


if __name__ == "__main__":
    main()
