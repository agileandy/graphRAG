"""
Flask API server for GraphRAG project.

This module provides a RESTful API for the GraphRAG system, allowing AI agents
to interact with the system programmatically.
"""
import os
import sys
import logging
import glob
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more verbose logging
    format='%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

# Explicitly load environment variables from the config file
config_env_path = os.path.expanduser("~/.graphrag/config.env")
if os.path.exists(config_env_path):
    logger.info(f"Loading environment variables from {config_env_path}")
    load_dotenv(config_env_path)
else:
    logger.warning(f"Config file not found at {config_env_path}, falling back to default .env")
    load_dotenv()

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase
from src.database.db_linkage import DatabaseLinkage
from src.processing.job_manager import JobManager

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize database connections
neo4j_db = Neo4jDatabase()
vector_db = VectorDatabase()
db_linkage = DatabaseLinkage(neo4j_db, vector_db)

# Initialize job manager
job_manager = JobManager()

# Verify database connections on startup
if not neo4j_db.verify_connection():
    logger.error("❌ Neo4j connection failed!")
    # Continue anyway, as the connection might be established later

if not vector_db.verify_connection():
    logger.error("❌ Vector database connection failed!")
    logger.info(f"ChromaDB directory: {vector_db.persist_directory}")
    # Continue anyway, as the connection might be established later

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns:
        Health status of the API and database connections
    """
    logger.info("Health check requested")
    logger.info(f"ChromaDB directory: {vector_db.persist_directory}")

    neo4j_status = neo4j_db.verify_connection()
    logger.info(f"Neo4j connection status: {neo4j_status}")

    vector_db_status = vector_db.verify_connection()
    logger.info(f"Vector DB connection status: {vector_db_status}")

    return jsonify({
        'status': 'ok' if neo4j_status and vector_db_status else 'degraded',
        'neo4j_connected': neo4j_status,
        'vector_db_connected': vector_db_status,
        'version': '1.0.0'
    })
@app.route('/version', methods=['GET'])
def get_version():
    """
    Endpoint to get the application version.

    Returns:
        A JSON object containing the application version.
    """
    app_version = os.getenv('APP_VERSION', 'unknown')
    return jsonify({'version': app_version})

@app.route('/search', methods=['POST'])
def search():
    """
    Perform a hybrid search using both vector and graph databases.

    Request body:
        query (str): Search query
        n_results (int, optional): Number of vector results to return (default: 5)
        max_hops (int, optional): Maximum number of hops in the graph (default: 2)
        repair_index (bool, optional): Whether to attempt to repair the index if it's unhealthy (default: True)

    Returns:
        Search results
    """
    data = request.json

    if not data or 'query' not in data:
        return jsonify({'error': 'Missing required parameter: query'}), 400

    query = data['query']
    n_results = data.get('n_results', 5)
    max_hops = data.get('max_hops', 2)
    repair_index = data.get('repair_index', True)

    # Check vector database index health if repair_index is True
    if repair_index:
        is_healthy, health_message = vector_db.check_index_health()
        if not is_healthy:
            # Try to repair the index
            success, repair_message = vector_db.repair_index()
            if not success:
                return jsonify({
                    'error': f"Vector database index is unhealthy and repair failed: {repair_message}",
                    'vector_results': {
                        'ids': [],
                        'documents': [],
                        'metadatas': [],
                        'distances': []
                    },
                    'graph_results': []
                }), 500

    try:
        results = db_linkage.hybrid_search(
            query_text=query,
            n_vector_results=n_results,
            max_graph_hops=max_hops
        )

        # Check if there's an error in the results
        if 'error' in results:
            return jsonify(results), 500

        return jsonify(results)
    except Exception as e:
        error_message = str(e)
        print(f"Error during search: {error_message}")

        # Create a fallback response with empty results
        fallback_response = {
            'error': error_message,
            'vector_results': {
                'ids': [],
                'documents': [],
                'metadatas': [],
                'distances': []
            },
            'graph_results': []
        }

        return jsonify(fallback_response), 500

@app.route('/concepts/<concept_name>', methods=['GET'])
def get_concept(concept_name: str):
    """
    Get information about a specific concept.

    Args:
        concept_name: Name of the concept

    Returns:
        Concept information and related concepts
    """
    try:
        # Find the concept by name (case-insensitive)
        query = """
        MATCH (c:Concept)
        WHERE toLower(c.name) CONTAINS toLower($name)
        RETURN c.id AS id, c.name AS name
        """
        results = neo4j_db.run_query(query, {"name": concept_name})

        if not results:
            return jsonify({'error': f"No concept found with name containing '{concept_name}'"}), 404

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

        return jsonify({
            'concept': {
                'id': concept_id,
                'name': concept_name
            },
            'related_concepts': unique_related
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/documents', methods=['POST'])
def add_document():
    """
    Add a document to the GraphRAG system.

    Request body:
        text (str): Document text
        metadata (dict, optional): Document metadata

    Returns:
        Status of the operation
    """
    data = request.json

    if not data or 'text' not in data:
        return jsonify({'error': 'Missing required parameter: text'}), 400

    text = data['text']
    metadata = data.get('metadata', {})

    try:
        # Import here to avoid circular imports
        from scripts.document_processing.add_document_core import add_document_to_graphrag
        from src.processing.duplicate_detector import DuplicateDetector

        # Initialize duplicate detector
        duplicate_detector = DuplicateDetector(vector_db)

        # Calculate document hash for duplicate checking
        doc_hash = duplicate_detector.generate_document_hash(text)
        metadata_with_hash = metadata.copy()
        metadata_with_hash["hash"] = doc_hash

        # Check for duplicates before adding
        is_dup, existing_doc_id, method = duplicate_detector.is_duplicate(text, metadata_with_hash)

        result = add_document_to_graphrag(
            text=text,
            metadata=metadata,
            neo4j_db=neo4j_db,
            vector_db=vector_db,
            duplicate_detector=duplicate_detector
        )

        if result:
            # Document was added successfully
            return jsonify({
                'status': 'success',
                'message': 'Document added successfully',
                'document_id': result.get('document_id'),
                'entities': result.get('entities', []),
                'relationships': result.get('relationships', [])
            })
        else:
            # Document was a duplicate
            return jsonify({
                'status': 'duplicate',
                'message': 'Document is a duplicate and was not added',
                'document_id': existing_doc_id,
                'duplicate_detection_method': method,
                'entities': [],
                'relationships': []
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/folders', methods=['POST'])
def add_folder():
    """
    Add all documents from a folder to the GraphRAG system.
    This endpoint processes documents asynchronously using the job management system.

    Request body:
        folder_path (str): Path to the folder containing documents
        recursive (bool, optional): Whether to process subfolders (default: False)
        file_types (list, optional): List of file extensions to process (default: [".pdf", ".txt", ".md"])
        default_metadata (dict, optional): Default metadata to apply to all documents

    Returns:
        Job information for tracking the folder processing
    """
    data = request.json

    if not data or 'folder_path' not in data:
        return jsonify({'error': 'Missing required parameter: folder_path'}), 400

    folder_path = data['folder_path']
    recursive = data.get('recursive', False)
    file_types = data.get('file_types', [".pdf", ".txt", ".md"])
    default_metadata = data.get('default_metadata', {})

    # Validate folder path
    if not os.path.isdir(folder_path):
        return jsonify({'error': f"Folder not found: {folder_path}"}), 404

    # Get list of files in the folder
    files = []
    for file_type in file_types:
        if recursive:
            # Use recursive glob pattern
            pattern = os.path.join(folder_path, "**", f"*{file_type}")
            files.extend(glob.glob(pattern, recursive=True))
        else:
            # Use non-recursive pattern
            pattern = os.path.join(folder_path, f"*{file_type}")
            files.extend(glob.glob(pattern))

    if not files:
        return jsonify({
            'status': 'error',
            'message': f"No files with types {file_types} found in {folder_path}"
        }), 404

    # Create a job for processing the folder
    job = job_manager.create_job(
        job_type="add-folder",
        params={
            "folder_path": folder_path,
            "recursive": recursive,
            "file_types": file_types,
            "default_metadata": default_metadata,
            "files": files
        }
    )

    # Define the task function
    def process_folder_task(job):
        """
        Process all files in a folder using multithreading.

        Args:
            job: Job object

        Returns:
            Processing results
        """
        from scripts.document_processing.add_document_core import add_document_to_graphrag
        from src.processing.duplicate_detector import DuplicateDetector
        import time
        import threading
        from concurrent.futures import ThreadPoolExecutor

        # Initialize duplicate detector
        duplicate_detector = DuplicateDetector(vector_db)

        files = job.params["files"]
        default_metadata = job.params.get("default_metadata", {})

        results = {
            "added_count": 0,
            "skipped_count": 0,
            "failed_count": 0,
            "details": []
        }

        # Create a lock for thread-safe updates to results
        results_lock = threading.Lock()
        # Create a lock for thread-safe progress updates
        progress_lock = threading.Lock()
        # Track processed files count
        processed_count = 0

        # Define a function to process a single file
        def process_file(file_info):
            nonlocal processed_count
            i, file_path = file_info
            filename = os.path.basename(file_path)
            file_result = {
                "file": filename,
                "success": False
            }

            try:
                logger.info(f"Processing file {i+1}/{len(files)}: {filename}")

                # Read file content based on file type
                try:
                    file_ext = os.path.splitext(file_path)[1].lower()

                    # Handle PDF files
                    if file_ext == '.pdf':
                        try:
                            import PyPDF2
                            with open(file_path, 'rb') as file:
                                reader = PyPDF2.PdfReader(file)
                                text = ""
                                # Extract text from each page
                                for page_num in range(len(reader.pages)):
                                    page = reader.pages[page_num]
                                    text += page.extract_text() + "\n\n"

                            if not text.strip():
                                logger.warning(f"PDF extraction returned empty text for {filename}")
                                file_result["error"] = "PDF extraction returned empty text"
                                with results_lock:
                                    results["failed_count"] += 1
                                    results["details"].append(file_result)
                                return
                        except ImportError:
                            logger.error("PyPDF2 is not installed. Please install it with 'pip install PyPDF2'.")
                            file_result["error"] = "PyPDF2 is not installed"
                            with results_lock:
                                results["failed_count"] += 1
                                results["details"].append(file_result)
                            return
                        except Exception as e:
                            logger.error(f"Failed to extract text from PDF {filename}: {str(e)}")
                            file_result["error"] = f"Failed to extract text from PDF: {str(e)}"
                            with results_lock:
                                results["failed_count"] += 1
                                results["details"].append(file_result)
                            return
                    # Handle text files
                    else:
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                text = f.read()
                        except UnicodeDecodeError:
                            # Try with a different encoding
                            try:
                                with open(file_path, 'r', encoding='latin-1') as f:
                                    text = f.read()
                            except Exception as e:
                                logger.error(f"Failed to read file {filename}: {str(e)}")
                                file_result["error"] = f"Failed to read file: {str(e)}"
                                with results_lock:
                                    results["failed_count"] += 1
                                    results["details"].append(file_result)
                                return
                except Exception as e:
                    logger.error(f"Failed to process file {filename}: {str(e)}")
                    file_result["error"] = f"Failed to process file: {str(e)}"
                    with results_lock:
                        results["failed_count"] += 1
                        results["details"].append(file_result)
                    return

                # Create metadata for the document
                metadata = default_metadata.copy()

                # Extract title from filename (remove extension and clean up)
                title = os.path.splitext(filename)[0]

                # Try to extract author information if in parentheses
                author = "Unknown"
                if "(" in title and ")" in title:
                    parts = title.split("(")
                    for part in parts[1:]:
                        if ")" in part:
                            potential_author = part.split(")")[0].strip()
                            if potential_author and "Z-Library" not in potential_author:
                                author = potential_author
                                break

                # Clean up title
                title = title.split("(")[0].strip()

                # Set default metadata if not provided
                if 'title' not in metadata:
                    metadata['title'] = title
                if 'author' not in metadata:
                    metadata['author'] = author
                if 'source' not in metadata:
                    metadata['source'] = "Folder Import"
                if 'filename' not in metadata:
                    metadata['filename'] = filename

                # Add document to GraphRAG system
                logger.debug(f"Adding document to GraphRAG: {filename}, text length: {len(text)}, metadata: {metadata}")
                try:
                    # Force rule-based concept extraction for folder add
                    # This is a workaround for the LLM-based extraction issues
                    metadata["force_rule_based"] = True

                    result = add_document_to_graphrag(
                        text=text,
                        metadata=metadata,
                        neo4j_db=neo4j_db,
                        vector_db=vector_db,
                        duplicate_detector=duplicate_detector
                    )

                    # Log the raw result for debugging
                    logger.debug(f"Raw result from add_document_to_graphrag: {result}")

                    if result:
                        # Document was added successfully
                        logger.info(f"Added document: {filename}, document_id: {result.get('document_id')}")
                        file_result["success"] = True
                        file_result["document_id"] = result.get("document_id")
                        file_result["entities_count"] = len(result.get("entities", []))
                        file_result["relationships_count"] = len(result.get("relationships", []))
                        with results_lock:
                            results["added_count"] += 1
                            results["details"].append(file_result)
                    else:
                        # Document was a duplicate or failed
                        logger.warning(f"Document not added: {filename}. Result was: {result}")
                        if isinstance(result, dict) and result.get("status") == "duplicate":
                            logger.info(f"Skipped duplicate document: {filename}")
                            file_result["success"] = True
                            file_result["status"] = "duplicate"
                            with results_lock:
                                results["skipped_count"] += 1
                                results["details"].append(file_result)
                        else:
                            logger.error(f"Failed to add document: {filename}. Unknown result: {result}")
                            file_result["success"] = False
                            file_result["error"] = f"Unknown result from add_document_to_graphrag: {result}"
                            with results_lock:
                                results["failed_count"] += 1
                                results["details"].append(file_result)
                except Exception as e:
                    logger.error(f"Exception in add_document_to_graphrag for {filename}: {str(e)}")
                    logger.error(traceback.format_exc())
                    file_result["success"] = False
                    file_result["error"] = f"Exception in add_document_to_graphrag: {str(e)}"
                    with results_lock:
                        results["failed_count"] += 1
                        results["details"].append(file_result)

            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")
                file_result["error"] = str(e)
                with results_lock:
                    results["failed_count"] += 1
                    results["details"].append(file_result)
            finally:
                # Update progress
                with progress_lock:
                    nonlocal processed_count
                    processed_count += 1
                    job.update_progress(processed_count, len(files))

        # Start the job
        job.start()

        # Determine the number of worker threads (limit to a reasonable number)
        max_workers = min(10, len(files))  # Use at most 10 threads or number of files, whichever is smaller

        # Process files in parallel using a thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all files for processing
            file_infos = [(i, file_path) for i, file_path in enumerate(files)]
            executor.map(process_file, file_infos)

        # Ensure final progress is 100%
        job.update_progress(len(files), len(files))

        return results

    # Start the job asynchronously
    job_manager.run_job_async(job, process_folder_task)

    # Return job information
    return jsonify({
        'status': 'accepted',
        'message': 'Folder processing started',
        'job_id': job.job_id,
        'total_files': len(files)
    })

@app.route('/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id: str):
    """
    Get the status of an asynchronous job.

    Args:
        job_id: Job ID

    Returns:
        Job status information
    """
    job = job_manager.get_job(job_id)

    if not job:
        return jsonify({'error': f"Job not found: {job_id}"}), 404

    return jsonify(job.to_dict())

@app.route('/jobs', methods=['GET'])
def list_jobs():
    """
    List all jobs, optionally filtered by status or type.

    Query parameters:
        status: Filter by job status (queued, running, completed, failed, cancelled)
        type: Filter by job type (add-document, add-folder, etc.)

    Returns:
        List of jobs
    """
    # Get filter parameters
    status_param = request.args.get('status')
    job_type = request.args.get('type')

    # Convert status string to JobStatus enum if provided
    status = None
    if status_param:
        from src.processing.job_manager import JobStatus
        try:
            status = JobStatus(status_param)
        except ValueError:
            # Invalid status, return empty list
            return jsonify({'jobs': []})

    # Get jobs
    jobs = job_manager.get_jobs(status=status, job_type=job_type)

    # Convert jobs to dictionaries
    job_dicts = [job.to_dict() for job in jobs]

    return jsonify({'jobs': job_dicts})

@app.route('/documents/<concept_name>', methods=['GET'])
def get_documents_for_concept(concept_name: str):
    """
    Get documents related to a specific concept.

    Args:
        concept_name: Name of the concept

    Returns:
        List of related documents
    """
    try:
        # Find the concept by name (case-insensitive)
        query = """
        MATCH (c:Concept)
        WHERE toLower(c.name) CONTAINS toLower($name)
        RETURN c.id AS id, c.name AS name
        """
        results = neo4j_db.run_query(query, {"name": concept_name})

        if not results:
            return jsonify({'error': f"No concept found with name containing '{concept_name}'"}), 404

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

        # Limit the number of results (optional query parameter)
        limit = request.args.get('limit', default=5, type=int)
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

        return jsonify({
            'concept': {
                'id': concept_id,
                'name': concept_name
            },
            'documents': documents
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/books', methods=['GET'])
def get_books():
    """
    Get all books in the system.

    Returns:
        List of books
    """
    try:
        query = """
        MATCH (b:Book)
        RETURN b.id AS id, b.title AS title, b.filename AS filename
        """
        books = neo4j_db.run_query(query)

        return jsonify({
            'books': books
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/books/<book_title>', methods=['GET'])
def get_book_concepts(book_title: str):
    """
    Get concepts mentioned in a specific book.

    Args:
        book_title: Title of the book

    Returns:
        Book information and related concepts
    """
    try:
        # Find the book by title (case-insensitive)
        query = """
        MATCH (b:Book)
        WHERE toLower(b.title) CONTAINS toLower($title)
        RETURN b.id AS id, b.title AS title, b.filename AS filename
        """
        results = neo4j_db.run_query(query, {"title": book_title})

        if not results:
            return jsonify({'error': f"No book found with title containing '{book_title}'"}), 404

        # Use the first matching book
        book_id = results[0]["id"]
        book_title = results[0]["title"]
        book_filename = results[0]["filename"]

        # Find concepts mentioned in this book
        query = """
        MATCH (b:Book {id: $book_id})-[:MENTIONS]->(c:Concept)
        RETURN c.id AS id, c.name AS name
        """
        concepts = neo4j_db.run_query(query, {"book_id": book_id})

        return jsonify({
            'book': {
                'id': book_id,
                'title': book_title,
                'filename': book_filename
            },
            'concepts': concepts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/concepts', methods=['GET'])
def get_all_concepts():
    """
    Get all concepts in the system.

    Returns:
        List of concepts
    """
    try:
        query = """
        MATCH (c:Concept)
        RETURN c.id AS id, c.name AS name
        """
        concepts = neo4j_db.run_query(query)

        return jsonify({
            'concepts': concepts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.teardown_appcontext
def close_db_connections(error=None):
    """
    Close database connections when the application context ends.
    """
    neo4j_db.close()

if __name__ == '__main__':
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Start the GraphRAG API server')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5001, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    args = parser.parse_args()

    # Start the server
    app.run(host=args.host, port=args.port, debug=True)