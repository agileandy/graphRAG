"""
LLM module for GraphRAG project.

This module provides utilities for integrating with Large Language Models (LLMs)
for concept extraction, relationship analysis, and semantic understanding.
"""

from src.llm.llm_provider import (
    LLMProvider,
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

__all__ = [
    # LLM Providers
    'LLMProvider',
    'OpenAICompatibleProvider',
    'OllamaProvider',
    'LLMManager',
    'create_llm_provider',
    
    # Concept Extraction
    'extract_concepts_with_llm',
    'analyze_concept_relationships',
    'summarize_text_with_llm',
    'translate_nl_to_graph_query',
    'analyze_sentiment'
]
