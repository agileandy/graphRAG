"""
LangChain tools for GraphRAG project.

This module provides LangChain tools for interacting with the GraphRAG system,
making it easy to integrate with AI agents.
"""
import os
import requests
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from langchain.tools import BaseTool

# Default API URL
DEFAULT_API_URL = os.getenv("GRAPHRAG_API_URL", "http://localhost:5001")

class GraphRAGSearchInput(BaseModel):
    """Input for GraphRAG search tool."""
    query: str = Field(..., description="The search query to send to the GraphRAG system")
    n_results: int = Field(5, description="Number of vector results to return")
    max_hops: int = Field(2, description="Maximum number of hops in the graph")

class GraphRAGConceptInput(BaseModel):
    """Input for GraphRAG concept tool."""
    concept_name: str = Field(..., description="Name of the concept to explore")

class GraphRAGDocumentInput(BaseModel):
    """Input for GraphRAG document tool."""
    concept_name: str = Field(..., description="Name of the concept to find documents for")
    limit: int = Field(5, description="Maximum number of documents to return")

class GraphRAGAddDocumentInput(BaseModel):
    """Input for GraphRAG add document tool."""
    text: str = Field(..., description="Document text to add to the GraphRAG system")
    title: Optional[str] = Field(None, description="Document title")
    source: Optional[str] = Field(None, description="Document source")

class GraphRAGSearchTool(BaseTool):
    """Tool for searching the GraphRAG system."""
    name = "graphrag_search"
    description = """
    Use this tool to search the GraphRAG system with a query.
    It performs a hybrid search using both vector and graph databases.
    """
    args_schema = GraphRAGSearchInput
    api_url: str = DEFAULT_API_URL

    def _run(self, query: str, n_results: int = 5, max_hops: int = 2) -> Dict[str, Any]:
        """Run the tool."""
        url = f"{self.api_url}/search"
        data = {
            "query": query,
            "n_results": n_results,
            "max_hops": max_hops
        }

        try:
            response = requests.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

class GraphRAGConceptTool(BaseTool):
    """Tool for exploring concepts in the GraphRAG system."""
    name = "graphrag_concept"
    description = """
    Use this tool to explore a concept in the GraphRAG system.
    It returns information about the concept and related concepts.
    """
    args_schema = GraphRAGConceptInput
    api_url: str = DEFAULT_API_URL

    def _run(self, concept_name: str) -> Dict[str, Any]:
        """Run the tool."""
        url = f"{self.api_url}/concepts/{concept_name}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

class GraphRAGDocumentTool(BaseTool):
    """Tool for finding documents related to a concept in the GraphRAG system."""
    name = "graphrag_documents"
    description = """
    Use this tool to find documents related to a concept in the GraphRAG system.
    It returns a list of documents that mention the concept.
    """
    args_schema = GraphRAGDocumentInput
    api_url: str = DEFAULT_API_URL

    def _run(self, concept_name: str, limit: int = 5) -> Dict[str, Any]:
        """Run the tool."""
        url = f"{self.api_url}/documents/{concept_name}?limit={limit}"

        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

class GraphRAGAddDocumentTool(BaseTool):
    """Tool for adding a document to the GraphRAG system."""
    name = "graphrag_add_document"
    description = """
    Use this tool to add a document to the GraphRAG system.
    It extracts entities and relationships from the document and adds them to the system.
    """
    args_schema = GraphRAGAddDocumentInput
    api_url: str = DEFAULT_API_URL

    def _run(self, text: str, title: Optional[str] = None, source: Optional[str] = None) -> Dict[str, Any]:
        """Run the tool."""
        url = f"{self.api_url}/documents"

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
            response = requests.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

def get_graphrag_tools(api_url: Optional[str] = None) -> List[BaseTool]:
    """
    Get a list of GraphRAG tools for use with LangChain.

    Args:
        api_url: URL of the GraphRAG API server (default: from environment or http://localhost:5001)

    Returns:
        List of LangChain tools
    """
    url = api_url or DEFAULT_API_URL

    return [
        GraphRAGSearchTool(api_url=url),
        GraphRAGConceptTool(api_url=url),
        GraphRAGDocumentTool(api_url=url),
        GraphRAGAddDocumentTool(api_url=url)
    ]