"""
Flask API server for GraphRAG project.

This module provides a RESTful API for the GraphRAG system, allowing AI agents
to interact with the system programmatically.
"""
import os
import sys
import json
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

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
    print("❌ Neo4j connection failed!")
    # Continue anyway, as the connection might be established later

if not vector_db.verify_connection():
    print("❌ Vector database connection failed!")
    # Continue anyway, as the connection might be established later

@app.route('/health', methods=['GET'])
def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        Health status of the API and database connections
    """
    neo4j_status = neo4j_db.verify_connection()
    vector_db_status = vector_db.verify_connection()
    
    return jsonify({
        'status': 'ok' if neo4j_status and vector_db_status else 'degraded',
        'neo4j_connected': neo4j_status,
        'vector_db_connected': vector_db_status,
        'version': '1.0.0'
    })

@app.route('/search', methods=['POST'])
def search() -> Dict[str, Any]:
    """
    Perform a hybrid search using both vector and graph databases.
    
    Request body:
        query (str): Search query
        n_results (int, optional): Number of vector results to return (default: 5)
        max_hops (int, optional): Maximum number of hops in the graph (default: 2)
    
    Returns:
        Search results
    """
    data = request.json
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing required parameter: query'}), 400
    
    query = data['query']
    n_results = data.get('n_results', 5)
    max_hops = data.get('max_hops', 2)
    
    try:
        results = db_linkage.hybrid_search(
            query_text=query,
            n_vector_results=n_results,
            max_graph_hops=max_hops
        )
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/concepts/<concept_name>', methods=['GET'])
def get_concept(concept_name: str) -> Dict[str, Any]:
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
def add_document() -> Dict[str, Any]:
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
        
        result = add_document_to_graphrag(
            text=text,
            metadata=metadata,
            neo4j_db=neo4j_db,
            vector_db=vector_db
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Document added successfully',
            'document_id': result.get('document_id'),
            'entities': result.get('entities', []),
            'relationships': result.get('relationships', [])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/documents/<concept_name>', methods=['GET'])
def get_documents_for_concept(concept_name: str) -> Dict[str, Any]:
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
def get_books() -> Dict[str, Any]:
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
def get_book_concepts(book_title: str) -> Dict[str, Any]:
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
def get_all_concepts() -> Dict[str, Any]:
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
    # Run the Flask app in debug mode
    app.run(debug=True, host='0.0.0.0', port=5000)