import argparse
import json
import os
import sys

import chromadb

# Adjust the path to import from the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

DEFAULT_CONFIG_PATH = "config/database_config.json"


def load_config(config_path):
    """Loads database configuration from a JSON file."""
    try:
        with open(config_path) as f:
            config = json.load(f)
        return config.get("chromadb")
    except FileNotFoundError:
        print(f"Error: Configuration file not found at {config_path}")
        return None
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {config_path}")
        return None


def verify_chromadb(config, collection_name_to_check=None) -> bool:
    """Verifies the connection to ChromaDB, lists collections, and optionally
    counts items in a specified collection.
    """
    if not config:
        print("ChromaDB configuration not loaded. Aborting verification.")
        return False

    host = config.get("host", "localhost")
    port = config.get("port", 8000)
    # path = config.get("path", "/") # Path is not directly used by HttpClient

    print(f"Attempting to connect to ChromaDB at http://{host}:{port}...")

    try:
        # client = chromadb.HttpClient(host=host, port=port, path=path) # Path is not a standard HttpClient param
        client = chromadb.HttpClient(host=host, port=port)
        client.heartbeat()  # Check if the server is alive
        print("Connection to ChromaDB successful.")
    except Exception as e:
        print(f"Error: Could not connect to ChromaDB: {e}")
        return False

    try:
        print("\nVerifying collections...")
        collections = client.list_collections()
        if collections:
            print("Collections found:")
            for collection in collections:
                print(
                    f"- {collection.name} (ID: {collection.id}, Metadata: {collection.metadata})"
                )
        else:
            print("No collections found.")

    except Exception as e:
        print(f"Error listing collections: {e}")
        # Continue even if listing fails, to allow specific collection check if requested

    if collection_name_to_check:
        print(f"\nVerifying specific collection: '{collection_name_to_check}'...")
        try:
            collection_instance = client.get_collection(name=collection_name_to_check)
            count = collection_instance.count()
            print(f"Collection '{collection_name_to_check}' found.")
            print(f"Item count in '{collection_name_to_check}': {count}")
        except (
            Exception
        ) as e:  # More specific exceptions could be chromadb.errors.CollectionNotFound
            print(f"Error accessing collection '{collection_name_to_check}': {e}")
            print(f"Please ensure the collection '{collection_name_to_check}' exists.")
            return False  # Consider if this should be a fatal error for the script's success

    print("\nChromaDB verification process completed.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verify ChromaDB connection and collections."
    )
    parser.add_argument(
        "--config",
        type=str,
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to the database configuration JSON file (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--collection",
        type=str,
        help="Name of a specific collection to check and count items.",
    )

    args = parser.parse_args()

    print("--- ChromaDB Verification Script ---")
    db_config = load_config(args.config)

    if db_config:
        success = verify_chromadb(db_config, args.collection)
        if success:
            print("\nVerification successful.")
        else:
            print("\nVerification encountered errors.")
            sys.exit(1)
    else:
        print("Failed to load database configuration. Exiting.")
        sys.exit(1)
