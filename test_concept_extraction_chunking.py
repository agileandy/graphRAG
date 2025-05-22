#!/usr/bin/env python3
"""Test script for concept extraction with document chunking.

This script tests:
1. Concept extraction with small text (no chunking)
2. Concept extraction with large text (with chunking)
3. Concept extraction with very large text (with optimized chunking)
"""

import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import the concept extractor
from src.processing.concept_extractor import ConceptExtractor


def test_small_text_extraction():
    """Test concept extraction with small text (no chunking needed)."""
    print("\n=== Testing Concept Extraction with Small Text ===")

    # Create a small test document
    test_text = """
    Machine learning is a subset of artificial intelligence that focuses on developing systems
    that can learn from and make decisions based on data. It involves algorithms that can
    improve automatically through experience and by the use of data.
    """

    # Initialize the concept extractor
    extractor = ConceptExtractor(use_nlp=True, use_llm=True)

    # Extract concepts
    print("Extracting concepts from small text...")
    concepts = extractor.extract_concepts(test_text)

    # Print results
    if concepts:
        print(f"✅ Successfully extracted {len(concepts)} concepts:")
        for concept in concepts:
            print(
                f"  - {concept.get('concept', 'Unknown')} (relevance: {concept.get('relevance', 'Unknown')})"
            )
    else:
        print("❌ Failed to extract any concepts")

    return len(concepts) > 0


def test_large_text_extraction():
    """Test concept extraction with large text (should trigger chunking)."""
    print("\n=== Testing Concept Extraction with Large Text ===")

    # Create a larger test document (around 5000 characters)
    paragraphs = []
    for i in range(1, 21):
        paragraphs.append(f"""
        Paragraph {i}: Machine learning algorithms build a model based on sample data, known as training data,
        in order to make predictions or decisions without being explicitly programmed to do so. Machine learning
        algorithms are used in a wide variety of applications, such as in medicine, email filtering, speech
        recognition, and computer vision, where it is difficult or unfeasible to develop conventional algorithms
        to perform the needed tasks.
        """)

    test_text = "\n".join(paragraphs)
    print(f"Text length: {len(test_text)} characters")

    # Initialize the concept extractor
    extractor = ConceptExtractor(use_nlp=True, use_llm=True)

    # Extract concepts
    print("Extracting concepts from large text (should trigger chunking)...")
    concepts = extractor.extract_concepts(test_text)

    # Print results
    if concepts:
        print(f"✅ Successfully extracted {len(concepts)} concepts:")
        for concept in concepts[:10]:  # Show only top 10
            print(
                f"  - {concept.get('concept', 'Unknown')} (relevance: {concept.get('relevance', 'Unknown')})"
            )
        if len(concepts) > 10:
            print(f"  ... and {len(concepts) - 10} more")
    else:
        print("❌ Failed to extract any concepts")

    return len(concepts) > 0


def test_very_large_text_extraction():
    """Test concept extraction with very large text (should trigger optimized chunking)."""
    print("\n=== Testing Concept Extraction with Very Large Text ===")

    # Create a very large test document (around 20000 characters)
    paragraphs = []
    for i in range(1, 81):
        paragraphs.append(f"""
        Paragraph {i}: Deep learning is part of a broader family of machine learning methods based on artificial
        neural networks with representation learning. Learning can be supervised, semi-supervised or unsupervised.
        Deep-learning architectures such as deep neural networks, deep belief networks, deep reinforcement learning,
        recurrent neural networks and convolutional neural networks have been applied to fields including computer vision,
        speech recognition, natural language processing, machine translation, bioinformatics, drug design, medical image
        analysis, climate science, material inspection and board game programs, where they have produced results comparable
        to and in some cases surpassing human expert performance.
        """)

    test_text = "\n".join(paragraphs)
    print(f"Text length: {len(test_text)} characters")

    # Initialize the concept extractor
    extractor = ConceptExtractor(use_nlp=True, use_llm=True)

    # Extract concepts
    print(
        "Extracting concepts from very large text (should trigger optimized chunking)..."
    )
    concepts = extractor.extract_concepts(test_text)

    # Print results
    if concepts:
        print(f"✅ Successfully extracted {len(concepts)} concepts:")
        for concept in concepts[:10]:  # Show only top 10
            print(
                f"  - {concept.get('concept', 'Unknown')} (relevance: {concept.get('relevance', 'Unknown')})"
            )
        if len(concepts) > 10:
            print(f"  ... and {len(concepts) - 10} more")
    else:
        print("❌ Failed to extract any concepts")

    return len(concepts) > 0


def main() -> None:
    """Main function."""
    print("Testing concept extraction with document chunking...")

    # Run tests
    small_ok = test_small_text_extraction()
    large_ok = test_large_text_extraction()
    very_large_ok = test_very_large_text_extraction()

    # Print summary
    print("\nTest Summary:")
    print(f"Small Text Extraction: {'✅ Passed' if small_ok else '❌ Failed'}")
    print(f"Large Text Extraction: {'✅ Passed' if large_ok else '❌ Failed'}")
    print(
        f"Very Large Text Extraction: {'✅ Passed' if very_large_ok else '❌ Failed'}"
    )


if __name__ == "__main__":
    main()
