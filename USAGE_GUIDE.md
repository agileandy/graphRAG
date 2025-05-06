# GraphRAG Usage Guide

This guide provides step-by-step instructions on how to use the GraphRAG system to add documents, create graph entries, and perform hybrid searches.

## Prerequisites

Before you begin, make sure you have:

1. Installed all dependencies: `pip install -r requirements.txt`
2. Started Neo4j: `./scripts/start_neo4j.sh` or `./neo4j/bin/neo4j start`
3. Set the Neo4j password to match your `.env` file (default: "graphrag")

## Quick Start

For a quick demonstration of the system, run:

```bash
python scripts/simple_demo.py
```

This script:
1. Adds a sample document about GraphRAG to the system
2. Extracts entities and relationships
3. Performs a hybrid search
4. Displays the results

## Adding Documents

### Adding a Single Document

To add a single document to the GraphRAG system:

```bash
python scripts/add_document.py
```

This script demonstrates:
- Adding a document to the vector database
- Extracting entities and relationships
- Creating nodes and relationships in Neo4j
- Performing a hybrid search

### Batch Processing Multiple Documents

To process multiple documents at once:

```bash
# First, create example documents
python scripts/batch_process.py --create-examples

# Then process the example documents
python scripts/batch_process.py --dir ./example_docs
```

This will:
1. Create example text and JSON files in the `./example_docs` directory
2. Process all files in the directory
3. Extract entities and relationships
4. Add them to the GraphRAG system

## Querying the System

### Interactive Mode

For an interactive query experience:

```bash
python scripts/query_graphrag.py
```

This will present a menu with options to:
1. Perform a hybrid search
2. Explore a concept
3. Find documents for a concept

### Direct Queries

You can also perform specific queries directly:

```bash
# Perform a hybrid search
python scripts/query_graphrag.py --query "How do knowledge graphs enhance RAG systems?"

# Explore a concept
python scripts/query_graphrag.py --concept "knowledge graph"

# Find documents for a concept
python scripts/query_graphrag.py --documents "large language model"
```

## Understanding the Results

### Hybrid Search Results

Hybrid search combines vector similarity search with graph traversal:

- **Vector Results**: Documents that are semantically similar to your query
- **Graph Results**: Concepts that are related to the concepts mentioned in your query through the knowledge graph

### Concept Exploration

When exploring a concept, you'll see:

- The concept details (ID, name)
- Other concepts that are directly related to it in the knowledge graph
- The strength of each relationship

### Document Retrieval

When retrieving documents for a concept, you'll see:

- Documents that mention the concept
- Metadata about each document (title, author, source)
- A snippet of the document content

## Customizing the System

### Improving Entity Extraction

The current entity extraction is based on simple keyword matching. To improve it:

1. Edit the `extract_entities` function in `scripts/add_document.py`
2. Implement more sophisticated NLP techniques or integrate with an LLM

### Enhancing Relationship Extraction

To improve relationship extraction:

1. Edit the `extract_relationships` function in `scripts/add_document.py`
2. Implement more advanced methods to capture semantic connections

### Modifying the Schema

To customize the Neo4j schema for your specific domain:

1. Edit the `create_schema` method in `src/database/neo4j_db.py`
2. Add or modify node labels and relationship types

## Managing the Database

### Cleaning the Database

To clean the database and remove all data:

```bash
# Clean both Neo4j and ChromaDB
python scripts/clean_database.py

# Clean only Neo4j
python scripts/clean_database.py --neo4j

# Clean only ChromaDB
python scripts/clean_database.py --chromadb

# Skip confirmation prompts
python scripts/clean_database.py --yes
```

### Initializing the Database

To initialize the database schema:

```bash
# Initialize both Neo4j and ChromaDB
python scripts/initialize_database.py

# Initialize only Neo4j
python scripts/initialize_database.py --neo4j

# Initialize only ChromaDB
python scripts/initialize_database.py --chromadb
```

### Resetting the Database

To reset the database (clean, initialize, and add sample data):

```bash
# Reset the database and add sample data
python scripts/reset_database.py

# Reset the database without adding sample data
python scripts/reset_database.py --no-sample

# Skip confirmation prompts
python scripts/reset_database.py --yes
```

## Troubleshooting

### Neo4j Connection Issues

If you encounter Neo4j connection issues:

1. Make sure Neo4j is running: `./neo4j/bin/neo4j status`
2. Check that your `.env` file has the correct credentials
3. Reset the Neo4j password if needed: `./scripts/reset_neo4j_password.sh`

### ChromaDB Issues

If you encounter ChromaDB issues:

1. Check that the `CHROMA_PERSIST_DIRECTORY` in your `.env` file is correct
2. Make sure the directory exists and is writable
3. Delete the directory and let ChromaDB recreate it if necessary
4. Try resetting the database: `python scripts/reset_database.py`

### Metadata Format Issues

ChromaDB has specific requirements for metadata:

1. Metadata values must be strings, integers, floats, or booleans
2. Lists and dictionaries must be converted to strings
3. Make sure all metadata values are properly formatted before adding documents