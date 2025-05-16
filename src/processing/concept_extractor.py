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
            "_comment": "To use OpenRouter for concept extraction, replace OPENROUTER_API_KEY with your actual API key from https://openrouter.ai/",
            "primary_provider": {
                "type": "openrouter",
                "api_key": "OPENROUTER_API_KEY",
                "model": "google/gemini-2.0-flash-exp:free",
                "temperature": 0.1,
                "max_tokens": 1000,
                "timeout": 60
            },
            "embedding_provider": {
                "type": "ollama",
                "api_base": "http://localhost:11434",
                "model": "snowflake-arctic-embed2:latest",
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

# We only use local LLM providers, not OpenAI
OPENAI_AVAILABLE = False
openai_client = None
logger.info("Using local LLM providers for concept extraction.")

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
        # Check if LLM is available through local providers
        self.use_llm = use_llm and llm_manager is not None
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

        # Extract common technical terms and phrases
        # Look for phrases with technical keywords
        tech_keywords = [
            "algorithm", "framework", "model", "system", "network", "protocol",
            "architecture", "platform", "language", "interface", "database",
            "learning", "intelligence", "neural", "data", "cloud", "computing",
            "security", "encryption", "blockchain", "internet", "web", "api",
            "software", "hardware", "device", "sensor", "robot", "automation",
            "prompt", "engineering", "llm", "gpt", "ai", "ml", "nlp", "rag"
        ]

        # Create patterns for technical terms
        for keyword in tech_keywords:
            # Look for phrases where the keyword is the main term
            # e.g., "machine learning", "neural network", "cloud computing"
            pattern = fr'\b[a-zA-Z]+ {keyword}\b'
            matches = re.findall(pattern, text, re.IGNORECASE)
            concepts.extend([match.strip() for match in matches if self._is_valid_concept(match)])

            # Look for phrases where the keyword is a modifier
            # e.g., "learning algorithm", "network architecture", "data model"
            pattern = fr'\b{keyword} [a-zA-Z]+\b'
            matches = re.findall(pattern, text, re.IGNORECASE)
            concepts.extend([match.strip() for match in matches if self._is_valid_concept(match)])

        # Extract multi-word technical terms (2-3 words)
        # This catches phrases like "artificial neural network", "deep learning model"
        multi_word_patterns = [
            r'\b[A-Za-z]+ [A-Za-z]+ [A-Za-z]+\b',  # 3-word phrases
            r'\b[A-Za-z]+ [A-Za-z]+\b'             # 2-word phrases
        ]

        for pattern in multi_word_patterns:
            matches = re.findall(pattern, text)
            # Filter matches to only include those with technical relevance
            for match in matches:
                match = match.strip()
                # Check if the phrase contains any technical keywords or is capitalized
                if (any(keyword in match.lower() for keyword in tech_keywords) or
                    match[0].isupper()) and self._is_valid_concept(match):
                    concepts.append(match)

        # Extract acronyms that might be technical terms
        acronyms = re.findall(r'\b[A-Z]{2,5}\b', text)
        concepts.extend([acronym for acronym in acronyms if len(acronym) >= 2])

        # Remove duplicates and normalize
        unique_concepts = set()
        normalized_concepts = []

        for concept in concepts:
            # Normalize concept (capitalize first letter of each word)
            words = concept.split()
            normalized = ' '.join(word.capitalize() if not word.isupper() else word for word in words)

            # Add to list if not already present
            if normalized.lower() not in unique_concepts:
                unique_concepts.add(normalized.lower())
                normalized_concepts.append(normalized)

        # Sort alphabetically
        return sorted(normalized_concepts)

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

    def extract_concepts_llm(self, text: str, max_concepts: int = 10, is_chunk: bool = False) -> List[Dict[str, Any]]:
        """
        Extract concepts using LLM-based approach.

        Args:
            text: Input text
            max_concepts: Maximum number of concepts to extract
            is_chunk: Whether the text is already a chunk (to avoid unnecessary truncation)

        Returns:
            List of extracted concepts with metadata
        """
        # Try using the LLMManager if available
        if llm_manager is not None:
            try:
                return self._extract_concepts_with_llm_manager(text, max_concepts, is_chunk)
            except Exception as e:
                logger.warning(f"Error using LLMManager for concept extraction: {e}")

        # If LLM extraction fails, fall back to NLP-based extraction
        logger.warning("LLM-based extraction not available. Using NLP-based extraction instead.")
        nlp_concepts = self.extract_concepts_nlp(text)
        return [{"concept": c, "relevance": 1.0, "source": "nlp"} for c in nlp_concepts[:max_concepts]]

    def _extract_concepts_with_llm_manager(self, text: str, max_concepts: int = 10, is_chunk: bool = False) -> List[Dict[str, Any]]:
        """
        Extract concepts using LLMManager with improved error handling for template issues.

        Args:
            text: Input text
            max_concepts: Maximum number of concepts to extract
            is_chunk: Whether the text is already a chunk (to avoid unnecessary truncation)

        Returns:
            List of extracted concepts with metadata
        """
        # Truncate text if too long and not already a chunk
        max_text_length = 4000
        if not is_chunk and len(text) > max_text_length:
            truncated_text = text[:max_text_length] + "..."
            logger.info(f"Text truncated from {len(text)} to {max_text_length} characters")
        else:
            # Even if it's a chunk, ensure it's not too large for the LLM
            if len(text) > max_text_length * 2:  # Allow chunks to be larger, but not excessively
                truncated_text = text[:max_text_length * 2] + "..."
                logger.info(f"Chunk truncated from {len(text)} to {max_text_length * 2} characters")
            else:
                truncated_text = text

        # Try with generic LLM prompt format
        try:
            # Generic LLM prompt format
            system_prompt = """You are a concept extraction assistant that identifies key technical and domain-specific concepts from text. Your task is to extract important concepts, their relevance, and definitions from the provided text."""

            user_prompt = f"""Extract up to {max_concepts} of the most important domain-specific concepts from the following text.
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

            # Check if llm_manager is None
            if llm_manager is None:
                logger.error("LLM manager is not initialized")
                return []

            # Generate response with generic prompt
            response = llm_manager.generate(
                user_prompt,
                system_prompt=system_prompt,
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

    # OpenAI method removed - we only use local LLM providers

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """
        Split text into smaller chunks for processing using the document processor.

        Args:
            text: Input text
            chunk_size: Maximum size of each chunk in characters
            overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks
        """
        # Import the document processor
        from src.processing.document_processor import smart_chunk_text, optimize_chunk_size

        # Determine optimal chunk size based on document characteristics
        optimal_chunk_size = optimize_chunk_size(text, default_size=chunk_size)

        # Use the smart chunking algorithm from document processor
        return smart_chunk_text(text, chunk_size=optimal_chunk_size, overlap=overlap, semantic_boundaries=True)

    def extract_concepts(self, text: str, method: str = "auto", max_concepts: int = 20) -> List[Dict[str, Any]]:
        """
        Extract concepts from text using the specified method.
        For long texts, chunks the text and processes each chunk separately.

        Args:
            text: Input text
            method: Extraction method ("rule", "nlp", "llm", or "auto")
            max_concepts: Maximum number of concepts to extract

        Returns:
            List of extracted concepts with metadata
        """
        # Determine method based on availability
        if method == "auto":
            if self.use_llm and llm_manager is not None:
                method = "llm"
            elif self.use_nlp and nlp is not None:
                method = "nlp"
            else:
                method = "rule"

:start_line:534
-------
        # Log the text length and method
:start_line:537
-------
:start_line:539
-------
:start_line:539
-------
:start_line:541
-------
:start_line:543
-------
:start_line:545
-------
:start_line:547
-------
:start_line:549
-------
:start_line:551
-------
:start_line:553
-------
:start_line:555
-------
:start_line:557
-------
:start_line:559
-------
:start_line:561
-------
:start_line:563
-------
:start_line:565
-------
:start_line:567
-------
:start_line:569
-------
:start_line:571
-------
:start_line:573
-------
:start_line:575
-------
:start_line:577
-------
:start_line:579
-------
:start_line:581
-------
:start_line:583
-------
:start_line:585
-------
        text_length = len(text)
        logger.info(f"ConceptExtractor: Extracting concepts from text of length {text_length} using method: {method}")

        # For LLM method, always chunk the text for consistent processing
        if method == "llm" and self.use_llm:
            # Determine appropriate chunk size based on text length
            if text_length > 50000:  # Very large document
                chunk_size = 1000
                overlap = 100
            elif text_length > 10000:  # Large document
                chunk_size = 1500
                overlap = 150
            else:  # Smaller document
                chunk_size = 2000
                overlap = 200

            # For very small texts, don't chunk
            if text_length <= 3000:
                logger.info(f"Text is small ({text_length} chars), processing as a single chunk")
                return self.extract_concepts_llm(text, max_concepts)

            logger.info(f"Chunking text of {text_length} chars with chunk_size={chunk_size}, overlap={overlap}")

            # Chunk the text using the document processor
            chunks = self._chunk_text(text, chunk_size=chunk_size, overlap=overlap)
            logger.info(f"Split text into {len(chunks)} chunks for processing")

            # Process each chunk
            all_concepts = []
            concepts_by_name = {}

            # Calculate concepts per chunk based on total desired concepts
            # Ensure we request more concepts per chunk than we need in total to get good coverage
            concepts_per_chunk = max(5, min(15, max_concepts))
            logger.info(f"Processing {len(chunks)} chunks with {concepts_per_chunk} concepts per chunk")

            for i, chunk in enumerate(chunks):
                logger.info(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")

                try:
                    # Extract concepts from this chunk, indicating it's already a chunk
                    chunk_concepts = self.extract_concepts_llm(chunk, concepts_per_chunk, is_chunk=True)
                    logger.info(f"Extracted {len(chunk_concepts)} concepts from chunk {i+1}")

                    # Merge with existing concepts
                    for concept in chunk_concepts:
                        concept_name = concept["concept"].lower()

                        if concept_name in concepts_by_name:
                            # Update existing concept with higher relevance
                            existing = concepts_by_name[concept_name]
                            existing["relevance"] = max(existing["relevance"], concept["relevance"])

                            # Merge definitions if they're different
                            if concept.get("definition") and concept["definition"] != existing.get("definition", ""):
                                existing["definition"] = (existing.get("definition", "") + " " + concept["definition"]).strip()
                        else:
                            # Add new concept
                            concepts_by_name[concept_name] = concept
                            all_concepts.append(concept)
                except Exception as e:
                    logger.error(f"Error processing chunk {i+1}: {e}")
                    # Continue with other chunks

            # If we didn't get any concepts, fall back to rule-based extraction
            if not all_concepts:
                logger.warning("LLM extraction failed to produce concepts, falling back to rule-based extraction")
                concepts = self.extract_concepts_rule_based(text)
                return [{"concept": c, "relevance": 1.0, "source": "rule"} for c in concepts[:max_concepts]]

            # Sort by relevance and limit to max_concepts
            all_concepts.sort(key=lambda x: x.get("relevance", 0), reverse=True)
            return all_concepts[:max_concepts]

        # For NLP method
        elif method == "nlp" and self.use_nlp and nlp is not None:
            # For very large texts, chunk and process separately
            if text_length > 100000:
                logger.info(f"Text is very large ({text_length} chars), chunking for NLP processing")
                chunks = self._chunk_text(text, chunk_size=50000, overlap=1000)

                all_concepts = []
                for i, chunk in enumerate(chunks):
                    chunk_concepts = self.extract_concepts_nlp(chunk)
                    all_concepts.extend(chunk_concepts)

                # Remove duplicates and sort by frequency
                from collections import Counter
                concept_counter = Counter(all_concepts)
                unique_concepts = [concept for concept, _ in concept_counter.most_common(max_concepts)]

                return [{"concept": c, "relevance": 1.0, "source": "nlp"} for c in unique_concepts]
            else:
                concepts = self.extract_concepts_nlp(text)
                return [{"concept": c, "relevance": 1.0, "source": "nlp"} for c in concepts[:max_concepts]]

        # For rule-based method
        else:
            concepts = self.extract_concepts_rule_based(text)
            return [{"concept": c, "relevance": 1.0, "source": "rule"} for c in concepts[:max_concepts]]

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