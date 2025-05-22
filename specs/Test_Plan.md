# Test Plan

## 1. Introduction/Overview

This document outlines the existing testing assets and practices within the GraphRAG project. It serves as an initial consolidation of findings to inform a more comprehensive test strategy. The project primarily utilizes Python for its testing efforts, with a significant number of tests located in the `tests/` directory.

## 2. Existing Test Assets

### 2.1. Test Directories:
*   **`tests/`**: Main directory for all tests.
    *   **`tests/component/`**: Contains component-level tests.
    *   **`tests/regression/`**: Contains regression tests, including subdirectories for `mcp_tests/`, `program_suite/`, and `web_api_tests/`.
    *   **`tests/regression/data/`**: Contains test data for regression tests (as per `tests/regression/README.md`).
    *   A `test_pdf.pdf` file exists directly under `tests/`, likely used by `tests/test_file_handlers.py`. The script `tests/test_file_handlers.py` also references a `test_files/` directory (e.g., `test_files/test_markdown.md`), but this directory was not directly observed in the root of `tests/`.

### 2.2. Test Script Files:
The `tests/` directory and its subdirectories contain numerous Python test files (`test_*.py`). Key categories include:

*   **General Tests (in `tests/`):**
    *   `test_add_document_with_concepts.py`
    *   `test_api_add_document.py`
    *   `test_duplicate_detection.py`
    *   `test_end_to_end.py`
    *   `test_file_handlers.py`
    *   `test_mcp_add_document_with_concepts.py`
    *   `test_mcp_add_document.py`
    *   `test_mcp_concept.py`
    *   `test_mcp_connection.py`
    *   `test_mcp_search.py`
    *   `test_mcp_server.py`
    *   `test_mpc_search_graphrag.py` (likely a typo, should be mcp)
    *   `test_neo4j.py`
    *   `test_setup.py`

*   **Component Tests (in `tests/component/`):**
    *   `test_async_processing.py`
    *   `test_concept_extraction.py`
    *   `test_deduplication.py`
    *   `test_embedding_model.py`
    *   `test_llm_concept_extraction.py`
    *   `test_llm_integration.py`
    *   `test_mcp_connection.py`
    *   `test_mcp_search.py`
    *   `test_neo4j.py`
    *   `test_vector_db.py`

*   **Regression Tests (in `tests/regression/` and its subdirectories):**
    *   A suite of tests covering service start/stop, DB initialization, document operations, NLP processing, search, deduplication, and MCP/API functionalities.
    *   Examples: `test_01_start_stop.py`, `web_api_tests/test_03_document_operations.py`, `mcp_tests/test_04_search_operations.py`.

*   **Other Test-related Scripts:**
    *   Various scripts in `scripts/database_management/` (e.g., `verify_neo4j.py`, `verify_vector_db.py`) perform connection tests and basic operation checks.
    *   `test_ollama_python.py`, `test_document_chunking.py`, `test_concept_extraction_chunking.py` appear to be standalone test scripts.

### 2.3. Test Documentation:
*   **`tests/regression/README.md`**: Provides an overview of the regression test structure, individual tests, and how to run them. Mentions a `data/` directory for test data.
*   **`docs/audit/methodologies.md`**: Mentions test cases, test coverage reports, and integrating tool outputs in an audit context.
*   **`src/graphRAG.egg-info/PKG-INFO`**: Mentions `tests/` directory and an example command to run a component test.

### 2.4. Test Configuration:
*   **`pyproject.toml`**: Lists `pytest` under the `[tool.poetry.group.dev.dependencies]` and `[test]` extra.
*   **`src/graphRAG.egg-info/requires.txt`**: Lists `pytest` under `[test]`.

## 3. Test Environment & Prerequisites

Based on the test scripts and documentation:
*   **Python Environment:** The tests are Python-based. Specific version requirements are not explicitly stated in the plan yet but are likely managed by `poetry`. The `scripts/check_python_version.sh` utility can be used to verify the active Python version against project expectations.
*   **Neo4j Database:** Many tests interact with Neo4j (e.g., `test_neo4j.py`, component tests, regression tests). A running Neo4j instance is a prerequisite. Configuration details (URI, user, password) are likely needed.
*   **Vector Database (ChromaDB):** Tests like `component/test_vector_db.py` and regression tests for search suggest a vector database (likely ChromaDB as seen in other project files) is required.
*   **API Server:** API tests (e.g., `test_api_add_document.py`, `tests/regression/web_api_tests/`) require the GraphRAG API server to be running. The environment details indicate `python src/api/server.py` is often running.
*   **MCP Server:** MCP tests (e.g., `test_mcp_server.py`, `tests/regression/mcp_tests/`) require the MCP server to be active.
*   **LLM/OpenRouter Access:** Tests involving LLM integration (e.g., `test_llm_integration.py`, `scripts/test_openrouter.py`) would require API keys and connectivity to services like OpenRouter.
*   **Environment Variables:** Specific environment variables for database connections, API keys, and server ports are likely required. `test_setup.py` might handle some of this. The `scripts/check_ports.sh` utility should be run before starting services to ensure necessary ports are available.

## 4. Test Data

*   **`tests/regression/data/`**: Explicitly mentioned in `tests/regression/README.md` as containing test documents and other data for regression tests.
*   **`tests/test_pdf.pdf`**: A PDF file located directly in the `tests/` directory, likely used by `tests/test_file_handlers.py`.
*   **`tests/create_test_pdf.py`**: A script to generate a test PDF.
*   **Inline Data/Generators:** Some tests appear to generate or define test data within the scripts themselves (e.g., `tests/regression/web_api_tests/test_04_search_operations.py` defines `CHROMA_TEST_DOC_TEXT`).
*   **`example_docs/`**: While not strictly test data, this directory is used in `tests/test_api_add_document.py` for testing folder addition, implying its contents serve as test inputs.

## 5. Test Execution

*   **`pytest`**: Indicated as the test runner in `pyproject.toml`.
*   **Direct Script Execution:**
    *   `tests/regression/run_all_tests.py`: Appears to be a master script to run all regression tests.
    *   `tests/regression/run_regression_tests.py`: Likely runs a specific set of regression tests.
    *   Individual test files can likely be run directly (e.g., `python -m tests.component.test_neo4j` as mentioned in `PKG-INFO`).
*   **Test Suites:** The `tests/regression/program_suite/` directory suggests the use of test suites, possibly managed by `pytest` or custom scripts.

## 6. How to Run the Tests (Recommended Workflow)

This section outlines the recommended steps to run the tests in a clean and consistent environment.

**0. Pre-flight Checks (Optional but Recommended):**
*   Check Python Version: `scripts/check_python_version.sh`
*   Check Port Availability: `scripts/check_ports.sh`
*   Ensure Dependencies: `scripts/install-dependencies.sh` (if not managed by `uv run pytest` or similar)

**1. Activate Virtual Environment:**
Ensure your project's virtual environment is activated. Based on project scripts, this is typically `.venv-py312/`. If you are not using `uv run` for every command, activate it:
```bash
source .venv-py312/bin/activate
```

**2. Ensure Databases are Clean:**
Before running tests, especially regression tests, it's crucial to start with clean databases. The `start-graphrag-local.sh` script indicates the following command:
```bash
uv run --python .venv-py312/bin/python scripts/clean_database.py --yes
```
*Note: This command will wipe existing data in Neo4j and ChromaDB. Do NOT run this on a production system.*
Alternatively, for more targeted cleaning, `scripts/database_management/clear_neo4j.py` or `scripts/database_management/reset_chromadb.py` can be used.

**3. Start Required Services:**
The GraphRAG API and MCP servers need to be running for many tests. The `tests/regression/test_utils.py` uses `./start-graphrag-local.sh` which in turn calls `./scripts/service_management/graphrag-service.sh start`.
```bash
./scripts/service_management/graphrag-service.sh start
```
Wait for the services to initialize. You can check their status with:
```bash
./scripts/service_management/graphrag-service.sh status
```
The `tests/regression/test_utils.py` script also contains a `wait_for_api_ready()` function that tests use internally.
*   Database Initialization: After services are up and databases are clean, run `uv run --python .venv-py312/bin/python scripts/database_management/initialize_database.py` to ensure schemas, indexes, and constraints are correctly set up.
*
### 3.1. Unit Testing
Unit tests are written using pytest to verify individual components.
They are located in the `tests/unit` directory.

### 3.2. Recently Added Unit Test Coverage (Post Bug Audit)

Based on the recent Bug Audit Report, the following unit tests have been added to `tests/unit/` to verify fixes and ensure robustness of key components:

*   **`/Users/andyspamer/Dev-Space/pythonProjects/graphRAG/tests/unit/test_ports.py`**:
    *   **Purpose**: Verifies the centralized port configuration system (`src/config/ports.py`).
    *   **Coverage**:
        *   Retrieval of default port values for services like API, MPC, and MCP.
        *   Correct overriding of port values using environment variables (e.g., `GRAPHRAG_PORT_API`).
        *   Handling of requests for unknown services or invalid port values in environment variables.
    *   **Related Bugs**: Addresses issues stemming from port mismatches and hardcoded ports (e.g., Bugs #2, #10, #11, #12, #13, #14-19, #20-25, #31, #32).

*   **`/Users/andyspamer/Dev-Space/pythonProjects/graphRAG/tests/unit/test_database_config.py`**:
    *   **Purpose**: Tests the configuration loading and initialization logic for database connections.
    *   **Coverage**:
        *   **Neo4j**: Verifies `Neo4jDatabase` URI parsing, ensuring the default port (7687) is correctly appended if missing (related to Bug #30). Tests behavior with and without explicit ports in `NEO4J_URI`.
        *   **VectorDatabase (ChromaDB)**: Tests `VectorDatabase` initialization, focusing on:
            *   Correct loading of directory paths from environment variables (`CHROMA_DB_DIRECTORY`).
            *   Conversion of relative paths to absolute paths (related to Bugs #4, #9).
            *   Proper handling and passing of the `CHROMA_TENANT` parameter, including defaulting to "default_tenant" (related to Bug #44).
            *   Error handling for missing essential environment variables.

*   **`/Users/andyspamer/Dev-Space/pythonProjects/graphRAG/tests/unit/test_processing_logic.py`**:
    *   **Purpose**: Validates core data processing functions and LLM interaction logic, particularly within `src/processing/concept_extractor.py` and `src/llm/llm_provider.py`.
    *   **Coverage**:
        *   **Document Chunking**: Tests `smart_chunk_text` (as used by `ConceptExtractor._chunk_text`) for correct behavior with basic text, paragraph preservation, and handling of large paragraphs by splitting sentences (related to Bug #34).
        *   **Concept Validation**: Verifies `_is_valid_concept` correctly filters out concepts containing stopwords (e.g., "part"), improving the quality of rule-based extracted concepts (related to Bug #37).
        *   **LLM Configuration**:
            *   Tests `load_llm_config` (from `concept_extractor.py`) for OpenRouter API key handling: prioritizing `OPENROUTER_API_KEY` environment variable and managing placeholder values (related to Bug #35).
            *   Verifies `create_llm_provider` (from `llm_provider.py`) correctly casts configuration values (e.g., `api_base`, `model`) to strings to prevent type errors (related to Bug #36, part 1).
        *   **Ollama Provider**: Ensures the `OllamaProvider` uses the correct `/api/embeddings` endpoint for generating embeddings (related to Bug #40).
        *   **Chunking Robustness**: Tests the `_chunk_text` method in `ConceptExtractor` to ensure it robustly returns a `list[str]`, even if its internal call to `smart_chunk_text` returns unexpected types or raises errors (related to Bug #36, part 2).

These unit tests aim to prevent regressions related to the fixed bugs and improve the overall stability of the configuration and processing components.


**4. Run Tests:**

*   **Running all tests with `pytest` (Recommended for comprehensive checks & coverage):**
    This will discover and run all tests configured in `pyproject.toml` (including component, regression, and other tests).
    ```bash
    uv run pytest
    ```
    *Refer to `pyproject.toml` under `[tool.pytest.ini_options]` for specific pytest configurations (e.g., coverage reporting via `--cov=src`).*

*   **Running the Full Regression Test Suite:**
    This script runs a sequence of regression tests as documented in `tests/regression/README.md`.
    ```bash
    uv run python -m tests.regression.run_all_tests
    ```

*   **Running Individual Regression Tests:**
    You can run specific regression tests by their module path.
    ```bash
    # Example:
    uv run python -m tests.regression.test_01_start_stop
    uv run python -m tests.regression.web_api_tests.test_03_document_operations
    uv run python -m tests.regression.mcp_tests.test_04_search_operations
    ```

*   **Running Individual Component or Other Tests:**
    Similarly, individual test files can be run.
    ```bash
    # Example (from PKG-INFO, adapted for uv):
    uv run python -m tests.component.test_neo4j
    # Example:
    uv run python -m tests.test_file_handlers
    ```

**5. Stop Services After Testing:**
Once testing is complete, stop the services:
```bash
./scripts/service_management/graphrag-service.sh stop
```
## 7. Current Test Coverage (High-Level)

Based on the file names and directory structure, there appears to be test coverage for:
*   **Core Components:** Database interactions (Neo4j, VectorDB), LLM integration, embedding models, file handling, concept extraction, deduplication.
*   **API Endpoints:** Document addition, folder addition, search operations, job management.
*   **MCP Server:** Connection, search, concept exploration, asynchronous processing.
*   **End-to-End Flows:** Indicated by `test_end_to_end.py` and the regression suite structure.
*   **Regression Testing:** A dedicated suite aims to ensure existing functionality remains stable.

Areas potentially lacking or needing more detailed investigation for coverage:
*   Specific edge cases or error handling scenarios.
*   UI testing (if a UI exists or is planned).
*   Performance and scalability testing.
*   Security vulnerability testing.
*   Comprehensive testing of all API endpoint parameters and variations.

## 8. Identified Gaps & Recommendations (Initial Thoughts)

*   **Centralized Test Documentation:** While `tests/regression/README.md` is good, a more comprehensive, overarching test strategy document would be beneficial. This `Test_Plan.md` is a starting point.
*   **Test Data Management:** Clarify the strategy for managing test data. Is `tests/regression/data/` the sole source, or are there others? How is test data versioned and maintained? The role of `tests/test_files/` (if it exists and where) needs clarification.
*   **Environment Consistency:** Document a clear and consistent way to set up the test environment. This should include leveraging scripts like `scripts/check_ports.sh`, `scripts/check_python_version.sh`, and the service management suite. Tools like Docker Compose are already in use (`docker-compose.yml`) and could be leveraged more explicitly for testing environments.
*   **CI/CD Integration:** Investigate how tests are integrated into CI/CD pipelines for automated execution.
*   **Coverage Reporting:** Implement and regularly review test coverage reports (e.g., using `pytest-cov`) to identify untested code paths.
*   **Standardize Test Execution:** While `pytest` is available, ensure all tests can be discovered and run through it for consistency.
*   **Clarity on `test_mpc_search_graphrag.py`:** This filename likely contains a typo and should be `test_mcp_search_graphrag.py`.
*   **Leverage Utility Scripts:** Systematically integrate the utility scripts from the `./scripts/` directory into the automated testing lifecycle for setup, data management, verification, and diagnostics, as detailed in Section 9.
## 9. Leveraging Utility Scripts for Enhanced Testing

The project contains a rich set of utility scripts in the `./scripts/` directory that can significantly enhance the testing process, from environment setup and data preparation to diagnostics and verification. Integrating these scripts into the testing workflow can lead to more robust, repeatable, and efficient testing.

### 9.1. Environment Setup and Management

*   **Port Availability:** Before starting services for testing, `scripts/check_ports.sh` can be used to ensure that all required ports (Neo4j, API, MCP) are free, preventing conflicts that could lead to test failures. This should be a preliminary step in test environment setup.
*   **Python Version Check:** `scripts/check_python_version.sh` helps ensure the correct Python environment is active, crucial for consistent test execution.
*   **Dependency Installation:** `scripts/install-dependencies.sh` can be used to ensure all project dependencies are correctly installed before tests run.
*   **Service Management:**
    *   The various service management scripts in `scripts/service_management/` (e.g., `graphrag-service-robust.sh`, `graphrag-service.sh`, `start_all_services.sh`) are essential for starting, stopping, and checking the status of Neo4j, the API server, and MCP servers. These are already referenced in the regression test utilities and should be the standard way to manage services during test setup and teardown.
    *   Individual service starters like `scripts/service_management/start_api_server.sh`, `scripts/service_management/start_mcp_server.sh`, and `scripts/service_management/start_neo4j.sh` can be used for more granular control if only specific services are needed for a particular test suite.

### 9.2. Database Preparation and Verification

*   **Database Initialization:** `scripts/database_management/initialize_database.py` is critical for setting up Neo4j constraints and indexes and ensuring ChromaDB is ready. This should be run after cleaning the database and before any tests that interact with the database.
*   **Database Cleaning:**
    *   `scripts/database_management/clean_database.py` provides a comprehensive way to clear Neo4j and reset ChromaDB. This is vital for ensuring tests run in a clean state, as noted in the "How to Run the Tests" section.
    *   `scripts/database_management/clear_neo4j.py` and `scripts/database_management/reset_chromadb.py` offer more focused cleaning if only one database needs resetting.
*   **Database Verification:**
    *   `scripts/database_management/verify_neo4j.py`, `scripts/database_management/verify_chromadb.py` (or `verify_vector_db.py`), and `scripts/database_management/verify_linkage.py` can be used as sanity checks after database setup or as part of diagnostic routines when tests fail. They confirm connectivity, basic operations, and the critical link between the graph and vector databases.
    *   `scripts/check_db_indexes.py` can be used to verify that database schemas and optimizations are correctly applied, which can be part of integration or pre-performance tests.

### 9.3. Test Data Generation and Ingestion

*   **Document Ingestion Scripts:**
    *   Scripts like `scripts/document_processing/add_ebooks_batch.py`, `scripts/document_processing/add_pdf_documents.py`, `scripts/document_processing/batch_process.py`, and `scripts/document_processing/process_ebooks.py` can be used to populate the databases with specific datasets for different test scenarios (e.g., testing with a large number of documents, specific file types, or particular content).
    *   `scripts/document_processing/add_50_random_ebooks.py` is useful for quickly generating a moderately sized, varied dataset.
    *   These scripts can be parameterized and called from test setup fixtures to create specific data states.
*   **Concept Extraction for Test Data:**
    *   `scripts/document_processing/extract_concepts_from_documents.py` and `scripts/document_processing/extract_concepts_with_llm.py` can be used to pre-process test documents and populate the graph with concepts, allowing tests to focus on querying and relationship analysis rather than the full ingestion pipeline if needed.

### 9.4. Test Execution Support and Diagnostics

*   **LLM/OpenRouter Tests:**
    *   `scripts/simple_openrouter_test.py` and `scripts/test_openrouter.py` can be used as preliminary checks to ensure OpenRouter connectivity and basic functionality before running tests that rely on LLM interactions.
    *   `scripts/test_relationship_strength.py` can be used to verify specific aspects of LLM-based relationship analysis.
*   **Querying and Verification:**
    *   `scripts/query/query_neo4j.py`, `scripts/query/query_graphrag.py`, and `scripts/query/query_ebooks.py` are invaluable for inspecting the state of the databases after test operations. They can be used to verify that data was written correctly, relationships were formed as expected, or search results are accurate. These can be integrated into test assertions or used for manual debugging.
    *   `scripts/query/list_documents.py` provides a quick way to check documents ingested via MPC.
*   **Graph Visualization:** `scripts/query/visualize_graph.py` can be extremely helpful for debugging complex graph-related test failures by allowing visual inspection of the graph state.
*   **Duplicate Detection Check:** `scripts/database_management/cleanup_duplicates.py` (in reporting mode) can be used to verify the behavior of deduplication logic under test.
*   **Data Optimization Verification:** `scripts/database_management/optimize_existing_data.py` (with `--dry-run`) could be used to check the state of data before and after tests that might affect chunking or indexing.
*   **Vector Index Health:** `scripts/database_management/repair_vector_index.py` can be used to check and potentially repair the vector index if vector search tests are failing inexplicably.

### 9.5. Configuration and Maintenance Tests

*   **Port Reference Checks:**
    *   `scripts/update_docs_port_references.py` and `scripts/update_port_references.py` are not direct testing tools but can be part of a pre-commit hook or CI step to ensure that documentation and code do not contain hardcoded ports, which could lead to test environment inconsistencies.
*   **Automated Audit:** `scripts/run_automated_audit.py` can be integrated into a CI pipeline to perform regular checks on code quality, documentation, and other aspects, indirectly supporting the reliability of the codebase under test.

By strategically incorporating these utility scripts, the test suite can become more automated, easier to debug, and provide greater confidence in the stability and correctness of the GraphRAG system.