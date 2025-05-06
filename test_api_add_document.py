"""
Test script to add a document using the API.
"""
import requests
import json
import sys

def test_api_add_document():
    """Test adding a document via the API."""
    api_url = "http://localhost:5001/api/documents"
    
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
            "concepts": "RAG,GraphRAG,Knowledge Graphs,Vector Embeddings,Hybrid Search,Deduplication,LLM"
        }
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

if __name__ == "__main__":
    success = test_api_add_document()
    if not success:
        sys.exit(1)
