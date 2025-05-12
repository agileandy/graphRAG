#!/usr/bin/env python3
"""
Script to extract concepts from documents in the vector database.

This script:
1. Retrieves documents from the vector database
2. Extracts concepts from each document
3. Adds the concepts to the graph database
4. Creates relationships between concepts and documents
"""
import sys
import os
import logging
import argparse
from typing import Dict, Any
from tqdm import tqdm

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.vector_db import VectorDatabase
from src.database.graph_db import GraphDatabase
from src.processing.concept_extractor import ConceptExtractor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_concepts_from_documents(
    collection_name: str = "documents",
    limit: int = 100,
    min_concept_length: int = 2,
    max_concept_length: int = 5,
    min_concept_weight: float = 0.5,
    use_nlp: bool = True,
    use_llm: bool = False,
    domain: str = "tech"
) -> Dict[str, Any]:
    """
    Extract concepts from documents in the vector database.
    
    Args:
        collection_name: Name of the collection to extract concepts from
        limit: Maximum number of documents to process
        min_concept_length: Minimum concept length in words
        max_concept_length: Maximum concept length in words
        min_concept_weight: Minimum concept weight to include
        use_nlp: Whether to use NLP-based extraction
        use_llm: Whether to use LLM-based extraction
        domain: Domain for stopwords ("general", "tech", "academic")
        
    Returns:
        Dictionary with statistics about the extraction process
    """
    # Initialize databases
    vector_db = VectorDatabase()
    graph_db = GraphDatabase()
    
    # Initialize concept extractor
    extractor = ConceptExtractor(
        use_nlp=use_nlp,
        use_llm=use_llm,
        domain=domain,
        min_concept_length=min_concept_length,
        max_concept_length=max_concept_length
    )
    
    # Connect to databases
    vector_db.connect()
    graph_db.connect()
    
    # Get documents from vector database
    logger.info(f"Retrieving documents from collection '{collection_name}'...")
    documents = vector_db.get_documents(collection_name, limit=limit)
    
    if not documents:
        logger.warning(f"No documents found in collection '{collection_name}'")
        return {"documents_processed": 0, "concepts_extracted": 0, "concepts_added": 0}
    
    logger.info(f"Retrieved {len(documents)} documents")
    
    # Statistics
    stats = {
        "documents_processed": 0,
        "concepts_extracted": 0,
        "concepts_added": 0,
        "concepts_per_document": {},
        "concept_frequencies": {}
    }
    
    # Process each document
    for doc in tqdm(documents, desc="Processing documents"):
        doc_id = doc.get("id")
        doc.get("metadata", {}).get("title", "Unknown")
        doc_text = doc.get("text", "")
        
        if not doc_text:
            logger.warning(f"Document {doc_id} has no text, skipping")
            continue
        
        # Extract concepts from document
        concepts = extractor.extract_concepts(doc_text)
        
        # Weight concepts
        weighted_concepts = extractor.weight_concepts(concepts, doc_text)
        
        # Filter concepts by weight
        filtered_concepts = [c for c in weighted_concepts if c.get("weight", 0) >= min_concept_weight]
        
        # Add concepts to graph database
        for concept in filtered_concepts:
            concept_name = concept["concept"]
            concept_weight = concept.get("weight", 1.0)
            
            # Update statistics
            stats["concepts_extracted"] += 1
            stats["concept_frequencies"][concept_name] = stats["concept_frequencies"].get(concept_name, 0) + 1
            
            # Add concept to graph database
            concept_node = graph_db.add_concept(concept_name)
            
            if concept_node:
                stats["concepts_added"] += 1
                
                # Add relationship between concept and document
                graph_db.add_document_concept_relationship(doc_id, concept_node["id"], weight=concept_weight)
        
        # Update statistics
        stats["documents_processed"] += 1
        stats["concepts_per_document"][doc_id] = len(filtered_concepts)
    
    # Calculate average concepts per document
    if stats["documents_processed"] > 0:
        stats["avg_concepts_per_document"] = sum(stats["concepts_per_document"].values()) / stats["documents_processed"]
    else:
        stats["avg_concepts_per_document"] = 0
    
    # Get top concepts
    stats["top_concepts"] = sorted(
        stats["concept_frequencies"].items(),
        key=lambda x: x[1],
        reverse=True
    )[:20]
    
    return stats

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Extract concepts from documents in the vector database")
    parser.add_argument("--collection", type=str, default="documents", help="Collection name")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of documents to process")
    parser.add_argument("--min-concept-length", type=int, default=2, help="Minimum concept length in words")
    parser.add_argument("--max-concept-length", type=int, default=5, help="Maximum concept length in words")
    parser.add_argument("--min-concept-weight", type=float, default=0.5, help="Minimum concept weight to include")
    parser.add_argument("--use-nlp", action="store_true", help="Use NLP-based extraction")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM-based extraction")
    parser.add_argument("--domain", type=str, default="tech", choices=["general", "tech", "academic"], help="Domain for stopwords")
    
    args = parser.parse_args()
    
    print(f"Extracting concepts from documents in collection '{args.collection}'...")
    print(f"Using NLP: {args.use_nlp}, Using LLM: {args.use_llm}, Domain: {args.domain}")
    print(f"Min concept length: {args.min_concept_length}, Max concept length: {args.max_concept_length}")
    print(f"Min concept weight: {args.min_concept_weight}")
    print(f"Processing up to {args.limit} documents")
    
    # Extract concepts
    stats = extract_concepts_from_documents(
        collection_name=args.collection,
        limit=args.limit,
        min_concept_length=args.min_concept_length,
        max_concept_length=args.max_concept_length,
        min_concept_weight=args.min_concept_weight,
        use_nlp=args.use_nlp,
        use_llm=args.use_llm,
        domain=args.domain
    )
    
    # Print statistics
    print("\nExtraction Statistics:")
    print(f"Documents processed: {stats['documents_processed']}")
    print(f"Concepts extracted: {stats['concepts_extracted']}")
    print(f"Concepts added to graph: {stats['concepts_added']}")
    print(f"Average concepts per document: {stats.get('avg_concepts_per_document', 0):.2f}")
    
    print("\nTop 20 Concepts:")
    for concept, frequency in stats.get("top_concepts", []):
        print(f"  - {concept}: {frequency}")

if __name__ == "__main__":
    main()
