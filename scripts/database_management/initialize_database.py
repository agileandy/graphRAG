"""
Script to initialize the GraphRAG database.

This script is used to initialize the Neo4j and Vector databases when the Docker container
starts for the first time. It creates the necessary constraints and indexes.
"""
import sys
import os
import time

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase

# Override environment variables for Docker container
os.environ["NEO4J_URI"] = "bolt://0.0.0.0:7687"
os.environ["GRAPHRAG_API_URL"] = "http://0.0.0.0:5000"

def initialize_neo4j(neo4j_db: Neo4jDatabase) -> bool:
    """
    Initialize the Neo4j database with constraints and indexes.

    Args:
        neo4j_db: Neo4j database instance

    Returns:
        True if successful, False otherwise
    """
    print("Initializing Neo4j database...")

    # Wait for Neo4j to be available
    max_retries = 30
    retry_interval = 2  # seconds

    for i in range(max_retries):
        if neo4j_db.verify_connection():
            print("✅ Neo4j connection established!")
            break
        print(f"Waiting for Neo4j to be available... ({i+1}/{max_retries})")
        time.sleep(retry_interval)
    else:
        print("❌ Failed to connect to Neo4j after multiple attempts.")
        return False

    try:
        # Create constraints
        print("Creating constraints...")

        # Constraint for Book nodes
        neo4j_db.run_query("""
        CREATE CONSTRAINT book_id IF NOT EXISTS
        FOR (b:Book)
        REQUIRE b.id IS UNIQUE
        """)

        # Constraint for Concept nodes
        neo4j_db.run_query("""
        CREATE CONSTRAINT concept_id IF NOT EXISTS
        FOR (c:Concept)
        REQUIRE c.id IS UNIQUE
        """)

        # Create indexes
        print("Creating indexes...")

        # Book indexes
        neo4j_db.run_query("""
        CREATE INDEX book_title IF NOT EXISTS
        FOR (b:Book)
        ON (b.title)
        """)

        neo4j_db.run_query("""
        CREATE INDEX book_category IF NOT EXISTS
        FOR (b:Book)
        ON (b.category)
        """)

        neo4j_db.run_query("""
        CREATE INDEX book_isbn IF NOT EXISTS
        FOR (b:Book)
        ON (b.isbn)
        """)

        # Chapter indexes
        neo4j_db.run_query("""
        CREATE INDEX chapter_title IF NOT EXISTS
        FOR (c:Chapter)
        ON (c.title)
        """)

        neo4j_db.run_query("""
        CREATE INDEX chapter_book_id IF NOT EXISTS
        FOR (c:Chapter)
        ON (c.book_id)
        """)

        # Section indexes
        neo4j_db.run_query("""
        CREATE INDEX section_title IF NOT EXISTS
        FOR (s:Section)
        ON (s.title)
        """)

        neo4j_db.run_query("""
        CREATE INDEX section_chapter_id IF NOT EXISTS
        FOR (s:Section)
        ON (s.chapter_id)
        """)

        # Concept indexes
        neo4j_db.run_query("""
        CREATE INDEX concept_name IF NOT EXISTS
        FOR (c:Concept)
        ON (c.name)
        """)

        neo4j_db.run_query("""
        CREATE INDEX concept_category IF NOT EXISTS
        FOR (c:Concept)
        ON (c.category)
        """)

        print("✅ Neo4j database initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Error initializing Neo4j database: {e}")
        return False

def initialize_vector_db(vector_db: VectorDatabase) -> bool:
    """
    Initialize the Vector database.

    Args:
        vector_db: Vector database instance

    Returns:
        True if successful, False otherwise
    """
    print("Initializing Vector database...")

    try:
        # Verify connection
        if vector_db.verify_connection():
            print("✅ Vector database connection established!")

            # ChromaDB automatically creates the collection if it doesn't exist
            # when we first interact with it, so we don't need to explicitly create it
            print("✅ Vector database initialized successfully!")

            return True
        else:
            print("❌ Failed to connect to Vector database.")
            return False
    except Exception as e:
        print(f"❌ Error initializing Vector database: {e}")
        return False

def main():
    """
    Main function to initialize the GraphRAG database.
    """
    print("Starting database initialization...")

    # Initialize Neo4j
    neo4j_db = Neo4jDatabase()
    neo4j_success = initialize_neo4j(neo4j_db)

    # Initialize Vector database
    vector_db = VectorDatabase()
    vector_success = initialize_vector_db(vector_db)

    # Close Neo4j connection
    neo4j_db.close()

    # Print summary
    print("\nInitialization Summary:")
    print(f"Neo4j Database: {'✅ Success' if neo4j_success else '❌ Failed'}")
    print(f"Vector Database: {'✅ Success' if vector_success else '❌ Failed'}")

    if neo4j_success and vector_success:
        print("\n✅ Database initialization completed successfully!")
        return 0
    else:
        print("\n❌ Database initialization failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())