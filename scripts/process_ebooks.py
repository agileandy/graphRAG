"""
Script to process ebooks and build a graph.

This script:
1. Extracts text from PDF files
2. Chunks the text into manageable segments
3. Extracts entities and relationships
4. Builds a knowledge graph in Neo4j
5. Stores text chunks in ChromaDB
"""
import sys
import os
import glob
import re
import uuid
import argparse
import PyPDF2
from typing import List, Dict, Any, Tuple
import time

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase

# Define a list of prompt engineering concepts for entity extraction
PROMPT_ENGINEERING_CONCEPTS = {
    "prompt engineering": "PE",
    "chain of thought": "COT",
    "few-shot learning": "FSL",
    "zero-shot learning": "ZSL",
    "in-context learning": "ICL",
    "retrieval augmented generation": "RAG",
    "prompt template": "PT",
    "system prompt": "SP",
    "user prompt": "UP",
    "assistant prompt": "AP",
    "prompt chaining": "PC",
    "prompt tuning": "PTU",
    "prompt optimization": "PO",
    "prompt injection": "PI",
    "prompt leaking": "PL",
    "prompt hacking": "PH",
    "jailbreaking": "JB",
    "role prompting": "RP",
    "persona prompting": "PP",
    "instruction prompting": "IP",
    "task-specific prompting": "TSP",
    "self-consistency": "SC",
    "tree of thought": "TOT",
    "reasoning": "RE",
    "step-by-step": "SBS",
    "fine-tuning": "FT",
    "parameter efficient fine-tuning": "PEFT",
    "low-rank adaptation": "LORA",
    "knowledge graph": "KG",
    "vector database": "VDB",
    "embedding": "EMB",
    "token": "TOK",
    "tokenization": "TKZ",
    "temperature": "TEMP",
    "top-p sampling": "TPS",
    "top-k sampling": "TKS",
    "beam search": "BS",
    "greedy decoding": "GD",
    "hallucination": "HAL",
    "context window": "CW",
    "attention mechanism": "AM",
    "transformer": "TR",
    "large language model": "LLM",
    "generative ai": "GAI",
    "natural language processing": "NLP",
    "natural language understanding": "NLU",
    "natural language generation": "NLG",
    "semantic search": "SS",
    "similarity search": "SIS",
    "cosine similarity": "CS",
    "vector embedding": "VE",
    "text embedding": "TE",
    "document embedding": "DE",
    "sentence embedding": "SE",
    "word embedding": "WE",
    "contextual embedding": "CE",
    "knowledge distillation": "KD",
    "knowledge extraction": "KE",
    "knowledge representation": "KR",
    "knowledge base": "KB",
    "ontology": "ONT",
    "taxonomy": "TAX",
    "semantic network": "SN",
    "semantic web": "SW",
    "semantic triple": "ST",
    "entity extraction": "EE",
    "named entity recognition": "NER",
    "relation extraction": "RE",
    "information extraction": "IE",
    "information retrieval": "IR",
    "question answering": "QA",
    "chatbot": "CB",
    "conversational ai": "CAI",
    "dialogue system": "DS",
    "dialogue management": "DM",
    "dialogue state tracking": "DST",
    "dialogue policy": "DP",
    "dialogue generation": "DG",
    "dialogue understanding": "DU",
    "dialogue context": "DC",
    "dialogue history": "DH",
    "dialogue turn": "DT",
    "dialogue act": "DA",
    "dialogue intent": "DI",
    "dialogue slot": "DS",
    "dialogue entity": "DE",
    "dialogue relation": "DR",
    "dialogue knowledge": "DK",
    "dialogue reasoning": "DR",
    "dialogue planning": "DP",
    "dialogue execution": "DE",
    "dialogue evaluation": "DE",
    "dialogue feedback": "DF",
    "dialogue optimization": "DO",
    "dialogue personalization": "DP",
    "dialogue adaptation": "DA",
    "dialogue learning": "DL",
    "dialogue memory": "DM",
    "dialogue attention": "DA",
    "dialogue focus": "DF",
    "dialogue topic": "DT",
    "dialogue domain": "DD",
    "dialogue task": "DT",
    "dialogue goal": "DG",
    "dialogue strategy": "DS",
}

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text
    """
    print(f"Extracting text from {os.path.basename(pdf_path)}...")
    
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            num_pages = len(reader.pages)
            
            # Extract text from each page
            for page_num in range(num_pages):
                page = reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
                    
                # Print progress for large PDFs
                if num_pages > 50 and page_num % 10 == 0:
                    print(f"  Processed {page_num}/{num_pages} pages...")
            
            print(f"  Extracted {num_pages} pages")
            return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Text to chunk
        chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters
        
    Returns:
        List of text chunks
    """
    chunks = []
    
    # Clean text: remove excessive whitespace and normalize line breaks
    text = re.sub(r'\s+', ' ', text)
    
    # Split text into sentences (simple approach)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    current_chunk = ""
    for sentence in sentences:
        # If adding this sentence would exceed chunk size, save current chunk and start a new one
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap from the end of the previous chunk
            if len(current_chunk) > overlap:
                # Find the last complete sentence within the overlap
                overlap_text = current_chunk[-overlap:]
                last_sentence_break = max(overlap_text.rfind('. '), overlap_text.rfind('! '), overlap_text.rfind('? '))
                
                if last_sentence_break != -1:
                    # Start with the last complete sentence in the overlap
                    current_chunk = current_chunk[-(overlap - last_sentence_break):] + " "
                else:
                    # If no sentence break found, just use the overlap
                    current_chunk = current_chunk[-overlap:] + " "
            else:
                current_chunk = ""
        
        current_chunk += sentence + " "
    
    # Add the last chunk if it's not empty
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    print(f"  Created {len(chunks)} chunks from text")
    return chunks

def extract_entities(text: str) -> List[Dict[str, Any]]:
    """
    Extract entities from text.
    
    Args:
        text: Text to extract entities from
        
    Returns:
        List of extracted entities
    """
    entities = []
    text_lower = text.lower()
    
    # Check for each concept in the text
    for concept, abbr in PROMPT_ENGINEERING_CONCEPTS.items():
        if concept.lower() in text_lower:
            entity_id = f"concept-{abbr.lower()}"
            
            # Check if entity already exists in the list
            if not any(e["id"] == entity_id for e in entities):
                entities.append({
                    "id": entity_id,
                    "name": concept.title(),
                    "type": "Concept",
                    "abbreviation": abbr
                })
    
    return entities

def extract_relationships(entities: List[Dict[str, Any]], text: str) -> List[Tuple[str, str, float]]:
    """
    Extract relationships between entities.
    
    Args:
        entities: List of extracted entities
        text: Text to extract relationships from
        
    Returns:
        List of relationships as (source_id, target_id, strength)
    """
    relationships = []
    
    # If we have at least 2 entities, create relationships between them
    if len(entities) >= 2:
        # Create relationships between all pairs of entities
        for i in range(len(entities)):
            for j in range(i+1, len(entities)):
                source_id = entities[i]["id"]
                target_id = entities[j]["id"]
                
                # Calculate a simple strength based on co-occurrence
                # In a real system, you would use more sophisticated methods
                strength = 0.5  # Default strength
                
                # Add the relationship
                relationships.append((source_id, target_id, strength))
    
    return relationships

def process_pdf_file(
    pdf_path: str,
    neo4j_db: Neo4jDatabase,
    vector_db: VectorDatabase,
    chunk_size: int = 1000,
    overlap: int = 200
) -> Dict[str, Any]:
    """
    Process a PDF file and add it to the GraphRAG system.
    
    Args:
        pdf_path: Path to the PDF file
        neo4j_db: Neo4j database instance
        vector_db: Vector database instance
        chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters
        
    Returns:
        Processing results
    """
    # Extract book metadata from filename
    filename = os.path.basename(pdf_path)
    book_title = os.path.splitext(filename)[0]
    
    # Create a unique ID for the book
    book_id = f"book-{uuid.uuid4().hex[:8]}"
    
    print(f"Processing book: {book_title} (ID: {book_id})")
    
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print(f"❌ Failed to extract text from {filename}")
        return {"success": False, "book_id": book_id, "title": book_title}
    
    # Create book node in Neo4j
    query = """
    CREATE (b:Book {
        id: $id,
        title: $title,
        filename: $filename,
        file_path: $file_path
    })
    RETURN b
    """
    neo4j_db.run_query(query, {
        "id": book_id,
        "title": book_title,
        "filename": filename,
        "file_path": pdf_path
    })
    print(f"  Created book node in Neo4j: {book_title}")
    
    # Chunk the text
    chunks = chunk_text(text, chunk_size, overlap)
    
    # Process each chunk
    all_entities = []
    all_relationships = []
    
    for i, chunk in enumerate(chunks):
        chunk_id = f"{book_id}-chunk-{i}"
        
        # Extract entities from chunk
        entities = extract_entities(chunk)
        
        # Extract relationships between entities
        relationships = extract_relationships(entities, chunk)
        
        # Add entities to Neo4j
        for entity in entities:
            # Check if entity already exists
            query = """
            MATCH (c:Concept {id: $id})
            RETURN c
            """
            results = neo4j_db.run_query(query, {"id": entity["id"]})
            
            if not results:
                # Create the entity
                query = """
                CREATE (c:Concept {
                    id: $id,
                    name: $name,
                    abbreviation: $abbreviation
                })
                RETURN c
                """
                neo4j_db.run_query(query, {
                    "id": entity["id"],
                    "name": entity["name"],
                    "abbreviation": entity.get("abbreviation", "")
                })
            
            # Create relationship between book and concept
            query = """
            MATCH (b:Book {id: $book_id})
            MATCH (c:Concept {id: $concept_id})
            MERGE (b)-[r:MENTIONS]->(c)
            RETURN r
            """
            neo4j_db.run_query(query, {
                "book_id": book_id,
                "concept_id": entity["id"]
            })
        
        # Add relationships to Neo4j
        for source_id, target_id, strength in relationships:
            # Check if relationship already exists
            query = """
            MATCH (a:Concept {id: $source_id})-[r:RELATED_TO]->(b:Concept {id: $target_id})
            RETURN r
            """
            results = neo4j_db.run_query(query, {"source_id": source_id, "target_id": target_id})
            
            if not results:
                # Create the relationship
                query = """
                MATCH (a:Concept {id: $source_id})
                MATCH (b:Concept {id: $target_id})
                CREATE (a)-[r:RELATED_TO {strength: $strength}]->(b)
                RETURN r
                """
                neo4j_db.run_query(query, {
                    "source_id": source_id,
                    "target_id": target_id,
                    "strength": strength
                })
        
        # Add chunk to vector database
        # Prepare metadata
        chunk_metadata = {
            "book_id": book_id,
            "book_title": book_title,
            "chunk_index": i,
            "filename": filename,
            "file_path": pdf_path
        }
        
        # Add concept IDs to metadata
        if entities:
            # ChromaDB doesn't support lists in metadata, so we'll join them into a string
            chunk_metadata["concept_ids"] = ",".join([entity["id"] for entity in entities])
            chunk_metadata["concept_id"] = entities[0]["id"]  # Primary concept
        
        # Add chunk to vector database
        vector_db.add_documents(
            documents=[chunk],
            metadatas=[chunk_metadata],
            ids=[chunk_id]
        )
        
        # Collect all entities and relationships
        all_entities.extend(entities)
        all_relationships.extend(relationships)
        
        # Print progress for large books
        if len(chunks) > 20 and i % 10 == 0:
            print(f"  Processed {i}/{len(chunks)} chunks...")
    
    print(f"  Added {len(chunks)} chunks to vector database")
    print(f"  Extracted {len(all_entities)} unique entities")
    print(f"  Created {len(all_relationships)} relationships")
    
    return {
        "success": True,
        "book_id": book_id,
        "title": book_title,
        "chunks": len(chunks),
        "entities": len(all_entities),
        "relationships": len(all_relationships)
    }

def process_directory(
    directory_path: str,
    neo4j_db: Neo4jDatabase,
    vector_db: VectorDatabase,
    chunk_size: int = 1000,
    overlap: int = 200
) -> List[Dict[str, Any]]:
    """
    Process all PDF files in a directory.
    
    Args:
        directory_path: Path to directory containing PDF files
        neo4j_db: Neo4j database instance
        vector_db: Vector database instance
        chunk_size: Maximum chunk size in characters
        overlap: Overlap between chunks in characters
        
    Returns:
        List of processing results
    """
    # Find all PDF files in the directory
    pdf_files = glob.glob(os.path.join(directory_path, "*.pdf"))
    
    print(f"Found {len(pdf_files)} PDF files in {directory_path}")
    
    results = []
    
    # Process each PDF file
    for i, pdf_path in enumerate(pdf_files):
        print(f"\nProcessing file {i+1}/{len(pdf_files)}: {os.path.basename(pdf_path)}")
        
        # Process the PDF file
        result = process_pdf_file(
            pdf_path=pdf_path,
            neo4j_db=neo4j_db,
            vector_db=vector_db,
            chunk_size=chunk_size,
            overlap=overlap
        )
        
        results.append(result)
    
    return results

def main():
    """
    Main function to process ebooks and build a graph.
    """
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Process ebooks and build a graph")
    parser.add_argument("--dir", "-d", type=str, required=True, help="Directory containing ebooks to process")
    parser.add_argument("--chunk-size", "-c", type=int, default=1000, help="Maximum chunk size in characters")
    parser.add_argument("--overlap", "-o", type=int, default=200, help="Overlap between chunks in characters")
    parser.add_argument("--clean", action="store_true", help="Clean the database before processing")
    args = parser.parse_args()
    
    # Check if directory exists
    if not os.path.isdir(args.dir):
        print(f"Directory not found: {args.dir}")
        return
    
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
    
    # Clean the database if requested
    if args.clean:
        print("\nCleaning the database...")
        
        # Clean Neo4j
        neo4j_db.run_query("MATCH (n) DETACH DELETE n")
        print("✅ Cleaned Neo4j database")
        
        # Initialize Neo4j schema
        neo4j_db.create_schema()
        print("✅ Initialized Neo4j schema")
    
    # Record start time
    start_time = time.time()
    
    # Process ebooks
    results = process_directory(
        directory_path=args.dir,
        neo4j_db=neo4j_db,
        vector_db=vector_db,
        chunk_size=args.chunk_size,
        overlap=args.overlap
    )
    
    # Record end time
    end_time = time.time()
    processing_time = end_time - start_time
    
    # Print summary
    print("\n" + "="*50)
    print("Processing Summary")
    print("="*50)
    print(f"Processed {len(results)} books")
    print(f"Total processing time: {processing_time:.2f} seconds")
    
    successful = [r for r in results if r.get("success", False)]
    print(f"Successfully processed: {len(successful)}/{len(results)}")
    
    if successful:
        total_chunks = sum(r.get("chunks", 0) for r in successful)
        total_entities = sum(r.get("entities", 0) for r in successful)
        total_relationships = sum(r.get("relationships", 0) for r in successful)
        
        print(f"Total chunks added: {total_chunks}")
        print(f"Total entities extracted: {total_entities}")
        print(f"Total relationships created: {total_relationships}")
    
    # Get entity count from Neo4j
    query = "MATCH (c:Concept) RETURN count(c) as count"
    result = neo4j_db.run_query_and_return_single(query)
    concept_count = result.get("count", 0)
    
    # Get relationship count from Neo4j
    query = "MATCH ()-[r:RELATED_TO]->() RETURN count(r) as count"
    result = neo4j_db.run_query_and_return_single(query)
    relationship_count = result.get("count", 0)
    
    print(f"Total concepts in Neo4j: {concept_count}")
    print(f"Total relationships in Neo4j: {relationship_count}")
    
    # Get document count from ChromaDB
    doc_count = vector_db.count()
    print(f"Total documents in ChromaDB: {doc_count}")
    
    # Close Neo4j connection
    neo4j_db.close()
    
    print("\n✅ Processing completed!")
    print("\nNext steps:")
    print("1. Query the system interactively with 'python scripts/query_graphrag.py'")
    print("2. Explore the knowledge graph in Neo4j Browser at http://localhost:7474/")

if __name__ == "__main__":
    main()