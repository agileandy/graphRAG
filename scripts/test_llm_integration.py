#!/usr/bin/env python3
"""
Script to test LLM integration for GraphRAG project.

This script tests:
1. Connection to LLM providers
2. Text generation
3. Concept extraction
4. Relationship analysis
"""
import sys
import os
import json
import logging
import argparse
from typing import Dict, Any

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.llm.llm_provider import (
    OpenAICompatibleProvider,
    OllamaProvider,
    LLMManager,
    create_llm_provider
)

from src.llm.concept_extraction import (
    extract_concepts_with_llm,
    analyze_concept_relationships,
    summarize_text_with_llm,
    translate_nl_to_graph_query,
    analyze_sentiment
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample texts for testing
SAMPLE_TEXTS = {
    "industry": """
    Industry 4.0 is the ongoing automation of traditional manufacturing and industrial practices, 
    using modern smart technology. Large-scale machine-to-machine communication (M2M) and the 
    Internet of Things (IoT) are integrated for increased automation, improved communication 
    and self-monitoring, and production of smart machines that can analyze and diagnose issues 
    without the need for human intervention.
    
    Industry 5.0 refers to people working alongside robots and smart machines. It's about 
    robots helping humans work better and faster by leveraging advanced technologies like 
    the Internet of Things (IoT) and big data. It adds a personal human touch to the 
    Industry 4.0 pillars of automation and efficiency.
    """,
    
    "machine_learning": """
    Machine Learning is a subset of artificial intelligence that provides systems the ability 
    to automatically learn and improve from experience without being explicitly programmed. 
    Machine Learning focuses on the development of computer programs that can access data and 
    use it to learn for themselves.
    
    Deep Learning is part of a broader family of machine learning methods based on artificial 
    neural networks with representation learning. Learning can be supervised, semi-supervised 
    or unsupervised. Deep learning architectures such as deep neural networks, deep belief 
    networks, recurrent neural networks and convolutional neural networks have been applied 
    to fields including computer vision, speech recognition, natural language processing, 
    audio recognition, social network filtering, machine translation, bioinformatics, drug 
    design, medical image analysis, material inspection and board game programs, where they 
    have produced results comparable to and in some cases surpassing human expert performance.
    """
}

def load_llm_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load LLM configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    # Default config path
    if config_path is None:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "llm_config.json")
    
    try:
        with open(config_path, "r") as f:
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
                "timeout": 60
            }
        }

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
    Test text generation with LLM.
    
    Args:
        llm_manager: LLM manager instance
    """
    print("\nTesting text generation...")
    
    prompt = "Explain the concept of GraphRAG (Graph Retrieval Augmented Generation) in 3-4 sentences."
    
    print(f"Prompt: {prompt}")
    
    try:
        response = llm_manager.generate(prompt)
        print(f"Response: {response}")
        print("✅ Text generation test passed")
        return True
    except Exception as e:
        print(f"❌ Text generation test failed: {e}")
        return False

def test_concept_extraction(llm_manager: LLMManager):
    """
    Test concept extraction with LLM.
    
    Args:
        llm_manager: LLM manager instance
    """
    print("\nTesting concept extraction...")
    
    for domain, text in SAMPLE_TEXTS.items():
        print(f"\nDomain: {domain}")
        
        try:
            concepts = extract_concepts_with_llm(text, llm_manager)
            
            if concepts:
                print(f"✅ Successfully extracted {len(concepts)} concepts:")
                for i, concept in enumerate(concepts[:5]):  # Show only first 5
                    print(f"  {i+1}. {concept.get('name', 'Unknown')} ({concept.get('type', 'Unknown')})")
                    if "description" in concept:
                        print(f"     Description: {concept['description']}")
                    if "related_concepts" in concept and concept["related_concepts"]:
                        print(f"     Related: {', '.join(concept['related_concepts'])}")
                
                if len(concepts) > 5:
                    print(f"  ... and {len(concepts) - 5} more")
            else:
                print("❌ Failed to extract any concepts")
                
        except Exception as e:
            print(f"❌ Concept extraction test failed: {e}")
    
    return True

def test_relationship_analysis(llm_manager: LLMManager):
    """
    Test relationship analysis with LLM.
    
    Args:
        llm_manager: LLM manager instance
    """
    print("\nTesting relationship analysis...")
    
    # First extract concepts
    text = SAMPLE_TEXTS["industry"]
    
    try:
        # Extract concepts
        concepts = extract_concepts_with_llm(text, llm_manager)
        
        if not concepts:
            print("❌ No concepts extracted for relationship analysis")
            return False
        
        # Analyze relationships
        relationships = analyze_concept_relationships(concepts, llm_manager)
        
        if relationships:
            print(f"✅ Successfully analyzed {len(relationships)} relationships:")
            for i, rel in enumerate(relationships[:5]):  # Show only first 5
                print(f"  {i+1}. {rel.get('source', 'Unknown')} --[{rel.get('type', 'RELATED_TO')}]--> {rel.get('target', 'Unknown')}")
                if "strength" in rel:
                    print(f"     Strength: {rel['strength']}")
                if "description" in rel:
                    print(f"     Description: {rel['description']}")
            
            if len(relationships) > 5:
                print(f"  ... and {len(relationships) - 5} more")
            
            return True
        else:
            print("❌ Failed to analyze any relationships")
            return False
            
    except Exception as e:
        print(f"❌ Relationship analysis test failed: {e}")
        return False

def test_summarization(llm_manager: LLMManager):
    """
    Test text summarization with LLM.
    
    Args:
        llm_manager: LLM manager instance
    """
    print("\nTesting text summarization...")
    
    for domain, text in SAMPLE_TEXTS.items():
        print(f"\nDomain: {domain}")
        
        try:
            summary = summarize_text_with_llm(text, llm_manager)
            
            if summary:
                print(f"✅ Successfully generated summary ({len(summary.split())} words):")
                print(f"  {summary}")
            else:
                print("❌ Failed to generate summary")
                
        except Exception as e:
            print(f"❌ Summarization test failed: {e}")
    
    return True

def test_query_translation(llm_manager: LLMManager):
    """
    Test natural language to query translation with LLM.
    
    Args:
        llm_manager: LLM manager instance
    """
    print("\nTesting query translation...")
    
    questions = [
        "What are the main concepts related to Industry 4.0?",
        "Which documents discuss machine learning and deep learning?",
        "How are IoT and Industry 5.0 connected?"
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        
        try:
            query_info = translate_nl_to_graph_query(question, llm_manager)
            
            if query_info and "cypher_query" in query_info and query_info["cypher_query"]:
                print(f"✅ Successfully translated to Cypher query:")
                print(f"  {query_info['cypher_query']}")
                
                if "explanation" in query_info:
                    print(f"  Explanation: {query_info['explanation']}")
                
                if "parameters" in query_info and query_info["parameters"]:
                    print(f"  Parameters: {json.dumps(query_info['parameters'])}")
            else:
                print("❌ Failed to translate to query")
                
        except Exception as e:
            print(f"❌ Query translation test failed: {e}")
    
    return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test LLM integration for GraphRAG project")
    parser.add_argument("--config", type=str, help="Path to LLM configuration file")
    parser.add_argument("--test", type=str, choices=["all", "generation", "concepts", "relationships", "summarization", "query"], default="all", help="Test to run")
    
    args = parser.parse_args()
    
    print("Testing LLM integration for GraphRAG project...")
    
    # Load configuration
    config = load_llm_config(args.config)
    
    # Set up LLM manager
    llm_manager = setup_llm_manager(config)
    
    # Run tests
    if args.test in ["all", "generation"]:
        test_text_generation(llm_manager)
    
    if args.test in ["all", "concepts"]:
        test_concept_extraction(llm_manager)
    
    if args.test in ["all", "relationships"]:
        test_relationship_analysis(llm_manager)
    
    if args.test in ["all", "summarization"]:
        test_summarization(llm_manager)
    
    if args.test in ["all", "query"]:
        test_query_translation(llm_manager)
    
    print("\nLLM integration tests completed!")

if __name__ == "__main__":
    main()
