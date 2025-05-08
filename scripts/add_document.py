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
from typing import List, Dict, Any, Tuple, Optional
import logging

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase
from src.database.db_linkage import DatabaseLinkage
from src.processing.duplicate_detector import DuplicateDetector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_entities_from_metadata(metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract entities from metadata 'concepts' field.

    Args:
        metadata: Document metadata with optional 'concepts' field

    Returns:
        List of extracted entities
    """
    entities = []

    # Check if concepts are provided in metadata
    if 'concepts' in metadata:
        # Split concepts by comma
        concept_names = [c.strip() for c in metadata['concepts'].split(',')]

        for concept_name in concept_names:
            if concept_name:  # Skip empty strings
                # Create a simple ID from the concept name
                concept_id = f"concept-{concept_name.lower().replace(' ', '-')}"

                entities.append({
                    "id": concept_id,
                    "name": concept_name,
                    "type": "Concept"
                })

    return entities

def extract_entities_from_text(text: str, domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Extract entities from text with domain-specific support.

    Args:
        text: Document text
        domain: Optional domain for domain-specific extraction

    Returns:
        List of extracted entities
    """
    # This is a simple implementation that can be extended with more sophisticated NLP
    entities = []

    # Define common keywords across domains
    common_keywords = {
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
        "chromadb": "CHROMA"
    }

    # Domain-specific keywords
    domain_keywords = {
        "AI": {
            "prompt engineering": "PE",
            "chain of thought": "COT",
            "few-shot learning": "FSL",
            "zero-shot learning": "ZSL",
            "multimodal": "MM",
            "text-to-image": "T2I",
            "diffusion model": "DM",
            "stable diffusion": "SD",
            "dall-e": "DALLE",
            "midjourney": "MJ",
            "gpt": "GPT",
            "bert": "BERT",
            "t5": "T5",
            "llama": "LLAMA",
            "claude": "CLAUDE"
        },
        "Programming": {
            "python": "PY",
            "javascript": "JS",
            "typescript": "TS",
            "java": "JAVA",
            "c++": "CPP",
            "rust": "RUST",
            "go": "GO",
            "docker": "DOCKER",
            "kubernetes": "K8S",
            "microservices": "MS",
            "api": "API",
            "rest": "REST",
            "graphql": "GQL",
            "database": "DB",
            "sql": "SQL",
            "nosql": "NOSQL",
            "git": "GIT",
            "ci/cd": "CICD",
            "devops": "DEVOPS"
        },
        "Finance": {
            "stock market": "SM",
            "investment": "INV",
            "portfolio": "PORT",
            "asset allocation": "AA",
            "diversification": "DIV",
            "risk management": "RM",
            "financial planning": "FP",
            "retirement": "RET",
            "tax strategy": "TAX",
            "cryptocurrency": "CRYPTO",
            "blockchain": "BC",
            "bitcoin": "BTC",
            "ethereum": "ETH",
            "defi": "DEFI",
            "nft": "NFT"
        },
        "Photography": {
            "exposure": "EXP",
            "aperture": "AP",
            "shutter speed": "SS",
            "iso": "ISO",
            "composition": "COMP",
            "depth of field": "DOF",
            "bokeh": "BOK",
            "raw": "RAW",
            "jpeg": "JPEG",
            "lightroom": "LR",
            "photoshop": "PS",
            "portrait": "PORT",
            "landscape": "LAND",
            "macro": "MACRO",
            "astrophotography": "ASTRO"
        }
    }

    # Determine which keywords to use based on domain
    keywords_to_use = common_keywords.copy()
    if domain and domain in domain_keywords:
        keywords_to_use.update(domain_keywords[domain])

    # Check for each keyword in the text
    text_lower = text.lower()
    for keyword, abbr in keywords_to_use.items():
        if keyword.lower() in text_lower:
            entity_id = f"concept-{abbr.lower()}"
            entities.append({
                "id": entity_id,
                "name": keyword.title(),
                "type": "Concept",
                "abbreviation": abbr,
                "domain": domain
            })

    return entities

def extract_entities(text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Extract entities from both text and metadata.

    Args:
        text: Document text
        metadata: Document metadata

    Returns:
        List of extracted entities
    """
    # Extract domain from metadata if available
    domain = metadata.get("category") if metadata else None

    # Extract entities from text with domain awareness
    text_entities = extract_entities_from_text(text, domain)

    # Extract entities from metadata if available
    metadata_entities = extract_entities_from_metadata(metadata) if metadata else []

    # Combine entities, avoiding duplicates by normalizing concept names
    normalized_entities = {}

    # Process text entities first
    for entity in text_entities:
        # Normalize the name (lowercase)
        normalized_name = entity["name"].lower()
        normalized_entities[normalized_name] = entity

    # Then process metadata entities, which can override text entities
    for entity in metadata_entities:
        normalized_name = entity["name"].lower()
        normalized_entities[normalized_name] = entity

    # Return the unique entities
    return list(normalized_entities.values())

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
    vector_db: VectorDatabase,
    duplicate_detector: DuplicateDetector
) -> Optional[Dict[str, Any]]:
    """
    Add a document to the GraphRAG system, with duplicate checking.

    Args:
        text: Document text
        metadata: Document metadata
        neo4j_db: Neo4j database instance
        vector_db: Vector database instance
        duplicate_detector: DuplicateDetector instance

    Returns:
        Dictionary with document ID and extracted entities, or None if duplicate
    """
    # Calculate document hash and add to metadata
    doc_hash = duplicate_detector.generate_document_hash(text)
    metadata["hash"] = doc_hash

    # Check for duplicates
    is_dup, existing_doc_id, method = duplicate_detector.is_duplicate(text, metadata)

    if is_dup:
        logger.info(f"Skipping duplicate document: {metadata.get('title', 'Unknown Title')} (ID: {existing_doc_id}, Method: {method})")
        return None # Indicate that the document was a duplicate and not added

    logger.info(f"Adding new document: {metadata.get('title', 'Unknown Title')}")

    # 1. Extract entities from the document and metadata
    entities = extract_entities(text, metadata)

    # 2. Extract relationships between entities
    relationships = extract_relationships(entities, text)

    # 3. Create a unique ID for the document
    doc_id = f"doc-{uuid.uuid4()}"

    # 4. Add entities to Neo4j with improved deduplication
    for entity in entities:
        # First, check if a concept with the same normalized name already exists
        normalized_name = entity["name"].lower()
        query = """
        MATCH (c:Concept)
        WHERE toLower(c.name) = $normalized_name
        RETURN c
        """
        existing_concepts = neo4j_db.run_query(query, {"normalized_name": normalized_name})

        if existing_concepts:
            # Use the existing concept ID instead of creating a new one
            existing_concept = existing_concepts[0]
            logger.info(f"Found existing concept with name '{entity['name']}' (ID: {existing_concept['c']['id']})")

            # Update the entity ID to match the existing concept
            entity["id"] = existing_concept['c']['id']

            # Update the existing concept with any new properties
            query = """
            MATCH (c:Concept {id: $id})
            SET c.name = $name,
                c.abbreviation = $abbreviation
            RETURN c
            """
            neo4j_db.run_query(query, {
                "id": entity["id"],
                "name": entity["name"],
                "abbreviation": entity.get("abbreviation", "")
            })
            logger.info(f"Updated existing concept: {entity['name']}")
        else:
            # Check if entity with this ID already exists
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
                    "abbreviation": entity.get("abbreviation", ""),
                    "domain": entity.get("domain", "")
                })
                logger.info(f"Created new concept: {entity['name']}")
            else:
                # Update the existing entity
                query = """
                MATCH (c:Concept {id: $id})
                SET c.name = $name,
                    c.abbreviation = $abbreviation
                RETURN c
                """
                neo4j_db.run_query(query, {
                    "id": entity["id"],
                    "name": entity["name"],
                    "abbreviation": entity.get("abbreviation", ""),
                    "domain": entity.get("domain", "")
                })
                logger.info(f"Updated concept: {entity['name']}")

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
            logger.info(f"Created relationship: {source_id} -> {target_id}")
        else:
            logger.info(f"Relationship already exists: {source_id} -> {target_id}")

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
    logger.info(f"Added document to vector database with ID: {doc_id}")

    return {
        "doc_id": doc_id,
        "entities": entities,
        "relationships": relationships
    }

def main():
    """
    Main function to demonstrate adding a document to the GraphRAG system.
    """
    logger.info("Initializing databases...")

    # Initialize databases
    neo4j_db = Neo4jDatabase()
    vector_db = VectorDatabase()
    db_linkage = DatabaseLinkage(neo4j_db, vector_db)
    duplicate_detector = DuplicateDetector(vector_db)

    # Verify connections
    if not neo4j_db.verify_connection():
        logger.error("❌ Neo4j connection failed!")
        return

    if not vector_db.verify_connection():
        logger.error("❌ Vector database connection failed!")
        return

    logger.info("✅ Database connections verified!")

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
        "source": "Example",
        "concepts": "Neural Networks, Deep Learning, Transformers, Attention Mechanism"
    }

    # Add document to GraphRAG system
    logger.info("\nAdding document to GraphRAG system...")
    result = add_document_to_graphrag(
        text=document_text,
        metadata=document_metadata,
        neo4j_db=neo4j_db,
        vector_db=vector_db,
        duplicate_detector=duplicate_detector
    )

    if result:
        # Perform a hybrid search
        logger.info("\nPerforming hybrid search...")
        search_results = db_linkage.hybrid_search(
            query_text="How do transformers work in deep learning?",
            n_vector_results=2,
            max_graph_hops=2
        )

        # Display search results
        logger.info("\nVector results:")
        for i, doc in enumerate(search_results["vector_results"]["documents"]):
            logger.info(f"  {i+1}. {doc[:100]}...")

        logger.info("\nGraph results:")
        for i, result in enumerate(search_results["graph_results"]):
            logger.info(f"  {i+1}. {result['name']} (Score: {result['relevance_score']})")

        logger.info("\n✅ Document added and search performed successfully!")
    else:
        logger.info("\nDocument was a duplicate and not added.")


    # Close Neo4j connection
    neo4j_db.close()


if __name__ == "__main__":
    main()