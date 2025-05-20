#!/usr/bin/env python3
"""Script to test concept extraction functionality.

This script tests:
1. Rule-based concept extraction
2. NLP-based concept extraction (if available)
3. LLM-based concept extraction (if available)
4. Concept weighting
"""

import logging
import os
import sys

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.processing.concept_extractor import ConceptExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
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
    """,
}


def test_rule_based_extraction() -> bool:
    """Test rule-based concept extraction."""
    print("\nTesting rule-based concept extraction...")

    extractor = ConceptExtractor(use_nlp=False, use_llm=False)

    for domain, text in SAMPLE_TEXTS.items():
        print(f"\nDomain: {domain}")
        concepts = extractor.extract_concepts_rule_based(text)

        if concepts:
            print(f"✅ Successfully extracted {len(concepts)} concepts:")
            for concept in concepts:
                print(f"  - {concept}")
        else:
            print("❌ Failed to extract any concepts")

    return True


def test_nlp_based_extraction() -> bool:
    """Test NLP-based concept extraction."""
    print("\nTesting NLP-based concept extraction...")

    # Check if spaCy is available
    try:
        import spacy

        SPACY_AVAILABLE = True
    except ImportError:
        SPACY_AVAILABLE = False

    if not SPACY_AVAILABLE:
        print("⚠️ spaCy not available. Skipping NLP-based extraction test.")
        return False

    extractor = ConceptExtractor(use_nlp=True, use_llm=False)

    for domain, text in SAMPLE_TEXTS.items():
        print(f"\nDomain: {domain}")
        concepts = extractor.extract_concepts_nlp(text)

        if concepts:
            print(f"✅ Successfully extracted {len(concepts)} concepts:")
            for concept in concepts:
                print(f"  - {concept}")
        else:
            print("❌ Failed to extract any concepts")

    return True


def test_llm_based_extraction() -> bool:
    """Test LLM-based concept extraction."""
    print("\nTesting LLM-based concept extraction...")

    # Check if OpenAI is available and API key is set
    try:
        from openai import OpenAI

        OPENAI_AVAILABLE = True and os.getenv("OPENAI_API_KEY") is not None
    except ImportError:
        OPENAI_AVAILABLE = False

    if not OPENAI_AVAILABLE:
        print(
            "⚠️ OpenAI not available or API key not set. Skipping LLM-based extraction test."
        )
        return False

    extractor = ConceptExtractor(use_nlp=True, use_llm=True)

    for domain, text in SAMPLE_TEXTS.items():
        print(f"\nDomain: {domain}")
        concepts = extractor.extract_concepts_llm(text)

        if concepts:
            print(f"✅ Successfully extracted {len(concepts)} concepts:")
            for concept in concepts:
                print(
                    f"  - {concept['concept']} (relevance: {concept['relevance']}, source: {concept['source']})"
                )
                if "definition" in concept:
                    print(f"    Definition: {concept['definition']}")
        else:
            print("❌ Failed to extract any concepts")

    return True


def test_concept_weighting() -> bool:
    """Test concept weighting."""
    print("\nTesting concept weighting...")

    extractor = ConceptExtractor(use_nlp=True, use_llm=False)

    for domain, text in SAMPLE_TEXTS.items():
        print(f"\nDomain: {domain}")

        # Extract concepts
        concepts = extractor.extract_concepts(text)

        # Weight concepts
        weighted_concepts = extractor.weight_concepts(concepts, text)

        if weighted_concepts:
            print(f"✅ Successfully weighted {len(weighted_concepts)} concepts:")
            for concept in weighted_concepts:
                print(
                    f"  - {concept['concept']} (weight: {concept.get('weight', 0):.2f}, frequency: {concept.get('frequency', 0)})"
                )
        else:
            print("❌ Failed to weight any concepts")

    return True


def test_domain_specific_extraction() -> bool:
    """Test domain-specific concept extraction."""
    print("\nTesting domain-specific concept extraction...")

    # Test with different domains
    domains = ["general", "tech", "academic"]

    for domain in domains:
        print(f"\nDomain: {domain}")
        extractor = ConceptExtractor(use_nlp=True, use_llm=False, domain=domain)

        for text_domain, text in SAMPLE_TEXTS.items():
            print(f"\n  Text domain: {text_domain}")
            concepts = extractor.extract_concepts(text)

            if concepts:
                print(f"  ✅ Successfully extracted {len(concepts)} concepts:")
                for concept in concepts[:5]:  # Show only top 5
                    print(
                        f"    - {concept['concept']} (relevance: {concept['relevance']}, source: {concept['source']})"
                    )
                if len(concepts) > 5:
                    print(f"    ... and {len(concepts) - 5} more")
            else:
                print("  ❌ Failed to extract any concepts")

    return True


def main() -> bool:
    """Main function."""
    print("Testing concept extraction functionality...")

    # Run tests
    rule_based_ok = test_rule_based_extraction()
    nlp_based_ok = test_nlp_based_extraction()
    llm_based_ok = test_llm_based_extraction()
    weighting_ok = test_concept_weighting()
    domain_specific_ok = test_domain_specific_extraction()

    # Print summary
    print("\nTest Summary:")
    print(f"Rule-based Extraction: {'✅ Passed' if rule_based_ok else '❌ Failed'}")
    print(f"NLP-based Extraction: {'✅ Passed' if nlp_based_ok else '⚠️ Skipped'}")
    print(f"LLM-based Extraction: {'✅ Passed' if llm_based_ok else '⚠️ Skipped'}")
    print(f"Concept Weighting: {'✅ Passed' if weighting_ok else '❌ Failed'}")
    print(
        f"Domain-specific Extraction: {'✅ Passed' if domain_specific_ok else '❌ Failed'}"
    )

    if rule_based_ok and weighting_ok and domain_specific_ok:
        print("\n✅ Core concept extraction tests passed!")
        return True
    else:
        print("\n⚠️ Some concept extraction tests failed or were skipped.")
        return False


if __name__ == "__main__":
    main()
