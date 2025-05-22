# Project Dictionary

This document provides a description of the files in the project.

## bin/graphrag-monitor.py
This script monitors the GraphRAG services (Neo4j, API, MPC) and restarts them if they crash. It checks for the existence of PID files, verifies if the processes are running, and optionally checks HTTP endpoints for responsiveness. It also collects resource usage information (CPU, memory, disk).

## bugMCP/bugAPI.py
This file implements a simple FastAPI server for bug tracking. It provides RESTful endpoints for managing bugs, including adding, updating, deleting, and retrieving bugs. It uses a JSON file to persist bug data.

## bugMCP/bugMCP.py
This file implements a TCP server for bug tracking using a custom protocol. It allows clients to add, update, delete, get, and list bugs. It uses a JSON file to persist bug data.

## bugMCP/bugMCP_mcp.py
This file implements a Model Context Protocol (MCP) server for bug tracking. It provides tools for adding, updating, deleting, and retrieving bugs using the FastMCP framework. It uses a JSON file to persist bug data.

## scripts/query/query_neo4j.py
This script allows direct querying of the Neo4j database. It takes command-line arguments for connection details and queries, and prints the results in JSON format. It includes functions for testing the connection, getting counts of nodes and relationships, and running custom Cypher queries.

## src/agent-tools/utils.py
This module provides utility functions for GraphRAG agent tools. It includes functions for loading configuration from environment variables, getting the MPC server URL, connecting to the MPC server, sending requests to the MPC server, formatting JSON data, and checking the ChromaDB version.

## src/config/ports.py
This module provides a centralized location for all port configurations used by GraphRAG services. It includes functions for getting a port by service name, checking if a port is in use, finding an available port, getting the service name for a port, checking for port conflicts, and printing the port configuration.

## src/database/graph_db.py
This module provides a unified interface for graph database operations, currently implemented using Neo4j. It includes methods for connecting, closing the connection, verifying the connection, creating a schema, clearing the database, adding documents and concepts, adding relationships between documents and concepts, getting concepts by name, getting related concepts, and getting documents by concept.

## src/database/neo4j_db.py
This module handles the connection and operations for the Neo4j graph database. It includes methods for connecting, closing the connection, verifying the connection, running queries, creating a schema, clearing the database, and creating dummy data.

## src/database/vector_db.py
This module handles the connection and operations for the ChromaDB vector database. It includes methods for connecting, verifying the connection, adding documents, querying the database, counting documents, processing document batches, checking index health, and repairing the index.

## src/llm/concept_extraction.py
This module provides functions for extracting concepts from text using LLMs, analyzing relationships between concepts, and enhancing the knowledge graph. It includes functions for extracting concepts with LLM, analyzing concept relationships, summarizing text with LLM, translating natural language to graph query, extracting concepts in two passes, and analyzing sentiment.

## src/llm/llm_provider.py
This module provides a flexible architecture for integrating with various LLM endpoints, including local LLM servers (e.g., LM Studio, Ollama) and cloud APIs. It defines abstract and concrete classes for LLM providers, including OpenAI-compatible and Ollama providers, and a manager class for handling multiple providers with fallback capabilities.

## src/loaders/markdown_loader.py
This module provides a `MarkdownLoader` class for loading and processing Markdown documents. It includes methods for extracting frontmatter and converting Markdown content to plain text.

## src/processing/document_hash.py
This module provides functions for generating hashes of documents and metadata for deduplication purposes. It includes functions for generating document hashes, generating metadata hashes, enriching metadata with hashes, calculating title similarity, and checking if a document is likely a duplicate.

## src/processing/document_processor.py
This module provides optimized document processing functions for smart chunking strategies, batch processing, metadata optimization, adaptive chunk sizing, and document hashing for deduplication.

## src/processing/duplicate_detector.py
This module provides functionality to detect duplicate documents in the GraphRAG system. It includes a `DuplicateDetector` class with methods for generating document hashes and checking if a document is a duplicate.

## src/search/reranker.py
This module provides a `Reranker` class for improving search results using a cross-encoder model. It includes methods for reranking documents based on relevance to a query.

## src/utils/config.py
This module provides utility functions for loading configuration settings from a file.

## src/utils/db_utils.py
This module provides utility functions for database operations, such as checking the ChromaDB version, checking database directories, and getting ChromaDB info.

## tests/component/test_mpc_connection.py
This script tests the connection to the GraphRAG MPC server.

## tests/create_test_pdf.py
This script creates a test PDF document for the GraphRAG system.

## tests/regression/run_all_tests.py
This script runs all regression tests in sequence.

## tests/regression/run_regression_tests.py
This script runs all regression tests for the GraphRAG system, with options to skip certain tests.

## tests/regression/test_message_passing_server.py
This script contains regression tests for the GraphRAG Message Passing Communication (MPC) server.

## tests/regression/test_model_context_server.py
This script contains regression tests for the GraphRAG Model Context Protocol (MCP) server.

## tests/regression/test_utils.py
This module provides utility functions for GraphRAG regression tests, such as printing sections and headers, waiting for an API to be ready, testing the MCP connection, getting tools from MCP, invoking tools from MCP, and printing test results.

## tests/test_mcp_server.py
This script tests the GraphRAG MCP server and its dependencies.

## tests/test_mpc_connection.py
This script tests the connection to the GraphRAG MPC server.
