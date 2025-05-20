"""Test script to add a document using the API."""

import json
import os
import sys

import requests

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_port

# Get API port from centralized configuration
api_port = get_port("api")


def test_api_add_document():
    """Test adding a document via the API."""
    api_url = f"http://localhost:{api_port}/documents"

    # Prepare document to add with explicit concepts
    document = {
        "text": """
        Retrieval-Augmented Generation (RAG) is a technique that enhances Large Language Models (LLMs)
        by retrieving relevant information from external knowledge sources before generating responses.

        GraphRAG extends traditional RAG by incorporating graph databases like Neo4j alongside vector
        databases. This hybrid approach allows for more contextual understanding by capturing relationships
        between concepts, not just semantic similarity.

        Key concepts in GraphRAG include:
        1. Knowledge Graphs - Storing relationships between entities
        2. Vector Embeddings - Numerical representations of text for semantic search
        3. Hybrid Search - Combining graph traversal with vector similarity
        4. Deduplication - Ensuring unique concepts despite different references

        GraphRAG provides more comprehensive and accurate responses by leveraging both the structured
        relationships in graphs and the semantic understanding from vector embeddings.
        """,
        "metadata": {
            "title": "GraphRAG and RAG Concepts",
            "source": "Test Document",
            "author": "Test Script",
            "concepts": "RAG,GraphRAG,Knowledge Graphs,Vector Embeddings,Hybrid Search,Deduplication,LLM",
        },
    }

    print(f"Sending document to {api_url}...")
    response = requests.post(api_url, json=document)

    print(f"Status code: {response.status_code}")
    print("\nResponse:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

    return response.status_code == 200 or response.status_code == 201


def test_api_add_folder():
    """Test adding a folder via the API."""
    api_url = f"http://localhost:{api_port}/folders"  # Assuming /folders endpoint for adding folders

    # Prepare data for adding a folder - specify the path to a test folder
    folder_data = {
        "folder_path": "example_docs/"  # Use an existing folder with test documents
    }

    print(f"Sending folder path to {api_url}...")
    response = requests.post(api_url, json=folder_data)

    print(f"Status code: {response.status_code}")
    print("\nResponse:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

    # Expecting a success status code (e.g., 200 or 201)
    return response.status_code == 200 or response.status_code == 201


if __name__ == "__main__":
    success_document = test_api_add_document()
    success_folder = test_api_add_folder()  # Add the new test call

    if not success_document or not success_folder:
        sys.exit(1)
