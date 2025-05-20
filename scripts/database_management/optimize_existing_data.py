"""Script to optimize existing data in the GraphRAG system.

This script:
1. Retrieves existing data from the vector database
2. Optimizes the data with improved chunking and metadata
3. Reindexes the data with optimized settings
"""

import argparse
import os
import sys
import time
import uuid
from typing import Any

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.vector_db import VectorDatabase
from src.processing.document_processor import (
    DEFAULT_BATCH_SIZE,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_OVERLAP,
    process_document_with_metadata,
)


def optimize_vector_database(
    vector_db: VectorDatabase,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    batch_size: int = DEFAULT_BATCH_SIZE,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Optimize existing data in the vector database.

    Args:
        vector_db: Vector database instance
        chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters
        batch_size: Number of documents per batch
        dry_run: If True, don't actually modify the database

    Returns:
        Dictionary with optimization results

    """
    # 1. Get existing data from the vector database
    print("Retrieving existing data from vector database...")

    # Create a new connection with optimized settings
    vector_db.connect(optimize_for_large_datasets=True)

    # Get all documents
    try:
        all_data = vector_db.get()

        total_docs = len(all_data.get("ids", []))
        print(f"Found {total_docs} documents in vector database")

        if total_docs == 0:
            print("No documents to optimize")
            return {"success": True, "optimized": 0, "total": 0}
    except Exception as e:
        print(f"Error retrieving data: {e}")
        return {"success": False, "error": str(e)}

    # 2. Group documents by source document
    print("Grouping documents by source...")

    # Group by doc_id if available, otherwise create new groups
    doc_groups = {}

    for i, doc_id in enumerate(all_data.get("ids", [])):
        metadata = (
            all_data.get("metadatas", [])[i]
            if i < len(all_data.get("metadatas", []))
            else {}
        )
        document = (
            all_data.get("documents", [])[i]
            if i < len(all_data.get("documents", []))
            else ""
        )

        # Get source document ID
        source_id = (
            metadata.get("doc_id", "").split("-chunk-")[0]
            if "-chunk-" in metadata.get("doc_id", "")
            else metadata.get("doc_id", "")
        )

        if not source_id:
            # Create a new source ID if none exists
            source_id = f"doc-{uuid.uuid4()}"

        # Add to group
        if source_id not in doc_groups:
            doc_groups[source_id] = {"documents": [], "metadatas": [], "ids": []}

        doc_groups[source_id]["documents"].append(document)
        doc_groups[source_id]["metadatas"].append(metadata)
        doc_groups[source_id]["ids"].append(doc_id)

    print(f"Grouped into {len(doc_groups)} source documents")

    # 3. Process each group
    print("Processing document groups...")

    optimized_count = 0

    for source_id, group in doc_groups.items():
        print(f"Processing group {source_id} with {len(group['documents'])} chunks...")

        # Combine all chunks into a single document
        full_text = " ".join(group["documents"])

        # Get metadata from first chunk (assuming it's consistent across chunks)
        base_metadata = group["metadatas"][0] if group["metadatas"] else {}

        # Remove chunk-specific metadata
        if "chunk_id" in base_metadata:
            del base_metadata["chunk_id"]
        if "chunk_index" in base_metadata:
            del base_metadata["chunk_index"]

        # Ensure doc_id is set
        base_metadata["doc_id"] = source_id

        if not dry_run:
            # Delete existing chunks
            for chunk_id in group["ids"]:
                try:
                    vector_db.collection.delete(ids=[chunk_id])
                except Exception as e:
                    print(f"Error deleting chunk {chunk_id}: {e}")

            # Process document with optimized chunking
            chunks, chunk_metadatas, chunk_ids = process_document_with_metadata(
                text=full_text,
                metadata=base_metadata,
                chunk_size=chunk_size,
                overlap=overlap,
            )

            # Add optimized chunks
            vector_db.process_document_batch(
                documents=chunks,
                metadatas=chunk_metadatas,
                ids=chunk_ids,
                batch_size=batch_size,
            )

            print(
                f"  Replaced {len(group['documents'])} chunks with {len(chunks)} optimized chunks"
            )
            optimized_count += 1
        else:
            print(
                f"  Would replace {len(group['documents'])} chunks with optimized chunks (dry run)"
            )

    return {"success": True, "optimized": optimized_count, "total": len(doc_groups)}


def main() -> None:
    """Main function to optimize existing data in the GraphRAG system."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Optimize existing data in the GraphRAG system"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help="Maximum chunk size in characters",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=DEFAULT_OVERLAP,
        help="Overlap between chunks in characters",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help="Number of documents per batch",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Don't actually modify the database"
    )
    parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip confirmation prompt"
    )
    args = parser.parse_args()

    # Initialize vector database
    vector_db = VectorDatabase()

    # Verify connection
    if not vector_db.verify_connection():
        print("❌ Vector database connection failed!")
        return

    print("✅ Vector database connection verified!")

    # Confirm optimization
    if not args.yes and not args.dry_run:
        response = input(
            "This will optimize all existing data in the vector database. Continue? (y/n): "
        )
        if response.lower() != "y":
            print("Operation cancelled")
            return

    # Optimize vector database
    print("\nOptimizing vector database...")
    start_time = time.time()

    result = optimize_vector_database(
        vector_db=vector_db,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    )

    end_time = time.time()
    duration = end_time - start_time

    # Print summary
    print("\nOptimization completed!")
    print(f"Time taken: {duration:.2f} seconds")

    if result["success"]:
        if args.dry_run:
            print(f"Would have optimized {result['total']} documents (dry run)")
        else:
            print(f"Optimized {result['optimized']} of {result['total']} documents")
    else:
        print(f"Optimization failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
