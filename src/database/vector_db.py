"""
Vector database connection and operations for GraphRAG project.
"""
import logging
import os
import time
import uuid
from typing import Dict, List, Optional, Any, cast

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

# Import utility functions
from src.utils.db_utils import check_chromadb_version, check_database_directories

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default batch size for adding documents
DEFAULT_BATCH_SIZE = 100
# Default retry settings
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_BACKOFF = 1.0  # seconds

class VectorDatabase:
    """
    Vector database connection and operations for GraphRAG project.
    """
    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize vector database connection.

        Args:
            persist_directory: Directory to persist vector database
                (default: from environment variable)
        """
        self.persist_directory = persist_directory or os.getenv(
            "CHROMA_PERSIST_DIRECTORY", "./data/chromadb"
        )
        self.client = None
        self.collection = None

        # Check ChromaDB version
        self.version_check_passed = check_chromadb_version()
        if not self.version_check_passed:
            logger.warning("ChromaDB version check failed. Some features may not work correctly.")

        # Check database directories
        check_database_directories()

    def connect(self,
                collection_name: str = "ebook_chunks",
                optimize_for_large_datasets: bool = True) -> None:
        """
        Connect to vector database and get or create collection.

        Args:
            collection_name: Name of the collection to use
            optimize_for_large_datasets: Whether to optimize for large datasets
        """
        # Ensure the persist directory exists
        os.makedirs(self.persist_directory, exist_ok=True)

        try:
            # Create client with persistence using the new client format
            logger.info(f"Connecting to ChromaDB at {self.persist_directory}")
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,  # Disable telemetry
                    allow_reset=True,            # Allow database reset
                )
            )

            # Configure collection settings for large datasets
            collection_metadata = {
                "hnsw:space": "cosine",  # Use cosine similarity
            }

            if optimize_for_large_datasets:
                # Add HNSW index parameters optimized for large datasets
                # Create a new dictionary with all settings
                collection_metadata = {
                    "hnsw:space": "cosine",  # Use cosine similarity
                    # Increase the number of connections in the graph for better recall
                    "hnsw:construction_ef": 128,  # Default is 100
                    "hnsw:search_ef": 128,        # Default is 10
                    "hnsw:M": 16,                 # Default is 16
                    # Optimize for memory usage
                    "hnsw:num_threads": 4,        # Use multiple threads for indexing
                    # Segment size settings to avoid compaction errors
                    "chroma:segments:max_size_bytes": 1073741824,  # 1GB max segment size
                    "chroma:segments:target_size_bytes": 536870912  # 512MB target segment size
                }

            # Get or create collection with optimized settings
            logger.info(f"Getting or creating collection: {collection_name}")
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata=collection_metadata
            )
            logger.info(f"Successfully connected to collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error connecting to ChromaDB: {e}")
            raise

    def verify_connection(self) -> bool:
        """
        Verify vector database connection.

        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            self.connect()
            # Check if we can get collection info
            assert self.collection is not None, "Collection is None after connect()"
            self.collection.count()
            return True
        except Exception as e:
            print(f"Vector database connection error: {e}")
            return False

    def add_documents(self,
                     documents: List[str],
                     embeddings: Optional[List[List[float]]] = None,
                     metadatas: Optional[List[Dict[str, Any]]] = None,
                     ids: Optional[List[str]] = None,
                     batch_size: int = DEFAULT_BATCH_SIZE) -> None:
        """
        Add documents to vector database.

        Args:
            documents: List of document texts
            embeddings: List of document embeddings (optional)
            metadatas: List of document metadata (optional)
            ids: List of document IDs (optional)
            batch_size: Number of documents to add in each batch
        """
        if self.collection is None:
            self.connect()

        # Generate IDs if not provided
        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        # Process in batches to avoid memory issues and improve performance
        total_docs = len(documents)

        if total_docs <= batch_size:
            # Small enough to add in one batch
            self._add_batch_with_retry(documents, embeddings, metadatas, ids)
        else:
            # Process in batches
            logger.info(f"Adding {total_docs} documents in batches of {batch_size}...")

            for i in range(0, total_docs, batch_size):
                end_idx = min(i + batch_size, total_docs)
                batch_docs = documents[i:end_idx]
                batch_ids = ids[i:end_idx]

                # Handle embeddings and metadata if provided
                batch_embeddings = None
                if embeddings is not None:
                    batch_embeddings = embeddings[i:end_idx]

                batch_metadatas = None
                if metadatas is not None:
                    batch_metadatas = metadatas[i:end_idx]

                # Add batch with retry logic
                self._add_batch_with_retry(batch_docs, batch_embeddings, batch_metadatas, batch_ids)

                logger.info(f"  Added batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size}: "
                      f"documents {i+1}-{end_idx} of {total_docs}")

                # Small delay to avoid overwhelming the database
                time.sleep(0.1)


    def _add_batch_with_retry(self,
                             documents: List[str],
                             embeddings: Optional[List[List[float]]] = None,
                             metadatas: Optional[List[Dict[str, Any]]] = None,
                             ids: Optional[List[str]] = None,
                             max_retries: int = DEFAULT_MAX_RETRIES,
                             initial_backoff: float = DEFAULT_INITIAL_BACKOFF) -> bool:
        """
        Add a batch of documents to ChromaDB with exponential backoff retry logic.

        Args:
            documents: List of document texts
            embeddings: List of document embeddings (optional)
            metadatas: List of document metadata (optional)
            ids: List of document IDs (optional)
            max_retries: Maximum number of retry attempts
            initial_backoff: Initial backoff time in seconds

        Returns:
            True if the batch was added successfully, False otherwise.
        """
        retry_count = 0
        backoff = initial_backoff
        batch_id = str(uuid.uuid4())[:8]  # Generate a short ID for this batch for logging

        # Ensure we have a connection
        if self.collection is None:
            self.connect()

        # Ensure IDs are provided
        if ids is None:
            ids = [f"doc-{batch_id}-{i}" for i in range(len(documents))]

        # Log batch information
        logger.info(f"Adding batch {batch_id} with {len(documents)} documents")

        # Try to add the batch with retries
        while retry_count <= max_retries:
            try:
                # Add the batch
                assert self.collection is not None, "Collection is None"
                self.collection.add(
                    documents=documents,
                    embeddings=cast(Any, embeddings),
                    metadatas=cast(Any, metadatas),
                    ids=ids
                )

                logger.info(f"Successfully added batch {batch_id} with {len(documents)} documents")
                return True

            except Exception as e:
                retry_count += 1
                error_type = type(e).__name__

                if "compaction" in str(e).lower():
                    # Special handling for compaction errors
                    logger.warning(
                        f"ChromaDB compaction error in batch {batch_id}: {e}. "
                        f"This may indicate the database is too large or needs optimization."
                    )

                    # If this is the last retry, try with a smaller batch size
                    if retry_count > max_retries and len(documents) > 10:
                        logger.info(f"Attempting to split batch {batch_id} into smaller chunks")

                        # Split the batch in half
                        mid = len(documents) // 2

                        # Process first half
                        first_half_success = self._add_batch_with_retry(
                            documents=documents[:mid],
                            embeddings=embeddings[:mid] if embeddings else None,
                            metadatas=metadatas[:mid] if metadatas else None,
                            ids=ids[:mid],
                            max_retries=max_retries,
                            initial_backoff=initial_backoff
                        )

                        # Process second half
                        second_half_success = self._add_batch_with_retry(
                            documents=documents[mid:],
                            embeddings=embeddings[mid:] if embeddings else None,
                            metadatas=metadatas[mid:] if metadatas else None,
                            ids=ids[mid:],
                            max_retries=max_retries,
                            initial_backoff=initial_backoff
                        )

                        return first_half_success and second_half_success

                if retry_count <= max_retries:
                    logger.warning(
                        f"Error adding batch {batch_id} to ChromaDB ({error_type}): {e}. "
                        f"Retry {retry_count}/{max_retries} in {backoff}s"
                    )
                    time.sleep(backoff)
                    backoff *= 2  # Exponential backoff
                else:
                    logger.error(
                        f"Failed to add batch {batch_id} after {max_retries} retries. "
                        f"Last error ({error_type}): {e}"
                    )
                    return False

        # This should never be reached due to the return statements above,
        # but adding it to satisfy the function's return type
        return False

    def query(self,
             query_texts: Optional[List[str]] = None,
             query_embeddings: Optional[List[List[float]]] = None,
             n_results: int = 5,
             where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Query vector database.

        Args:
            query_texts: List of query texts
            query_embeddings: List of query embeddings
            n_results: Number of results to return
            where: Filter query by metadata

        Returns:
            Query results
        """
        if self.collection is None:
            self.connect()

        # Use type assertion to handle potential None value
        assert self.collection is not None, "Collection is None after connect()"

        # Use type casting to handle type compatibility issues
        result = self.collection.query(
            query_texts=query_texts,
            query_embeddings=cast(Any, query_embeddings),
            n_results=n_results,
            where=where
        )

        # Convert the result to a dictionary
        return cast(Dict[str, Any], result)

    def get(self,
           ids: Optional[List[str]] = None,
           where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get documents from vector database.

        Args:
            ids: List of document IDs
            where: Filter query by metadata

        Returns:
            Documents
        """
        if self.collection is None:
            self.connect()

        # Use type assertion to handle potential None value
        assert self.collection is not None, "Collection is None after connect()"

        # Use type casting to handle type compatibility issues
        result = self.collection.get(
            ids=ids,
            where=where
        )

        # Convert the result to a dictionary
        return cast(Dict[str, Any], result)

    def count(self) -> int:
        """
        Count documents in vector database.

        Returns:
            Number of documents
        """
        if self.collection is None:
            self.connect()

        # Use type assertion to handle potential None value
        assert self.collection is not None, "Collection is None after connect()"
        return self.collection.count()

    def process_document_batch(self,
                          documents: List[str],
                          metadatas: List[Dict[str, Any]],
                          ids: Optional[List[str]] = None,
                          batch_size: int = DEFAULT_BATCH_SIZE) -> None:
        """
        Process a batch of documents with optimized settings.

        This method handles:
        1. Metadata optimization for efficient filtering
        2. Batch processing to avoid memory issues
        3. Proper ID generation if not provided

        Args:
            documents: List of document texts
            metadatas: List of document metadata
            ids: List of document IDs (optional)
            batch_size: Number of documents per batch
        """
        from src.processing.document_processor import optimize_metadata

        # Ensure connection
        if self.collection is None:
            self.connect()

        # Generate IDs if not provided
        if ids is None:
            ids = [f"doc-{i}" for i in range(len(documents))]

        # Optimize metadata for each document
        optimized_metadatas = [optimize_metadata(meta) for meta in metadatas]

        # Add documents in batches
        self.add_documents(
            documents=documents,
            metadatas=optimized_metadatas,
            ids=ids,
            batch_size=batch_size
        )

    def create_dummy_data(self) -> None:
        """
        Create dummy data for testing.
        """
        if self.collection is None:
            self.connect()

        # Create some dummy documents with metadata linking to Neo4j nodes
        documents = [
            "Neural networks are a set of algorithms, modeled loosely after the human brain, that are designed to recognize patterns.",
            "Decision trees are a non-parametric supervised learning method used for classification and regression.",
            "Gradient descent is an optimization algorithm used to minimize some function by iteratively moving in the direction of steepest descent."
        ]

        # Metadata linking to Neo4j nodes
        metadatas = [
            {
                "book_id": "book-001",
                "chapter_id": "chapter-001",
                "section_id": "section-001",
                "concept_id": "concept-001",
                "title": "Neural Networks",
                "source": "Introduction to Machine Learning"
            },
            {
                "book_id": "book-001",
                "chapter_id": "chapter-001",
                "section_id": "section-001",
                "concept_id": "concept-002",
                "title": "Decision Trees",
                "source": "Introduction to Machine Learning"
            },
            {
                "book_id": "book-001",
                "chapter_id": "chapter-001",
                "section_id": "section-002",
                "concept_id": "concept-003",
                "title": "Gradient Descent",
                "source": "Introduction to Machine Learning"
            }
        ]

        # IDs matching Neo4j node IDs for concepts
        ids = ["chunk-concept-001", "chunk-concept-002", "chunk-concept-003"]

        # Add documents
        self.add_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )