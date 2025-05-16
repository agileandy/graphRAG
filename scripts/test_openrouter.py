#!/usr/bin/env python3
"""
Test script for OpenRouter integration with Google Gemini 2.0 Flash.
This script tests the OpenRouter provider by generating text and extracting concepts.
"""
import sys
import os
import json
import logging
from typing import Dict, Any

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.llm.llm_provider import create_llm_provider, LLMManager
from src.llm.concept_extraction import extract_concepts_with_llm, analyze_concept_relationships

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load OpenRouter configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    # Default config path
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), "..", "config", "openrouter_config.json")
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}

def setup_llm_manager(config: Dict[str, Any]) -> LLMManager:
    """
    Set up LLM manager from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        LLM manager instance
    """
    # Create primary provider
    primary_config = config.get("primary_provider", {})
    try:
        primary_provider = create_llm_provider(primary_config)
        logger.info(f"Created primary provider: {primary_config.get('type')} with model {primary_config.get('model')}")
    except Exception as e:
        logger.error(f"Error creating primary provider: {e}")
        primary_provider = None
    
    # Create fallback provider if configured
    fallback_provider = None
    if "fallback_provider" in config:
        fallback_config = config.get("fallback_provider", {})
        try:
            fallback_provider = create_llm_provider(fallback_config)
            logger.info(f"Created fallback provider: {fallback_config.get('type')} with model {fallback_config.get('model')}")
        except Exception as e:
            logger.error(f"Error creating fallback provider: {e}")
    
    # Create LLM manager
    return LLMManager(primary_provider, fallback_provider)

def test_text_generation(llm_manager: LLMManager):
    """
    Test text generation with OpenRouter.
    
    Args:
        llm_manager: LLM manager instance
    """
    prompt = "Explain the concept of Retrieval-Augmented Generation (RAG) in 3-4 sentences."
    
    print("\n=== Testing Text Generation ===")
    print(f"Prompt: {prompt}")
    
    try:
        response = llm_manager.generate(
            prompt,
            system_prompt="You are a helpful AI assistant that provides concise explanations.",
            max_tokens=200
        )
        
        print("\nResponse:")
        print(response)
    except Exception as e:
        logger.error(f"Error generating text: {e}")

def test_concept_extraction(llm_manager: LLMManager):
    """
    Test concept extraction with OpenRouter.
    
    Args:
        llm_manager: LLM manager instance
    """
    text = """
    Retrieval-Augmented Generation (RAG) is a technique that enhances large language models by combining them with external knowledge retrieval. 
    In RAG, when a query is received, relevant information is first retrieved from a knowledge base, and then this information is used to augment the context provided to the language model. 
    This approach helps overcome the limitations of traditional language models, such as hallucinations and outdated knowledge, by grounding the generation in factual information. 
    RAG systems typically consist of an embedding model for semantic search, a vector database for storing document embeddings, and a language model for generating responses based on the retrieved context.
    
    GraphRAG extends this concept by incorporating knowledge graphs alongside vector embeddings. Instead of relying solely on semantic similarity for retrieval, GraphRAG leverages explicit relationships between concepts, enabling more precise and contextually relevant information retrieval. This hybrid approach combines the strengths of both vector-based retrieval and graph-based traversal.
    """
    
    print("\n=== Testing Concept Extraction ===")
    print(f"Extracting concepts from text ({len(text)} characters)...")
    
    try:
        concepts = extract_concepts_with_llm(text, llm_manager)
        
        print(f"\nExtracted {len(concepts)} concepts:")
        for i, concept in enumerate(concepts):
            print(f"\n{i+1}. {concept.get('name', 'Unknown')} ({concept.get('type', 'Unknown')})")
            print(f"   Description: {concept.get('description', 'No description')}")
            if "related_concepts" in concept and concept["related_concepts"]:
                print(f"   Related concepts: {', '.join(concept['related_concepts'])}")
        
        # Analyze relationships
        relationships = analyze_concept_relationships(concepts, llm_manager)
        
        print(f"\nIdentified {len(relationships)} relationships:")
        for i, rel in enumerate(relationships):
            print(f"\n{i+1}. {rel.get('source', '')} --{rel.get('type', 'RELATED_TO')}--> {rel.get('target', '')}")
            print(f"   Strength: {rel.get('strength', 0)}")
            print(f"   Description: {rel.get('description', 'No description')}")
    except Exception as e:
        logger.error(f"Error extracting concepts: {e}")

def main():
    """Main function."""
    print("Testing OpenRouter integration with Google Gemini 2.0 Flash")
    
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
    
    # Test text generation
    test_text_generation(llm_manager)
    
    # Test concept extraction
    test_concept_extraction(llm_manager)

if __name__ == "__main__":
    main()
