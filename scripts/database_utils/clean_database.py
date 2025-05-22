import argparse
import json
import os
import sys

# Add project root to sys.path to allow imports from src
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)

try:
    from neo4j import GraphDatabase
    from neo4j import exceptions as neo4j_exceptions
except ImportError:
    print(
        "Error: The 'neo4j' library is not installed. Please install it by running 'pip install neo4j'"
    )
    sys.exit(1)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    # Removed problematic import: from chromadb.exceptions import CollectionNotFoundException
except ImportError:
    print(
        "Error: The 'chromadb' library is not installed. Please install it by running 'pip install chromadb'"
    )
    sys.exit(1)

CONFIG_FILE_PATH = os.path.join(project_root, "config", "database_config.json")


def load_config():
    """Loads database configuration from the JSON file."""
    try:
        with open(CONFIG_FILE_PATH) as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {CONFIG_FILE_PATH}")
        print("Please create it with Neo4j and ChromaDB connection details.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {CONFIG_FILE_PATH}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred while loading config: {e}")
        sys.exit(1)


def clear_neo4j(config) -> bool | None:
    """Clears all nodes and relationships from Neo4j."""
    uri = config.get("uri")
    user = config.get("username")
    password = config.get("password")

    if not all([uri, user, password]):
        print(
            "Error: Neo4j configuration (uri, username, password) is missing or incomplete in config."
        )
        return False

    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print(f"Successfully connected to Neo4j at {uri}")
        with driver.session() as session:
            print("Clearing Neo4j database (deleting all nodes and relationships)...")
            session.run("MATCH (n) DETACH DELETE n")
            print("Neo4j database cleared successfully.")
        return True
    except neo4j_exceptions.AuthError:
        print(
            f"Error: Neo4j authentication failed for user '{user}'. Check credentials in {CONFIG_FILE_PATH}."
        )
        return False
    except neo4j_exceptions.ServiceUnavailable:
        print(
            f"Error: Could not connect to Neo4j at {uri}. Ensure the server is running."
        )
        return False
    except Exception as e:
        print(f"An error occurred while clearing Neo4j: {e}")
        return False
    finally:
        if driver:
            driver.close()


def reset_chromadb(config) -> bool | None:
    """Resets ChromaDB by deleting specified collections."""
    host = config.get("host", "localhost")
    port = config.get("port", 8000)
    config.get("path", "/")  # For HttpClient
    collections_to_delete = config.get("collections_to_delete", [])

    if not collections_to_delete:
        print(
            "Warning: No ChromaDB collections specified for deletion in config. Nothing to do for ChromaDB."
        )
        return True  # No action needed, so considered successful

    print(f"Attempting to connect to ChromaDB at host='{host}', port={port}...")
    try:
        # Using HttpClient, adjust if using a persistent client with a path
        client = chromadb.HttpClient(
            host=host, port=port, settings=ChromaSettings(anonymized_telemetry=False)
        )
        # For a persistent client, you might use:
        # client = chromadb.PersistentClient(path=os.path.join(project_root, "chroma_db_storage"))

        print("Successfully connected to ChromaDB.")
        if not collections_to_delete:
            print("No collections specified to delete in the configuration.")
            return True

        all_collections = [col.name for col in client.list_collections()]
        print(f"Available collections: {all_collections}")

        deleted_count = 0
        for collection_name in collections_to_delete:
            if collection_name in all_collections:
                try:
                    print(f"Deleting ChromaDB collection: {collection_name}...")
                    client.delete_collection(name=collection_name)
                    print(f"Collection '{collection_name}' deleted successfully.")
                    deleted_count += 1
                # Removed specific except block for CollectionNotFoundException
                except Exception as e:
                    print(f"Error deleting collection '{collection_name}': {e}")
            else:
                print(
                    f"Warning: Collection '{collection_name}' specified in config not found in ChromaDB. Skipping."
                )

        if deleted_count > 0:
            print(f"Successfully deleted {deleted_count} ChromaDB collection(s).")
        else:
            print(
                "No ChromaDB collections were deleted (either not found or not specified)."
            )
        return True

    except ConnectionRefusedError:  # More specific for network issues
        print(
            f"Error: Could not connect to ChromaDB at {host}:{port}. Ensure the server is running."
        )
        return False
    except Exception as e:
        print(f"An error occurred while resetting ChromaDB: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Cleans/resets specified databases.")
    parser.add_argument(
        "--neo4j", action="store_true", help="Clean the Neo4j database."
    )
    parser.add_argument("--chromadb", action="store_true", help="Reset the ChromaDB.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Clean/reset all databases (Neo4j and ChromaDB).",
    )

    args = parser.parse_args()

    if not any([args.neo4j, args.chromadb, args.all]):
        print(
            "No action specified. Use --neo4j, --chromadb, or --all. Defaulting to --all."
        )
        args.all = True  # Default to all if no flags are provided

    config = load_config()
    neo4j_config = config.get("neo4j", {})
    chromadb_config = config.get("chromadb", {})

    if args.all or args.neo4j:
        print("\n--- Cleaning Neo4j ---")
        if neo4j_config:
            if not clear_neo4j(neo4j_config):
                print("Neo4j cleaning failed.")
        else:
            print("Neo4j configuration not found in config file. Skipping Neo4j.")

    if args.all or args.chromadb:
        print("\n--- Resetting ChromaDB ---")
        if chromadb_config:
            if not reset_chromadb(chromadb_config):
                print("ChromaDB reset failed.")
        else:
            print("ChromaDB configuration not found in config file. Skipping ChromaDB.")

    print("\nDatabase cleaning/resetting process finished.")


if __name__ == "__main__":
    main()
