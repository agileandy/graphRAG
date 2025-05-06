"""
Script to reset the GraphRAG database.

This script:
1. Cleans the database (Neo4j and ChromaDB)
2. Initializes the database schema
3. Adds sample data (optional)
"""
import sys
import os
import argparse
import subprocess

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_script(script_name: str, args: list = None) -> bool:
    """
    Run a Python script.
    
    Args:
        script_name: Name of the script to run
        args: Command-line arguments for the script
        
    Returns:
        True if successful, False otherwise
    """
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    # Build command
    command = [sys.executable, script_path]
    if args:
        command.extend(args)
    
    # Run script
    print(f"Running {script_name}...")
    try:
        result = subprocess.run(command, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run {script_name}: {e}")
        return False

def main():
    """
    Main function to reset the GraphRAG database.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Reset the GraphRAG database")
    parser.add_argument("--no-sample", action="store_true", help="Skip adding sample data")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompts")
    args = parser.parse_args()
    
    # Confirm reset
    if not args.yes:
        response = input("Are you sure you want to reset the GraphRAG database? This will delete all existing data. (y/n): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return
    
    # Clean database
    clean_args = ["--yes"] if args.yes else []
    if not run_script("clean_database.py", clean_args):
        print("❌ Failed to clean database")
        return
    
    # Initialize database
    if not run_script("initialize_database.py"):
        print("❌ Failed to initialize database")
        return
    
    # Add sample data
    if not args.no_sample:
        print("\nAdding sample data...")
        
        # Create example documents
        if not run_script("batch_process.py", ["--create-examples"]):
            print("❌ Failed to create example documents")
            return
        
        # Process example documents
        if not run_script("batch_process.py", ["--dir", "./example_docs"]):
            print("❌ Failed to process example documents")
            return
    
    print("\n✅ Database reset completed successfully!")
    print("\nNext steps:")
    print("1. Query the system interactively with 'python scripts/query_graphrag.py'")
    print("2. Add your own documents with 'python scripts/add_document.py'")
    print("3. Explore the knowledge graph in Neo4j Browser at http://localhost:7474/")

if __name__ == "__main__":
    main()