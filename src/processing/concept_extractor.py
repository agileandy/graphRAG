"""
Concept extraction utilities for GraphRAG project.

This module provides utilities for extracting concepts from text using:
1. Rule-based extraction
2. NLP-based extraction
3. LLM-based extraction (if available)
"""
import re
import logging
import json
from typing import List, Dict, Any, Optional, Tuple, Set
import os
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# We'll use only rule-based extraction since spaCy has compatibility issues
SPACY_AVAILABLE = False
nlp = None

# Try to import OpenAI for LLM-based extraction
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
    # Check if API key is available
    if os.getenv("OPENAI_API_KEY"):
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    else:
        logger.warning("OpenAI API key not found. LLM-based concept extraction will not be available.")
        OPENAI_AVAILABLE = False
        openai_client = None
except ImportError:
    logger.warning("OpenAI not available. LLM-based concept extraction will not be available.")
    OPENAI_AVAILABLE = False
    openai_client = None

# Load domain-specific stopwords
DOMAIN_STOPWORDS = {
    "general": {"the", "and", "a", "an", "in", "on", "at", "to", "for", "with", "by", "about", "like", "through", "over", "before", "after", "between", "under", "during", "without", "of", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "can", "could", "will", "would", "shall", "should", "may", "might", "must", "this", "that", "these", "those", "it", "they", "them", "their", "he", "she", "him", "her", "his", "hers", "its", "theirs", "we", "us", "our", "ours", "you", "your", "yours", "i", "me", "my", "mine"},
    "tech": {"use", "using", "used", "user", "users", "system", "systems", "data", "information", "process", "processes", "method", "methods", "function", "functions", "value", "values", "example", "examples", "result", "results", "figure", "figures", "table", "tables", "section", "sections", "chapter", "chapters", "page", "pages", "see", "shown", "show", "shows", "showing", "note", "notes", "describe", "describes", "described", "describing", "description", "represent", "represents", "represented", "representing", "representation"},
    "academic": {"paper", "papers", "study", "studies", "research", "researcher", "researchers", "analysis", "analyze", "analyzed", "analyzing", "experiment", "experiments", "experimental", "theory", "theories", "theoretical", "hypothesis", "hypotheses", "method", "methods", "methodology", "methodologies", "approach", "approaches", "framework", "frameworks", "model", "models", "modeling", "modelling", "simulation", "simulations", "algorithm", "algorithms", "implementation", "implementations", "evaluation", "evaluations", "evaluate", "evaluated", "evaluating", "performance", "performances", "result", "results", "conclusion", "conclusions", "future", "work"}
}

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
        self.use_llm = use_llm and OPENAI_AVAILABLE
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
        if not self.use_llm or openai_client is None:
            logger.warning("LLM-based extraction not available. Using NLP-based extraction instead.")
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
        # Determine method based on availability
        if method == "auto":
            if self.use_llm and openai_client is not None:
                method = "llm"
            elif self.use_nlp and nlp is not None:
                method = "nlp"
            else:
                method = "rule"
        
        # Extract concepts using the specified method
        if method == "llm" and self.use_llm and openai_client is not None:
            return self.extract_concepts_llm(text, max_concepts)
        elif method == "nlp" and self.use_nlp and nlp is not None:
            concepts = self.extract_concepts_nlp(text)
            return [{"concept": c, "relevance": 1.0, "source": "nlp"} for c in concepts[:max_concepts]]
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
    extractor = ConceptExtractor(use_nlp=True, use_llm=False)
    
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
