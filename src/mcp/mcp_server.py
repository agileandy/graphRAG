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
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.database.db_linkage import DatabaseLinkage
from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase
from src.processing.duplicate_detector import DuplicateDetector
from src.processing.job_manager import JobManager, Job, JobStatus # Import Job and JobStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("mcp_server")

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
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "search",
        "description": "Perform hybrid search across the GraphRAG system",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "n_results": {
                    "type": "integer",
                    "description": "Number of results to return",
                    "default": 5,
                },
                "max_hops": {
                    "type": "integer",
                    "description": "Maximum number of hops in the graph",
                    "default": 2,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "concept",
        "description": "Get information about a concept",
        "inputSchema": {
            "type": "object",
            "properties": {
                "concept_name": {"type": "string", "description": "Name of the concept"}
            },
            "required": ["concept_name"],
        },
    },
    {
        "name": "documents",
        "description": "Get documents for a concept",
        "inputSchema": {
            "type": "object",
            "properties": {
                "concept_name": {
                    "type": "string",
                    "description": "Name of the concept",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of documents to return",
                    "default": 5,
                },
            },
            "required": ["concept_name"],
        },
    },
    {
        "name": "books-by-concept",
        "description": "Find books mentioning a concept",
        "inputSchema": {
            "type": "object",
            "properties": {
                "concept_name": {
                    "type": "string",
                    "description": "Name of the concept",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of books to return",
                    "default": 5,
                },
            },
            "required": ["concept_name"],
        },
    },
    {
        "name": "related-concepts",
        "description": "Find concepts related to a concept",
        "inputSchema": {
            "type": "object",
            "properties": {
                "concept_name": {
                    "type": "string",
                    "description": "Name of the concept",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of related concepts to return",
                    "default": 10,
                },
            },
            "required": ["concept_name"],
        },
    },
    {
        "name": "passages-about-concept",
        "description": "Find passages about a concept",
        "inputSchema": {
            "type": "object",
            "properties": {
                "concept_name": {
                    "type": "string",
                    "description": "Name of the concept",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of passages to return",
                    "default": 5,
                },
            },
            "required": ["concept_name"],
        },
    },
    {
        "name": "add_bug",
        "description": "Add a new bug to the system",
        "inputSchema": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Bug description"},
                "cause": {"type": "string", "description": "Bug cause"},
                "metadata": {
                    "type": "object",
                    "description": "Bug metadata",
                    "default": {},
                },
                "async": {
                    "type": "boolean",
                    "description": "Process bug asynchronously",
                    "default": True,
                },
            },
            "required": ["description", "cause"],
        },
    },
    {
        "name": "add-folder",
        "description": "Add a folder of documents to the system",
        "inputSchema": {
            "type": "object",
            "properties": {
                "folder_path": {
                    "type": "string",
                    "description": "Path to folder containing documents",
                },
                "metadata": {
                    "type": "object",
                    "description": "Document metadata",
                    "default": {},
                },
                "async": {
                    "type": "boolean",
                    "description": "Process documents asynchronously",
                    "default": True,
                },
            },
            "required": ["folder_path"],
        },
    },
    {
        "name": "job-status",
        "description": "Get status of a job",
        "inputSchema": {
            "type": "object",
            "properties": {"job_id": {"type": "string", "description": "Job ID"}},
            "required": ["job_id"],
        },
    },
    {
        "name": "list-jobs",
        "description": "List all jobs",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter jobs by status",
                    "enum": ["queued", "running", "completed", "failed", "cancelled"],
                    "default": None,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of jobs to return",
                    "default": 10,
                },
            },
            "required": [],
        },
    },
    {
        "name": "cancel-job",
        "description": "Cancel a job",
        "inputSchema": {
            "type": "object",
            "properties": {"job_id": {"type": "string", "description": "Job ID"}},
            "required": ["job_id"],
        },
    },
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
        "vector_db_collection": vector_db.collection.name
        if vector_db.collection
        else None,
        "neo4j_connected": neo4j_db.verify_connection(),
        "status": "success",
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
        return {"error": "Missing required parameter: query"}

    try:
        results = db_linkage.hybrid_search(
            query_text=query, n_vector_results=n_results, max_graph_hops=max_hops
        )

        return results
    except Exception as e:
        logger.exception(f"Error performing search: {e}")
        return {"error": str(e)}


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
        return {"error": "Missing required parameter: concept_name"}

    try:
        # Query Neo4j for concept information
        query = """
        MATCH (c:Concept {name: $concept_name})
        OPTIONAL MATCH (c)-[r:RELATED_TO]-(related:Concept)
        RETURN c, collect(distinct {name: related.name, strength: r.strength}) as related_concepts
        """

        result = neo4j_db.run_query_and_return_single(
            query, {"concept_name": concept_name}
        )

        if not result:
            return {"error": f"Concept not found: {concept_name}"}

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
            "documents": [
                {"title": doc["title"], "id": doc["id"]} for doc in documents
            ],
        }
    except Exception as e:
        logger.exception(f"Error getting concept information: {e}")
        return {"error": str(e)}


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
        return {"error": "Missing required parameter: concept_name"}

    try:
        # Query Neo4j for documents mentioning the concept
        query = """
        MATCH (c:Concept {name: $concept_name})<-[:MENTIONS]-(s:Section)<-[:CONTAINS*]-(d:Document)
        RETURN distinct d.title as title, d.id as id, d.author as author, d.year as year
        LIMIT $limit
        """

        documents = neo4j_db.run_query(
            query, {"concept_name": concept_name, "limit": limit}
        )

        return {
            "documents": [
                {"title": doc["title"], "id": doc["id"], "author": doc.get("author"), "year": doc.get("year")}
                for doc in documents
            ]
        }
    except Exception as e:
        logger.exception(f"Error getting documents for concept: {e}")
        return {"error": str(e)}


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
        return {"error": "Missing required parameter: concept_name"}

    try:
        # Query Neo4j for books mentioning the concept
        query = """
        MATCH (c:Concept {name: $concept_name})<-[:MENTIONS]-(s:Section)<-[:CONTAINS*]-(d:Document)
        WHERE d.document_type = 'book'
        RETURN distinct d.title as title, d.id as id, d.author as author, d.year as year
        LIMIT $limit
        """

        books = neo4j_db.run_query(query, {"concept_name": concept_name, "limit": limit})

        return {
            "books": [
                {"title": book["title"], "id": book["id"], "author": book.get("author"), "year": book.get("year")}
                for book in books
            ]
        }
    except Exception as e:
        logger.exception(f"Error getting books by concept: {e}")
        return {"error": str(e)}


async def handle_related_concepts(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle related-concepts request.

    Args:
        parameters: Request parameters:
            - concept_name: Name of the concept
            - limit: Optional maximum number of related concepts to return (default: 10)

    Returns:
        Related concepts
    """
    concept_name = parameters.get("concept_name")
    limit = parameters.get("limit", 10)

    if not concept_name:
        return {"error": "Missing required parameter: concept_name"}

    try:
        # Query Neo4j for related concepts
        query = """
        MATCH (c:Concept {name: $concept_name})-[r:RELATED_TO]-(related:Concept)
        RETURN related.name as name, r.strength as strength
        ORDER BY r.strength DESC
        LIMIT $limit
        """

        related = neo4j_db.run_query(query, {"concept_name": concept_name, "limit": limit})

        return {"related_concepts": related}
    except Exception as e:
        logger.exception(f"Error getting related concepts: {e}")
        return {"error": str(e)}


async def handle_passages_about_concept(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle passages-about-concept request.

    Args:
        parameters: Request parameters:
            - concept_name: Name of the concept
            - limit: Optional maximum number of passages to return (default: 5)

    Returns:
        Passages mentioning the concept
    """
    concept_name = parameters.get("concept_name")
    limit = parameters.get("limit", 5)

    if not concept_name:
        return {"error": "Missing required parameter: concept_name"}

    try:
        # Query Neo4j for passages mentioning the concept
        query = """
        MATCH (c:Concept {name: $concept_name})<-[:MENTIONS]-(p:Passage)
        RETURN p.text as text, p.document_id as document_id, p.section_id as section_id
        LIMIT $limit
        """

        passages = neo4j_db.run_query(query, {"concept_name": concept_name, "limit": limit})

        return {"passages": passages}
    except Exception as e:
        logger.exception(f"Error getting passages about concept: {e}")
        return {"error": str(e)}


def _run_add_document_task(job: Job) -> dict[str, Any] | None:
    """Wrapper function to run add_document_to_graphrag for a job."""
    from scripts.document_processing.add_document_core import (
        add_document_to_graphrag,
    )
    job_params = job.params
    # For add_bug, we expect 'description' and 'cause'
    description = job_params.get("description")
    cause = job_params.get("cause")

    if description is None or cause is None:
        logger.error(f"Job {job.job_id} for add_bug is missing 'description' or 'cause' parameter.")
        return {"status": "failure", "error": "Missing 'description' or 'cause' parameter for add_bug job."}

    text_param = f"Description: {description}\nCause: {cause}"

    return add_document_to_graphrag(
        text=text_param,
        metadata=job_params.get("metadata", {}),
        neo4j_db=neo4j_db,
        vector_db=vector_db,
        duplicate_detector=duplicate_detector,
    )

# TODO: Implement a similar wrapper for add_folder if async folder processing is needed
# def _run_add_folder_task(job: Job) -> dict[str, Any] | None:
#     """Wrapper function to run folder processing for a job."""
#     # from scripts.document_processing.add_document_core import process_folder_task
#     # job_params = job.params
#     # return process_folder_task(job_params.get("folder_path"), ...)
#     return {"status": "pending", "message": "Async folder processing not yet fully implemented"}


async def handle_add_bug(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle add_bug request.

    Args:
        parameters: Request parameters:
            - description: Bug description
            - cause: Bug cause
            - metadata: Optional bug metadata
            - async: Optional boolean to process asynchronously (default: True)

    Returns:
        Status of the operation
    """
    description = parameters.get("description")
    cause = parameters.get("cause")
    metadata = parameters.get("metadata", {})
    process_async = parameters.get("async", True)

    if not description or not cause:
        return {"error": "'description' and 'cause' are required"}

    text_for_processing = f"Description: {description}\nCause: {cause}"
    if "title" not in metadata:
        metadata["title"] = description

    try:
        doc_hash = duplicate_detector.generate_document_hash(text_for_processing)
        metadata_with_hash = metadata.copy()
        metadata_with_hash["hash"] = doc_hash

        is_dup, existing_doc_id, method = duplicate_detector.is_duplicate(
            text_for_processing, metadata_with_hash
        )

        if is_dup:
            logger.info(
                f"Bug '{metadata.get('title', 'Unknown Title')}' is a duplicate (ID: {existing_doc_id}, Method: {method}). Not adding."
            )
            return {
                "status": "duplicate",
                "message": "Bug is a duplicate and was not added.",
                "bug_id": existing_doc_id,
                "duplicate_detection_method": method,
            }

        if process_async:
            job = job_manager.create_job(
                "add_bug",
                {
                    "description": description,
                    "cause": cause,
                    "metadata": metadata,
                },
            )
            job_manager.run_job_async(job, _run_add_document_task)
            return {"status": "accepted", "message": "Bug processing started", "job_id": job.job_id, "bug_id": None}
        else:
            from scripts.document_processing.add_document_core import (
                add_document_to_graphrag,
            )
            result = add_document_to_graphrag(
                text=text_for_processing,
                metadata=metadata,
                neo4j_db=neo4j_db,
                vector_db=vector_db,
                duplicate_detector=duplicate_detector,
            )
            if result is None: # This implies a duplicate was found by add_document_to_graphrag
                 # Re-check with duplicate_detector to get the ID of the duplicate
                 logger.info("Synchronous add_document_to_graphrag returned None, re-checking for duplicate ID.")
                 is_dup_again, existing_doc_id_again, method_again = duplicate_detector.is_duplicate(
                     text_for_processing, metadata_with_hash
                 )
                 if is_dup_again:
                     logger.info(f"Confirmed duplicate on re-check. Existing ID: {existing_doc_id_again}, Method: {method_again}")
                     return {
                        "status": "duplicate",
                        "message": "Bug is a duplicate (detected during final processing) and was not added.",
                        "bug_id": existing_doc_id_again,
                        "duplicate_detection_method": method_again,
                    }
                 else:
                     # This case implies add_document_to_graphrag returned None for a reason other than a detectable duplicate,
                     # or the duplicate status somehow changed. This is less expected.
                     logger.warning("add_document_to_graphrag returned None, but no duplicate found on re-check.")
                     return {
                        "status": "failure",
                        "message": "Bug processing failed after initial duplicate check, and no duplicate found on re-check.",
                        "bug_id": None,
                        "error": "Inconsistent duplicate detection or other processing error."
                     }
            elif isinstance(result, dict) and result.get("status") == "failure":
                return {"status": "failure", "error": result.get("error"), "bug_id": None}
            elif isinstance(result, dict) and "document_id" in result:
                return {"status": "success", "message": "Bug added successfully.", "bug_id": result.get("document_id")}
            else:
                 return {"status": "failure", "error": "An unexpected error occurred during synchronous bug processing.", "bug_id": None}

    except Exception as e:
        logger.exception(f"Error adding bug: {e}")
        return {"status": "failure", "error": str(e), "bug_id": None}


async def handle_add_folder(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle add-folder request.

    Args:
        parameters: Request parameters:
            - folder_path: Path to folder containing documents
            - metadata: Optional document metadata
            - async: Optional boolean to process asynchronously (default: True)

    Returns:
        Status of the operation
    """
    folder_path = parameters.get("folder_path")
    metadata = parameters.get("metadata", {})
    process_async = parameters.get("async", True)

    if not folder_path:
        return {"error": "Missing required parameter: folder_path"}

    if not os.path.isdir(folder_path):
        return {"error": f"Folder not found: {folder_path}"}

    supported_file_types = [".pdf", ".txt", ".md"]
    files_to_process = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if any(file.endswith(ext) for ext in supported_file_types):
                files_to_process.append(os.path.join(root, file))

    if not files_to_process:
        return {"status": "completed", "message": f"No supported files found in folder: {folder_path}"}

    if process_async:
        job = job_manager.create_job(
            "add_folder",
            {
                "folder_path": folder_path,
                "files_to_process": files_to_process,
                "metadata": metadata,
            },
        )
        # TODO: Implement actual asynchronous folder processing task and pass it here
        # job_manager.run_job_async(job, _run_add_folder_task)
        logger.warning("Async folder processing is not fully implemented, job created but not run.")
        return {"status": "accepted", "message": f"Folder processing job created for {len(files_to_process)} files", "job_id": job.job_id}
    else:
        results = []
        for file_path in files_to_process:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
                file_metadata = metadata.copy()
                if "title" not in file_metadata:
                    file_metadata["title"] = os.path.basename(file_path)

                if text is None:
                     results.append({"status": "failure", "error": f"Could not read text from file: {os.path.basename(file_path)}", "document_id": None, "file": os.path.basename(file_path)})
                     continue

                doc_hash = duplicate_detector.generate_document_hash(text)
                file_metadata_with_hash = file_metadata.copy()
                file_metadata_with_hash["hash"] = doc_hash

                is_dup, existing_doc_id, method = duplicate_detector.is_duplicate(
                    text, file_metadata_with_hash
                )

                if is_dup:
                    logger.info(
                        f"Document '{file_metadata.get('title', 'Unknown Title')}' is a duplicate (ID: {existing_doc_id}, Method: {method}). Not adding."
                    )
                    results.append({
                        "status": "duplicate",
                        "message": f"Document '{os.path.basename(file_path)}' is a duplicate.",
                        "document_id": existing_doc_id,
                        "duplicate_detection_method": method,
                    })
                    continue

                from scripts.document_processing.add_document_core import (
                    add_document_to_graphrag,
                )

                result = add_document_to_graphrag(
                    text=text,
                    metadata=file_metadata,
                    neo4j_db=neo4j_db,
                    vector_db=vector_db,
                    duplicate_detector=duplicate_detector,
                )
                if result is None:
                     results.append({
                        "status": "duplicate",
                        "message": f"Document '{os.path.basename(file_path)}' is a duplicate.",
                        "document_id": None,
                        "duplicate_detection_method": "unknown",
                    })
                elif isinstance(result, dict) and result.get("status") == "failure":
                    results.append({"status": "failure", "error": result.get("error"), "document_id": None, "file": os.path.basename(file_path)})
                elif isinstance(result, dict) and "document_id" in result:
                    results.append({"status": "success", "document_id": result.get("document_id"), "file": os.path.basename(file_path)})
                else:
                     results.append({"status": "failure", "error": "An unexpected error occurred during synchronous document processing.", "document_id": None, "file": os.path.basename(file_path)})

            except Exception as e:
                logger.exception(f"Error processing file {file_path}: {e}")
                results.append({"status": "failure", "error": str(e), "document_id": None, "file": os.path.basename(file_path)})

        return {"status": "completed", "results": results}


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
        return {"error": "Missing required parameter: job_id"}

    job = job_manager.get_job(job_id)

    if not job:
        return {"error": f"Job not found: {job_id}"}

    job_message = job.error if job.status == JobStatus.FAILED else (job.result if job.status == JobStatus.COMPLETED else None)

    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "progress": job.progress,
        "message": job_message,
        "result": job.result,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.completed_at.isoformat() if job.completed_at else None,
    }


async def handle_list_jobs(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle list-jobs request.

    Args:
        parameters: Request parameters:
            - status: Optional filter by status
            - limit: Optional maximum number of jobs to return

    Returns:
        List of jobs
    """
    status_filter_str = parameters.get("status")
    status_filter = JobStatus(status_filter_str) if status_filter_str else None
    limit = parameters.get("limit", 10)

    all_jobs = job_manager.get_jobs(status=status_filter)

    jobs_to_return = all_jobs[:limit]


    return {
        "jobs": [
            {
                "job_id": job.job_id,
                "status": job.status.value,
                "progress": job.progress,
                "message": job.error if job.status == JobStatus.FAILED else (job.result if job.status == JobStatus.COMPLETED else None),
                "created_at": job.created_at.isoformat(),
                "updated_at": job.completed_at.isoformat() if job.completed_at else None,
            }
            for job in jobs_to_return
        ]
    }


async def handle_cancel_job(parameters: dict[str, Any]) -> dict[str, Any]:
    """Handle cancel-job request.

    Args:
        parameters: Request parameters:
            - job_id: Job ID

    Returns:
        Status of the operation
    """
    job_id = parameters.get("job_id")

    if not job_id:
        return {"error": "Missing required parameter: job_id"}

    success = job_manager.cancel_job(job_id)

    if success:
        return {"status": "success", "message": f"Job {job_id} cancelled"}
    else:
        return {"status": "error", "message": f"Job {job_id} not found or cannot be cancelled"}


async def handle_initialize(params: dict[str, Any]) -> dict[str, Any]:
    """Handle initialize request.

    Args:
        params: Initialize parameters

    Returns:
        Initialize response
    """
    client_capabilities = params.get("capabilities", {})
    client_info = params.get("clientInfo", {})
    protocol_version = params.get("protocolVersion")

    logger.info(f"Client connected: {client_info.get('name')} {client_info.get('version')}")
    logger.info(f"Client protocol version: {protocol_version}")

    # TODO: Implement capability negotiation

    return {
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "capabilities": {
            "tools": {"listChanged": False},
            "resources": {"subscribe": False, "listChanged": False},
            "prompts": {"listChanged": False},
            "logging": {},
        },
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        "instructions": "This is the GraphRAG MCP server. Available tools: ping, search, concept, documents, books-by-concept, related-concepts, passages-about-concept, add_bug, add-folder, job-status, list-jobs, cancel-job.",
    }


async def handle_get_tools(_: dict[str, Any]) -> dict[str, Any]:
    """Handle getTools request.

    Args:
        _: Request parameters (ignored)

    Returns:
        List of available tools
    """
    return {"tools": TOOLS}


TOOL_HANDLERS = {
    "ping": handle_ping,
    "search": handle_search,
    "concept": handle_concept,
    "documents": handle_documents,
    "books-by-concept": handle_books_by_concept,
    "related-concepts": handle_related_concepts,
    "passages-about-concept": handle_passages_about_concept,
    "add_bug": handle_add_bug,
    "add-folder": handle_add_folder,
    "job-status": handle_job_status,
    "list-jobs": handle_list_jobs,
    "cancel-job": handle_cancel_job,
}


async def handle_invoke_tool(params: dict[str, Any]) -> dict[str, Any]:
    """Handle invokeTool request.

    Args:
        params: InvokeTool parameters

    Returns:
        InvokeTool response with tool result, conforming to CallToolResult schema.
    """
    tool_name = params.get("name")
    tool_arguments = params.get("arguments", {}) # Corrected key to "arguments"

    if tool_name is None or tool_name not in TOOL_HANDLERS:
        error_response = {
            "error": {
                "code": -32601,
                "message": f"Tool not found: {tool_name}",
                "data": {"availableTools": list(TOOL_HANDLERS.keys())},
            }
        }
        return {
            "content": [{"type": "text", "text": json.dumps(error_response)}],
            "isError": True
        }

    try:
        handler = TOOL_HANDLERS[tool_name]
        tool_result_data = await handler(tool_arguments) # Pass tool_arguments

        if isinstance(tool_result_data, dict) and "error" in tool_result_data:
             return {
                "content": [{"type": "text", "text": json.dumps(tool_result_data)}],
                "isError": True
            }
        return {
            "content": [{"type": "text", "text": json.dumps(tool_result_data)}],
            "isError": False
        }
    except Exception as e:
        logger.exception(f"Error invoking tool {tool_name}")
        error_payload = {"error": f"Error invoking tool: {str(e)}"}
        return {
            "content": [{"type": "text", "text": json.dumps(error_payload)}] ,
            "isError": True,
        }


async def handle_connection(websocket) -> None:
    """Handle WebSocket connection.

    Args:
        websocket: WebSocket connection

    """
    client_id = id(websocket)
    logger.info(f"Client connected: {client_id} from {websocket.remote_address}")

    try:
        # Send a welcome message to confirm connection
        try:
            welcome_msg = {
                "jsonrpc": "2.0",
                "method": "notification",
                "params": {
                    "message": "Connected to GraphRAG MCP Server",
                    "server": SERVER_NAME,
                    "version": SERVER_VERSION,
                },
            }
            await websocket.send(json.dumps(welcome_msg))
        except Exception as e:
            logger.warning(f"Failed to send welcome message: {e}")

        # Process messages
        async for message in websocket:
            try:
                # Log received message (truncated for large messages)
                msg_preview = message[:200] + "..." if len(message) > 200 else message
                logger.debug(f"Received message from client {client_id}: {msg_preview}")

                # Parse message
                data = json.loads(message)

                # Extract JSON-RPC fields
                jsonrpc = data.get("jsonrpc")
                method = data.get("method")
                params = data.get("params", {})
                request_id = data.get("id")

                # Validate JSON-RPC version
                if jsonrpc != "2.0":
                    logger.warning(
                        f"Invalid JSON-RPC version from client {client_id}: {jsonrpc}"
                    )
                    response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32600,
                            "message": "Invalid JSON-RPC version, expected 2.0",
                        },
                        "id": request_id,
                    }
                    await websocket.send(json.dumps(response))
                    continue

                # Handle method
                result_payload = None
                error_payload = None

                logger.info(f"Processing method '{method}' from client {client_id}")

                if method == "initialize":
                    result_payload = await handle_initialize(params)
                elif method == "getTools" or method == "tools/list":
                    result_payload = await handle_get_tools(params)
                elif method == "invokeTool" or method == "tools/call":
                    result_payload = await handle_invoke_tool(params)
                else:
                    logger.warning(f"Unknown method '{method}' from client {client_id}")
                    error_payload = {"code": -32601, "message": f"Method not found: {method}"}

                # Prepare response
                response = {"jsonrpc": "2.0", "id": request_id}

                if error_payload:
                    response["error"] = error_payload
                elif result_payload is not None:
                    response["result"] = result_payload

                # Send response if it's a request (has an id)
                if request_id is not None:
                    await websocket.send(json.dumps(response))

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parse error from client {client_id}: {e}")
                response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"},
                    "id": None,
                }
                await websocket.send(json.dumps(response))
            except Exception as e:
                logger.exception(f"Error handling message from client {client_id}: {e}")
                response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                    "id": None,
                }
                await websocket.send(json.dumps(response))
    except websockets.exceptions.ConnectionClosed as e:
        logger.info(f"Client {client_id} disconnected: {e.code} {e.reason}")
    except Exception as e:
        logger.exception(f"Error handling connection for client {client_id}: {str(e)}")
    finally:
        logger.info(f"Connection closed for client {client_id}")


async def start_server(host: str = "localhost", port: int = 8767) -> None:
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


def main() -> None:
    """Main function to start the MCP server."""
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Start the GraphRAG MCP server")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8767, help="Server port")
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    args = parser.parse_args()

    # Set logging level
    logger.setLevel(getattr(logging, args.log_level))

    # Run the server
    logger.info(f"Starting MCP server on {args.host}:{args.port}")
    asyncio.run(start_server(host=args.host, port=args.port))


if __name__ == "__main__":
    main()
