"""
LLM-based concept extraction module for GraphRAG project.

This module provides utilities for extracting concepts from text using LLMs,
analyzing relationships between concepts, and enhancing the knowledge graph.
"""
import json
import logging
from typing import List, Dict, Any, Optional

from src.llm.llm_provider import LLMManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_concepts_with_llm(text: str, llm_manager: LLMManager, existing_concepts: Optional[List[Dict[str, Any]]] = None, is_chunk: bool = False) -> List[Dict[str, Any]]:
    """
    Extract concepts from text using LLM with enhanced context awareness.

    Args:
        text: Input text
        llm_manager: LLM manager instance
        existing_concepts: List of existing concepts in the knowledge base (optional)
        is_chunk: Whether the text is already a chunk (to avoid unnecessary truncation)

    Returns:
        List of extracted concepts with metadata
    """
    # Truncate text if too long and not already a chunk
    max_text_length = 3000  # Reduced to allow more room for existing concepts
    if not is_chunk and len(text) > max_text_length:
        truncated_text = text[:max_text_length] + "..."
        logger.info(f"Text truncated from {len(text)} to {max_text_length} characters")
    else:
        truncated_text = text

    # Format existing concepts if provided
    existing_concepts_text = ""
    if existing_concepts and len(existing_concepts) > 0:
        # Limit to 20 most relevant concepts to avoid overwhelming the prompt
        relevant_concepts = existing_concepts[:20]
        existing_concepts_text = "Existing concepts in the knowledge base:\n"
        for concept in relevant_concepts:
            concept_name = concept.get("name", "")
            concept_type = concept.get("type", "")
            concept_desc = concept.get("description", "")
            existing_concepts_text += f"- {concept_name} ({concept_type}): {concept_desc[:100]}...\n"

    # Prepare prompt for enhanced concept extraction
    prompt = f"""
    Extract the most important concepts from the following text and identify relationships between them.

    For each concept, provide:
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

    {existing_concepts_text}

    TEXT:
    {truncated_text}
    """

    # Generate response
    try:
        response = llm_manager.generate(
            prompt,
            system_prompt="You are an expert in knowledge extraction and ontology creation. Focus on identifying technical and domain-specific concepts that are truly relevant to the text.",
            max_tokens=2000
        )

        # Check if the response is an error message
        if response.startswith("Error:") or response.startswith("API Response:"):
            logger.warning(f"LLM error during concept extraction: {response}")
            # Return an empty list if there was an error
            return []
    except Exception as e:
        logger.error(f"Exception during concept extraction: {e}")
        return []

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

def analyze_concept_relationships(concepts: List[Dict[str, Any]], llm_manager: LLMManager, existing_concepts: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    """
    Analyze relationships between concepts using LLM with enhanced semantic relationship types.

    Args:
        concepts: List of concepts
        llm_manager: LLM manager instance
        existing_concepts: List of existing concepts in the knowledge base (optional)

    Returns:
        List of relationships with metadata
    """
    # Extract concept names
    concept_names = [concept["name"] for concept in concepts]

    # If too many concepts, limit to the first 15
    if len(concept_names) > 15:
        logger.info(f"Limiting relationship analysis to first 15 of {len(concept_names)} concepts")
        concept_names = concept_names[:15]

    # Format existing concepts if provided
    existing_concepts_text = ""
    if existing_concepts and len(existing_concepts) > 0:
        # Limit to 10 most relevant existing concepts
        relevant_concepts = existing_concepts[:10]
        existing_concepts_text = "\nExisting concepts in the knowledge base that might be related:\n"
        for concept in relevant_concepts:
            existing_concepts_text += f"- {concept.get('name', '')}\n"
        concept_names.extend([concept.get('name', '') for concept in relevant_concepts])

    # Prepare prompt for enhanced relationship analysis
    prompt = f"""
    Analyze the relationships between the following concepts:
    {', '.join(concept_names)}

    For each pair of related concepts, identify:
    1. The source concept
    2. The target concept
    3. The specific relationship type (see below)
    4. The relationship strength (a value between 0 and 1) - THIS IS VERY IMPORTANT
       - 0.1-0.3: Weak or tangential relationship
       - 0.4-0.6: Moderate relationship
       - 0.7-0.9: Strong relationship
       - 1.0: Direct, essential relationship
    5. A brief description of the relationship that explains why you assigned that strength value

    Use these specific semantic relationship types:
    - DEFINES_CONCEPT or EXPLAINS_TERM: When one concept explains or defines another
    - IS_A, TYPE_OF, or SUBCLASS_OF: For hierarchical relationships (X is a type of Y)
    - HAS_PART, CONTAINS_COMPONENT, or MODULE_OF: For compositional relationships (X contains Y)
    - USED_FOR, APPLIES_TO, or PURPOSE_IS: For functional relationships (X is used for Y)
    - IMPLEMENTS_METHOD, USES_TECHNIQUE, or EMPLOYS_ALGORITHM: For implementation relationships (X uses Y method)
    - HAS_ATTRIBUTE, HAS_PROPERTY, or CHARACTERIZED_BY: For characteristic relationships (X has property Y)
    - EXAMPLE_OF, ILLUSTRATES_CONCEPT, or DEMONSTRATES_USAGE: For exemplification relationships (X is an example of Y)
    - REQUIRES_INPUT, PRODUCES_OUTPUT, or HAS_PARAMETER: For I/O relationships (X requires Y as input)
    - STEP_IN_PROCESS, PRECEDES, or FOLLOWS: For sequential relationships (X comes before Y)
    - COMPARES_WITH, ALTERNATIVE_TO, or DIFFERENTIATED_FROM: For comparative relationships (X vs Y)
    - RELATED_TO: Only use this as a fallback when none of the above apply

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

    Only include relationships that are meaningful and relevant. Focus on quality over quantity.
    {existing_concepts_text}
    """

    # Generate response
    try:
        response = llm_manager.generate(
            prompt,
            system_prompt="You are an expert in knowledge graph construction and relationship analysis. Your task is to identify precise, meaningful relationships between concepts using specific relationship types.",
            max_tokens=2500
        )

        # Check if the response is an error message
        if response.startswith("Error:") or response.startswith("API Response:"):
            logger.warning(f"LLM error during relationship analysis: {response}")
            # Return an empty list if there was an error
            return []
    except Exception as e:
        logger.error(f"Exception during relationship analysis: {e}")
        return []

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

def extract_concepts_two_pass(document_text: str, llm_manager: LLMManager, chunk_size: int = 3000, overlap: int = 500) -> List[Dict[str, Any]]:
    """
    Implement a two-pass approach for concept extraction:
    1. First pass: Extract concepts from individual chunks
    2. Second pass: Analyze relationships between concepts across chunks

    Args:
        document_text: Full document text
        llm_manager: LLM manager instance
        chunk_size: Size of each chunk in characters
        overlap: Overlap between chunks in characters

    Returns:
        List of extracted concepts with metadata and relationships
    """
    # Split document into overlapping chunks
    chunks = []
    for i in range(0, len(document_text), chunk_size - overlap):
        chunk = document_text[i:i + chunk_size]
        if chunk:  # Ensure chunk is not empty
            chunks.append(chunk)

    logger.info(f"Split document into {len(chunks)} chunks for two-pass concept extraction")

    # First pass: Extract concepts from each chunk
    all_concepts = []
    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i+1}/{len(chunks)}")

        # Extract concepts from this chunk, indicating it's already a chunk
        chunk_concepts = extract_concepts_with_llm(chunk, llm_manager, is_chunk=True)

        # Add chunk index for tracking
        for concept in chunk_concepts:
            concept["chunk_index"] = i

        all_concepts.extend(chunk_concepts)

    # Deduplicate concepts by name (case-insensitive)
    unique_concepts = {}
    for concept in all_concepts:
        name_lower = concept["name"].lower()
        if name_lower not in unique_concepts:
            unique_concepts[name_lower] = concept
        else:
            # Merge information from duplicate concepts
            existing = unique_concepts[name_lower]
            # Combine related concepts lists
            related = set(existing.get("related_concepts", []))
            related.update(concept.get("related_concepts", []))
            existing["related_concepts"] = list(related)
            # Use the more detailed description
            if len(concept.get("description", "")) > len(existing.get("description", "")):
                existing["description"] = concept["description"]

    # Convert back to list
    deduplicated_concepts = list(unique_concepts.values())
    logger.info(f"Extracted {len(deduplicated_concepts)} unique concepts from {len(all_concepts)} total concepts")

    # Second pass: Analyze relationships between concepts
    relationships = analyze_concept_relationships(deduplicated_concepts, llm_manager)
    logger.info(f"Identified {len(relationships)} relationships between concepts")

    # Add relationship information to concepts
    for concept in deduplicated_concepts:
        concept["relationships"] = []
        for rel in relationships:
            if rel["source"] == concept["name"]:
                concept["relationships"].append({
                    "target": rel["target"],
                    "type": rel["type"],
                    "strength": rel["strength"],
                    "description": rel["description"]
                })

    return deduplicated_concepts

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
