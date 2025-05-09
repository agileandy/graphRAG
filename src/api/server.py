"""
Flask API server for GraphRAG project.

This module provides a RESTful API for the GraphRAG system, allowing AI agents
to interact with the system programmatically.
"""
import os
import sys
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
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

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize database connections
neo4j_db = Neo4jDatabase()
vector_db = VectorDatabase()
db_linkage = DatabaseLinkage(neo4j_db, vector_db)

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
        from scripts.add_document import add_document_to_graphrag
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