"""
Vector database connection and operations for GraphRAG project.
"""
import logging
import os
import time
import uuid
import shutil
from typing import Dict, List, Optional, Any, cast, Tuple

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv

# Import utility functions
from src.utils.db_utils import check_chromadb_version, check_database_directories

# Forward declaration to avoid circular imports
ChromaDuplicateDetector = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Explicitly load environment variables from the config file
config_env_path = os.path.expanduser("~/.graphrag/config.env")
if os.path.exists(config_env_path):
    logger.info(f"Loading environment variables from {config_env_path}")
    load_dotenv(config_env_path)
else:
    logger.warning(f"Config file not found at {config_env_path}, falling back to default .env")
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
        # Explicitly load environment variables again to ensure they're available in this instance
        config_env_path = os.path.expanduser("~/.graphrag/config.env")
        if os.path.exists(config_env_path):
            logger.info(f"Loading environment variables from {config_env_path} in VectorDatabase.__init__")
            load_dotenv(config_env_path)

        # Get the persist directory from the environment or use the provided value
        self.persist_directory = persist_directory or os.getenv(
            "CHROMA_PERSIST_DIRECTORY", "./data/chromadb"
        )

        # Convert to absolute path if it's a relative path
        if not os.path.isabs(self.persist_directory):
            self.persist_directory = os.path.abspath(self.persist_directory)

        # Log the directory being used for debugging
        logger.info(f"Using ChromaDB directory: {self.persist_directory}")

        self.client = None
        self.collection = None
        self.duplicate_detector = None

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

            # Initialize duplicate detector to None
            # We'll initialize it properly when needed to avoid circular imports
            self.duplicate_detector = None

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
            logger.info(f"Verifying connection to ChromaDB at {self.persist_directory}")
            self.connect()

            # Check if we can get collection info
            assert self.collection is not None, "Collection is None after connect()"
            count = self.collection.count()

            logger.info(f"Successfully connected to ChromaDB. Collection contains {count} documents.")
            return True
        except Exception as e:
            logger.error(f"Vector database connection error: {e}")
            return False

    def add_documents(self,
                     documents: List[str],
                     embeddings: Optional[List[List[float]]] = None,
                     metadatas: Optional[List[Dict[str, Any]]] = None,
                     ids: Optional[List[str]] = None,
                     batch_size: int = DEFAULT_BATCH_SIZE,
                     check_duplicates: bool = True) -> None:
        """
        Add documents to vector database.

        Args:
            documents: List of document texts
            embeddings: List of document embeddings (optional)
            metadatas: List of document metadata (optional)
            ids: List of document IDs (optional)
            batch_size: Number of documents to add in each batch
            check_duplicates: Whether to check for duplicates before adding
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
            self._add_batch_with_retry(documents, embeddings, metadatas, ids, check_duplicates)
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
                self._add_batch_with_retry(batch_docs, batch_embeddings, batch_metadatas, batch_ids, check_duplicates)

                logger.info(f"  Added batch {i//batch_size + 1}/{(total_docs + batch_size - 1)//batch_size}: "
                      f"documents {i+1}-{end_idx} of {total_docs}")

                # Small delay to avoid overwhelming the database
                time.sleep(0.1)

    def _add_batch_with_retry(self,
                             documents: List[str],
                             embeddings: Optional[List[List[float]]] = None,
                             metadatas: Optional[List[Dict[str, Any]]] = None,
                             ids: Optional[List[str]] = None,
                             check_duplicates: bool = True,
                             max_retries: int = DEFAULT_MAX_RETRIES,
                             initial_backoff: float = DEFAULT_INITIAL_BACKOFF) -> bool:
        """
        Add a batch of documents to ChromaDB with exponential backoff retry logic.

        Args:
            documents: List of document texts
            embeddings: List of document embeddings (optional)
            metadatas: List of document metadata (optional)
            ids: List of document IDs (optional)
            check_duplicates: Whether to check for duplicates before adding
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

        # Check for duplicates if requested
        if check_duplicates and metadatas:
            # Make sure duplicate detector is initialized
            if self.duplicate_detector is None and self.collection is not None:
                # Import here to avoid circular imports
                from src.processing.duplicate_detector import DuplicateDetector
                self.duplicate_detector = DuplicateDetector(self)

            if self.duplicate_detector is not None:
                # Filter out duplicates
                non_duplicate_indices = []
                for i, metadata in enumerate(metadatas):
                    # Get the document text
                    doc_text = documents[i] if i < len(documents) else ""
                    is_duplicate, _, _ = self.duplicate_detector.is_duplicate(doc_text, metadata)
                    if not is_duplicate:
                        non_duplicate_indices.append(i)

                if len(non_duplicate_indices) < len(documents):
                    logger.info(f"Filtered out {len(documents) - len(non_duplicate_indices)} duplicate documents")

                # Update lists to only include non-duplicates
                documents = [documents[i] for i in non_duplicate_indices]
                ids = [ids[i] for i in non_duplicate_indices]
                if embeddings:
                    embeddings = [embeddings[i] for i in non_duplicate_indices]
                if metadatas:
                    metadatas = [metadatas[i] for i in non_duplicate_indices]

                if not documents:
                    logger.info("All documents in batch were duplicates, skipping")
                    return True
            else:
                logger.warning("Duplicate detector not initialized, skipping duplicate check")

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
                            check_duplicates=check_duplicates,
                            max_retries=max_retries,
                            initial_backoff=initial_backoff
                        )

                        # Process second half
                        second_half_success = self._add_batch_with_retry(
                            documents=documents[mid:],
                            embeddings=embeddings[mid:] if embeddings else None,
                            metadatas=metadatas[mid:] if metadatas else None,
                            ids=ids[mid:],
                            check_duplicates=check_duplicates,
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
             where: Optional[Dict[str, Any]] = None,
             rerank: bool = False,
             rerank_top_k: Optional[int] = None) -> Dict[str, Any]:
        """
        Query vector database.

        Args:
            query_texts: List of query texts
            query_embeddings: List of query embeddings
            n_results: Number of results to return
            where: Filter query by metadata
            rerank: Whether to rerank results using a reranker
            rerank_top_k: Number of top results to return after reranking (defaults to n_results)

        Returns:
            Query results
        """
        if self.collection is None:
            self.connect()

        # Use type assertion to handle potential None value
        assert self.collection is not None, "Collection is None after connect()"

        # If reranking is requested, we need to get more results initially
        initial_n_results = n_results * 3 if rerank else n_results

        try:
            # Use type casting to handle type compatibility issues
            result = self.collection.query(
                query_texts=query_texts,
                query_embeddings=cast(Any, query_embeddings),
                n_results=initial_n_results,
                where=where
            )
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error during vector search: {error_message}")

            # Check if this is an HNSW index error
            if "hnsw" in error_message.lower() or "index" in error_message.lower():
                logger.warning("Detected HNSW index error, attempting to repair...")

                # Try to repair the index
                success, repair_message = self.repair_index()
                if success:
                    logger.info(f"Index repair successful: {repair_message}")

                    # Try the query again
                    try:
                        result = self.collection.query(
                            query_texts=query_texts,
                            query_embeddings=cast(Any, query_embeddings),
                            n_results=initial_n_results,
                            where=where
                        )
                        logger.info("Query successful after index repair")
                    except Exception as e2:
                        # Still failed, return empty results
                        logger.error(f"Query still failed after index repair: {e2}")
                        return self._create_empty_result()
                else:
                    logger.error(f"Index repair failed: {repair_message}")
                    return self._create_empty_result()
            else:
                # Not an index error, return empty results
                return self._create_empty_result()

        # Apply reranking if requested
        if rerank and query_texts and len(query_texts) > 0 and "documents" in result and result["documents"] and len(result["documents"]) > 0:
            try:
                # Import here to avoid circular imports
                from src.search.reranker import Reranker

                # Create reranker
                reranker = Reranker()

                # Prepare documents for reranking
                docs_to_rerank = []
                for i, doc_list in enumerate(result["documents"]):
                    for j, doc in enumerate(doc_list):
                        # Create document with text and metadata
                        metadata = {}
                        if "metadatas" in result and i < len(result["metadatas"]) and j < len(result["metadatas"][i]):
                            metadata = result["metadatas"][i][j]

                        doc_id = f"doc-{i}-{j}"
                        if "ids" in result and i < len(result["ids"]) and j < len(result["ids"][i]):
                            doc_id = result["ids"][i][j]

                        doc_dict = {
                            "text": doc,
                            "metadata": metadata,
                            "id": doc_id,
                            "original_index": (i, j)  # Store original indices for reconstruction
                        }
                        docs_to_rerank.append(doc_dict)

                # Rerank documents
                reranked_docs = reranker.rerank(
                    query=query_texts[0],  # Use the first query text
                    documents=docs_to_rerank,
                    top_k=rerank_top_k or n_results
                )

                # Reconstruct result with reranked documents
                reranked_result = {
                    "ids": [[] for _ in range(len(query_texts))],
                    "documents": [[] for _ in range(len(query_texts))],
                    "metadatas": [[] for _ in range(len(query_texts))],
                    "distances": [[] for _ in range(len(query_texts))]
                }

                # Add reranked documents to result
                for doc in reranked_docs:
                    i, j = doc["original_index"]
                    reranked_result["ids"][0].append(doc["id"])
                    reranked_result["documents"][0].append(doc["text"])
                    reranked_result["metadatas"][0].append(doc["metadata"])

                    # Use original distance or the reranker score (inverted since lower is better for distances)
                    distance = 0.0
                    if "score" in doc:
                        distance = 1.0 - doc["score"]
                    elif "distances" in result and i < len(result["distances"]) and j < len(result["distances"][i]):
                        distance = result["distances"][i][j]

                    reranked_result["distances"][0].append(distance)

                return reranked_result
            except Exception as e:
                logger.error(f"Error during reranking: {e}")
                # Fall back to original results
                logger.info("Falling back to original results without reranking")

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

    def _create_empty_result(self) -> Dict[str, Any]:
        """
        Create an empty result structure for when queries fail.

        Returns:
            Empty result dictionary with the same structure as a normal query result
        """
        return {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }

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

    def check_index_health(self) -> Tuple[bool, str]:
        """
        Check the health of the vector database index.

        This method attempts to perform a simple query to verify that the HNSW index
        is functioning correctly.

        Returns:
            Tuple of (is_healthy, message)
        """
        if self.collection is None:
            try:
                self.connect()
            except Exception as e:
                return False, f"Failed to connect to vector database: {e}"

        try:
            # Try to get the count of documents
            count = self.collection.count()
            logger.info(f"Vector database contains {count} documents")

            if count == 0:
                # No documents to query
                return True, "Vector database is empty but healthy"

            # Try a simple query to verify index functionality
            result = self.collection.query(
                query_texts=["test query to verify index health"],
                n_results=1
            )

            # If we get here, the query was successful
            return True, f"Vector database index is healthy, contains {count} documents"

        except Exception as e:
            error_message = str(e)
            logger.error(f"Vector database index health check failed: {error_message}")

            # Check for specific HNSW index errors
            if "hnsw" in error_message.lower() or "index" in error_message.lower():
                return False, f"HNSW index appears to be corrupted: {error_message}"

            return False, f"Vector database health check failed: {error_message}"

    def repair_index(self) -> Tuple[bool, str]:
        """
        Attempt to repair the vector database index.

        This method tries to repair the index by:
        1. Backing up the current database
        2. Creating a new collection with the same settings
        3. Migrating data from the backup if possible

        Returns:
            Tuple of (success, message)
        """
        if self.collection is None:
            try:
                self.connect()
            except Exception as e:
                return False, f"Failed to connect to vector database: {e}"

        collection_name = self.collection.name
        logger.info(f"Attempting to repair index for collection: {collection_name}")

        # Step 1: Create a backup of the current database
        backup_dir = f"{self.persist_directory}_backup_{int(time.time())}"
        try:
            logger.info(f"Creating backup of vector database at {backup_dir}")
            shutil.copytree(self.persist_directory, backup_dir)
            logger.info("Backup created successfully")
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False, f"Failed to create backup: {e}"

        # Step 2: Try to get existing data
        documents = []
        metadatas = []
        ids = []
        embeddings = []
        has_data = False

        try:
            # Get all documents from the collection
            if self.collection is not None:
                all_docs = self.collection.get()
                if all_docs:
                    documents = all_docs.get("documents", [])
                    metadatas = all_docs.get("metadatas", [])
                    ids = all_docs.get("ids", [])
                    embeddings = all_docs.get("embeddings", [])

                    has_data = len(documents) > 0
                    logger.info(f"Retrieved {len(documents)} documents from existing collection")
        except Exception as e:
            logger.error(f"Failed to retrieve documents from collection: {e}")
            has_data = False

        # Step 3: Reset the collection
        try:
            if collection_name:
                logger.info(f"Resetting collection: {collection_name}")
                if self.client is not None:
                    self.client.delete_collection(collection_name)
                else:
                    # Reconnect if client is None
                    self.connect()
                    if self.client is not None:
                        self.client.delete_collection(collection_name)

                # Reconnect to create a new collection
                self.collection = None
                self.connect(collection_name=collection_name)

                logger.info(f"Collection {collection_name} reset successfully")
            else:
                logger.error("Collection name is None or empty")
                return False, "Collection name is None or empty"
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            return False, f"Failed to reset collection: {e}"

        # Step 4: Restore data if we have it
        if has_data and documents:
            try:
                doc_count = len(documents)
                logger.info(f"Restoring {doc_count} documents to the new collection")

                # Add documents in batches
                batch_size = 100
                for i in range(0, doc_count, batch_size):
                    end_idx = min(i + batch_size, doc_count)

                    batch_docs = documents[i:end_idx]
                    batch_ids = ids[i:end_idx] if ids else None

                    # Handle metadatas and embeddings safely
                    batch_metadatas = None
                    if metadatas and i < len(metadatas):
                        batch_metadatas = metadatas[i:end_idx]

                    batch_embeddings = None
                    if embeddings and i < len(embeddings):
                        batch_embeddings = embeddings[i:end_idx]

                    # Cast to appropriate types to satisfy type checker
                    self.add_documents(
                        documents=batch_docs,
                        embeddings=cast(Optional[List[List[float]]], batch_embeddings),
                        metadatas=cast(Optional[List[Dict[str, Any]]], batch_metadatas),
                        ids=batch_ids,
                        check_duplicates=False  # Skip duplicate check since we're restoring
                    )

                logger.info("Data restoration completed successfully")
                return True, f"Index repaired and {doc_count} documents restored"
            except Exception as e:
                logger.error(f"Failed to restore data: {e}")
                return False, f"Index repaired but failed to restore data: {e}"

        return True, "Index repaired (no data to restore)"

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