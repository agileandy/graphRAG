"""
MPC (Message Passing Communication) server for GraphRAG project.

This module provides a simple MPC server that allows AI agents to interact with
the GraphRAG system through a WebSocket interface.
"""
import os
import sys
import json
import asyncio
import glob
import websockets
from typing import Dict, List, Any

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase
from src.database.db_linkage import DatabaseLinkage

# Initialize database connections
neo4j_db = Neo4jDatabase()
vector_db = VectorDatabase()
db_linkage = DatabaseLinkage(neo4j_db, vector_db)

# Define handler functions
async def handle_search(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle hybrid search request.

    Args:
        data: Request data containing:
            - query: Search query
            - n_results: Optional number of vector results to return (default: 5)
            - max_hops: Optional maximum number of hops in the graph (default: 2)

    Returns:
        Search results
    """
    if 'query' not in data:
        return {'error': 'Missing required parameter: query'}

    query = data['query']
    n_results = data.get('n_results', 5)
    max_hops = data.get('max_hops', 2)

    try:
        results = db_linkage.hybrid_search(
            query_text=query,
            n_vector_results=n_results,
            max_graph_hops=max_hops
        )

        return results
    except Exception as e:
        return {'error': str(e)}

async def handle_concept(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle concept request.

    Args:
        data: Request data

    Returns:
        Concept information and related concepts
    """
    if 'concept_name' not in data:
        return {'error': 'Missing required parameter: concept_name'}

    concept_name = data['concept_name']

    try:
        # Find the concept by name (case-insensitive)
        query = """
        MATCH (c:Concept)
        WHERE toLower(c.name) CONTAINS toLower($name)
        RETURN c.id AS id, c.name AS name
        """
        results = neo4j_db.run_query(query, {"name": concept_name})

        if not results:
            return {'error': f"No concept found with name containing '{concept_name}'"}

        # Use the first matching concept
        concept_id = results[0]["id"]
        concept_name = results[0]["name"]

        # Find related concepts
        query = """
        MATCH (c:Concept {id: $concept_id})-[r:RELATED_TO]-(related:Concept)
        RETURN related.id AS id, related.name AS name, r.strength AS strength
        ORDER BY r.strength DESC
        """
        related = neo4j_db.run_query(query, {"concept_id": concept_id})

        # De-duplicate related concepts by ID
        seen_ids = set()
        unique_related = []

        for item in related:
            if item["id"] not in seen_ids:
                seen_ids.add(item["id"])
                unique_related.append(item)

        return {
            'concept': {
                'id': concept_id,
                'name': concept_name
            },
            'related_concepts': unique_related
        }
    except Exception as e:
        return {'error': str(e)}

async def handle_documents(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle documents request.

    Args:
        data: Request data

    Returns:
        List of documents related to a concept
    """
    if 'concept_name' not in data:
        return {'error': 'Missing required parameter: concept_name'}

    concept_name = data['concept_name']
    limit = data.get('limit', 5)

    try:
        # Find the concept by name (case-insensitive)
        query = """
        MATCH (c:Concept)
        WHERE toLower(c.name) CONTAINS toLower($name)
        RETURN c.id AS id, c.name AS name
        """
        results = neo4j_db.run_query(query, {"name": concept_name})

        if not results:
            return {'error': f"No concept found with name containing '{concept_name}'"}

        # Use the first matching concept
        concept_id = results[0]["id"]
        concept_name = results[0]["name"]

        # Query vector database for chunks mentioning this concept
        results_primary = vector_db.get(
            where={"concept_id": concept_id}
        )

        # Then, try to find in the comma-separated concept_ids field
        all_docs = vector_db.get()

        # Filter documents that have the concept_id in their concept_ids field
        filtered_ids = []
        filtered_docs = []
        filtered_metadatas = []

        if all_docs.get("ids"):
            for i, doc_id in enumerate(all_docs["ids"]):
                metadata = all_docs["metadatas"][i]
                if "concept_ids" in metadata:
                    concept_ids = metadata["concept_ids"].split(",")
                    if concept_id in concept_ids:
                        filtered_ids.append(doc_id)
                        filtered_docs.append(all_docs["documents"][i])
                        filtered_metadatas.append(metadata)

        # Combine results
        combined_ids = results_primary.get("ids", []) + filtered_ids
        combined_docs = results_primary.get("documents", []) + filtered_docs
        combined_metadatas = results_primary.get("metadatas", []) + filtered_metadatas

        # Limit the number of results
        combined_ids = combined_ids[:limit]
        combined_docs = combined_docs[:limit]
        combined_metadatas = combined_metadatas[:limit]

        # Format the response
        documents = []
        for i, doc_id in enumerate(combined_ids):
            documents.append({
                'id': doc_id,
                'text': combined_docs[i],
                'metadata': combined_metadatas[i]
            })

        return {
            'concept': {
                'id': concept_id,
                'name': concept_name
            },
            'documents': documents
        }
    except Exception as e:
        return {'error': str(e)}

async def handle_add_document(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle add document request.

    Args:
        data: Request data containing:
            - text: Document text
            - metadata: Optional document metadata

    Returns:
        Status of the operation
    """
    if 'text' not in data:
        return {'error': 'Missing required parameter: text'}

    text = data['text']
    metadata = data.get('metadata', {})

    try:
        # Import here to avoid circular imports
        from scripts.add_document import add_document_to_graphrag

        result = add_document_to_graphrag(
            text=text,
            metadata=metadata,
            neo4j_db=neo4j_db,
            vector_db=vector_db
        )

        return {
            'status': 'success',
            'message': 'Document added successfully',
            'document_id': result.get('document_id'),
            'entities': result.get('entities', []),
            'relationships': result.get('relationships', [])
        }
    except Exception as e:
        return {'error': str(e)}

async def handle_add_folder(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle add folder request.

    Args:
        data: Request data containing:
            - folder_path: Path to the folder containing documents
            - recursive: Optional boolean to process subfolders (default: False)
            - file_types: Optional list of file extensions to process (default: [".txt", ".json"])

    Returns:
        Status of the operation
    """
    if 'folder_path' not in data:
        return {'error': 'Missing required parameter: folder_path'}

    folder_path = data['folder_path']
    recursive = data.get('recursive', False)
    file_types = data.get('file_types', [".txt", ".json"])

    # Validate folder path
    if not os.path.isdir(folder_path):
        return {'error': f"Folder not found: {folder_path}"}

    try:
        # Import here to avoid circular imports
        from scripts.add_document import add_document_to_graphrag

        # Find all matching files
        all_files = []

        if recursive:
            for file_type in file_types:
                pattern = os.path.join(folder_path, "**", f"*{file_type}")
                all_files.extend(glob.glob(pattern, recursive=True))
        else:
            for file_type in file_types:
                pattern = os.path.join(folder_path, f"*{file_type}")
                all_files.extend(glob.glob(pattern))

        if not all_files:
            return {
                'status': 'warning',
                'message': f"No matching files found in {folder_path}",
                'processed_files': 0,
                'entities': [],
                'relationships': []
            }

        # Process each file
        processed_files = 0
        all_entities = []
        all_relationships = []

        for file_path in all_files:
            file_name = os.path.basename(file_path)
            file_ext = os.path.splitext(file_path)[1].lower()

            try:
                if file_ext == '.txt':
                    # Read text file
                    with open(file_path, "r", encoding="utf-8") as f:
                        text = f.read()

                    # Create metadata from filename
                    metadata = {
                        "title": os.path.splitext(file_name)[0],
                        "source": "Text File",
                        "file_path": file_path
                    }

                elif file_ext == '.json':
                    # Read JSON file
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # Extract text and metadata
                    text = data.pop("text", "")
                    if not text:
                        continue

                    # Use remaining fields as metadata
                    metadata = data
                    metadata["source"] = "JSON File"
                    metadata["file_path"] = file_path

                else:
                    # Skip unsupported file types
                    continue

                # Add document to GraphRAG system
                result = add_document_to_graphrag(
                    text=text,
                    metadata=metadata,
                    neo4j_db=neo4j_db,
                    vector_db=vector_db
                )

                processed_files += 1
                all_entities.extend(result.get('entities', []))
                all_relationships.extend(result.get('relationships', []))

            except Exception as e:
                print(f"Error processing file {file_path}: {e}")

        return {
            'status': 'success',
            'message': f"Processed {processed_files} files from {folder_path}",
            'processed_files': processed_files,
            'entities': all_entities,
            'relationships': all_relationships
        }
    except Exception as e:
        return {'error': str(e)}

async def handle_books_by_concept(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle request to find books mentioning a specific concept.

    Args:
        data: Request data containing:
            - concept_name: Name of the concept

    Returns:
        List of books mentioning the concept
    """
    if 'concept_name' not in data:
        return {'error': 'Missing required parameter: concept_name'}

    concept_name = data['concept_name']

    try:
        # Import here to avoid circular imports
        from scripts.query_ebooks import find_books_by_concept

        books = find_books_by_concept(concept_name, neo4j_db)

        return {
            'status': 'success',
            'concept_name': concept_name,
            'books': books
        }
    except Exception as e:
        return {'error': str(e)}

async def handle_related_concepts(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle request to find concepts related to a specific concept.

    Args:
        data: Request data containing:
            - concept_name: Name of the concept
            - max_hops: Optional maximum number of hops in the graph (default: 2)

    Returns:
        List of related concepts
    """
    if 'concept_name' not in data:
        return {'error': 'Missing required parameter: concept_name'}

    concept_name = data['concept_name']
    max_hops = data.get('max_hops', 2)

    try:
        # Import here to avoid circular imports
        from scripts.query_ebooks import find_related_concepts

        related = find_related_concepts(concept_name, neo4j_db, max_hops)

        return {
            'status': 'success',
            'concept_name': concept_name,
            'related_concepts': related
        }
    except Exception as e:
        return {'error': str(e)}

async def handle_passages_about_concept(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle request to find passages about a specific concept.

    Args:
        data: Request data containing:
            - concept_name: Name of the concept
            - limit: Optional maximum number of passages to return (default: 5)

    Returns:
        List of passages about the concept
    """
    if 'concept_name' not in data:
        return {'error': 'Missing required parameter: concept_name'}

    concept_name = data['concept_name']
    limit = data.get('limit', 5)

    try:
        # Import here to avoid circular imports
        from scripts.query_ebooks import find_passages_about_concept

        passages = find_passages_about_concept(concept_name, neo4j_db, vector_db, limit)

        return {
            'status': 'success',
            'concept_name': concept_name,
            'passages': passages
        }
    except Exception as e:
        return {'error': str(e)}

# Map of action handlers
ACTION_HANDLERS = {
    # Search tools
    'search': handle_search,  # Hybrid search
    'concept': handle_concept,  # Get concept info
    'documents': handle_documents,  # Get documents for concept
    'books-by-concept': handle_books_by_concept,  # Find books mentioning a concept
    'related-concepts': handle_related_concepts,  # Find related concepts
    'passages-about-concept': handle_passages_about_concept,  # Find passages about a concept

    # Document addition tools
    'add-document': handle_add_document,  # Add a single document
    'add-folder': handle_add_folder  # Add a folder of documents
}

async def handle_connection(websocket):
    """
    Handle WebSocket connection.

    Args:
        websocket: WebSocket connection
    """
    client_id = id(websocket)
    print(f"Client connected: {client_id}")

    try:
        async for message in websocket:
            try:
                # Parse message as JSON
                data = json.loads(message)

                # Check if action is specified
                if 'action' not in data:
                    await websocket.send(json.dumps({
                        'error': 'Missing required parameter: action'
                    }))
                    continue

                action = data['action']

                # Check if action is supported
                if action not in ACTION_HANDLERS:
                    await websocket.send(json.dumps({
                        'error': f"Unsupported action: {action}",
                        'available_actions': list(ACTION_HANDLERS.keys())
                    }))
                    continue

                # Handle action
                handler = ACTION_HANDLERS[action]
                result = await handler(data)

                # Send response
                await websocket.send(json.dumps(result))
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    'error': 'Invalid JSON'
                }))
            except Exception as e:
                await websocket.send(json.dumps({
                    'error': str(e)
                }))
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        print(f"Client disconnected: {client_id}")

async def start_server(host: str = 'localhost', port: int = 8765):
    """
    Start the MPC server.

    Args:
        host: Server host
        port: Server port
    """
    server = await websockets.serve(handle_connection, host, port)
    print(f"MPC server started on ws://{host}:{port}")
    print(f"Available actions: {', '.join(ACTION_HANDLERS.keys())}")

    # Keep the server running
    await server.wait_closed()

def main():
    """
    Main function to start the MPC server.
    """
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Start the GraphRAG MPC server")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8765, help="Server port")
    args = parser.parse_args()

    # Start the server
    asyncio.run(start_server(args.host, args.port))

if __name__ == "__main__":
    main()