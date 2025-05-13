#!/usr/bin/env python3
"""
Script to import documents from a folder into the GraphRAG system.
"""

import os
import sys
import glob
import uuid
import hashlib
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    # Import required modules
    from src.database.neo4j_db import Neo4jDatabase
    from src.database.vector_db import VectorDatabase
    from src.processing.concept_extractor import ConceptExtractor
    from src.processing.duplicate_detector import DuplicateDetector
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.info("Make sure you're running this script from the project root directory")
    sys.exit(1)

def add_document_to_graphrag(
    text: str,
    metadata: Dict[str, Any],
    neo4j_db: Neo4jDatabase,
    vector_db: VectorDatabase,
    duplicate_detector: Optional[DuplicateDetector] = None
) -> Dict[str, Any]:
    """
    Add a document to the GraphRAG system.

    Args:
        text: Document text
        metadata: Document metadata
        neo4j_db: Neo4j database instance
        vector_db: Vector database instance
        duplicate_detector: Optional duplicate detector

    Returns:
        Dictionary with document ID and extracted entities
    """
    logger.info(f"Processing document: {metadata.get('title', 'Untitled')}")

    # Check for duplicates if a duplicate detector is provided
    if duplicate_detector:
        doc_hash = duplicate_detector.generate_document_hash(text)
        is_duplicate, existing_doc, _ = duplicate_detector.is_duplicate(text, metadata)

        if is_duplicate:
            logger.info(f"Duplicate document detected: {existing_doc}")
            return {
                "status": "duplicate",
                "existing_document": existing_doc
            }
    else:
        # Generate a simple hash if no duplicate detector
        doc_hash = hashlib.sha256(text.encode()).hexdigest()

    # 1. Extract concepts from the document
    from src.processing.concept_extractor import ConceptExtractor
    extractor = ConceptExtractor(use_nlp=True, use_llm=True)
    concept_data = extractor.extract_concepts(text, method="auto", max_concepts=20)

    # Convert to entities format
    entities = []
    for concept in concept_data:
        entity_id = f"concept-{uuid.uuid4()}"
        entities.append({
            "id": entity_id,
            "name": concept["concept"],
            "type": "Concept",
            "description": concept.get("definition", ""),
            "relevance": concept.get("relevance", 1.0)
        })

    # 2. Create relationships between entities (simple approach)
    relationships = []
    for i, source in enumerate(entities):
        for j, target in enumerate(entities):
            if i != j:
                # Simple relationship with default strength
                relationships.append((source["id"], target["id"], 0.5))

    # 3. Create a unique ID for the document
    doc_id = f"doc-{uuid.uuid4()}"

    # 4. Add entities to Neo4j
    for entity in entities:
        # Check if entity already exists
        query = """
        MATCH (c:Concept {name: $name})
        RETURN c.id AS id
        """
        result = neo4j_db.run_query_and_return_single(query, {"name": entity["name"]})

        if not result:
            # Create new entity
            query = """
            CREATE (c:Concept {
                id: $id,
                name: $name,
                type: $type,
                description: $description
            })
            RETURN c.id AS id
            """
            neo4j_db.run_query(query, {
                "id": entity["id"],
                "name": entity["name"],
                "type": entity.get("type", "Concept"),
                "description": entity.get("description", "")
            })

    # 5. Create Document node in Neo4j
    doc_properties = {
        "id": doc_id,
        "title": metadata.get("title", "Untitled Document"),
        "author": metadata.get("author", "Unknown"),
        "category": metadata.get("category", ""),
        "subcategory": metadata.get("subcategory", ""),
        "source": metadata.get("source", ""),
        "hash": doc_hash,
        "created_at": metadata.get("created_at", datetime.now().isoformat())
    }

    # Create Document node
    query = """
    CREATE (d:Document {
        id: $id,
        title: $title,
        author: $author,
        category: $category,
        subcategory: $subcategory,
        source: $source,
        hash: $hash,
        created_at: $created_at
    })
    RETURN d.id AS id
    """
    neo4j_db.run_query(query, doc_properties)

    # 6. Create relationships between document and entities
    for entity in entities:
        query = """
        MATCH (d:Document {id: $doc_id})
        MATCH (c:Concept {id: $concept_id})
        CREATE (d)-[r:MENTIONS]->(c)
        RETURN r
        """
        neo4j_db.run_query(query, {
            "doc_id": doc_id,
            "concept_id": entity["id"]
        })

    # 7. Create relationships between entities
    for source_id, target_id, strength in relationships:
        query = """
        MATCH (c1:Concept {id: $source_id})
        MATCH (c2:Concept {id: $target_id})
        MERGE (c1)-[r:RELATED_TO]->(c2)
        ON CREATE SET r.strength = $strength
        ON MATCH SET r.strength = CASE
            WHEN r.strength < $strength THEN $strength
            ELSE r.strength
        END
        RETURN r
        """
        neo4j_db.run_query(query, {
            "source_id": source_id,
            "target_id": target_id,
            "strength": strength
        })

    # 8. Add document to vector database
    # Update metadata with entity IDs
    doc_metadata = metadata.copy()
    doc_metadata["doc_id"] = doc_id

    # Add concept IDs to metadata
    if entities:
        # ChromaDB doesn't support lists in metadata, so we'll join them into a string
        doc_metadata["concept_ids"] = ",".join([entity["id"] for entity in entities])
        doc_metadata["concept_names"] = ",".join([entity["name"] for entity in entities])

    # Add document to vector database
    vector_db.add_documents(
        documents=[text],
        metadatas=[doc_metadata],
        ids=[doc_id]
    )

    return {
        "document_id": doc_id,
        "entities": entities,
        "relationships": relationships
    }

def process_pdf_file(file_path: str, neo4j_db: Neo4jDatabase, vector_db: VectorDatabase) -> Dict[str, Any]:
    """
    Process a PDF file and add it to the GraphRAG system.

    Args:
        file_path: Path to the PDF file
        neo4j_db: Neo4j database instance
        vector_db: Vector database instance

    Returns:
        Result of adding the document
    """
    try:
        # Extract text from PDF
        with open(file_path, 'rb') as file:
            import PyPDF2
            reader = PyPDF2.PdfReader(file)
            text = ""

            # Extract text from each page
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n\n"

        if not text:
            return {
                "status": "error",
                "message": f"Failed to extract text from {file_path}"
            }

        # Extract metadata from filename
        filename = os.path.basename(file_path)
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

        # Create metadata
        metadata = {
            "title": title,
            "author": author,
            "source": "PDF Import",
            "filename": filename,
            "file_path": file_path,
            "category": "AI",
            "subcategory": "Prompt Engineering"
        }

        # Add document to GraphRAG system
        duplicate_detector = DuplicateDetector(vector_db)
        result = add_document_to_graphrag(
            text=text,
            metadata=metadata,
            neo4j_db=neo4j_db,
            vector_db=vector_db,
            duplicate_detector=duplicate_detector
        )

        return {
            "status": "success",
            "document_id": result.get("document_id"),
            "entities": [entity["name"] for entity in result.get("entities", [])],
            "relationships": len(result.get("relationships", []))
        }

    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

def process_folder(folder_path: str, neo4j_db: Neo4jDatabase, vector_db: VectorDatabase) -> Dict[str, Any]:
    """
    Process all PDF files in a folder.

    Args:
        folder_path: Path to the folder
        neo4j_db: Neo4j database instance
        vector_db: Vector database instance

    Returns:
        Summary of processing results
    """
    # Get list of PDF files
    pdf_files = glob.glob(os.path.join(folder_path, "*.pdf"))

    if not pdf_files:
        return {
            "status": "error",
            "message": f"No PDF files found in {folder_path}"
        }

    logger.info(f"Found {len(pdf_files)} PDF files in {folder_path}")

    # Process each file
    results = {
        "total": len(pdf_files),
        "successful": 0,
        "failed": 0,
        "duplicates": 0,
        "details": []
    }

    for i, file_path in enumerate(pdf_files, 1):
        filename = os.path.basename(file_path)
        logger.info(f"[{i}/{len(pdf_files)}] Processing {filename}")

        result = process_pdf_file(file_path, neo4j_db, vector_db)

        if result.get("status") == "success":
            results["successful"] += 1
        elif result.get("status") == "duplicate":
            results["duplicates"] += 1
        else:
            results["failed"] += 1

        results["details"].append({
            "file": filename,
            "status": result.get("status"),
            "document_id": result.get("document_id"),
            "entities": result.get("entities", []),
            "relationships": result.get("relationships", 0)
        })

    return results

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Import documents into the GraphRAG system")
    parser.add_argument("--folder", required=True, help="Path to the folder containing documents")
    args = parser.parse_args()

    # Check if folder exists
    if not os.path.isdir(args.folder):
        logger.error(f"Folder not found: {args.folder}")
        sys.exit(1)

    # Initialize databases
    neo4j_db = Neo4jDatabase()
    vector_db = VectorDatabase()

    # Verify connections
    if not neo4j_db.verify_connection():
        logger.error("Neo4j connection failed!")
        sys.exit(1)

    if not vector_db.verify_connection():
        logger.error("Vector database connection failed!")
        sys.exit(1)

    logger.info("Database connections verified!")

    # Process folder
    try:
        results = process_folder(args.folder, neo4j_db, vector_db)

        # Print summary
        logger.info("\nProcessing Summary:")
        logger.info(f"Total files: {results['total']}")
        logger.info(f"Successfully processed: {results['successful']}")
        logger.info(f"Failed: {results['failed']}")
        logger.info(f"Duplicates: {results['duplicates']}")

        # Print details of successful documents
        if results['successful'] > 0:
            logger.info("\nSuccessfully processed documents:")
            for detail in results['details']:
                if detail['status'] == 'success':
                    logger.info(f"- {detail['file']}: {len(detail['entities'])} entities, {detail['relationships']} relationships")

    finally:
        # Close Neo4j connection
        neo4j_db.close()

if __name__ == "__main__":
    main()
