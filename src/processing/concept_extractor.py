"""Concept extraction utilities for GraphRAG project.

This module provides utilities for extracting concepts from text using:
1. Rule-based extraction
2. NLP-based extraction
3. LLM-based extraction (using the LLMManager from src.llm.llm_provider)

Note: This module is being refactored to use the LLMManager from src.llm.llm_provider
instead of direct OpenAI API calls. The old implementation is deprecated and will be
removed in a future version.
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

# Import LLM integration
from src.llm.llm_provider import LLMManager, create_llm_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# We'll use only rule-based extraction since spaCy has compatibility issues
SPACY_AVAILABLE = False
nlp = None

# Load domain-specific stopwords
DOMAIN_STOPWORDS = {
    "general": {
        "the",
        "and",
        "a",
        "an",
        "in",
        "on",
        "at",
        "to",
        "for",
        "with",
        "by",
        "about",
        "like",
        "through",
        "over",
        "before",
        "after",
        "between",
        "under",
        "during",
        "without",
        "of",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "can",
        "could",
        "will",
        "would",
        "shall",
        "should",
        "may",
        "might",
        "must",
        "part",  # Added "part"
        "this",
        "that",
        "these",
        "those",
        "it",
        "they",
        "them",
        "their",
        "he",
        "she",
        "him",
        "her",
        "his",
        "hers",
        "its",
        "theirs",
        "we",
        "us",
        "our",
        "ours",
        "you",
        "your",
        "yours",
        "i",
        "me",
        "my",
        "mine",
    },
    "tech": {
        "use",
        "using",
        "used",
        "user",
        "users",
        "system",
        "systems",
        "data",
        "information",
        "process",
        "processes",
        "method",
        "methods",
        "function",
        "functions",
        "value",
        "values",
        "example",
        "examples",
        "result",
        "results",
        "figure",
        "figures",
        "table",
        "tables",
        "section",
        "sections",
        "chapter",
        "chapters",
        "page",
        "pages",
        "see",
        "shown",
        "show",
        "shows",
        "showing",
        "note",
        "notes",
        "describe",
        "describes",
        "described",
        "describing",
        "description",
        "represent",
        "represents",
        "represented",
        "representing",
        "representation",
    },
    "academic": {
        "paper",
        "papers",
        "study",
        "studies",
        "research",
        "researcher",
        "researchers",
        "analysis",
        "analyze",
        "analyzed",
        "analyzing",
        "experiment",
        "experiments",
        "experimental",
        "theory",
        "theories",
        "theoretical",
        "hypothesis",
        "hypotheses",
        "method",
        "methods",
        "methodology",
        "methodologies",
        "approach",
        "approaches",
        "framework",
        "frameworks",
        "model",
        "models",
        "modeling",
        "modelling",
        "simulation",
        "simulations",
        "algorithm",
        "algorithms",
        "implementation",
        "implementations",
        "evaluation",
        "evaluations",
        "evaluate",
        "evaluated",
        "evaluating",
        "performance",
        "performances",
        "result",
        "results",
        "conclusion",
        "conclusions",
        "future",
        "work",
    },
}


def load_llm_config(config_path: str | None = None) -> dict[str, Any]:
    """Load LLM configuration from file.

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
        with open(config_path) as f:
            config = json.load(f)
    except Exception as e:
        logger.warning(
            f"Error loading LLM config from {config_path}: {e}. Falling back to default config."
        )
        # Return default config
        config = {
            "_comment": "To use OpenRouter for concept extraction, replace OPENROUTER_API_KEY with your actual API key from https://openrouter.ai/",
            "primary_provider": {
                "type": "openrouter",
                "api_key": "OPENROUTER_API_KEY",  # Placeholder
                "model": "google/gemini-2.0-flash-exp:free",
                "temperature": 0.1,
                "max_tokens": 1000,
                "timeout": 60,
            },
            "embedding_provider": {
                "type": "ollama",
                "api_base": "http://localhost:11434",
                "model": "snowflake-arctic-embed2:latest",
                "timeout": 60,
            },
        }

    # Specifically adjust for OpenRouter API key if it's the primary provider
    primary_provider_config = config.get("primary_provider", {})
    if primary_provider_config.get("type") == "openrouter":
        env_api_key = os.getenv("OPENROUTER_API_KEY")
        # Get key from config, which might be the placeholder if default was used
        config_api_key = primary_provider_config.get("api_key")

        if env_api_key:
            primary_provider_config["api_key"] = env_api_key
            logger.info(
                "Using OpenRouter API key from OPENROUTER_API_KEY environment variable."
            )
        elif config_api_key == "OPENROUTER_API_KEY" or not config_api_key:
            logger.warning(
                "OpenRouter API key is a placeholder or missing in LLM configuration, "
                "and OPENROUTER_API_KEY environment variable is not set. "
                "OpenRouter will be effectively disabled or fail if used."
            )
            primary_provider_config["api_key"] = ""  # Ensure placeholder is not used
        # If config_api_key is present and not the placeholder, and no env var, it will be used.

    return config


def setup_llm_manager(config: dict[str, Any]) -> LLMManager | None:
    """Set up LLM manager from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        LLM manager instance or None if setup fails

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
        return None

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


# Initialize LLM manager
llm_manager = None

# Try to initialize LLM manager
try:
    config = load_llm_config()
    llm_manager = setup_llm_manager(config)
    if llm_manager:
        logger.info("Initialized LLM manager for concept extraction")
    else:
        logger.warning(
            "Failed to initialize LLM manager. LLM-based concept extraction will use fallback methods."
        )
except Exception as e:
    logger.warning(f"Error initializing LLM manager: {e}")

# We only use local LLM providers, not OpenAI
OPENAI_AVAILABLE = False
openai_client = None
logger.info("Using local LLM providers for concept extraction.")


class ConceptExtractor:
    """Concept extraction for GraphRAG project.

    This class provides methods for extracting concepts from text using
    various techniques, from simple rule-based extraction to more
    sophisticated NLP and LLM-based approaches.
    """

    def __init__(
        self,
        use_nlp: bool = True,
        use_llm: bool = False,
        domain: str = "general",
        min_concept_length: int = 2,
        max_concept_length: int = 5,
    ) -> None:
        """Initialize concept extractor.

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

        # Load and compile domain-specific concept patterns
        raw_domain_patterns = self._load_domain_patterns(domain)
        self.compiled_domain_patterns = [
            re.compile(p, re.IGNORECASE) for p in raw_domain_patterns
        ]

        # General patterns for compound nouns and hyphenated terms
        self.compound_noun_pattern_str = r"\b([A-Z][a-zA-Z]*(?:\s+[A-Z][a-zA-Z]*)+)\b"  # Matches sequences of capitalized words
        self.hyphenated_term_pattern_str = r"\b([a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)+)\b"
        # Pattern for acronyms (e.g., NLP, AI, LLM)
        self.acronym_pattern_str = r"\b([A-Z]{2,})\b"

        self.compiled_compound_noun_pattern = re.compile(self.compound_noun_pattern_str)
        self.compiled_hyphenated_term_pattern = re.compile(
            self.hyphenated_term_pattern_str
        )
        self.compiled_acronym_pattern = re.compile(self.acronym_pattern_str)

        # Basic pattern for single or multiple words (potential concepts)
        # This will be used as a fallback and then filtered
        self.general_term_pattern_str = r"\b([a-zA-Z][a-zA-Z0-9]*(?:\s+[a-zA-Z][a-zA-Z0-9]*){0,3})\b"  # Up to 4 words
        self.compiled_general_term_pattern = re.compile(
            self.general_term_pattern_str, re.IGNORECASE
        )

    def _load_domain_patterns(self, domain: str) -> list[str]:
        """Load domain-specific concept patterns.

        Args:
            domain: Domain name

        Returns:
            List of regex patterns for the domain

        """
        # Default patterns for technical concepts
        patterns = [
            # General ML/AI
            r"\b[A-Z][a-z]+ (Learning|Network|Model|Algorithm|System|Framework|Technique|Approach)\b",
            r"\b(Deep|Machine|Reinforcement|Supervised|Unsupervised|Self-supervised|Federated) Learning\b",
            r"\b(Artificial Intelligence|AI|Machine Learning|ML|Deep Learning|DL)\b",
            r"\b(Neural Network(?:s)?|NN)\b",
            r"\b(Decision Tree(?:s)?|Random Forest(?:s)?|Support Vector Machine(?:s)?|SVM|Gradient Boosting)\b",
            r"\b(Natural Language Processing|NLP|Computer Vision|CV)\b",
            r"\b(Large Language Model(?:s)?|LLM(?:s)?|Generative AI|GenAI)\b",
            r"\b(Transformer(?: Model)?|Attention Mechanism|Self-Attention)\b",
            r"\b(Embedding(?:s)?|Tokenization|Vector Database(?:s)?)\b",
            # Broader Tech
            r"\b(Industry 4\.0|Industry 5\.0|Internet of Things|IoT)\b",
            r"\b(Big Data|Data Mining|Data Science|Data Analysis)\b",
            r"\b(Cloud Computing|Edge Computing|Fog Computing)\b",
            r"\b(Blockchain|Cryptocurrency|Smart Contract(?:s)?)\b",
            r"\b(Quantum Computing|Quantum Supremacy)\b",
            r"\b(Cybersecurity|Network Security|Information Security)\b",
            r"\b(Virtual Reality|VR|Augmented Reality|AR|Mixed Reality|MR)\b",
            r"\b(Robotic Process Automation|RPA)\b",
            # Specific tools/frameworks - can be expanded or loaded from config
            r"\b(TensorFlow|PyTorch|Keras|Scikit-learn)\b",
            r"\b(Apache Spark|Apache Hadoop)\b",
            r"\b(Docker|Kubernetes)\b",
        ]

        # Domain-specific additions (example for 'academic')
        if domain == "academic":
            patterns.extend(
                [
                    r"\b(Literature Review|Systematic Review)\b",
                    r"\b(Case Study|Empirical Study)\b",
                    r"\b(Statistical Analysis|Hypothesis Testing)\b",
                ]
            )
        elif domain == "finance":  # Example of another domain
            patterns.extend(
                [
                    r"\b(Algorithmic Trading|High-Frequency Trading)\b",
                    r"\b(Risk Management|Credit Scoring)\b",
                    r"\b(FinTech|Regulatory Technology|RegTech)\b",
                ]
            )

        # TODO: Load patterns from a configuration file based on domain for more flexibility
        return patterns

    def _normalize_plural(self, term: str) -> str:
        """Attempt to normalize plural forms to singular.
        This is a simple heuristic and may not cover all cases or be perfectly accurate.
        """
        lower_term = term.lower()
        if len(lower_term) < 3:  # Avoid processing very short terms like "is", "as"
            return term

        if lower_term.endswith("ies"):
            if (
                len(lower_term) > 3 and lower_term[-4].lower() not in "aeiou"
            ):  # e.g., 'studies' -> 'study'
                # Preserve case of the letter before 'y'
                return term[:-3] + ("Y" if term[-3].isupper() else "y")
        elif lower_term.endswith(
            "ses"
        ):  # e.g., 'processes' -> 'process', 'gases' -> 'gas'
            if lower_term.endswith("sses"):  # e.g. 'glasses' -> 'glass'
                return term[:-2]
            # Avoid 'analysis', 'basis', etc. - these are often singular or have irregular plurals
            # Check common irregulars that end in 'ses' if they are singular
            if lower_term not in [
                "analyses",
                "bases",
                "crises",
                "diagnoses",
                "ellipses",
                "hypotheses",
                "oases",
                "paralyses",
                "parentheses",
                "synopses",
                "syntheses",
                "theses",
                "series",
                "species",
            ]:
                # if it was 'processes' -> 'process'
                if (
                    len(term) > 1 and term[:-1].lower() + "s" == lower_term
                ):  # check if removing s makes sense
                    return term[:-1]
                # if it was 'gases' -> 'gas'
                elif (
                    len(term) > 2 and term[:-2].lower() + "es" == lower_term
                ):  # check if removing es makes sense
                    return term[:-2]

        elif lower_term.endswith("es"):
            # e.g., 'boxes' -> 'box', 'wishes' -> 'wish'
            # Avoid 'series', 'species', 'clothes', 'mathematics', 'physics', 'news'
            # also avoid common verbs like 'goes', 'does'
            if lower_term not in [
                "series",
                "species",
                "clothes",
                "mathematics",
                "physics",
                "news",
                "goes",
                "does",
            ]:
                if len(lower_term) > 2 and (
                    lower_term.endswith("xes")
                    or lower_term.endswith("shes")
                    or lower_term.endswith("ches")
                    or lower_term.endswith("oes")
                ):
                    # Check if removing 'es' leaves a valid word structure, very heuristic
                    if len(term[:-2]) > 1:  # Avoid 'he' -> 'h'
                        return term[:-2]

        # General 's' removal, avoid possessives and double 's'
        if (
            lower_term.endswith("s")
            and not lower_term.endswith("ss")
            and not lower_term.endswith("us")
        ):  # avoid 'class', 'bus'
            # Avoid possessives like 'it's' or words like 'analysis'
            if "'" not in term and len(term[:-1]) > 1:  # Ensure base is not too short
                # Check if base form is substantially different or too short
                if len(term[:-1]) >= (
                    self.min_concept_length - 1 if self.min_concept_length > 1 else 1
                ):  # Allow shorter base if min_concept_length is 1
                    # A simple check: if removing 's' results in a word in stopwords, it might be a verb (e.g. "uses" -> "use")
                    # This is imperfect. For now, just remove 's'.
                    return term[:-1]
        return term

    def extract_concepts_rule_based(self, text: str) -> list[str]:
        """Extract concepts using rule-based approach.

        This method applies a series of regular expressions to identify
        potential concepts. It prioritizes domain-specific patterns and
        then applies more general ones.

        Steps:
        1. Preprocess text (e.g., normalize whitespace).
        2. Apply compiled regex patterns (domain-specific, compound, hyphenated, acronyms).
        3. Apply a general term pattern as a fallback.
        4. Normalize extracted concepts (e.g., lowercase, handle plurals).
        5. Filter concepts based on length, stopwords, and validity using _is_valid_concept.
        6. Return a list of unique, valid concepts.
        """
        if not text:
            return []

        processed_text = re.sub(r"\s+", " ", text).strip()
        extracted_phrases = set()

        # --- Apply Compiled Patterns ---
        # 1. Domain-specific patterns (most specific)
        # These patterns are already compiled with re.IGNORECASE in __init__
        for pattern_obj in self.compiled_domain_patterns:
            try:
                matches = pattern_obj.findall(processed_text)
                for match in matches:
                    if isinstance(match, tuple):
                        # Handle patterns that return multiple groups, join non-empty ones
                        phrase = " ".join(m for m in match if m and m.strip()).strip()
                    elif isinstance(match, str):
                        phrase = match.strip()
                    else:
                        continue  # Should not happen with findall if pattern is valid
                    if phrase:
                        extracted_phrases.add(phrase)
            except re.error as e:
                logger.warning(
                    f"Regex error with domain pattern {pattern_obj.pattern}: {e}"
                )

        # 2. Compound Noun Pattern (Capitalized sequences)
        # This pattern is compiled without IGNORECASE to respect capitalization
        try:
            matches = self.compiled_compound_noun_pattern.findall(processed_text)
            for match in matches:  # This pattern returns a single string match
                if isinstance(match, str) and match.strip():
                    extracted_phrases.add(match.strip())
        except re.error as e:
            logger.warning(f"Regex error with compound noun pattern: {e}")

        # 3. Hyphenated Term Pattern
        # This pattern is compiled without IGNORECASE by default, can be made case-insensitive if needed
        try:
            matches = self.compiled_hyphenated_term_pattern.findall(processed_text)
            for match in matches:  # This pattern returns a single string match
                if isinstance(match, str) and match.strip():
                    extracted_phrases.add(match.strip())
        except re.error as e:
            logger.warning(f"Regex error with hyphenated term pattern: {e}")

        # 4. Acronym Pattern (e.g., NLP, AI, LLM)
        # This pattern is compiled without IGNORECASE to match uppercase acronyms
        try:
            matches = self.compiled_acronym_pattern.findall(processed_text)
            for match in matches:  # This pattern returns a single string match
                if (
                    isinstance(match, str) and match.strip() and len(match) > 1
                ):  # Ensure it's a multi-letter acronym
                    extracted_phrases.add(match.strip())
        except re.error as e:
            logger.warning(f"Regex error with acronym pattern: {e}")

        # 5. General Term Pattern (as a fallback, compiled with IGNORECASE)
        # This helps catch terms not covered by specific patterns.
        try:
            matches = self.compiled_general_term_pattern.findall(processed_text)
            for (
                match_candidate
            ) in matches:  # This pattern returns a single string match
                if isinstance(match_candidate, str) and match_candidate.strip():
                    extracted_phrases.add(match_candidate.strip())
        except re.error as e:
            logger.warning(f"Regex error with general term pattern: {e}")

        # --- Normalization and Filtering ---
        final_concepts = set()
        for phrase in extracted_phrases:
            # Strip whitespace again in case any pattern left some
            cleaned_phrase = phrase.strip()
            if not cleaned_phrase:
                continue

            # Attempt plural normalization.
            # For multi-word phrases, normalize the last word.
            # For single-word phrases, normalize the word itself.
            words = cleaned_phrase.split()
            if len(words) > 0:  # Ensure there are words to process
                if len(words) > 1:
                    # Try normalizing the last word of a multi-word phrase
                    last_word_normalized = self._normalize_plural(words[-1])
                    # Reconstruct the phrase only if normalization changed the last word and it's not empty
                    if (
                        last_word_normalized
                        and last_word_normalized.lower() != words[-1].lower()
                    ):
                        normalized_phrase_str = " ".join(
                            words[:-1] + [last_word_normalized]
                        )
                    else:  # No change or empty result, keep original
                        normalized_phrase_str = cleaned_phrase
                else:  # Single word phrase
                    normalized_phrase_str = self._normalize_plural(cleaned_phrase)
            else:  # Should not happen if cleaned_phrase is not empty
                normalized_phrase_str = cleaned_phrase

            # Use _is_valid_concept for filtering (length, stopwords etc.)
            # It's assumed _is_valid_concept handles its own casing logic for checks.
            if self._is_valid_concept(normalized_phrase_str):
                # Add the version that _is_valid_concept approved, then lowercase for set uniqueness.
                final_concepts.add(normalized_phrase_str.lower())
            # Fallback: if normalized version is not valid, check original cleaned phrase
            elif self._is_valid_concept(cleaned_phrase):
                final_concepts.add(cleaned_phrase.lower())

        return sorted(list(final_concepts))

    def extract_concepts_nlp(self, text: str) -> list[str]:
        """Extract concepts using NLP-based approach with spaCy.

        Args:
            text: Input text

        Returns:
            List of extracted concepts

        """
        if not self.use_nlp or nlp is None:
            logger.warning(
                "NLP-based extraction not available. Using rule-based extraction instead."
            )
            return self.extract_concepts_rule_based(text)

        concepts = []

        # Process text with spaCy
        doc = nlp(text)  # type: ignore

        # Extract noun chunks as potential concepts
        if hasattr(doc, "noun_chunks"):
            for chunk in doc.noun_chunks:  # type: ignore
                if self._is_valid_concept(chunk.text):
                    concepts.append(chunk.text)

        # Extract named entities as potential concepts
        if hasattr(doc, "ents"):
            for ent in doc.ents:  # type: ignore
                if ent.label_ in [
                    "ORG",
                    "PRODUCT",
                    "WORK_OF_ART",
                    "LAW",
                    "LANGUAGE",
                    "EVENT",
                    "FAC",
                ] and self._is_valid_concept(ent.text):
                    concepts.append(ent.text)

        # Extract technical terms using dependency parsing
        for token in doc:  # type: ignore
            # Look for compound noun phrases that might be technical terms
            if token.dep_ == "compound" and token.head.pos_ == "NOUN":
                compound_term = f"{token.text} {token.head.text}"
                if self._is_valid_concept(compound_term):
                    concepts.append(compound_term)

        # Remove duplicates and sort
        return sorted(list(set(concepts)))

    def extract_concepts_llm(
        self, text: str, max_concepts: int = 10
    ) -> dict[str, list[dict[str, Any]]]:
        """Extract concepts and relationships using the two-pass LLM-based approach.

        Args:
            text: Input text
            max_concepts: (Illustrative, actual concept count managed by two-pass logic)

        Returns:
            A dictionary containing 'concepts' and 'relationships'.

        """
        if llm_manager is not None:
            try:
                return self._extract_concepts_and_relationships_with_llm_manager(text)
            except Exception as e:
                logger.warning(
                    f"Error using LLMManager for two-pass concept extraction: {e}"
                )
                return {"concepts": [], "relationships": []}
        else:
            logger.warning(
                "LLM-based extraction not available. Cannot perform two-pass extraction."
            )
            return {"concepts": [], "relationships": []}

    def _llm_pass1_extract_concepts_from_chunk(
        self, text_chunk: str
    ) -> list[dict[str, Any]]:
        """Pass 1: Extract concepts from a single text chunk using LLM."""
        max_text_length = 3000  # Max length for a chunk to send to LLM
        truncated_text = (
            text_chunk[:max_text_length] + "..."
            if len(text_chunk) > max_text_length
            else text_chunk
        )

        prompt = f"""
        Extract the most important concepts from the following text.
        For each concept, provide:
        1. The concept name (name)
        2. The concept type (type) - e.g., TECHNOLOGY, PERSON, ORGANIZATION, PROCESS, ABSTRACT_IDEA, METRIC, FEATURE, ALGORITHM, DATA_STRUCTURE, ETC.
        3. A brief description based on the context (description)
        4. Related concepts mentioned *within this text chunk* (related_concepts) - list of strings, ensure these are actual concept names.

        Format the output as a JSON array of objects with the following structure:
        [
            {{
                "name": "concept_name",
                "type": "concept_type",
                "description": "brief_description_from_chunk",
                "related_concepts": ["related_concept_in_chunk_1", "related_concept_in_chunk_2"]
            }}
        ]
        Focus on identifying technical and domain-specific concepts that are truly relevant to this text chunk.
        Ensure the 'name' is concise and accurately represents the core idea.
        The 'description' should be specific to how the concept is presented in this chunk.
        If no concepts are found, return an empty array [].

        TEXT CHUNK:
        {truncated_text}
        """
        system_prompt = "You are an expert in knowledge extraction and ontology creation. Your task is to identify key concepts from the provided text chunk."

        if llm_manager is None:
            logger.error("LLM manager is not initialized for Pass 1.")
            return []
        try:
            response = llm_manager.generate(
                prompt, system_prompt=system_prompt, max_tokens=2000
            )
            if response.startswith("Error:") or response.startswith("API Response:"):
                logger.warning(
                    f"LLM error during Pass 1 concept extraction: {response}"
                )
                return []
            return self._parse_llm_json_response(response)
        except Exception as e:
            logger.error(f"Exception during Pass 1 concept extraction: {e}")
            return []

    def _llm_pass2_analyze_relationships(
        self, concepts: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Pass 2: Analyze relationships between a list of unique concepts using LLM."""
        concept_names = [
            concept["name"]
            for concept in concepts
            if isinstance(concept, dict)
            and "name" in concept
            and isinstance(concept["name"], str)
        ]
        if not concept_names:
            logger.info(
                "Pass 2: No valid concept names provided for relationship analysis."
            )
            return []

        max_concepts_for_analysis = 25
        if len(concept_names) > max_concepts_for_analysis:
            logger.info(
                f"Limiting relationship analysis to first {max_concepts_for_analysis} of {len(concept_names)} unique concepts."
            )
            concept_names_for_prompt = concept_names[:max_concepts_for_analysis]
        else:
            concept_names_for_prompt = concept_names

        prompt = f"""
        Analyze the relationships between the following concepts, which were extracted from a larger document:
        {", ".join(concept_names_for_prompt)}

        For each meaningful pair of related concepts from the list, identify:
        1. The source concept name (source) - must be one of the provided concept names.
        2. The target concept name (target) - must be one of the provided concept names.
        3. The specific semantic relationship type (type) - see suggested types below.
        4. The relationship strength (strength) - a value between 0.1 (weak) and 1.0 (direct, essential).
        5. A brief description of the relationship (description) explaining the connection and strength.

        Suggested semantic relationship types (use these or similar, be specific):
        - IS_A / TYPE_OF / SUBCLASS_OF (hierarchical)
        - PART_OF / HAS_PART / CONTAINS_COMPONENT (compositional)
        - USES / USED_FOR / APPLIES_TO / PURPOSE_IS (functional)
        - IMPLEMENTS / EMPLOYS_TECHNIQUE / BASED_ON_ALGORITHM (implementation/methodology)
        - HAS_PROPERTY / CHARACTERIZED_BY / ATTRIBUTE_OF (characteristics)
        - CAUSES / INFLUENCES / LEADS_TO (causal)
        - PRECEDES / FOLLOWS / STEP_IN (sequential)
        - COMPARES_TO / CONTRASTS_WITH / ANALOGOUS_TO (comparative)
        - INTERACTS_WITH / DEPENDS_ON / REQUIRES (dependency/interaction)
        - RELATED_TO (use as a last resort if no other type fits well)

        Format the output as a JSON array of objects:
        [
            {{
                "source": "source_concept_name",
                "target": "target_concept_name",
                "type": "relationship_type",
                "strength": 0.8,
                "description": "Description of why these concepts are related and why this strength."
            }}
        ]
        If no relationships are found, return an empty array [].
        Only include relationships that are clearly supported or implied by general knowledge about these concepts.
        Focus on quality and relevance of relationships. Ensure 'source' and 'target' are from the provided list.
        """
        system_prompt = "You are an expert in knowledge graph construction and semantic relationship analysis. Identify precise and meaningful relationships."

        if llm_manager is None:
            logger.error("LLM manager is not initialized for Pass 2.")
            return []
        try:
            response = llm_manager.generate(
                prompt, system_prompt=system_prompt, max_tokens=3000
            )
            if response.startswith("Error:") or response.startswith("API Response:"):
                logger.warning(
                    f"LLM error during Pass 2 relationship analysis: {response}"
                )
                return []
            return self._parse_llm_json_response(response)
        except Exception as e:
            logger.error(f"Exception during Pass 2 relationship analysis: {e}")
            return []

    def _parse_llm_json_response(self, response: str) -> list[dict[str, Any]]:
        """Parse JSON array from LLM response string.
        Handles cases where JSON might be embedded or be a single object.
        """
        try:
            # Attempt to find and parse a JSON array first
            json_array_start = response.find("[")
            json_array_end = response.rfind("]") + 1
            if json_array_start != -1 and json_array_end > json_array_start:
                json_str = response[json_array_start:json_array_end]
                parsed_data = json.loads(json_str)
                if isinstance(parsed_data, list):
                    return [
                        item for item in parsed_data if isinstance(item, dict)
                    ]  # Filter for dicts
                else:
                    logger.warning(
                        f"Parsed JSON from array markers is not a list. Got: {type(parsed_data)}. Response: {response[:200]}..."
                    )

            json_obj_start = response.find("{")
            json_obj_end = response.rfind("}") + 1
            if json_obj_start != -1 and json_obj_end > json_obj_start:
                json_str = response[json_obj_start:json_obj_end]
                parsed_data = json.loads(json_str)
                if isinstance(parsed_data, dict):
                    return [parsed_data]
                elif isinstance(parsed_data, list):
                    return [item for item in parsed_data if isinstance(item, dict)]
                else:
                    logger.warning(
                        f"Parsed JSON from object markers is not a dict or list. Got: {type(parsed_data)}. Response: {response[:200]}..."
                    )

            logger.debug(
                f"Could not find valid JSON array or object in LLM response: {response[:200]}..."
            )
            return []
        except json.JSONDecodeError:
            logger.warning(
                f"Failed to parse JSON from LLM response: {response[:200]}..."
            )
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM response: {e}")
            return []

    def _extract_concepts_and_relationships_with_llm_manager(
        self, text: str
    ) -> dict[str, list[dict[str, Any]]]:
        """Orchestrates the two-pass LLM concept and relationship extraction."""
        if llm_manager is None:
            logger.error(
                "LLM manager is not initialized. Cannot perform two-pass extraction."
            )
            return {"concepts": [], "relationships": []}

        chunks = self._chunk_text(text, chunk_size=2500, overlap=300)
        logger.info(
            f"Split document into {len(chunks)} chunks for two-pass LLM extraction."
        )

        all_chunk_concepts: list[dict[str, Any]] = []
        for i, chunk_text_item in enumerate(chunks):
            logger.info(
                f"Processing chunk {i + 1}/{len(chunks)} for Pass 1 concept extraction ({len(chunk_text_item)} chars)."
            )
            chunk_concepts = self._llm_pass1_extract_concepts_from_chunk(
                chunk_text_item
            )
            for concept in chunk_concepts:
                if isinstance(concept, dict):
                    concept["source_chunk_index"] = i
                    all_chunk_concepts.append(concept)
                else:
                    logger.warning(
                        f"Skipping non-dict item from Pass 1 chunk {i + 1}: {concept}"
                    )

        logger.info(
            f"Pass 1: Extracted {len(all_chunk_concepts)} raw concepts in total from all chunks."
        )

        unique_concepts_map: dict[str, dict[str, Any]] = {}
        for concept_item in all_chunk_concepts:
            if (
                not isinstance(concept_item, dict)
                or "name" not in concept_item
                or not isinstance(concept_item["name"], str)
            ):
                logger.warning(
                    f"Skipping invalid concept data during deduplication: {concept_item}"
                )
                continue

            name_lower = concept_item["name"].lower()
            if name_lower not in unique_concepts_map:
                unique_concepts_map[name_lower] = concept_item.copy()
            else:
                existing_concept = unique_concepts_map[name_lower]
                new_desc = concept_item.get("description", "")
                if new_desc and new_desc not in existing_concept.get("description", ""):
                    existing_concept["description"] = (
                        existing_concept.get("description", "") + "; " + new_desc
                    ).strip("; ")

                new_related = concept_item.get("related_concepts", [])
                if isinstance(new_related, list):
                    existing_related_set = set(
                        existing_concept.get("related_concepts", [])
                    )
                    existing_related_set.update(
                        r_concept
                        for r_concept in new_related
                        if isinstance(r_concept, str)
                    )
                    existing_concept["related_concepts"] = list(existing_related_set)

                current_chunk_idx = concept_item.get("source_chunk_index")
                if "source_chunk_indices" not in existing_concept:
                    first_occurrence_idx = existing_concept.get("source_chunk_index")
                    existing_concept["source_chunk_indices"] = (
                        [first_occurrence_idx]
                        if first_occurrence_idx is not None
                        else []
                    )

                if (
                    current_chunk_idx is not None
                    and current_chunk_idx
                    not in existing_concept["source_chunk_indices"]
                ):
                    existing_concept["source_chunk_indices"].append(current_chunk_idx)

        deduplicated_concepts_list = list(unique_concepts_map.values())
        for concept in deduplicated_concepts_list:
            concept.pop("source_chunk_index", None)

        logger.info(
            f"Pass 1: Consolidated to {len(deduplicated_concepts_list)} unique concepts."
        )

        relationships: list[dict[str, Any]] = []
        if deduplicated_concepts_list:
            logger.info(
                f"Starting Pass 2: Analyzing relationships among {len(deduplicated_concepts_list)} unique concepts."
            )
            relationships = self._llm_pass2_analyze_relationships(
                deduplicated_concepts_list
            )
            logger.info(f"Pass 2: Identified {len(relationships)} relationships.")
        else:
            logger.info(
                "Skipping Pass 2 as no unique concepts were extracted in Pass 1."
            )

        return {"concepts": deduplicated_concepts_list, "relationships": relationships}

    def _chunk_text(
        self, text: str, chunk_size: int = 1000, overlap: int = 100
    ) -> list[str]:
        """Split text into smaller chunks for processing using the document processor.

        Args:
            text: Input text
            chunk_size: Maximum size of each chunk in characters
            overlap: Number of characters to overlap between chunks

        Returns:
            List of text chunks

        """
        # Import the document processor
        from src.processing.document_processor import (
            optimize_chunk_size,
            smart_chunk_text,
        )

        # Determine optimal chunk size based on document characteristics
        optimal_chunk_size = optimize_chunk_size(text, default_size=chunk_size)

        # Use the smart chunking algorithm from document processor
        try:
            raw_chunks = smart_chunk_text(
                text,
                chunk_size=optimal_chunk_size,
                overlap=overlap,
                semantic_boundaries=True,
            )
            # Ensure it's a list of strings
            if isinstance(raw_chunks, list) and all(
                isinstance(c, str) for c in raw_chunks
            ):
                return raw_chunks
            elif isinstance(raw_chunks, list):  # It's a list, but not of strings
                logger.warning(
                    f"smart_chunk_text returned a list containing non-string elements from text (length {len(text)}). Converting all to string."
                )
                return [str(item) for item in raw_chunks]  # Attempt conversion
            else:
                logger.warning(
                    f"smart_chunk_text did not return a list for text (length {len(text)}). Got {type(raw_chunks)}. Returning empty list."
                )
                return []
        except Exception as e:
            logger.error(
                f"Error calling smart_chunk_text for text (length {len(text)}): {e}. Returning empty list.",
                exc_info=True,
            )
            return []

    def extract_concepts(
        self, text: str, method: str = "auto", max_concepts: int = 20
    ) -> dict[str, list[dict[str, Any]]]:
        """Extract concepts and relationships from text using the specified method.

        Args:
            text: Input text
            method: Extraction method ("rule", "nlp", "llm", "auto")
            max_concepts: Maximum number of concepts to extract (primarily for rule/nlp)

        Returns:
            A dictionary with 'concepts' and 'relationships' lists.

        """
        logger.info(
            f"ConceptExtractor: Extracting concepts from text of length {len(text)} using method: {method}, max_concepts: {max_concepts}"
        )

        output: dict[str, list[dict[str, Any]]] = {"concepts": [], "relationships": []}
        chosen_method = method

        if method == "auto":
            if self.use_llm and llm_manager:
                logger.info("Auto method: Selecting LLM-based extraction.")
                chosen_method = "llm"
            elif self.use_nlp:
                logger.info(
                    "Auto method: LLM not available, selecting NLP-based extraction."
                )
                chosen_method = "nlp"
            else:
                logger.info(
                    "Auto method: LLM and NLP not available, selecting rule-based extraction."
                )
                chosen_method = "rule"

        if chosen_method == "llm":
            if self.use_llm and llm_manager:
                llm_output_data = self.extract_concepts_llm(
                    text, max_concepts=max_concepts
                )
                output["concepts"] = llm_output_data.get("concepts", [])
                output["relationships"] = llm_output_data.get("relationships", [])
            else:
                logger.warning(
                    "LLM method selected, but LLM not available. Falling back."
                )
                if self.use_nlp:
                    chosen_method = "nlp"
                    logger.info("Falling back to NLP from LLM.")
                    concepts_list_nlp = self.extract_concepts_nlp(text)
                    output["concepts"] = [
                        {
                            "name": c,
                            "type": "Unknown",
                            "description": "Extracted via NLP (LLM fallback)",
                            "source": "nlp_fallback_llm",
                        }
                        for c in concepts_list_nlp[:max_concepts]
                    ]
                else:
                    chosen_method = "rule"
                    logger.info(
                        "Falling back to rule-based from LLM (NLP unavailable)."
                    )
                    concepts_list_rule = self.extract_concepts_rule_based(text)
                    output["concepts"] = [
                        {
                            "name": c,
                            "type": "Unknown",
                            "description": "Extracted via rule-based (LLM fallback)",
                            "source": "rule_fallback_llm",
                        }
                        for c in concepts_list_rule[:max_concepts]
                    ]
                output["relationships"] = []

        elif chosen_method == "nlp":
            if self.use_nlp:
                concepts_list_nlp = self.extract_concepts_nlp(text)
                output["concepts"] = [
                    {
                        "name": c,
                        "type": "Unknown",
                        "description": "Extracted via NLP",
                        "source": "nlp",
                    }
                    for c in concepts_list_nlp[:max_concepts]
                ]
            else:
                logger.warning(
                    "NLP method selected, but NLP not available. Falling back to rule-based."
                )
                chosen_method = "rule"
                concepts_list_rule = self.extract_concepts_rule_based(text)
                output["concepts"] = [
                    {
                        "name": c,
                        "type": "Unknown",
                        "description": "Extracted via rule-based (NLP fallback)",
                        "source": "rule_fallback_nlp",
                    }
                    for c in concepts_list_rule[:max_concepts]
                ]
            output["relationships"] = []

        elif chosen_method == "rule":
            concepts_list_rule = self.extract_concepts_rule_based(text)
            output["concepts"] = [
                {
                    "name": c,
                    "type": "Unknown",
                    "description": "Extracted via rule-based",
                    "source": "rule",
                }
                for c in concepts_list_rule[:max_concepts]
            ]
            output["relationships"] = []

        else:
            logger.error(
                f"Unknown extraction method resolved: {chosen_method}. Defaulting to rule-based."
            )
            concepts_list_rule = self.extract_concepts_rule_based(text)
            output["concepts"] = [
                {
                    "name": c,
                    "type": "Unknown",
                    "description": "Extracted via rule-based (unknown method fallback)",
                    "source": "rule_fallback_unknown",
                }
                for c in concepts_list_rule[:max_concepts]
            ]
            output["relationships"] = []

        if not isinstance(output.get("concepts"), list):
            output["concepts"] = []
        if not isinstance(output.get("relationships"), list):
            output["relationships"] = []

        if chosen_method != "llm" and len(output["concepts"]) > max_concepts:
            output["concepts"] = output["concepts"][:max_concepts]

        logger.info(
            f"Finalizing extraction: {len(output['concepts'])} concepts and {len(output['relationships'])} relationships using effective method: {chosen_method}."
        )
        return output

    def _is_valid_concept(self, concept: str) -> bool:
        """Check if a concept is valid.

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

        # Check for stopwords
        if any(word.lower() in self.stopwords for word in words):
            return False

        # Check if concept is purely numeric or very short
        if concept.isnumeric() or len(concept) < 3:
            return False

        # Check if concept starts or ends with special characters (allow internal hyphens/apostrophes)
        if not re.match(r"^[a-zA-Z0-9](?:.*[a-zA-Z0-9])?$", concept):
            # This regex allows concepts to start and end with alphanumeric,
            # permitting hyphens, spaces, etc., internally.
            # Example: "state-of-the-art" is valid, but "-concept" or "concept-" is not.
            # A more precise regex might be needed if specific internal characters are problematic.
            if not (concept[0].isalnum() and concept[-1].isalnum()):  # Simpler check
                return False

        # Check for excessive punctuation or non-alphanumeric characters
        # Count non-alphanumeric characters (excluding spaces, hyphens, apostrophes if allowed)
        allowed_internal_chars = {" ", "-", "'"}
        non_alnum_count = sum(
            1
            for char in concept
            if not char.isalnum() and char not in allowed_internal_chars
        )
        if (
            non_alnum_count > len(words) - 1
        ):  # Heuristic: more non-alnum than spaces between words
            return False

        return True

    def weight_concepts(
        self, concepts: list[dict[str, Any]], text: str
    ) -> list[dict[str, Any]]:
        """Weight concepts based on frequency, position, and other heuristics.
        This method is a placeholder and can be expanded.

        Args:
            concepts: List of extracted concepts (dictionaries)
            text: Original text

        Returns:
            List of concepts with updated relevance scores

        """
        # Example: Simple frequency-based weighting
        # This is very basic and would ideally be more sophisticated

        # Ensure concepts have 'name' and 'relevance'
        valid_concepts = []
        for concept_data in concepts:
            if isinstance(concept_data, dict) and "name" in concept_data:
                # Ensure 'relevance' exists, default to a base value if not
                if "relevance" not in concept_data:
                    concept_data["relevance"] = 0.5  # Default base relevance
                valid_concepts.append(concept_data)
            elif isinstance(concept_data, str):  # Handle if list of strings was passed
                valid_concepts.append(
                    {
                        "name": concept_data,
                        "relevance": 0.5,
                        "source": "unknown_str_to_dict",
                    }
                )

        text_lower = text.lower()
        for concept_data in valid_concepts:
            concept_name_lower = concept_data["name"].lower()
            try:
                # Basic frequency count
                frequency = text_lower.count(concept_name_lower)
                # Adjust relevance based on frequency (simple example)
                if frequency > 1:
                    concept_data["relevance"] = min(
                        1.0, concept_data.get("relevance", 0.5) + (frequency * 0.05)
                    )

                # Positional bonus (e.g., if in the first 20% of text)
                if text_lower.find(concept_name_lower) < len(text_lower) * 0.2:
                    concept_data["relevance"] = min(
                        1.0, concept_data.get("relevance", 0.5) + 0.1
                    )

            except Exception as e:
                logger.warning(
                    f"Error weighting concept '{concept_data.get('name', 'N/A')}': {e}"
                )
                # Keep existing or default relevance if weighting fails
                concept_data["relevance"] = concept_data.get("relevance", 0.5)

        # Sort by new relevance
        valid_concepts.sort(key=lambda x: x.get("relevance", 0), reverse=True)
        return valid_concepts
