"""
Script to add a document to the GraphRAG system.

This script demonstrates how to:
1. Add a document to the vector database
2. Extract entities and relationships
3. Create nodes and relationships in Neo4j
4. Perform a hybrid search
"""
import sys
import os
import uuid
from typing import List, Dict, Any, Tuple

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase
from src.database.db_linkage import DatabaseLinkage

def extract_entities(text: str) -> List[Dict[str, Any]]:
    """
    Simple entity extraction function.
    In a real system, you would use NLP techniques or LLMs for this.
    
    Args:
        text: Document text
        
    Returns:
        List of extracted entities
    """
    # This is a very simple implementation for demonstration
    # In a real system, you would use NLP or LLMs for entity extraction
    entities = []
    
    # Define some keywords to look for
    keywords = {
        "machine learning": "ML",
        "neural network": "NN",
        "deep learning": "DL",
        "artificial intelligence": "AI",
        "natural language processing": "NLP",
        "computer vision": "CV",
        "reinforcement learning": "RL",
        "supervised learning": "SL",
        "unsupervised learning": "UL",
        "transformer": "TR",
        "attention mechanism": "AM",
        "convolutional neural network": "CNN",
        "recurrent neural network": "RNN",
        "long short-term memory": "LSTM",
        "gated recurrent unit": "GRU",
        "generative adversarial network": "GAN",
        "transfer learning": "TL",
        "fine-tuning": "FT",
        "backpropagation": "BP",
        "gradient descent": "GD"
    }
    
    # Check for each keyword in the text
    for keyword, abbr in keywords.items():
        if keyword.lower() in text.lower():
            entity_id = f"concept-{abbr.lower()}"
            entities.append({
                "id": entity_id,
                "name": keyword.title(),
                "type": "Concept",
                "abbreviation": abbr
            })
    
    return entities

def extract_relationships(entities: List[Dict[str, Any]], text: str) -> List[Tuple[str, str, float]]:
    """
    Simple relationship extraction function.
    In a real system, you would use NLP techniques or LLMs for this.
    
    Args:
        entities: List of extracted entities
        text: Document text
        
    Returns:
        List of relationships as (source_id, target_id, strength)
    """
    # This is a very simple implementation for demonstration
    # In a real system, you would use NLP or LLMs for relationship extraction
    relationships = []
    
    # If we have at least 2 entities, create relationships between them
    if len(entities) >= 2:
        # Create relationships between all pairs of entities
        for i in range(len(entities)):
            for j in range(i+1, len(entities)):
                source_id = entities[i]["id"]
                target_id = entities[j]["id"]
                
                # Calculate a simple strength based on proximity in the text
                # In a real system, you would use more sophisticated methods
                strength = 0.5  # Default strength
                
                # Add the relationship
                relationships.append((source_id, target_id, strength))
    
    return relationships

def add_document_to_graphrag(
    text: str,
    metadata: Dict[str, Any],
    neo4j_db: Neo4jDatabase,
    vector_db: VectorDatabase
) -> Dict[str, Any]:
    """
    Add a document to the GraphRAG system.
    
    Args:
        text: Document text
        metadata: Document metadata
        neo4j_db: Neo4j database instance
        vector_db: Vector database instance
        
    Returns:
        Dictionary with document ID and extracted entities
    """
    # 1. Extract entities from the document
    entities = extract_entities(text)
    
    # 2. Extract relationships between entities
    relationships = extract_relationships(entities, text)
    
    # 3. Create a unique ID for the document
    doc_id = f"doc-{uuid.uuid4()}"
    
    # 4. Add entities to Neo4j
    for entity in entities:
        # Check if entity already exists
        query = f"""
        MATCH (c:Concept {{id: $id}})
        RETURN c
        """
        results = neo4j_db.run_query(query, {"id": entity["id"]})
        
        if not results:
            # Create the entity
            query = f"""
            CREATE (c:Concept {{
                id: $id,
                name: $name,
                abbreviation: $abbreviation
            }})
            RETURN c
            """
            neo4j_db.run_query(query, {
                "id": entity["id"],
                "name": entity["name"],
                "abbreviation": entity.get("abbreviation", "")
            })
            print(f"Created entity: {entity['name']}")
        else:
            print(f"Entity already exists: {entity['name']}")
    
    # 5. Add relationships to Neo4j
    for source_id, target_id, strength in relationships:
        # Check if relationship already exists
        query = f"""
        MATCH (a:Concept {{id: $source_id}})-[r:RELATED_TO]->(b:Concept {{id: $target_id}})
        RETURN r
        """
        results = neo4j_db.run_query(query, {"source_id": source_id, "target_id": target_id})
        
        if not results:
            # Create the relationship
            query = f"""
            MATCH (a:Concept {{id: $source_id}})
            MATCH (b:Concept {{id: $target_id}})
            CREATE (a)-[r:RELATED_TO {{strength: $strength}}]->(b)
            RETURN r
            """
            neo4j_db.run_query(query, {
                "source_id": source_id,
                "target_id": target_id,
                "strength": strength
            })
            print(f"Created relationship: {source_id} -> {target_id}")
        else:
            print(f"Relationship already exists: {source_id} -> {target_id}")
    
    # 6. Add document to vector database
    # Update metadata with entity IDs
    doc_metadata = metadata.copy()
    doc_metadata["doc_id"] = doc_id
    
    # Add concept IDs to metadata
    if entities:
        # ChromaDB doesn't support lists in metadata, so we'll join them into a string
        doc_metadata["concept_ids"] = ",".join([entity["id"] for entity in entities])
        doc_metadata["concept_id"] = entities[0]["id"]  # Primary concept
    
    # Add document to vector database
    vector_db.add_documents(
        documents=[text],
        metadatas=[doc_metadata],
        ids=[doc_id]
    )
    print(f"Added document to vector database with ID: {doc_id}")
    
    return {
        "doc_id": doc_id,
        "entities": entities,
        "relationships": relationships
    }

def main():
    """
    Main function to demonstrate adding a document to the GraphRAG system.
    """
    print("Initializing databases...")
    
    # Initialize databases
    neo4j_db = Neo4jDatabase()
    vector_db = VectorDatabase()
    db_linkage = DatabaseLinkage(neo4j_db, vector_db)
    
    # Verify connections
    if not neo4j_db.verify_connection():
        print("❌ Neo4j connection failed!")
        return
    
    if not vector_db.verify_connection():
        print("❌ Vector database connection failed!")
        return
    
    print("✅ Database connections verified!")
    
    # Example document
    document_text = """
    Neural Networks and Deep Learning: A Comprehensive Guide
    
    Neural networks are a set of algorithms, modeled loosely after the human brain, 
    that are designed to recognize patterns. They interpret sensory data through a 
    kind of machine perception, labeling or clustering raw input. The patterns they 
    recognize are numerical, contained in vectors, into which all real-world data, 
    be it images, sound, text or time series, must be translated.
    
    Deep learning is a subset of machine learning where artificial neural networks, 
    algorithms inspired by the human brain, learn from large amounts of data. Deep 
    learning is behind many recent advances in AI, including computer vision, natural 
    language processing, and speech recognition.
    
    Convolutional Neural Networks (CNNs) are particularly effective for image processing 
    tasks. They use convolutional layers to automatically and adaptively learn spatial 
    hierarchies of features from input images.
    
    Recurrent Neural Networks (RNNs) are designed for sequential data. Long Short-Term 
    Memory (LSTM) networks are a type of RNN capable of learning long-term dependencies, 
    making them ideal for tasks like language modeling and speech recognition.
    
    Transformers have revolutionized natural language processing with their attention 
    mechanism, which allows the model to focus on different parts of the input sequence 
    when producing the output.
    
    Training neural networks typically involves using gradient descent to minimize a 
    loss function. Backpropagation is used to calculate the gradient of the loss function 
    with respect to the weights of the network.
    
    Transfer learning is a technique where a pre-trained model is fine-tuned on a specific 
    task, allowing for effective learning with less data.
    """
    
    # Document metadata
    document_metadata = {
        "title": "Neural Networks and Deep Learning: A Comprehensive Guide",
        "author": "AI Researcher",
        "category": "AI",
        "source": "Example"
    }
    
    # Add document to GraphRAG system
    print("\nAdding document to GraphRAG system...")
    result = add_document_to_graphrag(
        text=document_text,
        metadata=document_metadata,
        neo4j_db=neo4j_db,
        vector_db=vector_db
    )
    
    # Perform a hybrid search
    print("\nPerforming hybrid search...")
    search_results = db_linkage.hybrid_search(
        query_text="How do transformers work in deep learning?",
        n_vector_results=2,
        max_graph_hops=2
    )
    
    # Display search results
    print("\nVector results:")
    for i, doc in enumerate(search_results["vector_results"]["documents"]):
        print(f"  {i+1}. {doc[:100]}...")
    
    print("\nGraph results:")
    for i, result in enumerate(search_results["graph_results"]):
        print(f"  {i+1}. {result['name']} (Score: {result['relevance_score']})")
    
    # Close Neo4j connection
    neo4j_db.close()
    
    print("\n✅ Document added and search performed successfully!")

if __name__ == "__main__":
    main()