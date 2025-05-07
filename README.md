# GraphRAG - Enhanced Information Synthesis and Retrieval

This project implements a GraphRAG (Retrieval-Augmented Generation with Knowledge Graphs) system for enhanced information synthesis and retrieval across a large collection of ebooks.

## Overview

GraphRAG combines the power of vector embeddings with knowledge graphs to overcome the limitations of traditional embedding-based RAG systems. By explicitly representing semantic connections and contextual relationships between ideas within and across books, GraphRAG enables more sophisticated information retrieval and synthesis.

## Project Structure

```
graphRAG/
├── data/                  # Data directory (created at runtime)
│   └── chromadb/          # ChromaDB persistence directory
├── scripts/               # Utility scripts
│   ├── verify_neo4j.py    # Script to verify Neo4j setup
│   ├── verify_vector_db.py # Script to verify vector database setup
│   ├── verify_linkage.py  # Script to verify database linkage
│   ├── add_document.py    # Script to add a document to the system
│   ├── query_graphrag.py  # Script to query the system
│   ├── batch_process.py   # Script to batch process multiple documents
│   ├── start_api_server.sh # Script to start the API server
│   ├── start_mpc_server.sh # Script to start the MPC server
│   ├── langchain_agent_example.py # Example of using GraphRAG with LangChain
│   ├── openai_function_example.py # Example of using GraphRAG with OpenAI functions
│   └── mpc_client_example.py # Example client for the MPC server
├── src/                   # Source code
│   ├── database/          # Database modules
│   │   ├── __init__.py
│   │   ├── neo4j_db.py    # Neo4j database connection and operations
│   │   ├── vector_db.py   # Vector database connection and operations
│   │   └── db_linkage.py  # Database linkage utilities
│   ├── api/               # API server
│   │   ├── __init__.py
│   │   ├── server.py      # Flask API server
│   │   └── wsgi.py        # WSGI entry point
│   ├── agents/            # Agent integration
│   │   ├── __init__.py
│   │   ├── langchain_tools.py # LangChain tools
│   │   └── openai_functions.py # OpenAI function calling integration
│   └── mpc/               # MPC server
│       ├── __init__.py
│       └── server.py      # WebSocket MPC server
├── tests/                 # Test directory
├── .env                   # Environment variables
├── .gitignore             # Git ignore file
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Prerequisites

- Python 3.8+
- Neo4j Community Edition
- ChromaDB (installed via pip)

## Installation

You can install GraphRAG either using Docker or manually.

### Option 1: Using Docker (Recommended)

The easiest way to get started with GraphRAG is to use Docker, which packages everything you need into a single container.

#### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop)

#### Steps

1. Clone the repository:

```bash
git clone <repository-url>
cd graphRAG
```

2. Build and start the container:

```bash
docker-compose up -d
```

This will:
- Build the Docker image
- Start Neo4j inside the container
- Start the API server
- Start the MPC server
- Expose all necessary ports

3. Access the services:

- Neo4j Browser: http://localhost:7474 (username: neo4j, password: graphrag)
- GraphRAG API: http://localhost:5000
- GraphRAG MPC Server: ws://localhost:8765

4. Stop the container:

```bash
docker-compose down
```

### Option 2: Manual Installation

If you prefer to install GraphRAG manually, follow these steps:

#### 1. Clone the repository

```bash
git clone <repository-url>
cd graphRAG
```

#### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

#### 3. Install dependencies

```bash
pip install -r requirements.txt
```

#### 4. Install and Set Up Neo4j

1. Download Neo4j Community Edition from [Neo4j Download Center](https://neo4j.com/download-center/)
2. Install Neo4j following the instructions for your operating system
3. Start Neo4j and create a new database (or use the default one)
4. Set the initial password for the 'neo4j' user
5. Make note of the connection URI, username, and password

Or use the provided installation script:

```bash
# Install Neo4j
./scripts/install_neo4j.sh

# Start Neo4j
./scripts/start_neo4j.sh

# Reset Neo4j password if needed
./scripts/reset_neo4j_password.sh
```

### 5. Configure Environment Variables

Create a `.env` file in the project root directory with the following content:

```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=graphrag

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY=./data/chromadb

# API Configuration
GRAPHRAG_API_URL=http://localhost:5000

# OpenAI API Key (for agent examples)
OPENAI_API_KEY=your_openai_api_key
```

Replace `graphrag` with the password you set for Neo4j if different, and add your OpenAI API key if you plan to use the agent examples.

## Verification

Run the following scripts to verify that the database setup is working correctly:

```bash
# Verify Neo4j connection and schema
uv run scripts/verify_neo4j.py

# Verify vector database connection
uv run scripts/verify_vector_db.py

# Verify database linkage
uv run scripts/verify_linkage.py

# Run a complete end-to-end test
./scripts/run_end_to_end_test.sh
```

The end-to-end test script:
1. Resets the databases (Neo4j and ChromaDB)
2. Verifies database connections
3. Adds a test document
4. Performs a search query
5. Displays the results

This is useful for ensuring that the entire system is working correctly, especially after making changes to the code or configuration.

## Usage

### Adding a Single Document

To add a single document to the GraphRAG system:

```bash
uv run scripts/add_document.py
```

This script demonstrates:
1. Adding a document to the vector database
2. Extracting entities and relationships
3. Creating nodes and relationships in Neo4j
4. Performing a hybrid search

### Batch Processing Multiple Documents

To process multiple documents at once:

```bash
# First, create example documents
uv run scripts/batch_process.py --create-examples

# Then process the example documents
uv run scripts/batch_process.py --dir ./example_docs
```

This script:
1. Processes all text and JSON files in a directory
2. Extracts entities and relationships from each document
3. Adds them to the GraphRAG system

### Querying the GraphRAG System

To query the GraphRAG system:

```bash
# Interactive mode
uv run scripts/query_graphrag.py

# Direct search
uv run scripts/query_graphrag.py --query "How do transformers work in deep learning?"

# Explore a concept
uv run scripts/query_graphrag.py --concept "neural network"

# Find documents for a concept
uv run scripts/query_graphrag.py --documents "machine learning"
```

This script demonstrates:
1. Performing hybrid searches using both vector and graph databases
2. Exploring the knowledge graph
3. Retrieving related documents

## Database Schema

### Neo4j Knowledge Graph Schema

The knowledge graph schema includes the following node types:

- **Book**: Represents an ebook
  - Properties: id, title, category, isbn

- **Chapter**: Represents a chapter within a book
  - Properties: id, title, number, book_id

- **Section**: Represents a section within a chapter
  - Properties: id, title, number, chapter_id

- **Concept**: Represents a concept or entity mentioned in the content
  - Properties: id, name

Relationship types:

- **CONTAINS**: Hierarchical relationship (Book → Chapter → Section)
- **MENTIONS**: Content mentions a concept (Section → Concept)
- **RELATED_TO**: Semantic relationship between concepts (Concept → Concept)
  - Properties: strength (float between 0 and 1)

### Vector Database Schema

The vector database stores text chunks with the following metadata:

- **id**: Unique identifier for the chunk
- **document**: The text content of the chunk
- **metadata**:
  - book_id: ID of the book this chunk belongs to
  - chapter_id: ID of the chapter this chunk belongs to
  - section_id: ID of the section this chunk belongs to
  - concept_id: ID of the concept this chunk is about
  - title: Title of the content
  - source: Source book title

## Database Linkage

The database linkage module provides utilities for connecting the Neo4j knowledge graph with the vector database:

- **get_node_chunks**: Get text chunks from the vector database for a specific Neo4j node
- **get_related_nodes**: Get Neo4j nodes related to a specific chunk in the vector database
- **hybrid_search**: Perform hybrid search using both vector and graph databases

## AI Agent Integration

GraphRAG provides several ways to integrate with AI agents:

### RESTful API Server

The GraphRAG API server provides a RESTful interface for AI agents to interact with the system:

```bash
# Start the API server
./scripts/start_api_server.sh
```

The API server provides the following endpoints:

- `GET /health` - Health check endpoint
- `POST /search` - Search the GraphRAG system
- `GET /concepts/<concept_name>` - Get information about a concept
- `GET /documents/<concept_name>` - Get documents related to a concept
- `POST /documents` - Add a document to the system
- `GET /books` - Get all books in the system
- `GET /books/<book_title>` - Get concepts mentioned in a book
- `GET /concepts` - Get all concepts in the system

### LangChain Integration

GraphRAG provides LangChain tools for easy integration with LangChain agents:

```bash
# Run the LangChain agent example
uv run scripts/langchain_agent_example.py
```

The LangChain integration provides the following tools:

- `graphrag_search` - Search the GraphRAG system
- `graphrag_concept` - Explore a concept
- `graphrag_documents` - Find documents related to a concept
- `graphrag_add_document` - Add a document to the system

### OpenAI Function Calling Integration

GraphRAG provides OpenAI function calling integration for easy integration with OpenAI models:

```bash
# Run the OpenAI function calling example
uv run scripts/openai_function_example.py
```

The OpenAI function calling integration provides the following functions:

- `graphrag_search` - Search the GraphRAG system
- `graphrag_concept` - Explore a concept
- `graphrag_documents` - Find documents related to a concept
- `graphrag_add_document` - Add a document to the system

### MPC Server Integration

GraphRAG provides a WebSocket-based MPC (Message Passing Communication) server for AI agents:

```bash
# Start the MPC server
./scripts/start_mpc_server.sh

# Run the MPC client example
uv run scripts/mpc_client_example.py
```

The MPC server supports the following actions:

- `search` - Search the GraphRAG system
- `concept` - Explore a concept
- `documents` - Find documents related to a concept
- `add_document` - Add a document to the system

## Docker Development

For detailed information about developing with Docker, see the [Docker Development Guide](docs/docker_development.md).

The guide covers:
- Development workflow options (volume mounts vs. inside container)
- How to synchronize changes between the container and local source code
- End-to-end testing procedures
- Troubleshooting common issues

### Volume Mounts for Development

The docker-compose.yml file includes volume mounts for source code to facilitate development:

```yaml
volumes:
  # Persist data
  - ./data:/app/data
  # Mount ebooks folder
  - /Users/andyspamer/ebooks:/app/ebooks
  # Mount source code for development
  - ./src:/app/src
  - ./scripts:/app/scripts
  - ./tools:/app/tools
```

This allows you to make changes to the local source code and have them immediately reflected in the container.

## Using Docker with AI Agents

When using the Docker container with AI agents, you'll need to make sure your agent can access the GraphRAG services. Here are some tips:

### Connecting to the API Server

If your agent is running outside the Docker container, use the following URL to connect to the API server:

```python
api_url = "http://localhost:5001"  # Note the port is 5001 in docker-compose.yml
```

If your agent is running inside the same Docker network, you can use the container name:

```python
api_url = "http://graphrag:5000"  # Inside container uses port 5000
```

### Connecting to the MPC Server

For the MPC server, use the following WebSocket URL:

```python
mpc_url = "ws://localhost:8766"  # From outside the container (port 8766 in docker-compose.yml)
mpc_url = "ws://graphrag:8765"   # From inside the Docker network (port 8765 inside container)
```

### Example: Using LangChain with Docker

```python
from src.agents.langchain_tools import get_graphrag_tools

# Connect to the GraphRAG API server in Docker
tools = get_graphrag_tools(api_url="http://localhost:5001")
```

### Example: Using OpenAI Functions with Docker

```python
from src.agents.openai_functions import get_graphrag_functions, get_graphrag_function_map

# Connect to the GraphRAG API server in Docker
functions = get_graphrag_functions(api_url="http://localhost:5001")
function_map = get_graphrag_function_map(api_url="http://localhost:5001")
```

## Extending the System

To extend the GraphRAG system for your specific use case:

1. **Improve Entity Extraction**: Replace the simple keyword-based entity extraction in `add_document.py` with more sophisticated NLP techniques or LLMs.

2. **Enhance Relationship Extraction**: Implement more advanced relationship extraction methods to better capture the semantic connections between concepts.

3. **Customize the Schema**: Modify the Neo4j schema to better represent your specific domain or content structure.

4. **Implement Advanced Chunking**: Develop more sophisticated text chunking strategies for better retrieval performance.

5. **Add Generation Capabilities**: Integrate with an LLM to add generation capabilities to the system.

6. **Extend Agent Integration**: Add more agent integration options or enhance the existing ones.

## License

[Specify your license here]