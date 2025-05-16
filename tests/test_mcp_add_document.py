"""
Test script for MPC server add-document functionality.
"""
import asyncio
import websockets
import json
import sys

async def test_add_document(uri):
    """Test add-document functionality."""
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")
            
            # Prepare document to add
            text = """
            GraphRAG is a hybrid approach that combines the strengths of graph databases and vector databases
            for retrieval-augmented generation. It uses Neo4j for storing and querying relationships between
            concepts, and a vector database like ChromaDB for semantic search capabilities. This approach
            provides more context-aware and comprehensive results compared to traditional RAG systems.
            """
            
            metadata = {
                "title": "GraphRAG Introduction",
                "source": "Test Document",
                "author": "Test Script"
            }
            
            # Prepare add-document message
            message = {
                'action': 'add-document',
                'text': text,
                'metadata': metadata
            }
            
            print("Sending document to add...")
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

async def main():
    uri = "ws://localhost:8766"
    success = await test_add_document(uri)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
