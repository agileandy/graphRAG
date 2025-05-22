#!/usr/bin/env python3
"""Simple test script for OpenRouter API."""

import json
import os
import sys

import requests

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# OpenRouter API key
# API_KEY = "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" # Leaked key removed
API_KEY = os.environ.get("OPENROUTER_API_KEY")
if not API_KEY:
    print("Error: OPENROUTER_API_KEY environment variable not set.")
    print("Please set it before running the script.")
    print("Example: export OPENROUTER_API_KEY='your_actual_api_key'")
    sys.exit(1) # Exit if the key is not found

# Model to use
MODEL = "meta-llama/llama-4-maverick:free"

# Test prompt
PROMPT = "Explain the concept of Retrieval-Augmented Generation (RAG) in 3-4 sentences."


def test_openrouter_api() -> None:
    """Test the OpenRouter API with a simple prompt."""
    print(f"Testing OpenRouter API with model: {MODEL}")
    print(f"Prompt: {PROMPT}")

    # Prepare the request payload
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": PROMPT},
        ],
        "temperature": 0.1,
        "max_tokens": 1000,  # Using a smaller value for faster response
    }

    # Set up headers
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://graphrag.local",
        "X-Title": "GraphRAG",
    }

    try:
        # Make the API request
        print("Sending request to OpenRouter API...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,  # Using a shorter timeout
        )

        # Print the response status code
        print(f"Response status code: {response.status_code}")

        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response
            result = response.json()

            # Extract and print the generated text
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0]["message"]
                content = message.get("content", "")
                print("\nGenerated text:")
                print(content)
            else:
                print("\nNo choices in response:")
                print(json.dumps(result, indent=2))
        else:
            print("\nError response:")
            print(response.text)

    except requests.exceptions.Timeout:
        print("Request timed out after 30 seconds")
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_openrouter_api()
