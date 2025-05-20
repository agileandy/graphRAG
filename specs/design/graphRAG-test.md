# GraphRAG Test Artifacts

## Test Strategy

The overall test strategy for GraphRAG aims to ensure the reliability, correctness, and performance of the system through a multi-layered testing approach. This document consolidates existing testing practices and outlines areas for future enhancement.

**Core Principles:**
*   **Comprehensive Coverage:** Strive for high test coverage across core components, API endpoints, MCP server functionalities, and end-to-end workflows.
*   **Automation:** Leverage automation for test execution, environment setup, and data management to ensure consistency and efficiency.
*   **Early Feedback:** Integrate testing into the development lifecycle and CI/CD pipelines to catch issues early.
*   **Maintainability:** Develop clear, well-documented, and maintainable test cases and scripts.
*   **Environment Consistency:** Ensure tests are run in a consistent and reproducible environment.

**Key Areas from `specs/Test_Plan.md`:**
*   The project primarily utilizes Python for its testing efforts, with `pytest` as the main test runner.
*   A significant number of tests are located in the `tests/` directory, categorized into `component/`, `regression/`, etc.
*   Identified Gaps & Recommendations (from `specs/Test_Plan.md` Section 8):
    *   Need for centralized and comprehensive test documentation (this document aims to address this).
    *   Clearer strategy for test data management and versioning.
    *   Standardized test environment setup, potentially leveraging Docker more explicitly.
    *   Formalized CI/CD integration for automated test execution.
    *   Implementation and regular review of test coverage reports.
    *   Standardization of test execution, ensuring all tests can be run via `pytest`.
*   Leveraging Utility Scripts (from `specs/Test_Plan.md` Section 9):
    *   Utilize scripts in `scripts/` for environment setup (port checks, Python version, dependencies), service management, database preparation (initialization, cleaning, verification), test data generation/ingestion, and diagnostics.

## Unit Tests

Unit tests in GraphRAG focus on testing individual components or modules in isolation. These are primarily located within the `tests/component/` directory.

**Methodology:**
*   Isolate the smallest testable parts of the application.
*   Mock external dependencies (databases, external APIs) where appropriate to ensure tests are fast and reliable.
*   Focus on verifying the logic of individual functions and classes.

**Examples (from `specs/Test_Plan.md` Section 2.2):**
*   `tests/component/test_concept_extraction.py`
*   `tests/component/test_deduplication.py`
*   `tests/component/test_embedding_model.py`
*   `tests/component/test_llm_concept_extraction.py`
*   `tests/component/test_neo4j.py`
*   `tests/component/test_vector_db.py`

The `tests/` directory also contains general tests that might be considered unit-level for specific functionalities, e.g., `tests/test_file_handlers.py`.

## Integration Tests

Integration tests verify the interaction between different components of the GraphRAG system. This includes interactions between services, databases, and internal modules.

**Methodology:**
*   Test interfaces and interactions between integrated components.
*   May involve running actual instances of services like Neo4j, ChromaDB, API server, and MCP server.
*   Focus on data flow and communication paths.

**Examples and Areas Covered (from `specs/Test_Plan.md` Sections 2.2, 6, 7):**
*   **API Tests:**
    *   `tests/test_api_add_document.py`
    *   Regression tests in `tests/regression/web_api_tests/` (e.g., `test_03_document_operations.py`)
*   **MCP Tests:**
    *   `tests/test_mcp_add_document_with_concepts.py`
    *   `tests/test_mcp_connection.py` (also in component tests, indicating varying scopes)
    *   `tests/test_mcp_search.py`
    *   `tests/test_mcp_server.py`
    *   Regression tests in `tests/regression/mcp_tests/` (e.g., `test_04_search_operations.py`)
*   **Database Interaction Tests:**
    *   `tests/test_neo4j.py` (can act as integration if testing against a live DB instance with other components)
    *   `tests/component/test_llm_integration.py`
*   **Regression Suite:** Many tests within the regression suite (`tests/regression/`) inherently test the integration of multiple parts of the system.

## End-to-End Tests

End-to-End (E2E) tests validate entire workflows or user scenarios from start to finish, simulating real user interactions with the system.

**Methodology:**
*   Test the complete application flow, including all integrated services and components.
*   Focus on user stories and critical paths through the system.
*   Requires a fully deployed or representative environment.

**Examples (from `specs/Test_Plan.md` Sections 2.2, 7):**
*   `tests/test_end_to_end.py`: Explicitly named for E2E testing.
*   The regression test suite, particularly `tests/regression/run_all_tests.py`, covers broader scenarios that can be considered E2E, such as:
    *   Service start/stop and initialization.
    *   Document ingestion through API/MCP.
    *   NLP processing.
    *   Search operations.
    *   Deduplication.

## Test Automation

Test automation is crucial for the GraphRAG project, with `pytest` being the primary test runner.

**Tools and Frameworks (from `specs/Test_Plan.md` Sections 2.4, 5, 6, 9 and `specs/design/README.md`):**
*   **Test Runner:** `pytest` (configured in `pyproject.toml`).
*   **Execution Scripts:**
    *   `uv run pytest` (recommended for comprehensive checks).
    *   `uv run python -m tests.regression.run_all_tests` (for the full regression suite).
    *   Direct execution of individual test modules (e.g., `uv run python -m tests.component.test_neo4j`).
*   **Utility Scripts for Automation (from `scripts/` directory, as detailed in `specs/Test_Plan.md` Section 9 and `specs/design/README.md` for locations):**
    *   Environment Setup: `scripts/check_ports.sh`, `scripts/check_python_version.sh`, `scripts/install-dependencies.sh`.
    *   Service Management: `scripts/service_management/graphrag-service.sh` (and variants like `start_all_services.sh`, `start_api_server.sh`, etc.).
    *   Database Management: `scripts/database_management/initialize_database.py`, `scripts/database_management/clean_database.py`, `scripts/database_management/verify_neo4j.py`, etc.
    *   The `CHANGES.md` notes standardization towards `scripts/clean_database.py` and `scripts/service_management/graphrag-service.sh`.
*   **CI/CD Integration:**
    *   `specs/Test_Plan.md` recommends investigating and formalizing CI/CD integration for automated test execution.
    *   `scripts/run_automated_audit.py` can be part of CI.
*   **Coverage Reporting:**
    *   `pytest-cov` is mentioned for coverage reports (e.g., `uv run pytest --cov=src`). Regular review is recommended.

**Recommended Workflow (summarized from `specs/Test_Plan.md` Section 6):**
1.  Pre-flight checks (Python version, port availability, dependencies).
2.  Activate virtual environment.
3.  Ensure databases are clean (e.g., using `scripts/clean_database.py --yes`).
4.  Start required services (e.g., using `scripts/service_management/graphrag-service.sh start`).
5.  Initialize databases (e.g., using `scripts/database_management/initialize_database.py`).
6.  Run tests (using `uv run pytest` or specific test scripts).
7.  Stop services after testing.

## Test Data Management

Managing test data effectively is essential for reliable and repeatable testing.

**Current Practices and Sources (from `specs/Test_Plan.md` Section 4):**
*   **Dedicated Test Data Directory:** `tests/regression/data/` is explicitly mentioned for regression test documents and other data.
*   **Specific Test Files:**
    *   `tests/test_pdf.pdf` (used by `tests/test_file_handlers.py`).
    *   `tests/create_test_pdf.py` (script to generate a test PDF).
*   **Inline Data/Generators:** Some tests define data internally (e.g., `CHROMA_TEST_DOC_TEXT` in `tests/regression/web_api_tests/test_04_search_operations.py`).
*   **Example Documents:** `example_docs/` directory is used as test input for folder addition tests (e.g., in `tests/test_api_add_document.py`).
*   **Document Ingestion Scripts for Data Population (from `specs/Test_Plan.md` Section 9.3 and `specs/design/README.md` for locations):**
    *   `scripts/document_processing/add_ebooks_batch.py`
    *   `scripts/document_processing/add_pdf_documents.py`
    *   `scripts/document_processing/add_50_random_ebooks.py`
    *   These can be used to create specific data states for test scenarios.

**Recommendations (from `specs/Test_Plan.md` Section 8.2):**
*   Clarify the overall strategy for managing test data.
*   Define how test data is versioned and maintained.
*   Clarify the role and location of any other test file directories (e.g., the mentioned `test_files/` directory).

The file `specs/design/test_markdown.md` was reviewed but primarily contains a general system overview rather than specific testing content.
The file `specs/design/CHANGES.md` provided context on script consolidation, relevant for test automation and data management script references.
The file `specs/design/README.md` (in `specs/design`) provided details on directory reorganization, helping to confirm current script locations.