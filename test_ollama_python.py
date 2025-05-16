#!/usr/bin/env python3
"""
Test script to check Ollama embeddings using the official Python client.
"""

import json

# Import the ollama module (should be installed with 'uv pip install ollama')
import ollama

def test_ollama_embeddings():
    """Test Ollama embeddings using the Python client."""
    print("Testing Ollama embeddings with Python client...")

    # List available models
    try:
        models = ollama.list()
        print(f"\nAvailable models: {json.dumps(models, indent=2)}")
    except Exception as e:
        print(f"Error listing models: {e}")

    # Test embeddings with a single input
    try:
        print("\nTesting embeddings with single input:")
        response = ollama.embeddings(
            model="snowflake-arctic-embed2",
            prompt="This is a test"
        )
        print(f"Response type: {type(response)}")
        print(f"Response attributes: {dir(response)}")

        # Access the embedding directly
        embedding = response.embedding
        print(f"Embedding dimensions: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")
    except Exception as e:
        print(f"Error generating embeddings: {e}")

    # Test embeddings with multiple inputs by making multiple calls
    try:
        print("\nTesting embeddings with multiple inputs (sequential calls):")
        texts = ["This is a test", "This is another test"]
        embeddings = []

        for text in texts:
            response = ollama.embeddings(
                model="snowflake-arctic-embed2",
                prompt=text
            )
            embeddings.append(response.embedding)

        print(f"Number of embeddings: {len(embeddings)}")
        for i, embedding in enumerate(embeddings):
            print(f"Embedding {i+1} dimensions: {len(embedding)}")
            print(f"First 5 values: {embedding[:5]}")
    except Exception as e:
        print(f"Error generating multiple embeddings: {e}")

if __name__ == "__main__":
    test_ollama_embeddings()
