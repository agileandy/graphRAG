"""
Concept extraction utilities for GraphRAG project.

This module provides utilities for extracting concepts from text using:
1. Rule-based extraction
2. NLP-based extraction
3. LLM-based extraction (using the LLMManager from src.llm.llm_provider)

Note: This module is being refactored to use the LLMManager from src.llm.llm_provider
instead of direct OpenAI API calls. The old implementation is deprecated and will be
removed in a future version.
"""
import re
import logging
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

# Import LLM integration
from src.llm.llm_provider import LLMManager, create_llm_provider

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# We'll use only rule-based extraction since spaCy has compatibility issues
SPACY_AVAILABLE = False
nlp = None

# Load domain-specific stopwords
DOMAIN_STOPWORDS = {
    "general": {"the", "and", "a", "an", "in", "on", "at", "to", "for", "with", "by", "about", "like", "through", "over", "before", "after", "between", "under", "during", "without", "of", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "can", "could", "will", "would", "shall", "should", "may", "might", "must", "this", "that", "these", "those", "it", "they", "them", "their", "he", "she", "him", "her", "his", "hers", "its", "theirs", "we", "us", "our", "ours", "you", "your", "yours", "i", "me", "my", "mine"},
    "tech": {"use", "using", "used", "user", "users", "system", "systems", "data", "information", "process", "processes", "method", "methods", "function", "functions", "value", "values", "example", "examples", "result", "results", "figure", "figures", "table", "tables", "section", "sections", "chapter", "chapters", "page", "pages", "see", "shown", "show", "shows", "showing", "note", "notes", "describe", "describes", "described", "describing", "description", "represent", "represents", "represented", "representing", "representation"},
    "academic": {"paper", "papers", "study", "studies", "research", "researcher", "researchers", "analysis", "analyze", "analyzed", "analyzing", "experiment", "experiments", "experimental", "theory", "theories", "theoretical", "hypothesis", "hypotheses", "method", "methods", "methodology", "methodologies", "approach", "approaches", "framework", "frameworks", "model", "models", "modeling", "modelling", "simulation", "simulations", "algorithm", "algorithms", "implementation", "implementations", "evaluation", "evaluations", "evaluate", "evaluated", "evaluating", "performance", "performances", "result", "results", "conclusion", "conclusions", "future", "work"}
}

def load_llm_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load LLM configuration from file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    # Default config path
    if config_path is None:
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent
        config_path = os.path.join(project_root, "config", "llm_config.json")

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

def setup_llm_manager(config: Dict[str, Any]) -> Optional[LLMManager]:
    """
    Set up LLM manager from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        LLM manager instance or None if setup fails
    """
    # Create primary provider
    primary_config = config.get("primary_provider", {})
    try:
        primary_provider = create_llm_provider(primary_config)
        logger.info(f"Created primary provider: {primary_config.get('type')} with model {primary_config.get('model')}")
    except Exception as e:
        logger.error(f"Error creating primary provider: {e}")
        return None

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

# Initialize LLM manager
llm_manager = None

# Try to initialize LLM manager
try:
    config = load_llm_config()
    llm_manager = setup_llm_manager(config)
    if llm_manager:
        logger.info("Initialized LLM manager for concept extraction")
    else:
        logger.warning("Failed to initialize LLM manager. LLM-based concept extraction will use fallback methods.")
except Exception as e:
    logger.warning(f"Error initializing LLM manager: {e}")

# For backward compatibility - DEPRECATED
# This will be removed in a future version
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    # Check if API key is available
    if os.getenv("OPENAI_API_KEY"):
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        logger.info("Initialized OpenAI client for concept extraction (DEPRECATED)")
    else:
        logger.info("OpenAI API key not found. Using LLMManager for concept extraction.")
        OPENAI_AVAILABLE = False
        openai_client = None
except ImportError:
    logger.warning("OpenAI not available. LLM-based concept extraction will use LLMManager.")
    OPENAI_AVAILABLE = False
    openai_client = None

class ConceptExtractor:
    """
    Concept extraction for GraphRAG project.

    This class provides methods for extracting concepts from text using
    various techniques, from simple rule-based extraction to more
    sophisticated NLP and LLM-based approaches.
    """

    def __init__(self,
                 use_nlp: bool = True,
                 use_llm: bool = False,
                 domain: str = "general",
                 min_concept_length: int = 2,
                 max_concept_length: int = 5):
        """
        Initialize concept extractor.

        Args:
            use_nlp: Whether to use NLP-based extraction
            use_llm: Whether to use LLM-based extraction
            domain: Domain for stopwords ("general", "tech", "academic")
            min_concept_length: Minimum concept length in words
            max_concept_length: Maximum concept length in words
        """
        self.use_nlp = use_nlp and SPACY_AVAILABLE
        # Check if LLM is available through either method
        self.use_llm = use_llm and (llm_manager is not None or OPENAI_AVAILABLE)
        self.domain = domain
        self.min_concept_length = min_concept_length
        self.max_concept_length = max_concept_length

        # Combine stopwords from general and domain-specific sets
        self.stopwords = DOMAIN_STOPWORDS["general"].union(
            DOMAIN_STOPWORDS.get(domain, set())
        )

        # Load domain-specific concept patterns if available
        self.domain_patterns = self._load_domain_patterns(domain)

    def _load_domain_patterns(self, domain: str) -> List[str]:
        """
        Load domain-specific concept patterns.

        Args:
            domain: Domain name

        Returns:
            List of regex patterns for the domain
        """
        # Default patterns for technical concepts
        default_patterns = [
            r'\b[A-Z][a-z]+ (Learning|Network|Model|Algorithm|Framework)\b',  # ML concepts
            r'\b(Deep|Machine|Reinforcement|Supervised|Unsupervised) Learning\b',  # Learning types
            r'\b(Neural Network|Decision Tree|Random Forest|Support Vector Machine|Gradient Boosting)\b',  # ML models
            r'\b(Industry 4\.0|Industry 5\.0|Internet of Things|IoT|AI|ML|DL)\b',  # Industry concepts
            r'\b(Big Data|Cloud Computing|Edge Computing|Blockchain|Quantum Computing)\b'  # Tech concepts
        ]

        # TODO: Load patterns from a configuration file based on domain
        return default_patterns

    def extract_concepts_rule_based(self, text: str) -> List[str]:
        """
        Extract concepts using rule-based approach.

        Args:
            text: Input text

        Returns:
            List of extracted concepts
        """
        concepts = []

        # Extract noun phrases using regex patterns
        # Look for capitalized phrases that might be concepts
        cap_phrases = re.findall(r'\b[A-Z][a-zA-Z]+(?: [a-zA-Z]+){0,4}\b', text)
        concepts.extend([phrase for phrase in cap_phrases if self._is_valid_concept(phrase)])

        # Extract domain-specific patterns
        for pattern in self.domain_patterns:
            matches = re.findall(pattern, text)
            concepts.extend([match for match in matches if self._is_valid_concept(match)])

        # Remove duplicates and sort
        return sorted(list(set(concepts)))

    def extract_concepts_nlp(self, text: str) -> List[str]:
        """
        Extract concepts using NLP-based approach with spaCy.

        Args:
            text: Input text

        Returns:
            List of extracted concepts
        """
        if not self.use_nlp or nlp is None:
            logger.warning("NLP-based extraction not available. Using rule-based extraction instead.")
            return self.extract_concepts_rule_based(text)

        concepts = []

        # Process text with spaCy
        doc = nlp(text)

        # Extract noun chunks as potential concepts
        for chunk in doc.noun_chunks:
            if self._is_valid_concept(chunk.text):
                concepts.append(chunk.text)

        # Extract named entities as potential concepts
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT", "WORK_OF_ART", "LAW", "LANGUAGE", "EVENT", "FAC"] and self._is_valid_concept(ent.text):
                concepts.append(ent.text)

        # Extract technical terms using dependency parsing
        for token in doc:
            # Look for compound noun phrases that might be technical terms
            if token.dep_ == "compound" and token.head.pos_ == "NOUN":
                compound_term = f"{token.text} {token.head.text}"
                if self._is_valid_concept(compound_term):
                    concepts.append(compound_term)

        # Remove duplicates and sort
        return sorted(list(set(concepts)))

    def extract_concepts_llm(self, text: str, max_concepts: int = 10) -> List[Dict[str, Any]]:
        """
        Extract concepts using LLM-based approach.

        Args:
            text: Input text
            max_concepts: Maximum number of concepts to extract

        Returns:
            List of extracted concepts with metadata
        """
        # First try using the LLMManager if available
        if llm_manager is not None:
            try:
                return self._extract_concepts_with_llm_manager(text, max_concepts)
            except Exception as e:
                logger.warning(f"Error using LLMManager for concept extraction: {e}")
                # Fall back to OpenAI client if available
                if self.use_llm and openai_client is not None:
                    logger.info("Falling back to OpenAI client for concept extraction (DEPRECATED)")
                    return self._extract_concepts_with_openai(text, max_concepts)

        # If LLMManager is not available, try using OpenAI client
        if self.use_llm and openai_client is not None:
            logger.warning("Using OpenAI client for concept extraction (DEPRECATED)")
            return self._extract_concepts_with_openai(text, max_concepts)

        # If neither is available, fall back to NLP-based extraction
        logger.warning("LLM-based extraction not available. Using NLP-based extraction instead.")
        nlp_concepts = self.extract_concepts_nlp(text)
        return [{"concept": c, "relevance": 1.0, "source": "nlp"} for c in nlp_concepts[:max_concepts]]

    def _extract_concepts_with_llm_manager(self, text: str, max_concepts: int = 10) -> List[Dict[str, Any]]:
        """
        Extract concepts using LLMManager with improved error handling for template issues.

        Args:
            text: Input text
            max_concepts: Maximum number of concepts to extract

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

        # Try with Phi-4 specific prompt format
        try:
            # Phi-4 specific prompt format
            phi4_system_prompt = """You are a concept extraction assistant that identifies key technical and domain-specific concepts from text. Your task is to extract important concepts, their relevance, and definitions from the provided text."""

            phi4_user_prompt = f"""Extract up to {max_concepts} of the most important domain-specific concepts from the following text.
For each concept, provide:
1. The concept name
2. A relevance score from 0.0 to 1.0
3. A brief definition based on the text

Text:
{truncated_text}

Format your response as a JSON array of objects, each with the following properties:
- concept: The concept name
- relevance: A score from 0.0 to 1.0 indicating the relevance of the concept to the text
- definition: A brief definition of the concept based on the text

Example format:
[
    {{"concept": "Concept 1", "relevance": 0.95, "definition": "Definition 1"}},
    {{"concept": "Concept 2", "relevance": 0.85, "definition": "Definition 2"}},
    ...
]

Only extract concepts that are truly relevant to the domain of the text. Quality is more important than quantity.
Focus on technical and domain-specific concepts."""

            # Generate response with Phi-4 specific prompt
            response = llm_manager.generate(
                phi4_user_prompt,
                system_prompt=phi4_system_prompt,
                max_tokens=1000,
                temperature=0.2
            )

            # Parse JSON from response
            try:
                # Find JSON in the response
                json_start = response.find('[')
                json_end = response.rfind(']') + 1

                if json_start >= 0 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    concepts = json.loads(json_str)
                    # Add source field
                    for concept in concepts:
                        concept["source"] = "llm"
                    logger.info(f"Successfully extracted {len(concepts)} concepts with Phi-4 prompt")
                    return concepts
                else:
                    logger.warning("Could not find JSON array in LLM response")
                    logger.debug(f"LLM response: {response}")

                    # Try to parse structured format as fallback
                    concepts = self._parse_structured_response(response)
                    if concepts:
                        logger.info(f"Successfully extracted {len(concepts)} concepts from structured response")
                        return concepts

                    # If still no concepts, try fallback to rule-based extraction
                    return []
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON from LLM response")
                logger.debug(f"LLM response: {response}")

                # Try to parse structured format as fallback
                concepts = self._parse_structured_response(response)
                if concepts:
                    logger.info(f"Successfully extracted {len(concepts)} concepts from structured response")
                    return concepts

                return []
        except Exception as e:
            logger.warning(f"Error using Phi-4 prompt: {e}")
            return []

    def _parse_structured_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse a structured response from the LLM.

        Args:
            response: LLM response text

        Returns:
            List of extracted concepts with metadata
        """
        concepts = []
        current_concept = {}

        for line in response.split('\n'):
            line = line.strip()
            if not line:
                continue

            if line.startswith('Concept:'):
                # If we have a previous concept, add it to the list
                if current_concept and 'concept' in current_concept:
                    concepts.append(current_concept)

                # Start a new concept
                current_concept = {'concept': line[8:].strip(), 'source': 'llm'}
            elif line.startswith('Relevance:'):
                try:
                    relevance = float(line[10:].strip())
                    current_concept['relevance'] = min(max(relevance, 0.0), 1.0)  # Ensure in range 0-1
                except ValueError:
                    current_concept['relevance'] = 0.8  # Default if parsing fails
            elif line.startswith('Definition:'):
                current_concept['definition'] = line[11:].strip()

        # Add the last concept if it exists
        if current_concept and 'concept' in current_concept:
            concepts.append(current_concept)

        return concepts

    def _extract_concepts_with_openai(self, text: str, max_concepts: int = 10) -> List[Dict[str, Any]]:
        """
        Extract concepts using OpenAI API (DEPRECATED).

        Args:
            text: Input text
            max_concepts: Maximum number of concepts to extract

        Returns:
            List of extracted concepts with metadata
        """
        logger.warning("Using deprecated OpenAI API for concept extraction. This will be removed in a future version.")

        if openai_client is None:
            logger.warning("OpenAI client not available. Using NLP-based extraction instead.")
            nlp_concepts = self.extract_concepts_nlp(text)
            return [{"concept": c, "relevance": 1.0, "source": "nlp"} for c in nlp_concepts[:max_concepts]]

        # Prepare prompt for OpenAI
        prompt = f"""
        Extract the most important domain-specific concepts from the following text.
        Return the result as a JSON array of objects, each with the following properties:
        - concept: The concept name
        - relevance: A score from 0.0 to 1.0 indicating the relevance of the concept to the text
        - definition: A brief definition of the concept based on the text

        Text:
        {text[:4000]}  # Limit text length to avoid token limits

        Format:
        [
            {{"concept": "Concept 1", "relevance": 0.95, "definition": "Definition 1"}},
            {{"concept": "Concept 2", "relevance": 0.85, "definition": "Definition 2"}},
            ...
        ]

        Extract at most {max_concepts} concepts. Focus on technical and domain-specific concepts.
        """

        try:
            # Call OpenAI API
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a concept extraction assistant that identifies key technical and domain-specific concepts from text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )

            # Parse response
            result = response.choices[0].message.content
            try:
                concepts = json.loads(result)
                # Add source field
                for concept in concepts:
                    concept["source"] = "llm"
                return concepts
            except json.JSONDecodeError:
                logger.error(f"Failed to parse LLM response as JSON: {result}")
                return []
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return []

    def extract_concepts(self, text: str, method: str = "auto", max_concepts: int = 20) -> List[Dict[str, Any]]:
        """
        Extract concepts from text using the specified method.

        Args:
            text: Input text
            method: Extraction method ("rule", "nlp", "llm", or "auto")
            max_concepts: Maximum number of concepts to extract

        Returns:
            List of extracted concepts with metadata
        """
        # Adjust max_concepts based on text length
        text_length = len(text)
        if text_length < 1000:  # Short text
            adjusted_max_concepts = min(5, max_concepts)
        elif text_length < 5000:  # Medium text
            adjusted_max_concepts = min(10, max_concepts)
        else:  # Long text
            adjusted_max_concepts = max_concepts

        logger.info(f"Adjusting max concepts from {max_concepts} to {adjusted_max_concepts} based on text length ({text_length} chars)")

        # Determine method based on availability
        if method == "auto":
            if self.use_llm and (llm_manager is not None or openai_client is not None):
                method = "llm"
            elif self.use_nlp and nlp is not None:
                method = "nlp"
            else:
                method = "rule"

        # Extract concepts using the specified method
        if method == "llm" and self.use_llm:
            return self.extract_concepts_llm(text, adjusted_max_concepts)
        elif method == "nlp" and self.use_nlp and nlp is not None:
            concepts = self.extract_concepts_nlp(text)
            return [{"concept": c, "relevance": 1.0, "source": "nlp"} for c in concepts[:adjusted_max_concepts]]
        else:
            concepts = self.extract_concepts_rule_based(text)
            return [{"concept": c, "relevance": 1.0, "source": "rule"} for c in concepts[:adjusted_max_concepts]]

    def _is_valid_concept(self, concept: str) -> bool:
        """
        Check if a concept is valid.

        Args:
            concept: Concept to check

        Returns:
            True if the concept is valid, False otherwise
        """
        # Normalize concept
        concept = concept.strip()

        # Check length
        words = concept.split()
        if len(words) < self.min_concept_length or len(words) > self.max_concept_length:
            return False

        # Check if concept contains only stopwords
        if all(word.lower() in self.stopwords for word in words):
            return False

        # Check if concept is too short
        if len(concept) < 4:
            return False

        return True

    def weight_concepts(self, concepts: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
        """
        Weight concepts based on frequency and position in text.

        Args:
            concepts: List of concepts
            text: Input text

        Returns:
            List of weighted concepts
        """
        weighted_concepts = []

        # Count occurrences of each concept
        concept_counts = {}
        for concept_dict in concepts:
            concept = concept_dict["concept"]
            # Case-insensitive count
            count = len(re.findall(re.escape(concept), text, re.IGNORECASE))
            concept_counts[concept] = count

        # Normalize counts
        max_count = max(concept_counts.values()) if concept_counts else 1

        # Weight concepts
        for concept_dict in concepts:
            concept = concept_dict["concept"]
            count = concept_counts.get(concept, 0)

            # Calculate frequency weight
            freq_weight = count / max_count if max_count > 0 else 0

            # Calculate position weight (concepts appearing earlier are more important)
            first_pos = text.lower().find(concept.lower())
            pos_weight = 1.0
            if first_pos >= 0:
                # Normalize position to 0-1 range (0 = start, 1 = end)
                norm_pos = first_pos / len(text)
                # Invert so earlier positions get higher weight
                pos_weight = 1.0 - (norm_pos * 0.5)  # Scale to 0.5-1.0 range

            # Calculate final weight
            weight = (freq_weight * 0.7) + (pos_weight * 0.3)

            # Create weighted concept
            weighted_concept = concept_dict.copy()
            weighted_concept["weight"] = weight
            weighted_concept["frequency"] = count

            weighted_concepts.append(weighted_concept)

        # Sort by weight
        return sorted(weighted_concepts, key=lambda x: x["weight"], reverse=True)

if __name__ == "__main__":
    # Example usage
    extractor = ConceptExtractor(use_nlp=True, use_llm=True)

    text = """
    Industry 4.0 is the ongoing automation of traditional manufacturing and industrial practices,
    using modern smart technology. Large-scale machine-to-machine communication (M2M) and the
    Internet of Things (IoT) are integrated for increased automation, improved communication
    and self-monitoring, and production of smart machines that can analyze and diagnose issues
    without the need for human intervention.

    Industry 5.0 refers to people working alongside robots and smart machines. It's about
    robots helping humans work better and faster by leveraging advanced technologies like
    the Internet of Things (IoT) and big data. It adds a personal human touch to the
    Industry 4.0 pillars of automation and efficiency.
    """

    print("Rule-based concepts:")
    rule_concepts = extractor.extract_concepts_rule_based(text)
    for concept in rule_concepts:
        print(f"  - {concept}")

    if SPACY_AVAILABLE:
        print("\nNLP-based concepts:")
        nlp_concepts = extractor.extract_concepts_nlp(text)
        for concept in nlp_concepts:
            print(f"  - {concept}")

    print("\nAuto-selected method concepts:")
    auto_concepts = extractor.extract_concepts(text)
    for concept in auto_concepts:
        print(f"  - {concept['concept']} (relevance: {concept['relevance']}, source: {concept['source']})")

    print("\nWeighted concepts:")
    weighted_concepts = extractor.weight_concepts(auto_concepts, text)
    for concept in weighted_concepts:
        print(f"  - {concept['concept']} (weight: {concept['weight']:.2f}, frequency: {concept['frequency']})")