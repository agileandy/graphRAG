#!/usr/bin/env python3
"""
Test script to check Ollama embeddings.
"""

import requests
import json

def test_embeddings():
    """Test Ollama embeddings."""
    print("Testing Ollama embeddings...")

    # Test with /api/embeddings endpoint
    try:
        print("\nTesting /api/embeddings endpoint:")
        response = requests.post(
            "http://localhost:11434/api/embeddings",
            json={"model": "snowflake-arctic-embed2", "input": "This is a test"},
            timeout=60
        )
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

    # Test with /api/embed endpoint
    try:
        print("\nTesting /api/embed endpoint:")
        response = requests.post(
            "http://localhost:11434/api/embed",
            json={"model": "snowflake-arctic-embed2", "prompt": "This is a test"},
            timeout=60
        )
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)[:200]}...")  # Show just the beginning
            print(f"Embedding dimensions: {len(result.get('embedding', []))}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

    # Test with /api/generate endpoint
    try:
        print("\nTesting /api/generate endpoint (for comparison):")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": "qwen3", "prompt": "Hello, how are you?", "stream": False},
            timeout=60
        )
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_embeddings()
