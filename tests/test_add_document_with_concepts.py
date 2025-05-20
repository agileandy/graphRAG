"""Test script for the modified add_document_with_concepts.py."""

import os
import sys
import unittest

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.document_processing.add_document_with_concepts import (
    add_document_to_graphrag,
)
from src.config import get_port
from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase


class TestAddDocumentWithConcepts(unittest.TestCase):
    """Test case for adding a document with concepts."""

    def setUp(self) -> None:
        """Set up test environment: initialize databases."""
        print("\nSetting up test environment...")
        # Get Neo4j port from centralized configuration
        docker_neo4j_port = get_port("docker_neo4j_bolt")

        # Initialize databases with Docker container connection details
        self.neo4j_db = Neo4jDatabase(
            uri=f"bolt://localhost:{docker_neo4j_port}",
            username="neo4j",
            password="graphrag",
        )
        self.vector_db = VectorDatabase()

        # Verify connections
        self.assertTrue(self.neo4j_db.verify_connection(), "Neo4j connection failed!")
        self.assertTrue(
            self.vector_db.verify_connection(), "Vector database connection failed!"
        )
        print("✅ Database connections verified!")

    def tearDown(self) -> None:
        """Clean up test environment: close database connections."""
        print("\nTearing down test environment...")
        self.neo4j_db.close()
        # Add cleanup for vector_db if necessary

    def test_add_document_with_concepts_success(self) -> None:
        """Test adding a document with concepts successfully."""
        print("\nRunning test_add_document_with_concepts_success...")
        # Example document
        document_text = """
        GraphRAG: Enhancing Retrieval-Augmented Generation with Knowledge Graphs

        Retrieval-Augmented Generation (RAG) is a technique that enhances Large Language Models (LLMs)
        by retrieving relevant information from external knowledge sources before generating responses.

        GraphRAG extends traditional RAG by incorporating graph databases like Neo4j alongside vector
        databases such as ChromaDB. This hybrid approach allows for more contextual understanding by
        capturing relationships between concepts, not just semantic similarity.

        Key concepts in GraphRAG include:
        1. Knowledge Graphs - Storing relationships between entities
        2. Vector Embeddings - Numerical representations of text for semantic search
        3. Hybrid Search - Combining graph traversal with vector similarity
        4. Deduplication - Ensuring unique concepts despite different references

        GraphRAG provides more comprehensive and accurate responses by leveraging both the structured
        relationships in graphs and the semantic understanding from vector embeddings.
        """

        # Document metadata with explicit concepts
        document_metadata = {
            "title": "GraphRAG and RAG Concepts",
            "author": "Test Script",
            "source": "Test Document",
            "concepts": "RAG,GraphRAG,Knowledge Graphs,Vector Embeddings,Hybrid Search,Deduplication,LLM",
        }

        # Add document to GraphRAG system
        print("\nAdding document to GraphRAG system...")
        result = add_document_to_graphrag(
            text=document_text,
            metadata=document_metadata,
            neo4j_db=self.neo4j_db,
            vector_db=self.vector_db,
        )

        # Assertions
        self.assertIsNotNone(
            result.get("document_id"), "Document ID should not be None"
        )
        self.assertGreater(
            len(result.get("entities", [])), 0, "Should extract at least one entity"
        )
        self.assertGreater(
            len(result.get("relationships", [])),
            0,
            "Should extract at least one relationship",
        )

        # Verify concepts in Neo4j
        print("\nVerifying concepts in Neo4j:")
        query = """
        MATCH (c:Concept)
        RETURN c.id AS id, c.name AS name
        """
        concepts = self.neo4j_db.run_query(query)
        self.assertGreater(len(concepts), 0, "Should find concepts in Neo4j")

        print("\n✅ test_add_document_with_concepts_success completed!")


if __name__ == "__main__":
    unittest.main()
