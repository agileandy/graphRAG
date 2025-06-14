# GraphRAG Project Dictionary

This document provides a comprehensive overview of the GraphRAG project's file structure, identifying the purpose of each file, highlighting duplications, and noting deprecated files.

## Core Components

### Database Layer

- **src/database/neo4j_db.py**: Core Neo4j database interface with connection management and query execution.
- **src/database/vector_db.py**: ChromaDB vector database interface for embedding storage and retrieval.
- **src/database/db_linkage.py**: Manages the linkage between Neo4j and ChromaDB.
- **src/database/graph_db.py**: Provides a unified interface for graph database operations.

### API Layer

- **src/api/server.py**: REST API server implementation using Flask.
- **src/api/wsgi.py**: WSGI entry point for the API server.

### MCP Layer

- **src/mcp/server.py**: WebSocket-based MCP server implementation.

### Processing Layer

- **src/processing/document_processor.py**: Core document processing pipeline.
- **src/processing/duplicate_detector.py**: Detects duplicate documents.
- **src/processing/concept_extractor.py**: Extracts concepts from documents using NLP.
- **src/processing/document_hash.py**: Generates document fingerprints for deduplication.
- **src/processing/file_handler.py**: Handles file operations for different document types.
- **src/processing/job_manager.py**: Manages asynchronous processing jobs.

### LLM Integration

- **src/llm/llm_provider.py**: Interface for LLM providers (OpenAI, Ollama, etc.).
- **src/llm/concept_extraction.py**: Uses LLMs for concept extraction.

### Document Loaders

- **src/loaders/pdf_loader.py**: Loads and processes PDF documents.
- **src/loaders/markdown_loader.py**: Loads and processes Markdown documents.

### Agent Tools

- **src/agent-tools/*.py**: MCP tools for AI agents to interact with GraphRAG.

### Utility Functions

- **src/utils/db_utils.py**: Database utility functions.

## Scripts

### Service Management

- **scripts/start-graphrag-local.sh**: **MAIN ENTRY POINT** - User-friendly script to start all GraphRAG services locally with proper environment checks.
- **scripts/service_management/graphrag-service.sh**: **PRIMARY SERVICE MANAGEMENT SCRIPT** - Comprehensive script for starting, stopping, and monitoring all GraphRAG services locally.
- **bin/graphrag-monitor.py**: Monitors GraphRAG services and restarts them if they crash.
- **scripts/service_management/start_all_services.sh**: Starts all services using tmux (alternative to graphrag-service.sh).
- **scripts/service_management/start_neo4j.sh**: Starts Neo4j server (used by start_all_services.sh).
- **scripts/service_management/start_api_server.sh**: Starts API server (used by start_all_services.sh).
- **scripts/service_management/start_mcp_server.sh**: Starts MCP server (used by start_all_services.sh).
- **scripts/service_management/stop_neo4j.sh**: Stops Neo4j server.
- **scripts/service_management/bugapi-service.sh**: Manages the Bug Tracking API server.
- **scripts/service_management/bugmcp-service.sh**: Manages the Bug Tracking MCP server.

### Database Management

- **scripts/clean_database.py**: **PRIMARY DATABASE CLEANING SCRIPT** - Clears both Neo4j and ChromaDB.
- **scripts/reset_chromadb.py**: Resets only the ChromaDB vector database.
- **scripts/clear_neo4j.py**: Clears only the Neo4j database.
- **scripts/initialize_database.py**: Initializes the databases with schema and indexes.
- **scripts/verify_chromadb.py**: Verifies ChromaDB installation and connection.
- **scripts/verify_neo4j.py**: Verifies Neo4j installation and connection.
- **scripts/verify_vector_db.py**: Verifies vector database functionality.
- **scripts/verify_linkage.py**: Verifies the linkage between Neo4j and ChromaDB.

### Document Processing

- **scripts/add_document.py**: Adds a single document to GraphRAG.
- **scripts/add_document_with_concepts.py**: Adds a document with manually specified concepts.
- **scripts/batch_process.py**: Processes multiple documents in batch.
- **scripts/process_ebooks.py**: Processes ebooks from a directory.
- **scripts/extract_concepts_from_documents.py**: Extracts concepts from documents.
- **scripts/extract_concepts_with_llm.py**: Extracts concepts using LLM.
- **scripts/cleanup_duplicates.py**: Identifies and removes duplicate entries.

### Query and Visualization

- **scripts/query_ebooks.py**: Queries the GraphRAG system for ebooks.
- **scripts/query_graphrag.py**: General-purpose query interface.
- **scripts/visualize_graph.py**: Visualizes the knowledge graph.

### Testing

- **scripts/test_concept_extraction.py**: Tests concept extraction.
- **scripts/test_deduplication.py**: Tests deduplication functionality.
- **scripts/test_llm_concept_extraction.py**: Tests LLM-based concept extraction.
- **scripts/test_llm_integration.py**: Tests LLM integration.
- **scripts/test_neo4j_connection.py**: Tests Neo4j connection.
- **scripts/simple_demo.py**: Simple demonstration of GraphRAG functionality.

### Docker Management

- **scripts/docker_build_debug.sh**: Builds Docker image with debug options.
- **scripts/docker_build_run.sh**: Builds and runs Docker container.
- **scripts/docker_stop.sh**: Stops Docker container.

### Installation and Configuration

- **scripts/install_neo4j.sh**: Installs Neo4j locally.
- **scripts/reset_neo4j_password.sh**: Resets Neo4j password.
- **scripts/update_neo4j_config.sh**: Updates Neo4j configuration.
- **scripts/download_nltk_data.py**: Downloads NLTK data.
- **scripts/check_ports.sh**: Checks if required ports are available.

## Tools

- **tools/add_all_ebooks.py**: Adds all ebooks from a directory.
- **tools/add_pdf_documents.py**: Adds PDF documents.
- **tools/add_prompting_ebooks.py**: Adds ebooks about prompting.
- **tools/graphrag**: Command-line interface for GraphRAG.
- **tools/graphrag_mcp_client.py**: MCP client for GraphRAG.
- **tools/list_documents.py**: Lists documents in the system.
- **tools/query_neo4j.py**: Queries Neo4j directly.
- **tools/test_async_processing.py**: Tests asynchronous processing.
- **tools/test_mcp_connection.py**: Tests MCP connection.
- **tools/test_mcp_search.py**: Tests MCP search functionality.

## Configuration Files

- **config/llm_config.json**: Configuration for LLM integration.
- **lmstudio_config.json**: Configuration for LM Studio.
- **neo4j.conf**: Neo4j configuration.
- **docker-compose.yml**: Docker Compose configuration.
- **Dockerfile**: Docker image definition.
- **requirements.txt**: Python dependencies.
- **requirements-update.txt**: Updated Python dependencies.

## Documentation

- **README.md**: Project overview.
- **USAGE_GUIDE.md**: Usage guide.
- **activeDevelopment.md**: Active development notes.
- **systemDesign.md**: System design documentation.
- **docs/database_optimizations.md**: Database optimization documentation.
- **docs/docker_development.md**: Docker development documentation.
- **docs/local_deployment.md**: Local deployment documentation.
- **docs/mcp_server_setup.md**: MCP server setup documentation.
- **specs/Done/**: Completed specifications.
- **specs/Todo/**: Pending specifications.

## Duplicated Functionality

1. **Database Reset Scripts**:
   - `scripts/clean_database.py` (primary)
   - `scripts/reset_chromadb.py` (partial duplicate)
   - `scripts/clear_neo4j.py` (partial duplicate)

2. **Service Management Scripts**:
   - `scripts/service_management/graphrag-service.sh` (primary)
   - `scripts/service_management/start_all_services.sh` (alternative using tmux)
   - Individual start/stop scripts (partial duplicates)

3. **Document Addition Scripts**:
   - `scripts/add_document.py` (primary)
   - `scripts/add_document_with_concepts.py` (specialized version)
   - `tools/add_pdf_documents.py` (specialized version)
   - `tools/add_all_ebooks.py` (specialized version)
   - `tools/add_prompting_ebooks.py` (specialized version)

4. **MCP Testing Scripts**:
   - `tools/test_mcp_connection.py` (primary)
   - `tools/test_mcp_search.py` (specialized version)

## Deprecated Files

1. **Old Test Files**:
   - `test_add_document_with_concepts.py`
   - `test_api_add_document.py`
   - `test_mcp_add_document.py`
   - `test_mcp_add_document_with_concepts.py`
   - `test_mcp_concept.py`
   - `test_mcp_connection.py`
   - `test_mcp_search.py`
   - `test_mcp_search_graphrag.py`

2. **Removed Scripts**:
   - `scripts/start_api_local.sh` (removed - functionality covered by graphrag-service.sh)
   - `scripts/start_mcp_local.sh` (removed - functionality covered by graphrag-service.sh)
   - `scripts/reset_database.py` (removed - functionality covered by clean_database.py)
   - `tools/reset_databases.py` (removed - functionality covered by clean_database.py)
   - `scripts/check_neo4j_connection.py` (removed - functionality covered by verify_neo4j.py)
   - `scripts/check_neo4j.py` (removed - functionality covered by verify_neo4j.py)
   - `scripts/optimized_add_document.py` (removed - optimizations should be merged into add_document.py)
   - `tools/test_mcp_client.py` (removed - functionality covered by test_mpc_connection.py)
   - `mcp_settings.json` (removed - replaced by more specific configuration files)
   - `run-git.sh` (removed - temporary utility)
   - `test_lmstudio_direct.py` (removed - test script)
   - `test_lmstudio_spacy.py` (removed - test script)

## Recommended Files for Running Services Locally

### Essential Service Management

- **scripts/start-graphrag-local.sh**: Use this as the main entry point for starting all GraphRAG services locally.
  ```bash
  # Start all services
  ./scripts/start-graphrag-local.sh
  ```

- **scripts/service_management/graphrag-service.sh**: Use this for more fine-grained control over the services.
  ```bash
  # Start all services
  ./scripts/service_management/graphrag-service.sh start

  # Check status
  ./scripts/service_management/graphrag-service.sh status

  # Stop all services
  ./scripts/service_management/graphrag-service.sh stop

  # Restart all services
  ./scripts/service_management/graphrag-service.sh restart

  # Start individual services
  ./scripts/service_management/graphrag-service.sh start-neo4j
  ./scripts/service_management/graphrag-service.sh start-api
  ./scripts/service_management/graphrag-service.sh start-mcp
  ```

### Database Management

- **scripts/clean_database.py**: Use this as the primary script for clearing both Neo4j and ChromaDB.
  ```bash
  # Clear both databases with confirmation
  python scripts/clean_database.py

  # Clear both databases without confirmation
  python scripts/clean_database.py --yes

  # Clear only Neo4j
  python scripts/clean_database.py --neo4j

  # Clear only ChromaDB
  python scripts/clean_database.py --chromadb
  ```

### Document Processing

- **scripts/add_document.py**: Use this for adding individual documents.
  ```bash
  python scripts/add_document.py /path/to/document.pdf
  ```

- **tools/test_async_processing.py**: Use this for asynchronous processing of documents.
  ```bash
  python tools/test_async_processing.py add-document /path/to/document.pdf
  python tools/test_async_processing.py add-folder /path/to/folder
  python tools/test_async_processing.py list-jobs
  python tools/test_async_processing.py cancel-job job_id
  ```

### Querying

- **scripts/query_graphrag.py**: Use this for querying the GraphRAG system.
  ```bash
  python scripts/query_graphrag.py "your query here"
  ```

## Conclusion

The GraphRAG project has a comprehensive set of tools and scripts for managing the system. The primary scripts for local deployment are:

1. **scripts/start-graphrag-local.sh** as the main entry point for starting all services
2. **scripts/service_management/graphrag-service.sh** for detailed service management
3. **scripts/clean_database.py** for database management
4. **scripts/add_document.py** and **scripts/document_processing/test_async_processing.py** for document processing
5. **scripts/query_graphrag.py** for querying

There is some duplication in functionality, particularly in database reset scripts and service management scripts. The deprecated files are mostly old test files that have been replaced by newer versions.