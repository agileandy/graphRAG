"""
Optimized script to add documents to the GraphRAG system.

This script demonstrates how to:
1. Process documents with optimized chunking
2. Extract entities and relationships
3. Add them to the GraphRAG system with batch processing
"""
import sys
import os
import uuid
import argparse
from typing import Dict, List, Any, Tuple, Optional

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase
from src.processing.document_processor import (
    smart_chunk_text,
    optimize_metadata,
    process_document_with_metadata,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_OVERLAP,
    DEFAULT_BATCH_SIZE
)

def extract_entities_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Extract entities from text.
    
    Args:
        text: Text to extract entities from
        
    Returns:
        List of extracted entities
    """
    # Simple keyword-based entity extraction
    # In a production system, you would use NLP or LLMs for this
    keywords = {
        "neural network": "NN",
        "deep learning": "DL",
        "machine learning": "ML",
        "artificial intelligence": "AI",
        "natural language processing": "NLP",
        "computer vision": "CV",
        "reinforcement learning": "RL",
        "transformer": "TR",
        "attention mechanism": "AM",
        "fine-tuning": "FT",
        "embedding": "EMB",
        "hybrid search": "HS",
        "deduplication": "DD",
        "large language model": "LLM",
        "llm": "LLM",
        "neo4j": "NEO",
        "chromadb": "CHROMA",
        "vector database": "VDB",
        "knowledge graph": "KG",
        "graph database": "GDB"
    }
    
    entities = []
    text_lower = text.lower()
    
    # Check for each keyword in the text
    for keyword, abbr in keywords.items():
        if keyword.lower() in text_lower:
            entity_id = f"concept-{abbr.lower()}"
            
            # Check if entity already exists in the list
            if not any(e["id"] == entity_id for e in entities):
                entities.append({
                    "id": entity_id,
                    "name": keyword.title(),
                    "type": "Concept",
                    "abbreviation": abbr
                })
    
    return entities

def extract_relationships(entities: List[Dict[str, Any]], text: str) -> List[Tuple[str, str, float]]:
    """
    Extract relationships between entities.
    
    Args:
        entities: List of extracted entities
        text: Document text
        
    Returns:
        List of relationships as (source_id, target_id, strength)
    """
    relationships = []
    
    # Simple co-occurrence based relationship extraction
    # In a production system, you would use more sophisticated methods
    if len(entities) > 1:
        for i, source in enumerate(entities):
            for target in entities[i+1:]:
                # Calculate a simple strength based on proximity in the list
                # In a real system, you would use semantic similarity or other metrics
                strength = 0.5  # Default strength
                
                # Add relationship
                relationships.append((source["id"], target["id"], strength))
    
    return relationships

def add_optimized_document(
    text: str,
    metadata: Dict[str, Any],
    neo4j_db: Neo4jDatabase,
    vector_db: VectorDatabase,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    batch_size: int = DEFAULT_BATCH_SIZE
) -> Dict[str, Any]:
    """
    Add a document to the GraphRAG system with optimized processing.
    
    Args:
        text: Document text
        metadata: Document metadata
        neo4j_db: Neo4j database instance
        vector_db: Vector database instance
        chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters
        batch_size: Number of documents to add in each batch
        
    Returns:
        Dictionary with document ID and extracted entities
    """
    # 1. Create a unique ID for the document
    doc_id = f"doc-{uuid.uuid4()}"
    metadata["doc_id"] = doc_id
    
    # 2. Extract entities from the document
    entities = extract_entities_from_text(text)
    
    # 3. Extract relationships between entities
    relationships = extract_relationships(entities, text)
    
    # 4. Add entities to Neo4j
    for entity in entities:
        query = """
        MERGE (c:Concept {id: $id})
        ON CREATE SET c.name = $name, c.type = $type, c.abbreviation = $abbreviation
        """
        neo4j_db.run_query(query, entity)
    
    print(f"Added {len(entities)} entities to Neo4j")
    
    # 5. Add relationships to Neo4j
    for source_id, target_id, strength in relationships:
        query = """
        MATCH (source:Concept {id: $source_id})
        MATCH (target:Concept {id: $target_id})
        MERGE (source)-[r:RELATED_TO]->(target)
        ON CREATE SET r.strength = $strength
        """
        neo4j_db.run_query(query, {
            "source_id": source_id,
            "target_id": target_id,
            "strength": strength
        })
    
    print(f"Added {len(relationships)} relationships to Neo4j")
    
    # 6. Process document into optimized chunks with metadata
    chunks, chunk_metadatas, chunk_ids = process_document_with_metadata(
        text=text,
        metadata=metadata,
        chunk_size=chunk_size,
        overlap=overlap
    )
    
    # 7. Add document chunks to vector database in batches
    vector_db.process_document_batch(
        documents=chunks,
        metadatas=chunk_metadatas,
        ids=chunk_ids,
        batch_size=batch_size
    )
    
    print(f"Added {len(chunks)} chunks to vector database")
    
    return {
        "doc_id": doc_id,
        "entities": entities,
        "relationships": relationships,
        "chunks": len(chunks)
    }

def main():
    """
    Main function to demonstrate adding a document to the GraphRAG system.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Add a document to the GraphRAG system")
    parser.add_argument("--file", "-f", type=str, help="Path to document file")
    parser.add_argument("--title", "-t", type=str, help="Document title")
    parser.add_argument("--author", "-a", type=str, help="Document author")
    parser.add_argument("--category", "-c", type=str, help="Document category")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help="Maximum chunk size in characters")
    parser.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP, help="Overlap between chunks in characters")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Number of documents per batch")
    args = parser.parse_args()
    
    # Initialize databases
    neo4j_db = Neo4jDatabase()
    vector_db = VectorDatabase()
    
    # Verify connections
    if not neo4j_db.verify_connection():
        print("❌ Neo4j connection failed!")
        return
    
    if not vector_db.verify_connection():
        print("❌ Vector database connection failed!")
        return
    
    print("✅ Database connections verified!")
    
    # Read document from file or use example text
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            document_text = f.read()
        
        # Use filename as title if not provided
        title = args.title or os.path.splitext(os.path.basename(args.file))[0]
    else:
        # Example document
        document_text = """
        GraphRAG: Enhancing LLMs with Knowledge Graphs
        
        Retrieval-Augmented Generation (RAG) has become a powerful technique for enhancing Large Language Models (LLMs) by providing them with external knowledge. Traditional RAG systems rely on vector embeddings to retrieve relevant information, but this approach has limitations when dealing with complex relationships between concepts.
        
        GraphRAG addresses these limitations by incorporating knowledge graphs into the retrieval process. By explicitly modeling the relationships between entities and concepts, GraphRAG enables more sophisticated retrieval that considers the semantic structure of the information.
        
        The key components of a GraphRAG system include:
        
        1. Vector Database: Stores text embeddings for efficient similarity search
        2. Knowledge Graph: Represents entities and their relationships
        3. Hybrid Retrieval: Combines vector similarity with graph traversal
        4. Large Language Model: Generates responses based on retrieved context
        
        By incorporating knowledge graphs, GraphRAG explicitly represents the relationships between entities and concepts, enabling more sophisticated retrieval that considers the semantic structure of the information. This approach is particularly valuable for complex domains where understanding the relationships between concepts is crucial.
        """
        
        title = args.title or "GraphRAG: Enhancing LLMs with Knowledge Graphs"
    
    # Document metadata
    document_metadata = {
        "title": title,
        "author": args.author or "Example Author",
        "category": args.category or "AI",
        "source": "Optimized Example"
    }
    
    # Add document to GraphRAG system
    print("\nAdding document to GraphRAG system...")
    result = add_optimized_document(
        text=document_text,
        metadata=document_metadata,
        neo4j_db=neo4j_db,
        vector_db=vector_db,
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        batch_size=args.batch_size
    )
    
    # Print summary
    print("\nDocument added successfully!")
    print(f"Document ID: {result['doc_id']}")
    print(f"Entities: {len(result['entities'])}")
    print(f"Relationships: {len(result['relationships'])}")
    print(f"Chunks: {result['chunks']}")

if __name__ == "__main__":
    main()
