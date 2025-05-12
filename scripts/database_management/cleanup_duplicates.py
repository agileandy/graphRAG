import sys
import os
import logging
from collections import defaultdict

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from database.neo4j_db import Neo4jDatabase
from database.vector_db import VectorDatabase
# generate_document_hash is a method of DuplicateDetector, no need to import separately

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_and_report_duplicates():
    """Find and report duplicate documents in the database."""
    logger.info("Starting duplicate detection and reporting...")
    try:
        vector_db = VectorDatabase()
        vector_db.connect('documents') # Connect to the 'documents' collection
        collection = vector_db.collection # Access the collection after connecting

        if collection is None:
             logger.error("Failed to connect to ChromaDB collection.")
             return None

        # Get all documents (this might be slow for very large databases)
        # Consider fetching in batches if performance is an issue
        all_docs = collection.get(include=['metadatas'])

        if not all_docs or not all_docs.get('ids'):
            logger.info("No documents found in the collection.")
            return {
                'total_documents': 0,
                'unique_documents': 0,
                'duplicate_sets': 0,
                'duplicates': {}
            }

        # Group by hash
        docs_by_hash = defaultdict(list)
        # Instantiate DuplicateDetector to use generate_document_hash method
        # duplicate_detector = DuplicateDetector(vector_db) # Not needed here

        # Ensure all_docs is not None and contains 'ids' and 'metadatas' which are lists of the same length
        if all_docs and isinstance(all_docs.get('ids'), list) and isinstance(all_docs.get('metadatas'), list) and len(all_docs['ids']) == len(all_docs['metadatas']):
            ids = all_docs['ids']
            metadatas = all_docs['metadatas']
            for i, doc_id in enumerate(ids):
                metadata = metadatas[i]
                doc_hash = metadata.get('hash') # Get hash from metadata

                if doc_hash:
                    docs_by_hash[doc_hash].append({
                        'id': doc_id,
                        'title': metadata.get('title', 'N/A'),
                        'filepath': metadata.get('filepath', 'N/A')
                    })
                else:
                    logger.warning(f"Document {doc_id} is missing hash metadata.")
        else:
             logger.warning("Could not retrieve document IDs and metadatas correctly from ChromaDB.")


        # Find duplicates (hashes with more than one document)
        duplicates = {h: docs for h, docs in docs_by_hash.items() if len(docs) > 1}

        # Generate report
        report = {
            'total_documents': len(all_docs.get('ids', []) if all_docs and isinstance(all_docs.get('ids'), list) else []), # Handle potential None or non-list
            'unique_documents': len(docs_by_hash),
            'duplicate_sets': len(duplicates),
            'duplicates': duplicates
        }

        logger.info(f"Duplicate detection complete. Found {len(duplicates)} duplicate sets.")
        return report

    except Exception as e:
        logger.error(f"An error occurred during duplicate detection: {e}")
        return None

def remove_duplicate_document(doc_id_to_remove, neo4j_db: Neo4jDatabase):
    """
    Safely remove a duplicate document from ChromaDB and update Neo4j relationships.
    This is a placeholder and requires careful implementation to preserve relationships.
    """
    logger.info(f"Attempting to remove duplicate document with ID: {doc_id_to_remove}")
    try:
        vector_db = VectorDatabase()
        vector_db.connect('documents') # Connect to the 'documents' collection
        collection = vector_db.collection # Access the collection after connecting

        if collection is None:
             logger.error("Failed to connect to ChromaDB collection for removal.")
             return False

        # TODO: Implement logic to identify the 'master' document and transfer relationships
        # from the duplicate to the master in Neo4j before removing the duplicate.
        # This will require querying Neo4j for relationships connected to doc_id_to_remove
        # and re-pointing them to the master document's ID.

        # Example placeholder for removal (DO NOT USE IN PRODUCTION WITHOUT RELATIONSHIP HANDLING)
        # collection.delete(ids=[doc_id_to_remove])
        # logger.info(f"Document {doc_id_to_remove} removed from ChromaDB (relationships NOT handled).")

        logger.warning(f"Removal of document {doc_id_to_remove} skipped. Safe removal with relationship handling is not yet implemented.")
        return False # Indicate removal was not performed

    except Exception as e:
        logger.error(f"An error occurred during duplicate removal for {doc_id_to_remove}: {e}")
        return False

if __name__ == "__main__":
    report = find_and_report_duplicates()
    if report:
        print("--- Duplicate Report ---")
        print(f"Total Documents: {report['total_documents']}")
        print(f"Unique Documents: {report['unique_documents']}")
        print(f"Duplicate Sets: {report['duplicate_sets']}")
        print("\nDetails:")
        if report['duplicate_sets'] > 0:
            for hash_val, docs in report['duplicates'].items():
                print(f"\nHash: {hash_val}")
                for doc in docs:
                    print(f"  - ID: {doc['id']}, Title: {doc['title']}, Filepath: {doc['filepath']}")
        else:
            print("No duplicate documents found.")

    # Example of how removal might be called (requires implementation)
    # neo4j_db = Neo4jDatabase()
    # # Assuming you want to remove the second document in the first duplicate set found
    # if report and report['duplicate_sets'] > 0:
    #     first_duplicate_set_hash = list(report['duplicates'].keys())[0]
    #     if len(report['duplicates'][first_duplicate_set_hash]) > 1:
    #         doc_to_remove_id = report['duplicates'][first_duplicate_set_hash][1]['id']
    #         # remove_duplicate_document(doc_to_remove_id, neo4j_db)
    # neo4j_db.close()