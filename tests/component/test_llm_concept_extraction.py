#!/usr/bin/env python3
"""Script to test LLM-based concept extraction.

This script:
1. Loads sample text
2. Extracts concepts using LLM
3. Analyzes relationships between concepts
4. Displays the results
"""

import argparse
import json
import logging
import os
import sys
from typing import Any

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.llm.concept_extraction import (
    analyze_concept_relationships,
    extract_concepts_with_llm,
    summarize_text_with_llm,
)
from src.llm.llm_provider import (
    LLMManager,
    create_llm_provider,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Sample texts for testing
SAMPLE_TEXTS = {
    "ai": """
    Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to natural intelligence displayed by animals including humans.
    AI research has been defined as the field of study of intelligent agents, which refers to any system that perceives its environment and takes actions that maximize its chance of achieving its goals.

    The term "artificial intelligence" had previously been used to describe machines that mimic and display "human" cognitive skills that are associated with the human mind, such as "learning" and "problem-solving".
    This definition has since been rejected by major AI researchers who now describe AI in terms of rationality and acting rationally, which does not limit how intelligence can be articulated.

    AI applications include advanced web search engines (e.g., Google), recommendation systems (used by YouTube, Amazon, and Netflix), understanding human speech (such as Siri and Alexa),
    self-driving cars (e.g., Waymo), generative or creative tools (ChatGPT and AI art), automated decision-making, and competing at the highest level in strategic game systems (such as chess and Go).

    As machines become increasingly capable, tasks considered to require "intelligence" are often removed from the definition of AI, a phenomenon known as the AI effect. For instance, optical character recognition is frequently excluded from things considered to be AI, having become a routine technology.
    """,
    "graphrag": """
    GraphRAG (Graph-based Retrieval Augmented Generation) is an advanced approach to knowledge retrieval and generation that combines the strengths of knowledge graphs with vector embeddings and large language models.

    In traditional RAG systems, documents are embedded in a vector space and retrieved based on similarity to a query. While effective, this approach can miss important contextual relationships between concepts.

    GraphRAG addresses this limitation by organizing knowledge in a graph structure, where nodes represent concepts, documents, or entities, and edges represent relationships between them. This graph structure allows for more nuanced retrieval that considers not just semantic similarity but also structural relationships.

    The key components of a GraphRAG system include:

    1. Knowledge Graph: Stores concepts, documents, and their relationships in a structured format.
    2. Vector Database: Maintains embeddings of documents and concepts for similarity-based retrieval.
    3. Hybrid Retrieval: Combines graph traversal and vector similarity to find the most relevant information.
    4. Large Language Model: Generates coherent responses based on the retrieved context.

    GraphRAG offers several advantages over traditional RAG:
    - Better handling of complex queries that involve multiple concepts
    - Improved explainability through explicit relationship modeling
    - Enhanced context awareness by considering the network of related information
    - More precise retrieval by leveraging both semantic and structural information

    Applications of GraphRAG include question answering systems, knowledge management platforms, research assistants, and any system that benefits from structured knowledge retrieval and generation.
    """,
    "neo4j": """
    Neo4j is a graph database management system developed by Neo4j, Inc. It is an ACID-compliant transactional database with native graph storage and processing. Neo4j is the most popular graph database according to DB-Engines ranking.

    Neo4j is implemented in Java and accessible from software written in other languages using the Cypher Query Language through a transactional HTTP endpoint, or through the binary "Bolt" protocol.

    Neo4j has both a Community Edition and Enterprise Edition of the database. The Enterprise Edition includes all that Community Edition has to offer, plus extra enterprise requirements such as backups, clustering, and failover abilities.

    Neo4j's graph database uses a schema-optional property graph data model. This means that data is represented as nodes connected by directed, typed relationships, with properties on both. This structure allows for the flexible and intuitive modeling of domain data.

    Cypher is Neo4j's graph query language that allows users to store and retrieve data from the graph database. Cypher's syntax provides a visual and logical way to match patterns of nodes and relationships in the graph.

    Neo4j is widely used in various applications including fraud detection, real-time recommendation engines, master data management, network and IT operations, and identity and access management.
    """,
}


def load_llm_config(config_path: str = None) -> dict[str, Any]:
    """Load LLM configuration from file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    """
    # Default config path
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "config", "llm_config.json"
        )

    try:
        with open(config_path) as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading LLM config: {e}")
        # Return default config
        return {
            "primary_provider": {
                "type": "openai-compatible",
                "api_base": "http://192.168.1.21:1234/v1",
                "api_key": "dummy-key",
                "model": "lmstudio-community/Phi-4-mini-reasoning-MLX-4bit",
                "temperature": 0.1,
                "max_tokens": 1000,
                "timeout": 60,
            }
        }


def setup_llm_manager(config: dict[str, Any]) -> LLMManager:
    """Set up LLM manager from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        LLM manager instance

    """
    # Create primary provider
    primary_config = config.get("primary_provider", {})
    try:
        primary_provider = create_llm_provider(primary_config)
        logger.info(
            f"Created primary provider: {primary_config.get('type')} with model {primary_config.get('model')}"
        )
    except Exception as e:
        logger.error(f"Error creating primary provider: {e}")
        primary_provider = None

    # Create fallback provider if configured
    fallback_provider = None
    if "fallback_provider" in config:
        fallback_config = config.get("fallback_provider", {})
        try:
            fallback_provider = create_llm_provider(fallback_config)
            logger.info(
                f"Created fallback provider: {fallback_config.get('type')} with model {fallback_config.get('model')}"
            )
        except Exception as e:
            logger.error(f"Error creating fallback provider: {e}")

    # Create LLM manager
    return LLMManager(primary_provider, fallback_provider)


def test_concept_extraction(llm_manager: LLMManager, text_key: str = "graphrag") -> None:
    """Test concept extraction with LLM.

    Args:
        llm_manager: LLM manager instance
        text_key: Key of text to use from SAMPLE_TEXTS

    """
    print(f"\nTesting concept extraction on {text_key} text...")

    text = SAMPLE_TEXTS.get(text_key, "")
    if not text:
        print(f"Text key '{text_key}' not found")
        return

    # Extract concepts
    print("Extracting concepts...")
    concepts = extract_concepts_with_llm(text, llm_manager)

    if concepts:
        print(f"✅ Successfully extracted {len(concepts)} concepts:")
        for i, concept in enumerate(concepts):
            print(
                f"  {i + 1}. {concept.get('name', 'Unknown')} ({concept.get('type', 'Unknown')})"
            )
            if "description" in concept:
                print(f"     Description: {concept['description']}")
            if "related_concepts" in concept and concept["related_concepts"]:
                print(f"     Related: {', '.join(concept['related_concepts'])}")
    else:
        print("❌ Failed to extract any concepts")

    # Analyze relationships
    if concepts:
        print("\nAnalyzing relationships between concepts...")
        relationships = analyze_concept_relationships(concepts, llm_manager)

        if relationships:
            print(f"✅ Successfully analyzed {len(relationships)} relationships:")
            for i, rel in enumerate(relationships):
                print(
                    f"  {i + 1}. {rel.get('source', 'Unknown')} --[{rel.get('type', 'RELATED_TO')}]--> {rel.get('target', 'Unknown')}"
                )
                if "strength" in rel:
                    print(f"     Strength: {rel['strength']}")
                if "description" in rel:
                    print(f"     Description: {rel['description']}")
        else:
            print("❌ Failed to analyze any relationships")

    # Generate summary
    print("\nGenerating summary...")
    summary = summarize_text_with_llm(text, llm_manager)

    if summary:
        print(f"✅ Successfully generated summary ({len(summary.split())} words):")
        print(f"  {summary}")
    else:
        print("❌ Failed to generate summary")


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Test LLM-based concept extraction")
    parser.add_argument("--config", type=str, help="Path to LLM configuration file")
    parser.add_argument(
        "--text",
        type=str,
        choices=list(SAMPLE_TEXTS.keys()),
        default="graphrag",
        help="Text to use for testing",
    )

    args = parser.parse_args()

    print("Testing LLM-based concept extraction...")

    # Load configuration
    config = load_llm_config(args.config)

    # Set up LLM manager
    llm_manager = setup_llm_manager(config)

    # Test concept extraction
    test_concept_extraction(llm_manager, args.text)

    print("\nLLM-based concept extraction test completed!")


if __name__ == "__main__":
    main()
