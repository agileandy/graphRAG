#!/usr/bin/env python3
"""Script to test vector search functionality.

This script:
1. Connects to the vector database
2. Performs a test search
3. Verifies the results
"""

import argparse
import json
import logging
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.db_linkage import DatabaseLinkage
from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> bool:
    """Main function."""
    parser = argparse.ArgumentParser(description="Test vector search functionality")
    parser.add_argument(
        "--query", type=str, default="neural networks", help="Search query"
    )
    parser.add_argument(
        "--n-results", type=int, default=5, help="Number of results to return"
    )
    parser.add_argument(
        "--repair", action="store_true", help="Attempt to repair the index if needed"
    )
    parser.add_argument("--verbose", action="store_true", help="Show detailed results")
    args = parser.parse_args()

    print(f"Testing vector search with query: '{args.query}'")

    # Initialize databases
    vector_db = VectorDatabase()
    neo4j_db = Neo4jDatabase()
    db_linkage = DatabaseLinkage(neo4j_db, vector_db)

    # Check vector database index health
    if args.repair:
        print("\nChecking vector database index health...")
        is_healthy, health_message = vector_db.check_index_health()

        if is_healthy:
            print(f"✅ Vector index is healthy: {health_message}")
        else:
            print(f"❌ Vector index is unhealthy: {health_message}")

            # Try to repair the index
            print("\nAttempting to repair the vector index...")
            success, repair_message = vector_db.repair_index()

            if success:
                print(f"✅ Vector index repair successful: {repair_message}")
            else:
                print(f"❌ Vector index repair failed: {repair_message}")
                return False

    # Perform vector search
    print("\nPerforming vector search...")
    try:
        vector_results = vector_db.query(
            query_texts=[args.query], n_results=args.n_results
        )

        # Display results
        if (
            vector_results
            and "documents" in vector_results
            and vector_results["documents"]
        ):
            print(
                f"✅ Vector search successful! Found {len(vector_results['documents'][0])} results."
            )

            if args.verbose:
                print("\nResults:")
                for i, doc in enumerate(vector_results["documents"][0]):
                    print(f"\n{i + 1}. {doc[:200]}...")

                    if "metadatas" in vector_results and i < len(
                        vector_results["metadatas"][0]
                    ):
                        metadata = vector_results["metadatas"][0][i]
                        print(f"   Metadata: {json.dumps(metadata, indent=2)}")
        else:
            print("❌ Vector search returned no results.")
    except Exception as e:
        print(f"❌ Vector search failed: {e}")
        return False

    # Perform hybrid search
    print("\nPerforming hybrid search...")
    try:
        hybrid_results = db_linkage.hybrid_search(
            query_text=args.query, n_vector_results=args.n_results, max_graph_hops=2
        )

        # Display results
        if hybrid_results:
            vector_count = len(
                hybrid_results.get("vector_results", {}).get("documents", [])
            )
            graph_count = len(hybrid_results.get("graph_results", []))

            print(
                f"✅ Hybrid search successful! Found {vector_count} vector results and {graph_count} graph results."
            )

            if args.verbose:
                print("\nVector Results:")
                for i, doc in enumerate(
                    hybrid_results.get("vector_results", {}).get("documents", [])
                ):
                    print(f"\n{i + 1}. {doc[:200]}...")

                print("\nGraph Results:")
                for i, concept in enumerate(hybrid_results.get("graph_results", [])):
                    print(
                        f"\n{i + 1}. {concept.get('name')} (Score: {concept.get('relevance_score', 0)})"
                    )
        else:
            print("❌ Hybrid search returned no results.")
    except Exception as e:
        print(f"❌ Hybrid search failed: {e}")
        return False

    print("\n✅ Vector search test completed successfully!")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
