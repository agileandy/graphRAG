#!/usr/bin/env python3
"""Test script for relationship strength analysis with OpenRouter."""

import json
import logging
import os
import sys
from typing import Any

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.llm.concept_extraction import (
    analyze_concept_relationships,
)
from src.llm.llm_provider import LLMManager, create_llm_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_config(config_path: str = None) -> dict[str, Any]:
    """Load OpenRouter configuration from file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    """
    # Default config path
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "openrouter_config.json"
        )

    try:
        with open(config_path) as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}


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


def test_relationship_strength(llm_manager: LLMManager) -> None:
    """Test relationship strength analysis with OpenRouter.

    Args:
        llm_manager: LLM manager instance

    """
    # Define a set of concepts with clear relationships
    concepts = [
        {
            "name": "Retrieval-Augmented Generation",
            "type": "TECHNIQUE",
            "description": "A technique that enhances large language models by combining them with external knowledge retrieval.",
        },
        {
            "name": "GraphRAG",
            "type": "TECHNIQUE",
            "description": "An extension of RAG that incorporates knowledge graphs alongside vector embeddings.",
        },
        {
            "name": "Vector Database",
            "type": "TECHNOLOGY",
            "description": "A database optimized for storing and querying vector embeddings.",
        },
        {
            "name": "Knowledge Graph",
            "type": "TECHNOLOGY",
            "description": "A graph-structured database that stores knowledge in a connected format.",
        },
        {
            "name": "Neo4j",
            "type": "SOFTWARE",
            "description": "A graph database management system.",
        },
    ]

    print("\n=== Testing Relationship Strength Analysis ===")
    print(f"Analyzing relationships between {len(concepts)} concepts...")

    try:
        # Analyze relationships with emphasis on strength
        relationships = analyze_concept_relationships(concepts, llm_manager)

        if relationships:
            print(f"\nIdentified {len(relationships)} relationships:")

            # Group relationships by strength
            strength_groups = {
                "weak": [],
                "moderate": [],
                "strong": [],
                "essential": [],
            }

            for rel in relationships:
                strength = rel.get("strength", 0)
                if strength < 0.4:
                    strength_groups["weak"].append(rel)
                elif strength < 0.7:
                    strength_groups["moderate"].append(rel)
                elif strength < 1.0:
                    strength_groups["strong"].append(rel)
                else:
                    strength_groups["essential"].append(rel)

            # Print relationships by strength category
            for category, rels in strength_groups.items():
                if rels:
                    print(f"\n{category.upper()} RELATIONSHIPS ({len(rels)}):")
                    for i, rel in enumerate(rels):
                        print(
                            f"\n{i + 1}. {rel.get('source', '')} --{rel.get('type', 'RELATED_TO')}--> {rel.get('target', '')}"
                        )
                        print(f"   Strength: {rel.get('strength', 0)}")
                        print(
                            f"   Description: {rel.get('description', 'No description')}"
                        )
        else:
            print("No relationships identified.")
    except Exception as e:
        logger.error(f"Error analyzing relationships: {e}")


def main() -> None:
    """Main function."""
    print("Testing relationship strength analysis with OpenRouter")

    # Load configuration
    config = load_config()
    if not config:
        logger.error("Failed to load configuration")
        return

    # Set up LLM manager
    llm_manager = setup_llm_manager(config)
    if not llm_manager or not llm_manager.primary_provider:
        logger.error("Failed to set up LLM manager")
        return

    # Test relationship strength analysis
    test_relationship_strength(llm_manager)


if __name__ == "__main__":
    main()
