"""MCP (Model Context Protocol) server for GraphRAG project.

This module implements the Model Context Protocol server that allows AI agents
to interact with the GraphRAG system through standardized tools.

The server follows the JSON-RPC 2.0 protocol and implements the MCP specification.
"""
import asyncio
import glob
import json
import logging
import os
import sys
import time
from typing import Any

import websockets

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.db_linkage import DatabaseLinkage
from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase
from src.processing.duplicate_detector import DuplicateDetector
from src.processing.job_manager import JobManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mcp_server')

# Initialize database connections
neo4j_db = Neo4jDatabase()
vector_db = VectorDatabase()
db_linkage = DatabaseLinkage(neo4j_db, vector_db)

# Initialize job manager
job_manager = JobManager()

# Initialize duplicate detector
duplicate_detector = DuplicateDetector(vector_db)

# MCP protocol version
MCP_PROTOCOL_VERSION = "2024-11-05"

# Server information
SERVER_NAME = "GraphRAG MCP Server"
SERVER_VERSION = "1.0.0"

# Tool definitions
TOOLS = [
    {
        "name": "ping",
        "description": "Simple ping for connection testing",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "search",
        "description": "Perform hybrid search across the GraphRAG system",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "n_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5
                },
                "max_hops": {
                    "type": "integer",
                    "description": "Maximum number of hops in the graph",
                    "default": 2
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "concept",
        "description": "Get information about a concept",
        "parameters": {
            "type": "object",
            "properties": {
                "concept_name": {
                    "type": "string",
                    "description": "Name of the concept"
                }
            },
            "required": ["concept_name"]
        }
    },
    {
        "name": "documents",
        "description": "Get documents for a concept",
        "parameters": {
            "type": "object",
            "properties": {
                "concept_name": {
                    "type": "string",
                    "description": "Name of the concept"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of documents to return",
                    "default": 5
                }
            },
            "required": ["concept_name"]
        }
    },
    {
        "name": "books-by-concept",
        "description": "Find books mentioning a concept",
        "parameters": {
            "type": "object",
            "properties": {
                "concept_name": {
                    "type": "string",
                    "description": "Name of the concept"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of books to return",
                    "default": 5
                }
            },
            "required": ["concept_name"]
        }
    },
    {
        "name": "related-concepts",
        "description": "Find concepts related to a concept",
        "parameters": {
            "type": "object",
            "properties": {
                "concept_name": {
                    "type": "string",
                    "description": "Name of the concept"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of related concepts to return",
                    "default": 10
                }
            },
            "required": ["concept_name"]
        }
    },
    {
        "name": "passages-about-concept",
        "description": "Find passages about a concept",
        "parameters": {
            "type": "object",
            "properties": {
                "concept_name": {
                    "type": "string",
                    "description": "Name of the concept"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of passages to return",
                    "default": 5
                }
            },
            "required": ["concept_name"]
        }
    },
    {
        "name": "add-document",
        "description": "Add a single document to the system",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Document text"
                },
                "file_path": {
                    "type": "string",
                    "description": "Path to document file"
                },
                "metadata": {
                    "type": "object",
                    "description": "Document metadata",
                    "default": {}
                },
                "async": {
                    "type": "boolean",
                    "description": "Process document asynchronously",
                    "default": True
                }
            },
            "oneOf": [
                {"required": ["text"]},
                {"required": ["file_path"]}
            ]
        }
    },
    {
        "name": "add-folder",
        "description": "Add a folder of documents to the system",
        "parameters": {
            "type": "object",
            "properties": {
                "folder_path": {
                    "type": "string",
                    "description": "Path to folder containing documents"
                },
                "metadata": {
                    "type": "object",
                    "description": "Document metadata",
                    "default": {}
                },
                "async": {
                    "type": "boolean",
                    "description": "Process documents asynchronously",
                    "default": True
                }
            },
            "required": ["folder_path"]
        }
    },
    {
        "name": "job-status",
        "description": "Get status of a job",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job ID"
                }
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "list-jobs",
        "description": "List all jobs",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter jobs by status",
                    "enum": ["pending", "running", "completed", "failed", "cancelled"],
                    "default": None
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of jobs to return",
                    "default": 10
                }
            },
            "required": []
        }
    },
    {
        "name": "cancel-job",
        "description": "Cancel a job",
        "parameters": {
            "type": "object",
            "properties": {
                "job_id": {
                    "type": "string",
                    "description": "Job ID"
                }
            },
            "required": ["job_id"]
        }
    }
]

# Tool handlers
async def handle_ping(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle ping request.

    Args:
        parameters: Request parameters (empty for ping)

    Returns:
        Ping response

    """
    # Ensure vector database is connected
    vector_db.connect()

    # Ensure Neo4j database is connected
    neo4j_db.verify_connection()

    return {
        "message": "Pong!",
        "timestamp": time.time(),
        "vector_db_collection": vector_db.collection.name if vector_db.collection else None,
        "neo4j_connected": neo4j_db.verify_connection(),
        "status": "success"
    }

async def handle_search(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle search request.

    Args:
        parameters: Request parameters:
            - query: Search query
            - n_results: Optional number of results to return (default: 5)
            - max_hops: Optional maximum number of hops in the graph (default: 2)

    Returns:
        Search results

    """
    query = parameters.get("query")
    n_results = parameters.get("n_results", 5)
    max_hops = parameters.get("max_hops", 2)

    if not query:
        return {
            "error": "Missing required parameter: query"
        }

    try:
        results = db_linkage.hybrid_search(
            query_text=query,
            n_vector_results=n_results,
            max_graph_hops=max_hops
        )

        return results
    except Exception as e:
        logger.exception(f"Error performing search: {e}")
        return {
            "error": str(e)
        }

async def handle_concept(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle concept request.

    Args:
        parameters: Request parameters:
            - concept_name: Name of the concept

    Returns:
        Concept information

    """
    concept_name = parameters.get("concept_name")

    if not concept_name:
        return {
            "error": "Missing required parameter: concept_name"
        }

    try:
        # Query Neo4j for concept information
        query = """
        MATCH (c:Concept {name: $concept_name})
        OPTIONAL MATCH (c)-[r:RELATED_TO]-(related:Concept)
        RETURN c, collect(distinct {name: related.name, strength: r.strength}) as related_concepts
        """

        result = neo4j_db.run_query_and_return_single(query, {"concept_name": concept_name})

        if not result:
            return {
                "error": f"Concept not found: {concept_name}"
            }

        concept = result["c"]
        related_concepts = result["related_concepts"]

        # Query Neo4j for documents mentioning the concept
        query = """
        MATCH (c:Concept {name: $concept_name})<-[:MENTIONS]-(s:Section)<-[:CONTAINS*]-(d:Document)
        RETURN distinct d.title as title, d.id as id
        LIMIT 5
        """

        documents = neo4j_db.run_query(query, {"concept_name": concept_name})

        return {
            "name": concept["name"],
            "category": concept.get("category", ""),
            "related_concepts": related_concepts,
            "documents": [{"title": doc["title"], "id": doc["id"]} for doc in documents]
        }
    except Exception as e:
        logger.exception(f"Error getting concept information: {e}")
        return {
            "error": str(e)
        }

async def handle_documents(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle documents request.

    Args:
        parameters: Request parameters:
            - concept_name: Name of the concept
            - limit: Optional maximum number of documents to return (default: 5)

    Returns:
        Documents mentioning the concept

    """
    concept_name = parameters.get("concept_name")
    limit = parameters.get("limit", 5)

    if not concept_name:
        return {
            "error": "Missing required parameter: concept_name"
        }

    try:
        # Query Neo4j for documents mentioning the concept
        query = """
        MATCH (c:Concept {name: $concept_name})<-[:MENTIONS]-(s:Section)<-[:CONTAINS*]-(d:Document)
        RETURN distinct d.title as title, d.id as id, d.author as author, d.year as year
        LIMIT $limit
        """

        documents = neo4j_db.run_query(query, {"concept_name": concept_name, "limit": limit})

        return {
            "concept": concept_name,
            "documents": [
                {
                    "title": doc["title"],
                    "id": doc["id"],
                    "author": doc.get("author", ""),
                    "year": doc.get("year", "")
                }
                for doc in documents
            ]
        }
    except Exception as e:
        logger.exception(f"Error getting documents: {e}")
        return {
            "error": str(e)
        }

async def handle_books_by_concept(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle books-by-concept request.

    Args:
        parameters: Request parameters:
            - concept_name: Name of the concept
            - limit: Optional maximum number of books to return (default: 5)

    Returns:
        Books mentioning the concept

    """
    concept_name = parameters.get("concept_name")
    limit = parameters.get("limit", 5)

    if not concept_name:
        return {
            "error": "Missing required parameter: concept_name"
        }

    try:
        # Query Neo4j for books mentioning the concept
        query = """
        MATCH (c:Concept {name: $concept_name})<-[:MENTIONS]-(s:Section)<-[:CONTAINS*]-(b:Book)
        RETURN distinct b.title as title, b.id as id, b.author as author, b.year as year
        LIMIT $limit
        """

        books = neo4j_db.run_query(query, {"concept_name": concept_name, "limit": limit})

        return {
            "concept": concept_name,
            "books": [
                {
                    "title": book["title"],
                    "id": book["id"],
                    "author": book.get("author", ""),
                    "year": book.get("year", "")
                }
                for book in books
            ]
        }
    except Exception as e:
        logger.exception(f"Error getting books: {e}")
        return {
            "error": str(e)
        }

async def handle_related_concepts(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle related-concepts request.

    Args:
        parameters: Request parameters:
            - concept_name: Name of the concept
            - limit: Optional maximum number of related concepts to return (default: 10)

    Returns:
        Concepts related to the given concept

    """
    concept_name = parameters.get("concept_name")
    limit = parameters.get("limit", 10)

    if not concept_name:
        return {
            "error": "Missing required parameter: concept_name"
        }

    try:
        # Query Neo4j for related concepts
        query = """
        MATCH (c:Concept {name: $concept_name})-[r:RELATED_TO]-(related:Concept)
        RETURN related.name as name, r.strength as strength
        ORDER BY r.strength DESC
        LIMIT $limit
        """

        related_concepts = neo4j_db.run_query(query, {"concept_name": concept_name, "limit": limit})

        return {
            "concept": concept_name,
            "related_concepts": [
                {
                    "name": concept["name"],
                    "strength": concept["strength"]
                }
                for concept in related_concepts
            ]
        }
    except Exception as e:
        logger.exception(f"Error getting related concepts: {e}")
        return {
            "error": str(e)
        }

async def handle_passages_about_concept(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle passages-about-concept request.

    Args:
        parameters: Request parameters:
            - concept_name: Name of the concept
            - limit: Optional maximum number of passages to return (default: 5)

    Returns:
        Passages about the concept

    """
    concept_name = parameters.get("concept_name")
    limit = parameters.get("limit", 5)

    if not concept_name:
        return {
            "error": "Missing required parameter: concept_name"
        }

    try:
        # Get concept node ID from Neo4j
        query = """
        MATCH (c:Concept {name: $concept_name})
        RETURN id(c) as node_id
        """

        result = neo4j_db.run_query_and_return_single(query, {"concept_name": concept_name})

        if not result:
            return {
                "error": f"Concept not found: {concept_name}"
            }

        node_id = result["node_id"]

        # Get chunks mentioning the concept
        chunks = db_linkage.get_node_chunks(node_id, "Concept")

        # Limit the number of chunks
        chunks = chunks[:limit]

        return {
            "concept": concept_name,
            "passages": [
                {
                    "text": chunk["text"],
                    "document": chunk["metadata"].get("document_title", ""),
                    "section": chunk["metadata"].get("section_title", ""),
                    "page": chunk["metadata"].get("page", "")
                }
                for chunk in chunks
            ]
        }
    except Exception as e:
        logger.exception(f"Error getting passages: {e}")
        return {
            "error": str(e)
        }

async def handle_add_document(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle add-document request.

    Args:
        parameters: Request parameters:
            - text: Document text (optional if file_path is provided)
            - file_path: Path to document file (optional if text is provided)
            - metadata: Optional document metadata
            - async: Optional flag to process document asynchronously (default: true)

    Returns:
        Result of adding the document

    """
    text = parameters.get("text")
    file_path = parameters.get("file_path")
    metadata = parameters.get("metadata", {})
    process_async = parameters.get("async", True)

    if not text and not file_path:
        return {
            "error": "Missing required parameter: either text or file_path must be provided"
        }

    try:
        # If file_path is provided, read the file
        if file_path and not text:
            if not os.path.exists(file_path):
                return {
                    "error": f"File not found: {file_path}"
                }

            with open(file_path) as f:
                text = f.read()

        # Import here to avoid circular imports
        from scripts.add_document import add_document_to_graphrag

        if process_async:
            # Create a job for asynchronous processing
            job = job_manager.create_job(
                job_type="process_document",
                params={
                    "text": text,
                    "metadata": metadata
                },
                created_by="mcp_server"
            )

            # Start the job asynchronously
            job_manager.run_job_async(
                job=job,
                task_func=lambda: add_document_to_graphrag(
                    text=text,
                    metadata=metadata,
                    neo4j_db=neo4j_db,
                    vector_db=vector_db,
                    duplicate_detector=duplicate_detector
                )
            )

            return {
                "job_id": job.job_id,
                "status": "pending",
                "message": "Document processing started"
            }
        else:
            # Process synchronously
            result = add_document_to_graphrag(
                text=text,
                metadata=metadata,
                neo4j_db=neo4j_db,
                vector_db=vector_db,
                duplicate_detector=duplicate_detector
            )

            return {
                "status": "success",
                "message": "Document added successfully",
                "document_id": result.get("document_id") if result else None,
                "entities": result.get("entities", []) if result else [],
                "relationships": result.get("relationships", []) if result else []
            }
    except Exception as e:
        logger.exception(f"Error adding document: {e}")
        return {
            "error": str(e)
        }

async def handle_add_folder(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle add-folder request.

    Args:
        parameters: Request parameters:
            - folder_path: Path to folder containing documents
            - metadata: Optional document metadata
            - async: Optional flag to process documents asynchronously (default: true)

    Returns:
        Result of adding the folder

    """
    folder_path = parameters.get("folder_path")
    metadata = parameters.get("metadata", {})
    process_async = parameters.get("async", True)

    if not folder_path:
        return {
            "error": "Missing required parameter: folder_path"
        }

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return {
            "error": f"Folder not found: {folder_path}"
        }

    try:
        # Find all documents in the folder
        document_files = []
        for ext in ["*.pdf", "*.txt", "*.md"]:
            document_files.extend(glob.glob(os.path.join(folder_path, ext)))

        if not document_files:
            return {
                "error": f"No documents found in folder: {folder_path}"
            }

        # Import here to avoid circular imports
        from scripts.add_document import add_document_to_graphrag

        if process_async:
            # Create a job for asynchronous processing
            job = job_manager.create_job(
                job_type="process_folder",
                params={
                    "folder_path": folder_path,
                    "metadata": metadata
                },
                created_by="mcp_server"
            )

            # Start the job asynchronously
            async def process_folder():
                total_files = len(document_files)
                processed_files = 0

                job.start()

                for file_path in document_files:
                    try:
                        with open(file_path) as f:
                            text = f.read()

                        file_metadata = metadata.copy()
                        file_metadata["file_path"] = file_path

                        add_document_to_graphrag(
                            text=text,
                            metadata=file_metadata,
                            neo4j_db=neo4j_db,
                            vector_db=vector_db,
                            duplicate_detector=duplicate_detector
                        )

                        processed_files += 1
                        job.update_progress(processed_files, total_files)
                    except Exception as e:
                        logger.exception(f"Error processing file {file_path}: {e}")

                job.complete({
                    "processed_files": processed_files,
                    "total_files": total_files
                })

            # Run the folder processing task
            asyncio.create_task(process_folder())

            return {
                "job_id": job.job_id,
                "status": "pending",
                "message": f"Folder processing started ({len(document_files)} files)"
            }
        else:
            # Process synchronously
            processed_files = 0
            results = []

            for file_path in document_files:
                try:
                    with open(file_path) as f:
                        text = f.read()

                    file_metadata = metadata.copy()
                    file_metadata["file_path"] = file_path

                    result = add_document_to_graphrag(
                        text=text,
                        metadata=file_metadata,
                        neo4j_db=neo4j_db,
                        vector_db=vector_db,
                        duplicate_detector=duplicate_detector
                    )

                    processed_files += 1
                    results.append({
                        "file_path": file_path,
                        "document_id": result.get("document_id") if result else None
                    })
                except Exception as e:
                    logger.exception(f"Error processing file {file_path}: {e}")
                    results.append({
                        "file_path": file_path,
                        "error": str(e)
                    })

            return {
                "status": "success",
                "message": f"Folder processed successfully ({processed_files}/{len(document_files)} files)",
                "results": results
            }
    except Exception as e:
        logger.exception(f"Error adding folder: {e}")
        return {
            "error": str(e)
        }

async def handle_job_status(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle job-status request.

    Args:
        parameters: Request parameters:
            - job_id: Job ID

    Returns:
        Job status

    """
    job_id = parameters.get("job_id")

    if not job_id:
        return {
            "error": "Missing required parameter: job_id"
        }

    try:
        job = job_manager.get_job(job_id)

        if not job:
            return {
                "error": f"Job not found: {job_id}"
            }

        return {
            "job_id": job.job_id,
            "job_type": job.job_type,
            "status": job.status,
            "progress": job.progress,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "result": job.result,
            "error": job.error
        }
    except Exception as e:
        logger.exception(f"Error getting job status: {e}")
        return {
            "error": str(e)
        }

async def handle_list_jobs(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle list-jobs request.

    Args:
        parameters: Request parameters:
            - status: Optional filter by job status
            - limit: Optional maximum number of jobs to return (default: 10)

    Returns:
        List of jobs

    """
    status = parameters.get("status")
    limit = parameters.get("limit", 10)

    try:
        # Get all jobs from the job manager
        all_jobs = job_manager.jobs.values()

        # Filter by status if specified
        if status:
            jobs = [j for j in all_jobs if j.status == status]
        else:
            jobs = list(all_jobs)

        # Sort jobs by creation time (newest first)
        jobs.sort(key=lambda j: j.created_at if j.created_at else 0, reverse=True)

        # Limit the number of jobs
        jobs = jobs[:limit]

        return {
            "jobs": [
                {
                    "job_id": job.job_id,
                    "job_type": job.job_type,
                    "status": job.status,
                    "progress": job.progress,
                    "created_at": job.created_at.isoformat() if job.created_at else None
                }
                for job in jobs
            ]
        }
    except Exception as e:
        logger.exception(f"Error listing jobs: {e}")
        return {
            "error": str(e)
        }

async def handle_cancel_job(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle cancel-job request.

    Args:
        parameters: Request parameters:
            - job_id: Job ID

    Returns:
        Result of cancelling the job

    """
    job_id = parameters.get("job_id")

    if not job_id:
        return {
            "error": "Missing required parameter: job_id"
        }

    try:
        result = job_manager.cancel_job(job_id)

        if result:
            return {
                "status": "success",
                "message": f"Job cancelled: {job_id}"
            }
        else:
            return {
                "error": f"Failed to cancel job: {job_id}"
            }
    except Exception as e:
        logger.exception(f"Error cancelling job: {e}")
        return {
            "error": str(e)
        }

# Map of tool handlers
TOOL_HANDLERS = {
    "ping": handle_ping,
    "search": handle_search,
    "concept": handle_concept,
    "documents": handle_documents,
    "books-by-concept": handle_books_by_concept,
    "related-concepts": handle_related_concepts,
    "passages-about-concept": handle_passages_about_concept,
    "add-document": handle_add_document,
    "add-folder": handle_add_folder,
    "job-status": handle_job_status,
    "list-jobs": handle_list_jobs,
    "cancel-job": handle_cancel_job
}

async def handle_initialize(params: dict[str, Any]) -> dict[str, Any]:
    """Handle initialize request.

    Args:
        params: Initialize parameters

    Returns:
        Initialize response

    """
    client_protocol_version = params.get("protocolVersion")
    client_info = params.get("clientInfo", {})

    logger.info(f"Client connected: {client_info.get('name')} {client_info.get('version')}")
    logger.info(f"Client protocol version: {client_protocol_version}")

    return {
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION
        },
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "capabilities": {}
    }

async def handle_get_tools(_: dict[str, Any]) -> dict[str, Any]:
    """Handle getTools request.

    Args:
        _: GetTools parameters (unused)

    Returns:
        GetTools response with tool definitions

    """
    return {
        "tools": TOOLS
    }

async def handle_invoke_tool(params: dict[str, Any]) -> dict[str, Any]:
    """Handle invokeTool request.

    Args:
        params: InvokeTool parameters

    Returns:
        InvokeTool response with tool result

    """
    tool_name = params.get("name")
    tool_parameters = params.get("parameters", {})

    if tool_name not in TOOL_HANDLERS:
        return {
            "error": {
                "code": -32601,
                "message": f"Tool not found: {tool_name}",
                "data": {
                    "availableTools": list(TOOL_HANDLERS.keys())
                }
            }
        }

    try:
        handler = TOOL_HANDLERS[tool_name]
        result = await handler(tool_parameters)
        return {
            "result": result
        }
    except Exception as e:
        logger.exception(f"Error invoking tool {tool_name}")
        return {
            "error": {
                "code": -32603,
                "message": f"Error invoking tool: {str(e)}"
            }
        }

async def handle_connection(websocket):
    """Handle WebSocket connection.

    Args:
        websocket: WebSocket connection

    """
    client_id = id(websocket)
    logger.info(f"Client connected: {client_id}")

    try:
        async for message in websocket:
            try:
                # Parse message
                data = json.loads(message)

                # Extract JSON-RPC fields
                jsonrpc = data.get("jsonrpc")
                method = data.get("method")
                params = data.get("params", {})
                request_id = data.get("id")

                # Validate JSON-RPC version
                if jsonrpc != "2.0":
                    response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32600,
                            "message": "Invalid JSON-RPC version"
                        },
                        "id": request_id
                    }
                    await websocket.send(json.dumps(response))
                    continue

                # Handle method
                result = None
                error = None

                if method == "initialize":
                    result = await handle_initialize(params)
                elif method == "getTools":
                    result = await handle_get_tools(params)
                elif method == "invokeTool":
                    result = await handle_invoke_tool(params)
                else:
                    error = {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }

                # Prepare response
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id
                }

                if error:
                    response["error"] = error
                else:
                    response["result"] = result

                # Send response
                await websocket.send(json.dumps(response))

            except json.JSONDecodeError:
                # Invalid JSON
                response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    },
                    "id": None
                }
                await websocket.send(json.dumps(response))
            except Exception as e:
                # Internal error
                logger.exception("Error handling message")
                response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    },
                    "id": None
                }
                await websocket.send(json.dumps(response))
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {client_id}")
    except Exception:
        logger.exception(f"Error handling connection for client {client_id}")

async def start_server(host: str = 'localhost', port: int = 8767):
    """Start the MCP server.

    Args:
        host: Server host
        port: Server port

    """
    server = await websockets.serve(handle_connection, host, port)
    logger.info(f"MCP server started on ws://{host}:{port}")
    logger.info(f"Available tools: {', '.join(TOOL_HANDLERS.keys())}")

    # Keep the server running
    await server.wait_closed()

def main():
    """Main function to start the MCP server.
    """
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Start the GraphRAG MCP server")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8767, help="Server port")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    args = parser.parse_args()

    # Set logging level
    logger.setLevel(getattr(logging, args.log_level))

    # Start the server
    try:
        asyncio.run(start_server(args.host, args.port))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception:
        logger.exception("Error starting server")
        sys.exit(1)

if __name__ == "__main__":
    main()
