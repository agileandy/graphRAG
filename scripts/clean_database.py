"""
Script to clean the GraphRAG database.

This script:
1. Clears all data from Neo4j (logical deletion)
2. Physically deletes Neo4j database files (optional)
3. Resets the ChromaDB vector database
"""
import sys
import os
import shutil
import argparse
import subprocess
import time

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase
from dotenv import load_dotenv

def clean_neo4j(neo4j_db: Neo4jDatabase, confirm: bool = False) -> bool:
    """
    Clear all data from Neo4j.

    Args:
        neo4j_db: Neo4j database instance
        confirm: Whether to skip confirmation prompt

    Returns:
        True if successful, False otherwise
    """
    print("Preparing to clear all data from Neo4j...")

    # Verify connection
    if not neo4j_db.verify_connection():
        print("❌ Neo4j connection failed!")
        return False

    # Get node count
    query = "MATCH (n) RETURN count(n) as count"
    result = neo4j_db.run_query_and_return_single(query)
    node_count = result.get("count", 0)

    # Get relationship count
    query = "MATCH ()-[r]->() RETURN count(r) as count"
    result = neo4j_db.run_query_and_return_single(query)
    rel_count = result.get("count", 0)

    print(f"Found {node_count} nodes and {rel_count} relationships in Neo4j")

    # Confirm deletion
    if not confirm:
        response = input("Are you sure you want to delete all data from Neo4j? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return False

    # Clear all data
    print("Clearing all data from Neo4j...")
    neo4j_db.run_query("MATCH (n) DETACH DELETE n")

    # Verify deletion
    query = "MATCH (n) RETURN count(n) as count"
    result = neo4j_db.run_query_and_return_single(query)
    new_count = result.get("count", 0)

    if new_count == 0:
        print("✅ Successfully cleared all data from Neo4j")
        return True
    else:
        print(f"❌ Failed to clear all data. {new_count} nodes remain.")
        return False

def physically_delete_neo4j(confirm: bool = False, restart: bool = True) -> bool:
    """
    Physically delete Neo4j database files.

    Args:
        confirm: Whether to skip confirmation prompt
        restart: Whether to restart Neo4j after deletion

    Returns:
        True if successful, False otherwise
    """
    print("Preparing to physically delete Neo4j database files...")

    # Determine Neo4j data directories
    # Check environment variables first
    neo4j_home = os.getenv("NEO4J_HOME")
    neo4j_data_dir = os.getenv("NEO4J_DATA_DIR")

    # If environment variables are set, use them
    if neo4j_home and neo4j_data_dir:
        neo4j_dir = neo4j_home
        neo4j_data_dir = os.path.join(neo4j_data_dir, 'data', 'databases')
        neo4j_tx_dir = os.path.join(neo4j_data_dir, 'data', 'transactions')
        print("Using Neo4j installation from environment variables:")
        print(f"  NEO4J_HOME: {neo4j_home}")
        print(f"  NEO4J_DATA_DIR: {neo4j_data_dir}")
    else:
        # Check standard locations
        home_dir = os.path.expanduser('~')

        # Check ~/.local/neo4j (standard location for binaries)
        local_neo4j_dir = os.path.join(home_dir, '.local', 'neo4j')

        # Check ~/.graphrag/neo4j (application data location)
        graphrag_neo4j_dir = os.path.join(home_dir, '.graphrag', 'neo4j')

        # Check project directory (legacy location)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        project_neo4j_dir = os.path.join(project_root, 'neo4j')

        # Determine which Neo4j installation to use
        if os.path.exists(local_neo4j_dir) and os.path.isdir(local_neo4j_dir):
            # Using standard installation with data in .graphrag
            neo4j_dir = local_neo4j_dir
            neo4j_data_dir = os.path.join(graphrag_neo4j_dir, 'data', 'databases')
            neo4j_tx_dir = os.path.join(graphrag_neo4j_dir, 'data', 'transactions')
            print("Using Neo4j installation in ~/.local/neo4j with data in ~/.graphrag/neo4j")
        elif os.path.exists(project_neo4j_dir) and os.path.isdir(project_neo4j_dir):
            # Legacy installation in project directory
            neo4j_dir = project_neo4j_dir
            neo4j_data_dir = os.path.join(project_neo4j_dir, 'data', 'databases')
            neo4j_tx_dir = os.path.join(project_neo4j_dir, 'data', 'transactions')
            print(f"Using Neo4j installation in project directory: {neo4j_dir}")
        else:
            print("❌ Neo4j installation not found in standard locations")
            return False

    # Check if Neo4j data directory exists
    if not os.path.exists(neo4j_data_dir):
        print(f"Neo4j data directory not found: {neo4j_data_dir}")
        return False

    # Confirm deletion
    if not confirm:
        print("⚠️  WARNING: This will physically delete all Neo4j database files!")
        print(f"Neo4j data directory: {neo4j_data_dir}")
        print(f"Neo4j transaction directory: {neo4j_tx_dir}")
        response = input("Are you sure you want to physically delete Neo4j database files? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return False

    # Stop Neo4j server if it's running
    print("Stopping Neo4j server...")
    # Get project root for scripts
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    stop_script = os.path.join(project_root, 'scripts', 'stop_neo4j.sh')

    if os.path.exists(stop_script):
        try:
            subprocess.run([stop_script], check=True)
            print("✅ Neo4j server stopped")
            # Wait for Neo4j to fully stop
            time.sleep(5)
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Failed to stop Neo4j server: {e}")
            print("Continuing with deletion anyway...")
    else:
        print("⚠️  Warning: Neo4j stop script not found. Continuing with deletion anyway...")

    # Delete Neo4j data directories
    success = True

    # Delete databases directory
    if os.path.exists(neo4j_data_dir):
        print(f"Deleting Neo4j databases directory: {neo4j_data_dir}")
        try:
            # Delete all contents but keep the directory
            for item in os.listdir(neo4j_data_dir):
                item_path = os.path.join(neo4j_data_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            print("✅ Successfully deleted Neo4j databases directory contents")
        except Exception as e:
            print(f"❌ Failed to delete Neo4j databases directory: {e}")
            success = False

    # Delete transactions directory
    if os.path.exists(neo4j_tx_dir):
        print(f"Deleting Neo4j transactions directory: {neo4j_tx_dir}")
        try:
            # Delete all contents but keep the directory
            for item in os.listdir(neo4j_tx_dir):
                item_path = os.path.join(neo4j_tx_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            print("✅ Successfully deleted Neo4j transactions directory contents")
        except Exception as e:
            print(f"❌ Failed to delete Neo4j transactions directory: {e}")
            success = False

    # Restart Neo4j if requested
    if restart and success:
        print("Restarting Neo4j server...")
        # Get project root for scripts (if not already defined)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        start_script = os.path.join(project_root, 'scripts', 'start_neo4j.sh')

        if os.path.exists(start_script):
            try:
                # Start Neo4j in the background
                subprocess.Popen([start_script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print("✅ Neo4j server restarting in the background")
                print("⚠️  Note: It may take a few moments for Neo4j to fully start")
            except Exception as e:
                print(f"❌ Failed to restart Neo4j server: {e}")
                success = False
        else:
            print("⚠️  Warning: Neo4j start script not found. Neo4j server not restarted.")
            success = False

    return success

def clean_chromadb(vector_db: VectorDatabase, confirm: bool = False) -> bool:
    """
    Reset the ChromaDB vector database.

    Args:
        vector_db: Vector database instance
        confirm: Whether to skip confirmation prompt

    Returns:
        True if successful, False otherwise
    """
    print("Preparing to reset ChromaDB...")

    # Get the persist directory
    persist_dir = vector_db.persist_directory

    # Check if directory exists
    if not os.path.exists(persist_dir):
        print(f"ChromaDB directory not found: {persist_dir}")
        return False

    # Confirm deletion
    if not confirm:
        response = input(f"Are you sure you want to delete ChromaDB directory: {persist_dir}? (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return False

    # Delete the directory
    print(f"Deleting ChromaDB directory: {persist_dir}")
    try:
        shutil.rmtree(persist_dir)
        print("✅ Successfully deleted ChromaDB directory")

        # Recreate the directory
        os.makedirs(persist_dir, exist_ok=True)
        print("✅ Recreated empty ChromaDB directory")

        return True
    except Exception as e:
        print(f"❌ Failed to delete ChromaDB directory: {e}")
        return False

def main():
    """
    Main function to clean the GraphRAG database.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Clean the GraphRAG database")
    parser.add_argument("--neo4j", action="store_true", help="Clean only Neo4j")
    parser.add_argument("--chromadb", action="store_true", help="Clean only ChromaDB")
    parser.add_argument("--physical-delete", action="store_true",
                        help="Physically delete Neo4j database files (destructive operation)")
    parser.add_argument("--no-restart", action="store_true",
                        help="Do not restart Neo4j after physical deletion")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompts")
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Initialize databases
    neo4j_db = Neo4jDatabase()
    vector_db = VectorDatabase()

    # Handle physical deletion of Neo4j if requested
    if args.physical_delete:
        if args.chromadb and not args.neo4j:
            print("⚠️  Warning: --physical-delete is only applicable to Neo4j, but --chromadb was specified without --neo4j")
            print("Ignoring --physical-delete option")
        else:
            # Physical deletion of Neo4j
            physically_delete_neo4j(confirm=args.yes, restart=not args.no_restart)

            # If physical deletion was performed, skip logical deletion
            if not args.chromadb:
                # Close Neo4j connection
                neo4j_db.close()
                print("\n✅ Database cleaning completed")
                return

    # Clean databases based on arguments (logical deletion)
    if args.neo4j or not (args.neo4j or args.chromadb):
        clean_neo4j(neo4j_db, args.yes)

    if args.chromadb or not (args.neo4j or args.chromadb):
        clean_chromadb(vector_db, args.yes)

    # Close Neo4j connection
    neo4j_db.close()

    print("\n✅ Database cleaning completed")

if __name__ == "__main__":
    main()