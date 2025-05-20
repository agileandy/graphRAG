#!/usr/bin/env python3
"""Test script for the embedding model update.

This script tests the embedding model and reranker functionality.
"""

import logging
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.vector_db import VectorDatabase
from src.llm.llm_provider import create_llm_provider
from src.search.reranker import Reranker
from src.utils.config import (
    get_embedding_provider_config,
    get_reranker_provider_config,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_embedding_provider() -> bool | None:
    """Test the embedding provider."""
    print("\n=== Testing Embedding Provider ===")

    # Load configuration
    config = get_embedding_provider_config()
    print(f"Embedding provider configuration: {config}")

    # Create embedding provider
    try:
        provider = create_llm_provider(config)
        print(f"Created embedding provider: {provider.__class__.__name__}")

        # Test getting embeddings
        texts = [
            "This is a test sentence for embeddings.",
            "Another test sentence to check embedding dimensions.",
        ]

        print(f"Getting embeddings for {len(texts)} texts...")
        embeddings = provider.get_embeddings(texts)

        # Check embeddings
        if embeddings and len(embeddings) > 0:
            print("Successfully generated embeddings!")
            print(f"Embedding dimensions: {len(embeddings[0])}")
            print(f"First few values of first embedding: {embeddings[0][:5]}...")
            return True
        else:
            print("Failed to generate embeddings.")
            return False
    except Exception as e:
        print(f"Error testing embedding provider: {e}")
        return False


def test_reranker() -> bool | None:
    """Test the reranker."""
    print("\n=== Testing Reranker ===")

    # Load configuration
    config = get_reranker_provider_config()
    print(f"Reranker configuration: {config}")

    # Create reranker
    try:
        reranker = Reranker(config=config)
        print(f"Created reranker with provider: {reranker.provider.__class__.__name__}")

        # Test reranking
        query = "What is machine learning?"
        documents = [
            {
                "text": "Machine learning is a branch of artificial intelligence.",
                "id": "doc1",
            },
            {"text": "Deep learning is a subset of machine learning.", "id": "doc2"},
            {
                "text": "Python is a programming language often used for data science.",
                "id": "doc3",
            },
            {
                "text": "Neural networks are used in deep learning applications.",
                "id": "doc4",
            },
            {"text": "The weather today is sunny and warm.", "id": "doc5"},
        ]

        print(f"Reranking {len(documents)} documents for query: '{query}'")
        reranked_docs = reranker.rerank(query, documents)

        # Check reranked documents
        if reranked_docs and len(reranked_docs) > 0:
            print("Successfully reranked documents!")
            print("\nReranked documents (in order of relevance):")
            for i, doc in enumerate(reranked_docs):
                print(f"{i + 1}. [{doc.get('score', 0):.4f}] {doc.get('text', '')}")
            return True
        else:
            print("Failed to rerank documents.")
            return False
    except Exception as e:
        print(f"Error testing reranker: {e}")
        return False


def test_vector_db_reranking() -> bool | None:
    """Test vector database with reranking."""
    print("\n=== Testing Vector Database with Reranking ===")

    # Create vector database
    try:
        vector_db = VectorDatabase()
        print("Created vector database")

        # Verify connection
        if not vector_db.verify_connection():
            print("Failed to connect to vector database.")
            return False

        # Create dummy data if needed
        if vector_db.count() == 0:
            print("Creating dummy data...")
            vector_db.create_dummy_data()

        # Test query with reranking
        query = "neural networks"
        print(f"Querying vector database for: '{query}'")

        # First without reranking
        print("\nResults without reranking:")
        results = vector_db.query(query_texts=[query], n_results=3)
        if "documents" in results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                print(f"{i + 1}. {doc}")
        else:
            print("No results found.")

        # Then with reranking
        print("\nResults with reranking:")
        reranked_results = vector_db.query(
            query_texts=[query], n_results=3, rerank=True
        )
        if "documents" in reranked_results and reranked_results["documents"]:
            for i, doc in enumerate(reranked_results["documents"][0]):
                print(f"{i + 1}. {doc}")
        else:
            print("No results found.")

        return True
    except Exception as e:
        print(f"Error testing vector database with reranking: {e}")
        return False


def main() -> int:
    """Main function."""
    print("Testing embedding model update...")

    # Test embedding provider
    embedding_success = test_embedding_provider()

    # Test reranker
    reranker_success = test_reranker()

    # Test vector database with reranking
    vector_db_success = test_vector_db_reranking()

    # Print summary
    print("\n=== Test Summary ===")
    print(f"Embedding Provider: {'✅ Success' if embedding_success else '❌ Failed'}")
    print(f"Reranker: {'✅ Success' if reranker_success else '❌ Failed'}")
    print(f"Vector DB Reranking: {'✅ Success' if vector_db_success else '❌ Failed'}")

    if embedding_success and reranker_success and vector_db_success:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
