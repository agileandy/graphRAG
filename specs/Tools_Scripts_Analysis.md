# Tools and Scripts Analysis

This document provides an inventory and functional analysis of scripts located in the `./tools` and `./scripts` directories, identifies potential overlaps, and offers initial recommendations.

## `./tools` Directory Analysis

*   **Inventory:** No files or subdirectories found in `./tools`.
*   **Functional Analysis:** Not applicable.
*   **Observations:** The `./tools` directory is currently empty. Its intended purpose should be clarified or it could be removed if not planned for future use.

## `./scripts` Directory Analysis

### Root Level Scripts:

1.  **`check_db_indexes.py`**
    *   **Purpose:** Checks database indexes and optimizations for Neo4j and ChromaDB.
    *   **Functionality:**
        *   Connects to Neo4j, lists indexes and constraints.
        *   Connects to ChromaDB, checks collection information and metadata.
    *   **Dependencies:** `src.database.neo4j_db`, `src.database.vector_db`.
    *   **Arguments:** None.
    *   **Observations:** Useful for database health checks and diagnostics.

2.  **`check_ports.sh`**
    *   **Purpose:** Checks if required network ports are available.
    *   **Functionality:**
        *   Loads environment variables from `.env` (if present).
        *   Defines default ports for Neo4j, API, MCP, Bug MCP.
        *   Uses `lsof` to check if ports are in use.
    *   **Dependencies:** `lsof`, `.env` file (optional).
    *   **Arguments:** None.
    *   **Observations:** Essential for ensuring services can start without port conflicts.

3.  **`check_python_version.sh`**
    *   **Purpose:** Verifies that the Python version in the specified virtual environment matches an expected version.
    *   **Functionality:**
        *   Checks for the existence of the `.venv-py312` virtual environment.
        *   Compares the Python version within the venv against `EXPECTED_VERSION="3.12.8"`.
        *   Provides instructions to recreate the venv if versions mismatch.
    *   **Dependencies:** `uv` (for venv creation instructions), specific Python version (`3.12.8`).
    *   **Arguments:** None.
    *   **Observations:** Helps maintain environment consistency. The Python path in the script is hardcoded for a specific user (`/Users/andyspamer/...`).

4.  **`extract_concepts_with_openrouter.sh`**
    *   **Purpose:** A wrapper script to extract concepts from documents using an LLM via OpenRouter.
    *   **Functionality:**
        *   Activates the Python virtual environment.
        *   Parses command-line arguments for collection name, limit, batch size, text length, chunk size/overlap, and config path.
        *   Calls `scripts/document_processing/extract_concepts_with_llm.py` with the provided arguments.
    *   **Dependencies:** Python virtual environment, `scripts/document_processing/extract_concepts_with_llm.py`, `config/openrouter_config.json`.
    *   **Arguments:** `--collection`, `--limit`, `--batch-size`, `--min-text-length`, `--chunk-size`, `--chunk-overlap`.
    *   **Observations:** Provides a command-line interface for LLM-based concept extraction.

5.  **`install-dependencies.sh`**
    *   **Purpose:** Installs Python dependencies.
    *   **Functionality:** Uses `uv pip install -r requirements.txt` to install dependencies.
    *   **Dependencies:** `uv`, `requirements.txt`.
    *   **Arguments:** None.
    *   **Observations:** Standard dependency installation script.

6.  **`run_automated_audit.py`**
    *   **Purpose:** Performs an automated code audit using the `aider` tool.
    *   **Functionality:**
        *   Defines audit sections (project structure, code quality, documentation, git, workflow, security, testing, configuration).
        *   Generates prompts for `aider` for each section.
        *   Runs `aider` (with `--no-auto-commit`, `--no-git` flags) and parses its output.
        *   Generates a markdown audit report (`./project/audit/audit-report.md`).
    *   **Dependencies:** `aider` tool, Python 3.
    *   **Arguments:** None.
    *   **Observations:** A comprehensive audit tool leveraging an external AI coding assistant.

7.  **`simple_openrouter_test.py`**
    *   **Purpose:** A basic test script for the OpenRouter API.
    *   **Functionality:**
        *   Sends a predefined prompt to a specified OpenRouter model (`meta-llama/llama-4-maverick:free`).
        *   Prints the API response.
        *   API key is hardcoded.
    *   **Dependencies:** `requests` library.
    *   **Arguments:** None.
    *   **Observations:** Useful for quick OpenRouter API connectivity and functionality checks. Hardcoded API key is a security risk.

8.  **`start_bug_service.sh`**
    *   **Purpose:** Starts the bug tracking API server (`bugMCP/bugAPI.py`).
    *   **Functionality:**
        *   Checks if the service is already running on the defined port.
        *   Starts `bugMCP/bugAPI.py` using `nohup` and logs output.
        *   Manages a PID file (`$HOME/.graphrag/pids/bug_api.pid`).
        *   Waits for the server to start and verifies.
    *   **Dependencies:** Python virtual environment, `bugMCP/bugAPI.py`, `nc`.
    *   **Arguments:** None (port is hardcoded or from env).
    *   **Observations:** A simple service runner for the bug API.

9.  **`start-graphrag-local.sh`**
    *   **Purpose:** Starts the complete GraphRAG service locally.
    *   **Functionality:**
        *   Checks for Neo4j installation, virtual environment, Python version, and required Python packages.
        *   Calls `scripts/service_management/graphrag-service.sh start` to start all services.
        *   Prints usage instructions for other scripts.
    *   **Dependencies:** `neo4j` (brew), `uv`, `scripts/check_python_version.sh`, `scripts/service_management/graphrag-service.sh`.
    *   **Arguments:** None.
    *   **Observations:** Acts as a primary entry point for starting the local development environment.

10. **`test_openrouter.py`**
    *   **Purpose:** Tests OpenRouter integration for text generation and concept extraction.
    *   **Functionality:**
        *   Loads LLM configuration (primary and fallback providers).
        *   Sets up an `LLMManager`.
        *   Tests text generation with a sample prompt.
        *   Tests concept extraction and relationship analysis from a sample text using `src.llm.concept_extraction` functions.
    *   **Dependencies:** `src.llm.llm_provider`, `src.llm.concept_extraction`, `config/openrouter_config.json`.
    *   **Arguments:** None.
    *   **Observations:** More comprehensive test for OpenRouter integration than `simple_openrouter_test.py`.

11. **`test_relationship_strength.py`**
    *   **Purpose:** Tests relationship strength analysis using OpenRouter.
    *   **Functionality:**
        *   Loads LLM configuration and sets up `LLMManager`.
        *   Defines a set of sample concepts.
        *   Calls `analyze_concept_relationships` from `src.llm.concept_extraction`.
        *   Prints identified relationships grouped by strength.
    *   **Dependencies:** `src.llm.llm_provider`, `src.llm.concept_extraction`, `config/openrouter_config.json`.
    *   **Arguments:** None.
    *   **Observations:** Focused test for the relationship strength analysis feature.

12. **`update_docs_port_references.py`**
    *   **Purpose:** Updates hardcoded port references in documentation files.
    *   **Functionality:**
        *   Scans `.md`, `.txt`, `.json` files in `docs`, `specs`, `bugMCP` directories.
        *   Uses regex to find hardcoded ports and replaces them with environment variable placeholders (e.g., `${GRAPHRAG_PORT_SERVICE}`).
        *   Uses `src.config.ports` for the mapping of ports to service names.
    *   **Dependencies:** `src.config.ports`.
    *   **Arguments:** None.
    *   **Observations:** Helps maintain consistency in documentation regarding port numbers.

13. **`update_port_references.py`**
    *   **Purpose:** Scans the codebase for hardcoded port numbers and suggests replacements.
    *   **Functionality:**
        *   Scans various file types (`.py`, `.sh`, `.md`, etc.) across the project.
        *   Uses regex to find hardcoded ports.
        *   Suggests replacements using `get_port('service_name')` based on `src.config.ports`.
        *   Does not automatically apply changes, only reports findings.
    *   **Dependencies:** `src.config.ports`.
    *   **Arguments:** None.
    *   **Observations:** Useful for identifying and refactoring hardcoded ports in the codebase.

---

### `./scripts/database_management/` Directory:

1.  **`clean_database.py`**
    *   **Purpose:** Clears data from Neo4j (logically or physically) and resets ChromaDB.
    *   **Functionality:**
        *   Logically clears Neo4j by deleting all nodes and relationships.
        *   Optionally, physically deletes Neo4j data files (stops/restarts Neo4j service via `scripts/stop_neo4j.sh` and `scripts/start_neo4j.sh`).
        *   Resets ChromaDB by deleting and recreating its persistence directory.
    *   **Dependencies:** `src.database.neo4j_db`, `src.database.vector_db`, `dotenv`, `scripts/stop_neo4j.sh`, `scripts/start_neo4j.sh` (for physical delete).
    *   **Arguments:** `--neo4j`, `--chromadb`, `--physical-delete`, `--no-restart`, `--yes` (skip confirmation).
    *   **Observations:** Provides comprehensive database cleaning options.

2.  **`cleanup_duplicates.py`**
    *   **Purpose:** Finds and reports duplicate documents in ChromaDB.
    *   **Functionality:**
        *   Connects to ChromaDB 'documents' collection.
        *   Retrieves all documents and groups them by a 'hash' field in their metadata.
        *   Reports sets of documents with identical hashes.
        *   Includes a placeholder function `remove_duplicate_document` which is not fully implemented for safe removal with relationship handling.
    *   **Dependencies:** `src.database.neo4j_db` (for planned removal), `src.database.vector_db`.
    *   **Arguments:** None.
    *   **Observations:** Useful for identifying duplicates. The removal part needs careful implementation.

3.  **`clear_neo4j.py`**
    *   **Purpose:** Clears all data from the Neo4j database.
    *   **Functionality:** Connects to Neo4j and executes `MATCH (n) DETACH DELETE n`.
    *   **Dependencies:** `neo4j` library, `src.config` (for port).
    *   **Arguments:** None.
    *   **Observations:** A focused script for wiping Neo4j. `clean_database.py` offers similar logical clear functionality.

4.  **`initialize_database.py`**
    *   **Purpose:** Initializes Neo4j (constraints, indexes) and VectorDB (ChromaDB).
    *   **Functionality:**
        *   Waits for Neo4j connection.
        *   Creates UNIQUE constraints for `Book.id` and `Concept.id`.
        *   Creates indexes on various properties of `Book`, `Chapter`, `Section`, and `Concept` nodes.
        *   Verifies VectorDB connection (ChromaDB auto-creates collection).
    *   **Dependencies:** `src.database.neo4j_db`, `src.database.vector_db`.
    *   **Arguments:** None.
    *   **Observations:** Essential for setting up the database schema for the first time, especially in Docker environments.

5.  **`optimize_existing_data.py`**
    *   **Purpose:** Optimizes existing data in the vector database by re-chunking and re-indexing.
    *   **Functionality:**
        *   Retrieves all documents from ChromaDB.
        *   Groups document chunks by their original source document ID.
        *   For each source document, combines its chunks, then re-processes (chunks) the full text with potentially new chunking parameters.
        *   Deletes old chunks and adds new, optimized chunks to ChromaDB.
    *   **Dependencies:** `src.database.vector_db`, `src.processing.document_processor`.
    *   **Arguments:** `--chunk-size`, `--overlap`, `--batch-size`, `--dry-run`, `--yes`.
    *   **Observations:** Useful for improving data quality in the vector store if chunking strategies change.

6.  **`repair_vector_index.py`**
    *   **Purpose:** Checks and attempts to repair the ChromaDB vector index.
    *   **Functionality:**
        *   Uses `vector_db.check_index_health()` and `vector_db.repair_index()`.
        *   Verifies health after repair and tests a simple query.
    *   **Dependencies:** `src.database.vector_db`.
    *   **Arguments:** `--force`, `--verify`.
    *   **Observations:** Addresses potential issues with ChromaDB index health.

7.  **`reset_chromadb.py`**
    *   **Purpose:** Resets the ChromaDB database.
    *   **Functionality:**
        *   Deletes the ChromaDB persistence directory.
        *   Recreates the directory.
        *   Initializes a new ChromaDB database and adds dummy data.
    *   **Dependencies:** `src.utils.db_utils` (for version check), `src.database.vector_db`.
    *   **Arguments:** None.
    *   **Observations:** A focused script for wiping ChromaDB. `clean_database.py` offers similar functionality.

8.  **`verify_chromadb.py`**
    *   **Purpose:** Verifies ChromaDB installation, configuration, connection, and basic operations.
    *   **Functionality:**
        *   Checks ChromaDB version and database directories.
        *   Tests connection, document count, adding a test document, querying, and retrieving by ID.
    *   **Dependencies:** `src.utils.db_utils`, `src.database.vector_db`.
    *   **Arguments:** None.
    *   **Observations:** Good for diagnosing ChromaDB setup issues.

9.  **`verify_linkage.py`**
    *   **Purpose:** Verifies the linkage and interaction between Neo4j and the vector database.
    *   **Functionality:**
        *   Tests hybrid search (`db_linkage.hybrid_search`).
        *   Tests `db_linkage.get_node_chunks`.
        *   Tests `db_linkage.get_related_nodes`.
    *   **Dependencies:** `src.database.neo4j_db`, `src.database.vector_db`, `src.database.db_linkage`.
    *   **Arguments:** None.
    *   **Observations:** Important for ensuring the core RAG functionality is working.

10. **`verify_neo4j.py`**
    *   **Purpose:** Verifies Neo4j database connection and setup.
    *   **Functionality:**
        *   Tests connection.
        *   Calls `neo4j_db.create_schema()` (which creates constraints and indexes).
        *   Checks for existing data or creates dummy data.
        *   Runs a test query to count nodes.
    *   **Dependencies:** `src.database.neo4j_db`.
    *   **Arguments:** None.
    *   **Observations:** Good for diagnosing Neo4j setup issues. `initialize_database.py` also handles schema creation.

11. **`verify_vector_db.py`**
    *   **Purpose:** Verifies vector database (ChromaDB) connection and setup.
    *   **Functionality:**
        *   Tests connection.
        *   Creates dummy data.
        *   Runs test queries (count, specific query).
    *   **Dependencies:** `src.database.vector_db`.
    *   **Arguments:** None.
    *   **Observations:** Similar to `verify_chromadb.py`, potentially redundant.

---

### `./scripts/document_processing/` Directory:

1.  **`add_50_random_ebooks.py`**
    *   **Purpose:** Selects 50 random PDF ebooks from a specified directory and adds them to GraphRAG via an MPC server.
    *   **Functionality:**
        *   Scans a directory for PDF files (recursively).
        *   Randomly selects 50 files.
        *   Connects to an MPC server (default `ws://localhost:8766`).
        *   Uses `process_pdf_file` function (imported from `add_ebooks_batch.py`) to process and send each selected PDF to the MPC server.
    *   **Dependencies:** `add_ebooks_batch.py` (for `process_pdf_file`), `websockets` library. `PyPDF2` is an indirect dependency via `add_ebooks_batch.py`.
    *   **Arguments:** None (directory and number of books are hardcoded).
    *   **Observations:** Useful for populating the database with a random subset of ebooks for testing.

2.  **`add_document_core.py`**
    *   **Purpose:** Core script for adding a single document (text and metadata) to the GraphRAG system, including entity/relationship extraction and database updates.
    *   **Functionality:**
        *   Extracts entities from metadata (if 'concepts' field present) and text (using `ConceptExtractor` which supports rule-based, NLP, and LLM methods).
        *   Extracts relationships between entities (rule-based and relevance-based).
        *   Performs duplicate detection using `DuplicateDetector`.
        *   Adds document, entities, and relationships to Neo4j and ChromaDB directly (not via MPC).
        *   Handles chunking for large documents before adding to vector DB.
    *   **Dependencies:** `src.database.neo4j_db`, `src.database.vector_db`, `src.database.db_linkage`, `src.processing.duplicate_detector`, `src.processing.concept_extractor`.
    *   **Arguments:** (Called as a library) `text`, `metadata`, `neo4j_db`, `vector_db`, `duplicate_detector`.
    *   **Observations:** A central piece of logic for document ingestion and graph building.

3.  **`add_document_with_concepts.py`**
    *   **Purpose:** Adds a document to GraphRAG, with a focus on explicitly provided concepts in metadata.
    *   **Functionality:**
        *   Extracts entities from a 'concepts' field in metadata and from text using a simpler keyword-based approach.
        *   Extracts basic relationships (all pairs).
        *   Adds document, entities, and relationships to Neo4j and ChromaDB directly.
    *   **Dependencies:** `src.database.neo4j_db`, `src.database.vector_db`.
    *   **Arguments:** (Called as a library) `text`, `metadata`, `neo4j_db`, `vector_db`.
    *   **Observations:** Appears to be an earlier or alternative version of `add_document_core.py` with less sophisticated extraction.

4.  **`add_ebooks_batch.py`**
    *   **Purpose:** Adds all PDF ebooks from specified directories to GraphRAG via an MPC server.
    *   **Functionality:**
        *   Connects to an MPC server.
        *   Scans specified root directory for subdirectories (categories).
        *   For each PDF file found (recursively or not based on arg):
            *   Extracts text using `PyPDF2`.
            *   Chunks text if it exceeds `MAX_MESSAGE_SIZE`.
            *   Sends document text and metadata to the MPC server's "add-document" action.
    *   **Dependencies:** `PyPDF2`, `websockets` library.
    *   **Arguments:** `--url` (MPC server), `--root` (ebooks root dir), `--recursive`, `--directory` (specific dir), `--file` (single file), `--verbose`.
    *   **Observations:** Primary script for batch ingesting ebooks through the MPC server.

5.  **`add_pdf_documents.py`**
    *   **Purpose:** Adds PDF documents from a local folder to GraphRAG via an MPC server.
    *   **Functionality:**
        *   Connects to an MPC server.
        *   Processes a single specified PDF file or all PDFs in a specified folder.
        *   Extracts text using `PyPDF2`.
        *   Sends document text and metadata (including hardcoded "concepts" string) to MPC server's "add-document" action.
    *   **Dependencies:** `PyPDF2`, `websockets` library.
    *   **Arguments:** `--url` (MPC server), `--folder`, `--file`.
    *   **Observations:** Similar to `add_ebooks_batch.py` but perhaps intended for more generic PDFs rather than a structured ebook library. Metadata for concepts is hardcoded.

6.  **`add_prompting_ebooks.py`**
    *   **Purpose:** Adds "prompting" ebooks to GraphRAG via an MPC server and includes query/exploration features.
    *   **Functionality:**
        *   Connects to an MPC server.
        *   Can add an entire folder of PDFs or individual PDF files by sending "add-folder" or "add-document" actions to MPC.
        *   Includes options to search, get concept info, and get related concepts via MPC actions.
    *   **Dependencies:** `websockets` library. (PDF processing is presumably handled by the MPC server).
    *   **Arguments:** `--url`, `--folder`, `--method` (folder/individual), `--verify`, `--search-only`, `--query`, `--concept`, `--related`.
    *   **Observations:** Combines ingestion with querying capabilities, all through the MPC server.

7.  **`batch_process.py`**
    *   **Purpose:** Batch processes multiple documents of various types from a directory into GraphRAG.
    *   **Functionality:**
        *   Uses `FileHandler` to process supported file types (PDF, DOCX, etc.) and also manually handles `.txt` and `.json`.
        *   For each file, extracts text and metadata.
        *   Calls `add_document_to_graphrag` (from `add_document_core.py`) to ingest into Neo4j and ChromaDB directly.
    *   **Dependencies:** `src.database.neo4j_db`, `src.database.vector_db`, `src.processing.duplicate_detector`, `src.processing.file_handler`, `scripts.document_processing.add_document_core`.
    *   **Arguments:** `--dir` (directory to process), `--create-examples`, `--example-dir`.
    *   **Observations:** A generic batch processor for various file types, interacting directly with databases.

8.  **`extract_concepts_from_documents.py`**
    *   **Purpose:** Retrieves documents from the vector database, extracts concepts, and adds them to the graph database.
    *   **Functionality:**
        *   Connects to VectorDB and GraphDB.
        *   Uses `ConceptExtractor` (configurable for NLP, LLM, domain) to extract and weight concepts from document text.
        *   Adds concepts to Neo4j and creates `MENTIONS` relationships between documents and concepts.
    *   **Dependencies:** `src.database.vector_db`, `src.database.graph_db`, `src.processing.concept_extractor`, `tqdm`.
    *   **Arguments:** `--collection`, `--limit`, `--min-concept-length`, `--max-concept-length`, `--min-concept-weight`, `--use-nlp`, `--use-llm`, `--domain`.
    *   **Observations:** Post-processes documents already in the vector store to enrich the knowledge graph with concepts.

9.  **`extract_concepts_with_llm.py`**
    *   **Purpose:** Extracts concepts from documents using an LLM (two-pass approach), analyzes relationships, and adds to the graph database.
    *   **Functionality:**
        *   Connects to VectorDB and GraphDB.
        *   Retrieves documents.
        *   Uses `extract_concepts_two_pass` and `analyze_concept_relationships` from `src.llm.concept_extraction` with an `LLMManager`.
        *   Adds concepts and their relationships to Neo4j.
        *   Optionally generates and stores summaries in Neo4j.
    *   **Dependencies:** `src.database.vector_db`, `src.database.graph_db`, `src.llm.llm_provider`, `src.llm.concept_extraction`, `tqdm`.
    *   **Arguments:** `--collection`, `--limit`, `--batch-size`, `--config` (LLM config), `--min-text-length`, `--chunk-size`, `--chunk-overlap`.
    *   **Observations:** Focuses on a sophisticated LLM-based approach for concept and relationship extraction.

10. **`process_ebooks.py`**
    *   **Purpose:** Processes PDF ebooks to extract text, chunk, extract entities (rule-based for "prompt engineering"), and build a graph directly in Neo4j and ChromaDB.
    *   **Functionality:**
        *   Extracts text from PDFs using `PyPDF2`.
        *   Chunks text.
        *   Extracts entities based on a predefined `PROMPT_ENGINEERING_CONCEPTS` dictionary.
        *   Extracts basic co-occurrence relationships.
        *   Adds book nodes, concept nodes, and relationships to Neo4j.
        *   Adds text chunks with metadata to ChromaDB.
    *   **Dependencies:** `PyPDF2`, `src.database.neo4j_db`, `src.database.vector_db`, `src.config`.
    *   **Arguments:** `--dir` (ebooks directory), `--limit` (files), `--chunk-size`, `--overlap`, `--reprocess`.
    *   **Observations:** A self-contained script for processing ebooks with a specific focus on prompt engineering concepts and direct database interaction.

---

### `./scripts/query/` Directory:

1.  **`list_documents.py`**
    *   **Purpose:** Lists documents in the GraphRAG system by querying an MPC server.
    *   **Functionality:** Connects to MPC (default `ws://localhost:8766`) and sends a "documents" action.
    *   **Dependencies:** `websockets` library.
    *   **Arguments:** `limit` (optional, command line).
    *   **Observations:** Simple utility for viewing documents via MPC.

2.  **`query_ebooks.py`**
    *   **Purpose:** Provides specialized queries for exploring an ebook knowledge graph (Neo4j and ChromaDB directly).
    *   **Functionality:**
        *   Finds books mentioning a concept.
        *   Finds concepts related to a concept (multi-hop).
        *   Finds passages (chunks from ChromaDB) about a concept.
        *   Performs hybrid search using `DatabaseLinkage`.
    *   **Dependencies:** `src.database.neo4j_db`, `src.database.vector_db`, `src.database.db_linkage`.
    *   **Arguments:** `--books` (concept), `--related` (concept), `--passages` (concept), `--search` (query), `--limit`, `--hops`. Offers interactive mode if no args.
    *   **Observations:** Tailored for an ebook graph structure.

3.  **`query_graphrag.py`**
    *   **Purpose:** General script for querying the GraphRAG system (Neo4j and ChromaDB directly).
    *   **Functionality:**
        *   Performs hybrid search using `DatabaseLinkage`.
        *   Explores a concept and its direct relations in Neo4j.
        *   Gets documents related to a concept from ChromaDB.
    *   **Dependencies:** `src.database.neo4j_db`, `src.database.vector_db`, `src.database.db_linkage`.
    *   **Arguments:** `--query`, `--concept`, `--documents`. Offers interactive mode if no args.
    *   **Observations:** A general-purpose query tool for direct database interaction.

4.  **`query_neo4j.py`**
    *   **Purpose:** Allows direct querying of the Neo4j database.
    *   **Functionality:**
        *   Provides functions to test connection, get node/relationship/concept/document counts.
        *   Get all concepts, concept by name, related concepts, documents by concept.
        *   Allows running custom Cypher queries.
    *   **Dependencies:** `neo4j` library, `src.config` (for port).
    *   **Arguments:** Various flags for predefined queries (`--test`, `--counts`, `--concepts`, etc.) or `--query` for custom Cypher.
    *   **Observations:** Powerful utility for direct Neo4j inspection and debugging.

5.  **`visualize_graph.py`**
    *   **Purpose:** Visualizes the Neo4j knowledge graph using Pyvis.
    *   **Functionality:**
        *   Visualizes concepts and their relationships.
        *   Visualizes books and their related concepts (all or specific book).
        *   Visualizes a concept and its neighborhood (multi-hop).
        *   Exports graph data (nodes, relationships) to a JSON file.
        *   Saves visualizations as HTML files and attempts to open them in a browser.
    *   **Dependencies:** `src.database.neo4j_db`, `pyvis` library.
    *   **Arguments:** Various flags (`--concepts`, `--books`, `--book`, `--concept`, `--export`), `--limit`, `--hops`, `--output`. Offers interactive mode.
    *   **Observations:** Excellent tool for understanding the graph structure visually.

---

### `./scripts/service_management/` Directory:

1.  **`bugapi-service.sh`**
    *   **Purpose:** Manages the Bug Tracking API server (`bugMCP/bugAPI.py`).
    *   **Functionality:** Start, stop, restart, status check. Uses `pgrep`/`pkill`. Logs to `bugMCP/bugapi.log`.
    *   **Dependencies:** Python venv, `bugMCP/bugAPI.py`, `netstat` (optional for status).
    *   **Arguments:** `start|stop|status|restart`, `--host`, `--port`, `--log-level`.
    *   **Observations:** Standard service script for the bug API.

2.  **`bugmcp-service.sh`**
    *   **Purpose:** Manages the Bug Tracking MCP server (`bugMCP/bugMCP_mcp.py`).
    *   **Functionality:** Start, stop, restart, status check. Uses `pgrep`/`pkill`. Logs to `bugMCP/bugmcp.log`.
    *   **Dependencies:** Python venv, `bugMCP/bugMCP_mcp.py`, `netstat` (optional for status).
    *   **Arguments:** `start|stop|status|restart`, `--host`, `--port`, `--log-level`.
    *   **Observations:** Standard service script for the bug MCP. Very similar structure to `bugapi-service.sh`.

3.  **`graphrag-service-improved.sh`**
    *   **Purpose:** Improved service management for core GraphRAG services (Neo4j, API, MCP).
    *   **Functionality:** Start, stop, restart, status. Uses `.env` for config. Robust port and process checks. Graceful and force kill for API/MCP.
    *   **Dependencies:** Neo4j, Python venv, `gunicorn`, `src.api.wsgi:app`, `src.mcp.server`, `nc`, `lsof`.
    *   **Arguments:** `start|stop|restart|status`.
    *   **Observations:** A more refined service script than the basic `graphrag-service.sh`.

4.  **`graphrag-service-robust.sh`**
    *   **Purpose:** Enhanced and robust service management for GraphRAG (Neo4j, API, MCP).
    *   **Functionality:** Start, stop, restart, status. Uses `~/.graphrag/config.env`. Manages PID files in `~/.graphrag/pids`. Extensive checks for running processes and port usage.
    *   **Dependencies:** Neo4j, Python venv, `gunicorn`, `src.api.wsgi:app`, `src.mcp.server`, `nc`, `curl`, `lsof`.
    *   **Arguments:** `start|stop|restart|status`.
    *   **Observations:** Appears to be the most comprehensive and robust service management script.

5.  **`graphrag-service.sh`**
    *   **Purpose:** General service management for GraphRAG (Neo4j, API, MCP, Bug API).
    *   **Functionality:** Start, stop, restart, status. Uses `.env` for config. Manages PID files.
    *   **Dependencies:** Neo4j, Python venv, `gunicorn`, `src.api.wsgi:app`, `src.mcp.server`, `bugMCP/bugAPI.py`, `nc`, `lsof`.
    *   **Arguments:** `start|stop|restart|status`.
    *   **Observations:** A general script covering more services than `graphrag-service-improved.sh` but perhaps less refined in its checks than `graphrag-service-robust.sh`.

6.  **`graphrag-simple.sh`**
    *   **Purpose:** A very basic service management script for GraphRAG (Neo4j, API, MCP).
    *   **Functionality:** Start, stop, restart, status, force-kill. Uses hardcoded default paths and ports.
    *   **Dependencies:** Neo4j, Python venv, `gunicorn`, `src.api.wsgi:app`, `src.mcp.server`, `nc`, `lsof`.
    *   **Arguments:** `start|stop|restart|status|force-kill` and individual service start/stop commands.
    *   **Observations:** A minimal approach, less configurable.

7.  **`start_all_services.sh`**
    *   **Purpose:** Starts all core GraphRAG services (Neo4j, API, MCP) in separate `tmux` windows.
    *   **Functionality:** Creates a `tmux` session named `graphrag` and starts each service in a new window by calling their respective start scripts.
    *   **Dependencies:** `tmux`, `./scripts/start_neo4j.sh`, `./scripts/start_api_server.sh`, `./scripts/service_management/start_mcp_server.sh`.
    *   **Arguments:** None.
    *   **Observations:** Provides a convenient way to manage multiple services in a terminal session.

8.  **`start_api_server.sh`**
    *   **Purpose:** Starts the GraphRAG API server.
    *   **Functionality:** Activates Python venv, installs project in editable mode (`uv pip install -e .`), then starts `gunicorn` with `src.api.wsgi:app`.
    *   **Dependencies:** Python venv, `uv`, `gunicorn`, `src.api.wsgi:app`.
    *   **Arguments:** None (port from `GRAPHRAG_API_PORT` or default 5001).
    *   **Observations:** Focused script for starting just the API server.

9.  **`start_mcp_server.sh`**
    *   **Purpose:** Starts the GraphRAG MCP server.
    *   **Functionality:** Runs `python -m src.mcp.server`.
    *   **Dependencies:** Python venv, `src.mcp.server`.
    *   **Arguments:** Passes through any arguments (`$@`) to the Python module.
    *   **Observations:** Simple script to launch the MCP server module.

10. **`start_mpc_server.sh`**
    *   **Purpose:** Identical to `start_mcp_server.sh`.
    *   **Functionality:** Runs `python -m src.mcp.server`.
    *   **Dependencies:** Python venv, `src.mcp.server`.
    *   **Arguments:** Passes through any arguments (`$@`) to the Python module.
    *   **Observations:** This is a duplicate/typo of `start_mcp_server.sh`.

11. **`start_neo4j.sh`**
    *   **Purpose:** Starts the Neo4j server.
    *   **Functionality:** Calls `neo4j console` using a hardcoded path to the Neo4j binary (`/Users/andyspamer/.local/neo4j/bin/neo4j`).
    *   **Dependencies:** Neo4j installation at the specified hardcoded path.
    *   **Arguments:** None.
    *   **Observations:** Very simple but path is hardcoded, making it not portable.

12. **`stop_neo4j.sh`**
    *   **Purpose:** Stops the Neo4j server.
    *   **Functionality:** Calls `neo4j stop` using a hardcoded path to the Neo4j binary.
    *   **Dependencies:** Neo4j installation at the specified hardcoded path.
    *   **Arguments:** None.
    *   **Observations:** Very simple, path hardcoded.

---

## Identified Overlaps and Redundancies

### 1. Service Management Scripts:
*   **High Overlap:** `graphrag-service-improved.sh`, `graphrag-service-robust.sh`, `graphrag-service.sh`, and `graphrag-simple.sh` all provide start/stop/restart/status functionality for Neo4j, API, and MCP servers. They vary in terms of configuration sources (`.env`, `~/.graphrag/config.env`, hardcoded), PID management, and robustness of checks.
    *   `graphrag-service-robust.sh` appears to be the most feature-complete for core services.
    *   `graphrag-service.sh` additionally manages the Bug API.
*   **Component Scripts:** `start_api_server.sh`, `start_mcp_server.sh`, `start_neo4j.sh`, `stop_neo4j.sh` are more granular and are used by `start_all_services.sh` or can be run independently.
*   **Orchestration:** `start_all_services.sh` uses `tmux` to manage multiple services, a different approach from the single-script managers.
*   **Bug Tracking Services:** `bugapi-service.sh` and `bugmcp-service.sh` are dedicated to the bug tracking components. `graphrag-service.sh` also includes Bug API management.
*   **Typo/Duplicate:** `start_mpc_server.sh` is identical to `start_mcp_server.sh`.

### 2. Document Ingestion and Processing:
*   **Core Logic:** `add_document_core.py` (uses `ConceptExtractor`) and `add_document_with_concepts.py` (simpler extraction) both define core logic for adding documents directly to databases. `add_document_core.py` seems more current.
*   **PDF Ingestion via MPC:** `add_ebooks_batch.py`, `add_pdf_documents.py`, `add_prompting_ebooks.py`, and `add_50_random_ebooks.py` all handle PDF ingestion through an MPC server. They differ mainly in the scope of files they process (e.g., specific folders, random selection) and some metadata handling. `add_50_random_ebooks.py` reuses logic from `add_ebooks_batch.py`.
*   **Direct PDF Ingestion:** `process_ebooks.py` ingests PDFs directly into databases with its own rule-based entity extraction, overlapping with the MPC-based PDF scripts and the general `add_document_core.py`.
*   **Generic Batch Processing:** `batch_process.py` uses `FileHandler` for various file types and `add_document_core.py` for direct database ingestion, providing a more generic alternative to the PDF-specific scripts.

### 3. Concept Extraction:
*   **Multiple Approaches:**
    *   `extract_concepts_from_documents.py` uses `ConceptExtractor` (configurable for NLP/LLM).
    *   `extract_concepts_with_llm.py` focuses on a specific two-pass LLM approach.
    *   `add_document_core.py` also uses `ConceptExtractor`.
    *   `process_ebooks.py` has its own rule-based entity extraction for "prompt engineering concepts".
    *   `add_document_with_concepts.py` has a very simple keyword-based text entity extraction.
*   These scripts represent different strategies or stages of development for concept extraction.

### 4. Database Cleaning:
*   `clean_database.py` is a comprehensive script that can logically clear Neo4j (similar to `clear_neo4j.py`) and reset ChromaDB (similar to `reset_chromadb.py`). It also offers physical Neo4j deletion.
*   `clear_neo4j.py` and `reset_chromadb.py` are more focused, single-purpose scripts.

### 5. Database Verification:
*   `verify_chromadb.py` and `verify_vector_db.py` are nearly identical in purpose and functionality (verifying ChromaDB).
*   `verify_neo4j.py` and `initialize_database.py` both handle Neo4j schema creation/verification.

### 6. Querying:
*   `query_ebooks.py` and `query_graphrag.py` provide similar functionalities (hybrid search, concept exploration) for direct database querying. `query_ebooks.py` might be more tailored to a specific "ebook" graph structure.
*   `query_neo4j.py` is a general-purpose tool for direct Cypher queries.
*   `add_prompting_ebooks.py` also includes MPC-based search/concept query features.

### 7. Port Configuration Management:
*   `update_docs_port_references.py` (for documentation) and `update_port_references.py` (for codebase) both aim to replace hardcoded ports with configuration-based references, differing only in their target files.

### 8. Path Hardcoding:
*   `check_python_version.sh`, `start_api_server.sh` (venv path), `start_neo4j.sh`, `stop_neo4j.sh` contain hardcoded paths, reducing portability. Some service management scripts also make assumptions about `NEO4J_HOME` or binary locations.

---

## Initial Recommendations

1.  **Consolidate Service Management:**
    *   Evaluate `graphrag-service-robust.sh`, `graphrag-service-improved.sh`, and `graphrag-service.sh`. Select the best one as the primary service management script (likely `graphrag-service-robust.sh` due to its comprehensive checks and PID management).
    *   Standardize configuration loading (e.g., always use `.env` or `~/.graphrag/config.env`).
    *   Decide if the `tmux` approach in `start_all_services.sh` is preferred or if the single service script is sufficient. If `tmux` is kept, ensure it calls the consolidated service script or its components.
    *   Deprecate or absorb functionality from `graphrag-simple.sh`.
    *   Integrate Bug API/MCP management into the chosen primary service script if desired, or keep `bugapi-service.sh` and `bugmcp-service.sh` if modularity is preferred.
    *   Remove the duplicate `start_mpc_server.sh`.

2.  **Streamline Document Ingestion:**
    *   Identify a primary document ingestion pathway. `add_document_core.py` (with `ConceptExtractor`) seems like a strong candidate for direct DB ingestion.
    *   For MPC-based ingestion, consolidate `add_ebooks_batch.py`, `add_pdf_documents.py`, and `add_prompting_ebooks.py` into a single, more configurable script if their core PDF processing and MPC interaction logic is similar.
    *   Clarify the role of `process_ebooks.py`. If its direct DB interaction and specific entity extraction are still needed, ensure it doesn't conflict with other ingestion methods. Otherwise, consider integrating its unique aspects into `add_document_core.py`.
    *   `batch_process.py` is valuable for handling diverse file types directly; ensure its `FileHandler` is comprehensive.

3.  **Unify Concept Extraction:**
    *   Standardize on a primary concept extraction strategy. `ConceptExtractor` (used in `add_document_core.py` and `extract_concepts_from_documents.py`) seems flexible.
    *   If the two-pass LLM approach in `extract_concepts_with_llm.py` is superior, integrate it into `ConceptExtractor` or make it the default LLM method.
    *   Deprecate simpler/older extraction methods in scripts like `add_document_with_concepts.py` and the rule-based one in `process_ebooks.py` if they are superseded.

4.  **Refactor Database Utilities:**
    *   Use `clean_database.py` as the main script for clearing/resetting databases, potentially deprecating the individual `clear_neo4j.py` and `reset_chromadb.py`.
    *   Consolidate `verify_chromadb.py` and `verify_vector_db.py` into one script.
    *   Ensure `initialize_database.py` and `verify_neo4j.py` don't have conflicting schema setup logic. `initialize_database.py` seems more appropriate for the initial setup.

5.  **Standardize Query Scripts:**
    *   If `query_ebooks.py` offers genuinely unique queries for an "ebook" specific schema, keep it. Otherwise, merge its useful functionalities into the more general `query_graphrag.py`.
    *   `query_neo4j.py` is a useful low-level tool.

6.  **Port Configuration:**
    *   The two `update_*_port_references.py` scripts are fine but ensure they are run as part of development or CI to maintain consistency.

7.  **Address Hardcoding:**
    *   Remove hardcoded paths in `check_python_version.sh`, `start_api_server.sh`, `start_neo4j.sh`, `stop_neo4j.sh`. Use environment variables or relative paths derived from the script's location.
    *   The hardcoded API key in `simple_openrouter_test.py` should be removed and loaded from env or config.

8.  **`./tools` Directory:**
    *   Clarify the purpose of the `./tools` directory. If it's not intended for use, remove it. If it is, populate it with relevant utilities.

9.  **Review `cleanup_duplicates.py`:**
    *   The duplicate removal functionality is noted as a placeholder. This should be fully implemented or the script's purpose clarified to be reporting-only.

This analysis should serve as a good starting point for reorganizing and refining the project's tooling and scripts.