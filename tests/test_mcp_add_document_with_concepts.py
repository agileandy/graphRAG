"""Test script for MPC server add-document functionality with concepts."""

import asyncio
import json
import sys

import websockets


async def test_add_document_with_concepts(uri) -> bool | None:
    """Test add-document functionality with concepts."""
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")

            # Prepare document to add with explicit concepts
            text = """
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
            """

            metadata = {
                "title": "GraphRAG and RAG Concepts",
                "source": "Test Document",
                "author": "Test Script",
                "concepts": "RAG,GraphRAG,Knowledge Graphs,Vector Embeddings,Hybrid Search,Deduplication,LLM",
            }

            # Prepare add-document message
            message = {"action": "add-document", "text": text, "metadata": metadata}

            print("Sending document with concepts to add...")
            await websocket.send(json.dumps(message))

            print("Waiting for response...")
            response = await websocket.recv()

            print("\nAdd document result:")
            response_data = json.loads(response)
            print(json.dumps(response_data, indent=2))

            return True
    except Exception as e:
        print(f"Add document failed: {e}")
        return False


async def main() -> None:
    uri = "ws://localhost:8766"
    success = await test_add_document_with_concepts(uri)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
