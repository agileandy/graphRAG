"""
MPC (Message Passing Communication) server for GraphRAG project.

This module provides a simple MPC server that allows AI agents to interact with
the GraphRAG system through a WebSocket interface.

Features:
- Asynchronous processing of long-running tasks
- Job status tracking and progress reporting
- Duplicate detection for documents
"""
import os
import sys
import json
import asyncio
import glob
import time
import uuid
import websockets
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase
from src.database.db_linkage import DatabaseLinkage
from src.processing.job_manager import JobManager, JobStatus
from src.processing.duplicate_detector import DuplicateDetector

# Initialize database connections
neo4j_db = Neo4jDatabase()
vector_db = VectorDatabase()
db_linkage = DatabaseLinkage(neo4j_db, vector_db)

# Initialize job manager
job_manager = JobManager()

# Initialize duplicate detector
duplicate_detector = DuplicateDetector(vector_db)

# Map of client connections to their active jobs
client_jobs: Dict[int, Set[str]] = {}

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

async def handle_add_document(data: Dict[str, Any], client_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Handle add document request.

    Args:
        data: Request data containing:
            - text: Document text
            - metadata: Optional document metadata
            - async: Optional boolean to process asynchronously (default: False)
        client_id: ID of the client making the request

    Returns:
        Status of the operation or job ID if async
    """
    if 'text' not in data:
        return {'error': 'Missing required parameter: text'}

    text = data['text']
    metadata = data.get('metadata', {})
    process_async = data.get('async', False)

    try:
        # Ensure vector database is connected
        vector_db.connect()

        # Ensure Neo4j database is connected
        if not neo4j_db.verify_connection():
            return {'error': 'Neo4j database connection failed'}

        # Check for duplicates
        is_duplicate, existing_id, method = duplicate_detector.is_duplicate(text, metadata)
        if is_duplicate:
            return {
                'status': 'duplicate',
                'message': f'Document already exists in the database (detected by {method})',
                'document_id': existing_id
            }

        # If async processing is requested, create a job
        if process_async:
            # Create a job
            job = job_manager.create_job(
                job_type="add-document",
                params={
                    'text': text,
                    'metadata': metadata
                },
                created_by=str(client_id) if client_id else None
            )

            # Add job to client's active jobs
            if client_id is not None:
                if client_id not in client_jobs:
                    client_jobs[client_id] = set()
                client_jobs[client_id].add(job.job_id)

            # Start the job
            job_manager.run_job_async(job, _process_add_document_job)

            return {
                'status': 'accepted',
                'message': 'Document processing started',
                'job_id': job.job_id
            }

        # Synchronous processing
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

async def _process_add_document_job(job) -> Dict[str, Any]:
    """
    Process an add document job.

    Args:
        job: Job object

    Returns:
        Result of the operation
    """
    # Import here to avoid circular imports
    from scripts.add_document import add_document_to_graphrag

    # Extract parameters
    text = job.params['text']
    metadata = job.params.get('metadata', {})

    # Update job progress
    job.update_progress(0, 1)

    # Process document
    result = add_document_to_graphrag(
        text=text,
        metadata=metadata,
        neo4j_db=neo4j_db,
        vector_db=vector_db
    )

    # Update job progress
    job.update_progress(1, 1)

    return {
        'document_id': result.get('document_id'),
        'entities': result.get('entities', []),
        'relationships': result.get('relationships', [])
    }

async def handle_add_folder(data: Dict[str, Any], client_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Handle add folder request.

    Args:
        data: Request data containing:
            - folder_path: Path to the folder containing documents
            - recursive: Optional boolean to process subfolders (default: False)
            - file_types: Optional list of file extensions to process (default: [".txt", ".json"])
            - async: Optional boolean to process asynchronously (default: True)
        client_id: ID of the client making the request

    Returns:
        Status of the operation or job ID if async
    """
    if 'folder_path' not in data:
        return {'error': 'Missing required parameter: folder_path'}

    folder_path = data['folder_path']
    recursive = data.get('recursive', False)
    file_types = data.get('file_types', [".txt", ".json"])
    process_async = data.get('async', True)  # Default to async for folders

    # Validate folder path
    if not os.path.isdir(folder_path):
        return {'error': f"Folder not found: {folder_path}"}

    try:
        # Ensure vector database is connected
        vector_db.connect()

        # Ensure Neo4j database is connected
        if not neo4j_db.verify_connection():
            return {'error': 'Neo4j database connection failed'}

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

        # If async processing is requested, create a job
        if process_async:
            # Create a job
            job = job_manager.create_job(
                job_type="add-folder",
                params={
                    'folder_path': folder_path,
                    'recursive': recursive,
                    'file_types': file_types,
                    'files': all_files  # Pass the list of files to avoid re-scanning
                },
                created_by=str(client_id) if client_id else None
            )

            # Set initial job progress
            job.update_progress(0, len(all_files))

            # Add job to client's active jobs
            if client_id is not None:
                if client_id not in client_jobs:
                    client_jobs[client_id] = set()
                client_jobs[client_id].add(job.job_id)

            # Start the job
            job_manager.run_job_async(job, _process_add_folder_job)

            return {
                'status': 'accepted',
                'message': f'Processing {len(all_files)} files from {folder_path}',
                'job_id': job.job_id,
                'total_files': len(all_files)
            }

        # Synchronous processing
        # Import here to avoid circular imports
        from scripts.add_document import add_document_to_graphrag

        # Process each file
        processed_files = 0
        skipped_files = 0
        duplicate_files = 0
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
                        skipped_files += 1
                        continue

                    # Use remaining fields as metadata
                    metadata = data
                    metadata["source"] = "JSON File"
                    metadata["file_path"] = file_path

                else:
                    # Skip unsupported file types
                    skipped_files += 1
                    continue

                # Check for duplicates
                is_duplicate, existing_id, method = duplicate_detector.is_duplicate(text, metadata)
                if is_duplicate:
                    print(f"Skipping duplicate file: {file_path} (detected by {method})")
                    duplicate_files += 1
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
                skipped_files += 1

        return {
            'status': 'success',
            'message': f"Processed {processed_files} files from {folder_path}",
            'processed_files': processed_files,
            'skipped_files': skipped_files,
            'duplicate_files': duplicate_files,
            'total_files': len(all_files),
            'entities': all_entities,
            'relationships': all_relationships
        }
    except Exception as e:
        return {'error': str(e)}

async def _process_add_folder_job(job) -> Dict[str, Any]:
    """
    Process an add folder job.

    Args:
        job: Job object

    Returns:
        Result of the operation
    """
    # Import here to avoid circular imports
    from scripts.add_document import add_document_to_graphrag

    # Extract parameters
    folder_path = job.params['folder_path']
    all_files = job.params['files']

    # Process each file
    processed_files = 0
    skipped_files = 0
    duplicate_files = 0
    all_entities = []
    all_relationships = []

    for i, file_path in enumerate(all_files):
        # Update job progress
        job.update_progress(i, len(all_files))

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
                    skipped_files += 1
                    continue

                # Use remaining fields as metadata
                metadata = data
                metadata["source"] = "JSON File"
                metadata["file_path"] = file_path

            else:
                # Skip unsupported file types
                skipped_files += 1
                continue

            # Check for duplicates
            is_duplicate, existing_id, method = duplicate_detector.is_duplicate(text, metadata)
            if is_duplicate:
                print(f"Skipping duplicate file: {file_path} (detected by {method})")
                duplicate_files += 1
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
            skipped_files += 1

    # Update final job progress
    job.update_progress(len(all_files), len(all_files))

    return {
        'message': f"Processed {processed_files} files from {folder_path}",
        'processed_files': processed_files,
        'skipped_files': skipped_files,
        'duplicate_files': duplicate_files,
        'total_files': len(all_files),
        'entities_count': len(all_entities),
        'relationships_count': len(all_relationships)
    }

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

# Simple ping handler for connection testing
async def handle_ping(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle ping request.

    Args:
        data: Request data

    Returns:
        Ping response
    """
    # Ensure vector database is connected
    vector_db.connect()

    # Ensure Neo4j database is connected
    neo4j_db.verify_connection()

    return {
        'status': 'success',
        'message': 'Pong!',
        'timestamp': time.time(),
        'vector_db_collection': vector_db.collection.name if vector_db.collection else None,
        'neo4j_connected': neo4j_db.verify_connection()
    }

async def handle_job_status(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle job status request.

    Args:
        data: Request data containing:
            - job_id: ID of the job to check

    Returns:
        Job status
    """
    if 'job_id' not in data:
        return {'error': 'Missing required parameter: job_id'}

    job_id = data['job_id']
    job = job_manager.get_job(job_id)

    if not job:
        return {'error': f"Job not found: {job_id}"}

    return {
        'status': job.status,
        'progress': job.progress,
        'total_items': job.total_items,
        'processed_items': job.processed_items,
        'created_at': job.created_at.isoformat() if job.created_at else None,
        'started_at': job.started_at.isoformat() if job.started_at else None,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'result': job.result,
        'error': job.error
    }

async def handle_list_jobs(data: Dict[str, Any], client_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Handle list jobs request.

    Args:
        data: Request data containing:
            - status: Optional job status to filter by
            - job_type: Optional job type to filter by
        client_id: ID of the client making the request

    Returns:
        List of jobs
    """
    status = data.get('status')
    job_type = data.get('job_type')

    # Convert status string to enum if provided
    if status and isinstance(status, str):
        try:
            status = JobStatus(status)
        except ValueError:
            return {'error': f"Invalid job status: {status}"}

    # Get jobs
    jobs = job_manager.get_jobs(
        status=status,
        job_type=job_type,
        created_by=str(client_id) if client_id else None
    )

    # Convert jobs to dictionaries
    job_dicts = [job.to_dict() for job in jobs]

    return {
        'status': 'success',
        'jobs': job_dicts
    }

async def handle_cancel_job(data: Dict[str, Any], client_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Handle cancel job request.

    Args:
        data: Request data containing:
            - job_id: ID of the job to cancel
        client_id: ID of the client making the request

    Returns:
        Status of the operation
    """
    if 'job_id' not in data:
        return {'error': 'Missing required parameter: job_id'}

    job_id = data['job_id']
    job = job_manager.get_job(job_id)

    if not job:
        return {'error': f"Job not found: {job_id}"}

    # Check if the client is allowed to cancel this job
    if client_id and job.created_by and job.created_by != str(client_id):
        return {'error': f"Not authorized to cancel job: {job_id}"}

    # Cancel the job
    success = job_manager.cancel_job(job_id)

    if success:
        return {
            'status': 'success',
            'message': f"Job cancelled: {job_id}"
        }
    else:
        return {
            'error': f"Failed to cancel job: {job_id}"
        }

# Map of action handlers
ACTION_HANDLERS = {
    # Utility tools
    'ping': handle_ping,  # Simple ping for connection testing

    # Search tools
    'search': handle_search,  # Hybrid search
    'concept': handle_concept,  # Get concept info
    'documents': handle_documents,  # Get documents for concept
    'books-by-concept': handle_books_by_concept,  # Find books mentioning a concept
    'related-concepts': handle_related_concepts,  # Find related concepts
    'passages-about-concept': handle_passages_about_concept,  # Find passages about a concept

    # Document addition tools
    'add-document': handle_add_document,  # Add a single document
    'add-folder': handle_add_folder,  # Add a folder of documents

    # Job management tools
    'job-status': handle_job_status,  # Get job status
    'list-jobs': handle_list_jobs,  # List jobs
    'cancel-job': handle_cancel_job  # Cancel a job
}

async def handle_connection(websocket):
    """
    Handle WebSocket connection.

    Args:
        websocket: WebSocket connection
    """
    client_id = id(websocket)
    print(f"Client connected: {client_id}")

    # Initialize client's job set
    client_jobs[client_id] = set()

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

                # Check if handler accepts client_id parameter
                import inspect
                sig = inspect.signature(handler)
                if 'client_id' in sig.parameters:
                    result = await handler(data, client_id)
                else:
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
        # Clean up client's jobs
        if client_id in client_jobs:
            del client_jobs[client_id]
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