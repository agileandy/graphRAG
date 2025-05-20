import json
import os
from neo4j import GraphDatabase, exceptions

# Adjust the path to config.json based on the script's location
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'database_config.json')

def load_neo4j_config():
    """Loads Neo4j configuration from the config file."""
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        return config.get('neo4j')
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {CONFIG_PATH}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {CONFIG_PATH}")
        return None

def initialize_schema(driver):
    """
    Initializes the Neo4j schema by creating constraints and indexes.
    This function is idempotent.
    """
    # Constraints to be created
    constraints = [
        ("concept_name_unique", "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE"),
        ("document_id_unique", "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE")
    ]

    # Indexes to be created (example, adjust as needed)
    # Neo4j automatically creates backing indexes for unique constraints,
    # so explicit index creation for these properties might be redundant.
    # Add other indexes if necessary, e.g., for frequently queried non-unique properties.
    indexes = [
        # ("concept_name_idx", "CREATE INDEX IF NOT EXISTS FOR (c:Concept) ON (c.name)"), # Covered by unique constraint
        # ("document_id_idx", "CREATE INDEX IF NOT EXISTS FOR (d:Document) ON (d.id)")   # Covered by unique constraint
    ]

    with driver.session() as session:
        print("Applying schema constraints...")
        for name, query in constraints:
            try:
                session.run(query)
                print(f"Successfully applied/verified constraint: {name}")
            except exceptions.Neo4jError as e:
                print(f"Error applying constraint {name}: {e}")
            except Exception as e:
                print(f"An unexpected error occurred while applying constraint {name}: {e}")

        if indexes:
            print("\nApplying schema indexes...")
            for name, query in indexes:
                try:
                    session.run(query)
                    print(f"Successfully applied/verified index: {name}")
                except exceptions.Neo4jError as e:
                    print(f"Error applying index {name}: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred while applying index {name}: {e}")
        else:
            print("\nNo additional indexes to apply beyond those for unique constraints.")


def main():
    """Main function to initialize the Neo4j database schema."""
    neo4j_config = load_neo4j_config()
    if not neo4j_config:
        return

    uri = neo4j_config.get('uri')
    username = neo4j_config.get('username')
    password = neo4j_config.get('password')

    if not all([uri, username, password]):
        print("Error: Neo4j URI, username, or password missing in configuration.")
        return

    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
        print("Successfully connected to Neo4j.")
        initialize_schema(driver)
    except exceptions.AuthError:
        print(f"Error: Neo4j authentication failed for user '{username}'. Check credentials.")
    except exceptions.ServiceUnavailable:
        print(f"Error: Could not connect to Neo4j at {uri}. Ensure the server is running.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if driver:
            driver.close()
            print("Neo4j connection closed.")

if __name__ == "__main__":
    main()