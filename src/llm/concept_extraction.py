"""
LLM-based concept extraction module for GraphRAG project.

This module provides utilities for extracting concepts from text using LLMs,
analyzing relationships between concepts, and enhancing the knowledge graph.
"""
import json
import logging
from typing import List, Dict, Any

from src.llm.llm_provider import LLMManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_concepts_with_llm(text: str, llm_manager: LLMManager) -> List[Dict[str, Any]]:
    """
    Extract concepts from text using LLM.

    Args:
        text: Input text
        llm_manager: LLM manager instance

    Returns:
        List of extracted concepts with metadata
    """
    # Truncate text if too long
    max_text_length = 4000
    if len(text) > max_text_length:
        truncated_text = text[:max_text_length] + "..."
        logger.info(f"Text truncated from {len(text)} to {max_text_length} characters")
    else:
        truncated_text = text

    # Prepare prompt for concept extraction
    prompt = f"""
    Extract key concepts from the following text. For each concept, identify:
    1. The concept name
    2. The concept type (PERSON, ORGANIZATION, LOCATION, TECHNOLOGY, PROCESS, ABSTRACT, etc.)
    3. A brief description based on the context
    4. Related concepts mentioned in the text

    Format the output as a JSON array of objects with the following structure:
    [
        {{
            "name": "concept_name",
            "type": "concept_type",
            "description": "brief_description",
            "related_concepts": ["related1", "related2"]
        }}
    ]

    TEXT:
    {truncated_text}
    """

    # Generate response
    response = llm_manager.generate(
        prompt, 
        system_prompt="You are an expert in knowledge extraction and ontology creation.",
        max_tokens=2000
    )

    # Parse JSON from response
    try:
        # Find JSON in the response (it might be embedded in text)
        json_start = response.find('[')
        json_end = response.rfind(']') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            concepts = json.loads(json_str)
            return concepts
        else:
            logger.warning("Could not find JSON array in LLM response")
            return []
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from LLM response")
        logger.debug(f"LLM response: {response}")
        return []

def analyze_concept_relationships(concepts: List[Dict[str, Any]], llm_manager: LLMManager) -> List[Dict[str, Any]]:
    """
    Analyze relationships between concepts using LLM.

    Args:
        concepts: List of concepts
        llm_manager: LLM manager instance

    Returns:
        List of relationships with metadata
    """
    # Extract concept names
    concept_names = [concept["name"] for concept in concepts]
    
    # If too many concepts, limit to the first 20
    if len(concept_names) > 20:
        logger.info(f"Limiting relationship analysis to first 20 of {len(concept_names)} concepts")
        concept_names = concept_names[:20]

    # Prepare prompt for relationship analysis
    prompt = f"""
    Analyze the relationships between the following concepts:
    {', '.join(concept_names)}

    For each pair of related concepts, identify:
    1. The source concept
    2. The target concept
    3. The relationship type (e.g., IS_PART_OF, DEPENDS_ON, INFLUENCES, SIMILAR_TO, etc.)
    4. The relationship strength (a value between 0 and 1)
    5. A brief description of the relationship

    Format the output as a JSON array of objects with the following structure:
    [
        {{
            "source": "source_concept",
            "target": "target_concept",
            "type": "relationship_type",
            "strength": 0.8,
            "description": "brief_description"
        }}
    ]

    Only include relationships that are meaningful and relevant.
    """

    # Generate response
    response = llm_manager.generate(
        prompt, 
        system_prompt="You are an expert in knowledge graph construction and relationship analysis.",
        max_tokens=2000
    )

    # Parse JSON from response
    try:
        # Find JSON in the response
        json_start = response.find('[')
        json_end = response.rfind(']') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            relationships = json.loads(json_str)
            return relationships
        else:
            logger.warning("Could not find JSON array in LLM response")
            return []
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from LLM response")
        logger.debug(f"LLM response: {response}")
        return []

def summarize_text_with_llm(text: str, llm_manager: LLMManager, max_length: int = 200) -> str:
    """
    Generate a concise summary of text using LLM.

    Args:
        text: Input text
        llm_manager: LLM manager instance
        max_length: Maximum summary length in words

    Returns:
        Text summary
    """
    # Truncate text if too long
    max_text_length = 4000
    if len(text) > max_text_length:
        truncated_text = text[:max_text_length] + "..."
        logger.info(f"Text truncated from {len(text)} to {max_text_length} characters for summarization")
    else:
        truncated_text = text

    # Prepare prompt for summarization
    prompt = f"""
    Summarize the following text in a concise manner, focusing on the key points and main concepts.
    The summary should be no longer than {max_length} words.

    TEXT:
    {truncated_text}
    """

    # Generate response
    summary = llm_manager.generate(
        prompt, 
        system_prompt="You are an expert in summarizing complex information clearly and concisely.",
        max_tokens=500
    )

    return summary.strip()

def translate_nl_to_graph_query(question: str, llm_manager: LLMManager) -> Dict[str, Any]:
    """
    Translate natural language question to graph query.

    Args:
        question: Natural language question
        llm_manager: LLM manager instance

    Returns:
        Dictionary with query information
    """
    # Prepare prompt for query translation
    prompt = f"""
    Translate the following natural language question into a Cypher query for Neo4j:

    QUESTION: {question}

    The knowledge graph has the following structure:
    - Nodes with label 'Concept' have properties: name, type, description
    - Nodes with label 'Document' have properties: title, author, summary, content
    - Relationships between Concepts: RELATED_TO with properties: strength, context
    - Relationships between Concepts and Documents: APPEARS_IN with properties: count, context

    Format your response as a JSON object with the following structure:
    {{
        "cypher_query": "MATCH ... RETURN ...",
        "parameters": {{"param1": "value1", ...}},
        "explanation": "Brief explanation of the query"
    }}
    """

    # Generate response
    response = llm_manager.generate(
        prompt, 
        system_prompt="You are an expert in Neo4j and Cypher query language.",
        max_tokens=1000
    )

    # Parse JSON from response
    try:
        # Find JSON in the response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1

        if json_start >= 0 and json_end > json_start:
            json_str = response[json_start:json_end]
            query_info = json.loads(json_str)
            return query_info
        else:
            logger.warning("Could not find JSON object in LLM response")
            return {
                "cypher_query": "",
                "parameters": {},
                "explanation": "Failed to parse query from LLM response"
            }
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from LLM response")
        logger.debug(f"LLM response: {response}")
        return {
            "cypher_query": "",
            "parameters": {},
            "explanation": "Failed to parse query from LLM response"
        }

def analyze_sentiment(text: str, llm_manager: LLMManager) -> str:
    """
    Analyze sentiment of text using LLM.

    Args:
        text: Input text
        llm_manager: LLM manager instance

    Returns:
        Sentiment label (POSITIVE, NEGATIVE, NEUTRAL, or MIXED)
    """
    # Truncate text if too long
    max_text_length = 1000
    if len(text) > max_text_length:
        truncated_text = text[:max_text_length] + "..."
        logger.info(f"Text truncated from {len(text)} to {max_text_length} characters for sentiment analysis")
    else:
        truncated_text = text

    # Prepare prompt for sentiment analysis
    prompt = f"""
    Analyze the sentiment of the following text. Respond with only one word: POSITIVE, NEGATIVE, NEUTRAL, or MIXED.

    TEXT:
    {truncated_text}
    """

    # Generate response
    response = llm_manager.generate(
        prompt, 
        system_prompt="You are an expert in sentiment analysis.",
        max_tokens=50
    )

    # Extract sentiment
    response = response.strip().upper()
    if "POSITIVE" in response:
        return "POSITIVE"
    elif "NEGATIVE" in response:
        return "NEGATIVE"
    elif "NEUTRAL" in response:
        return "NEUTRAL"
    elif "MIXED" in response:
        return "MIXED"
    else:
        logger.warning(f"Unexpected sentiment response: {response}")
        return "UNKNOWN"
