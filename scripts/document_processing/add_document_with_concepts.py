"""Modified version of add_document.py that supports explicit concepts in metadata."""

import os
import sys
import uuid
from typing import Any

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase


def extract_entities_from_metadata(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract entities from metadata 'concepts' field.

    Args:
        metadata: Document metadata with optional 'concepts' field

    Returns:
        List of extracted entities

    """
    entities = []

    # Check if concepts are provided in metadata
    if "concepts" in metadata:
        # Split concepts by comma
        concept_names = [c.strip() for c in metadata["concepts"].split(",")]

        for concept_name in concept_names:
            if concept_name:  # Skip empty strings
                # Create a simple ID from the concept name
                concept_id = f"concept-{concept_name.lower().replace(' ', '-')}"

                entities.append(
                    {"id": concept_id, "name": concept_name, "type": "Concept"}
                )

    return entities


def extract_entities_from_text(text: str) -> list[dict[str, Any]]:
    """Simple entity extraction function.
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
        "gradient descent": "GD",
        "rag": "RAG",
        "retrieval-augmented generation": "RAG",
        "graphrag": "GRAG",
        "knowledge graph": "KG",
        "vector database": "VDB",
        "embedding": "EMB",
        "hybrid search": "HS",
        "deduplication": "DD",
        "large language model": "LLM",
        "llm": "LLM",
        "neo4j": "NEO",
        "chromadb": "CHROMA",
    }

    # Check for each keyword in the text
    for keyword, abbr in keywords.items():
        if keyword.lower() in text.lower():
            entity_id = f"concept-{abbr.lower()}"
            entities.append(
                {
                    "id": entity_id,
                    "name": keyword.title(),
                    "type": "Concept",
                    "abbreviation": abbr,
                }
            )

    return entities


def extract_relationships(
    entities: list[dict[str, Any]], text: str
) -> list[tuple[str, str, float]]:
    """Simple relationship extraction function.
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
            for j in range(i + 1, len(entities)):
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
    metadata: dict[str, Any],
    neo4j_db: Neo4jDatabase,
    vector_db: VectorDatabase,
) -> dict[str, Any]:
    """Add a document to the GraphRAG system.

    Args:
        text: Document text
        metadata: Document metadata
        neo4j_db: Neo4j database instance
        vector_db: Vector database instance

    Returns:
        Dictionary with document ID and extracted entities

    """
    # 1. Extract entities from metadata and text
    metadata_entities = extract_entities_from_metadata(metadata)
    text_entities = extract_entities_from_text(text)

    # Combine entities, avoiding duplicates by ID
    entity_ids = set()
    entities = []

    for entity in metadata_entities + text_entities:
        if entity["id"] not in entity_ids:
            entity_ids.add(entity["id"])
            entities.append(entity)

    # 2. Extract relationships between entities
    relationships = extract_relationships(entities, text)

    # 3. Create a unique ID for the document
    doc_id = f"doc-{uuid.uuid4()}"

    # 4. Add entities to Neo4j
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
            neo4j_db.run_query(
                query,
                {
                    "id": entity["id"],
                    "name": entity["name"],
                    "abbreviation": entity.get("abbreviation", ""),
                },
            )
            print(f"Created entity: {entity['name']}")
        else:
            print(f"Entity already exists: {entity['name']}")

    # 5. Add relationships to Neo4j
    for source_id, target_id, strength in relationships:
        # Check if relationship already exists
        query = """
        MATCH (a:Concept {id: $source_id})-[r:RELATED_TO]->(b:Concept {id: $target_id})
        RETURN r
        """
        results = neo4j_db.run_query(
            query, {"source_id": source_id, "target_id": target_id}
        )

        if not results:
            # Create the relationship
            query = """
            MATCH (a:Concept {id: $source_id})
            MATCH (b:Concept {id: $target_id})
            CREATE (a)-[r:RELATED_TO {strength: $strength}]->(b)
            RETURN r
            """
            neo4j_db.run_query(
                query,
                {"source_id": source_id, "target_id": target_id, "strength": strength},
            )
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
    vector_db.add_documents(documents=[text], metadatas=[doc_metadata], ids=[doc_id])
    print(f"Added document to vector database with ID: {doc_id}")

    return {"document_id": doc_id, "entities": entities, "relationships": relationships}


if __name__ == "__main__":
    print("This script is meant to be imported, not run directly.")
    print("To add a document, import the add_document_to_graphrag function.")
