"""
OpenAI function calling integration for GraphRAG project.

This module provides functions that can be used with OpenAI's function calling
feature, making it easy to integrate with AI agents.
"""
import os
import requests
from typing import Dict, List, Any, Optional, Callable
from src.config import get_port

# Get API port from centralized configuration
api_port = get_port('api')

# Default API URL
DEFAULT_API_URL = os.getenv("GRAPHRAG_API_URL", f"http://localhost:{api_port}")

def get_graphrag_functions(api_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get a list of GraphRAG functions for use with OpenAI function calling.

    Args:
        api_url: URL of the GraphRAG API server (default: from environment or centralized configuration)

    Returns:
        List of function definitions
    """
    return [
        {
            "name": "graphrag_search",
            "description": "Search the GraphRAG system with a query",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to send to the GraphRAG system"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of vector results to return",
                        "default": 5
                    },
                    "max_hops": {
                        "type": "integer",
                        "description": "Maximum number of hops in the graph",
                        "default": 2
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "graphrag_concept",
            "description": "Explore a concept in the GraphRAG system",
            "parameters": {
                "type": "object",
                "properties": {
                    "concept_name": {
                        "type": "string",
                        "description": "Name of the concept to explore"
                    }
                },
                "required": ["concept_name"]
            }
        },
        {
            "name": "graphrag_documents",
            "description": "Find documents related to a concept in the GraphRAG system",
            "parameters": {
                "type": "object",
                "properties": {
                    "concept_name": {
                        "type": "string",
                        "description": "Name of the concept to find documents for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of documents to return",
                        "default": 5
                    }
                },
                "required": ["concept_name"]
            }
        },
        {
            "name": "graphrag_add_document",
            "description": "Add a document to the GraphRAG system",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Document text to add to the GraphRAG system"
                    },
                    "title": {
                        "type": "string",
                        "description": "Document title"
                    },
                    "source": {
                        "type": "string",
                        "description": "Document source"
                    }
                },
                "required": ["text"]
            }
        }
    ]

def get_graphrag_function_map(api_url: Optional[str] = None) -> Dict[str, Callable]:
    """
    Get a map of GraphRAG function names to their implementations.

    Args:
        api_url: URL of the GraphRAG API server (default: from environment or centralized configuration)

    Returns:
        Dictionary mapping function names to their implementations
    """
    url = api_url or DEFAULT_API_URL

    def graphrag_search(query: str, n_results: int = 5, max_hops: int = 2) -> Dict[str, Any]:
        """Search the GraphRAG system with a query."""
        api_url = f"{url}/search"
        data = {
            "query": query,
            "n_results": n_results,
            "max_hops": max_hops
        }

        try:
            response = requests.post(api_url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def graphrag_concept(concept_name: str) -> Dict[str, Any]:
        """Explore a concept in the GraphRAG system."""
        api_url = f"{url}/concepts/{concept_name}"

        try:
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def graphrag_documents(concept_name: str, limit: int = 5) -> Dict[str, Any]:
        """Find documents related to a concept in the GraphRAG system."""
        api_url = f"{url}/documents/{concept_name}?limit={limit}"

        try:
            response = requests.get(api_url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    def graphrag_add_document(text: str, title: Optional[str] = None, source: Optional[str] = None) -> Dict[str, Any]:
        """Add a document to the GraphRAG system."""
        api_url = f"{url}/documents"

        metadata = {}
        if title:
            metadata["title"] = title
        if source:
            metadata["source"] = source

        data = {
            "text": text,
            "metadata": metadata
        }

        try:
            response = requests.post(api_url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    return {
        "graphrag_search": graphrag_search,
        "graphrag_concept": graphrag_concept,
        "graphrag_documents": graphrag_documents,
        "graphrag_add_document": graphrag_add_document
    }