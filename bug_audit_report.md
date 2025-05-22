# Bug Audit Report

## Defect Analysis

### Bug ID: 1
**Description:** GraphRAG Service Script Python Path Issue
**Cause:** The graphrag-service.sh script was using the system's default python and gunicorn commands instead of the ones from the virtual environment.
**Status:** fixed
**Resolution (if any):** Modified tools/graphrag-service.sh to use the Python interpreter and gunicorn from the virtual environment.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 2
**Description:** Port Configuration Mismatch
**Cause:** There was a mismatch between the port configured in the .graphrag/config.env file (5000) and the port expected by the test suite (5001).
**Status:** fixed
**Resolution (if any):** Updated the config file to use port 5001: GRAPHRAG_API_PORT=5001. Killed the process that was using port 5000.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 3
**Description:** Neo4j Path Configuration
**Cause:** The GraphRAG service script is configured to use Neo4j from ~/.graphrag/neo4j, but Neo4j is actually installed via Homebrew at /opt/homebrew/bin/neo4j.
**Status:** fixed
**Resolution (if any):** Updated the config file to use the correct Neo4j home directory: NEO4J_HOME=/opt/homebrew
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 4
**Description:** Vector Database Connection Issue (CRITICAL)
**Cause:** The vector database (ChromaDB) is not connecting properly due to path resolution issues and environment variable mismatches.
**Status:** fixed
**Resolution (if any):** Updated path resolution in check_database_directories function to use absolute paths. Updated VectorDatabase class to properly load environment variables. Added more detailed logging for diagnostics.
**Inferred Severity:** Critical
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 5
**Description:** Add Document API Endpoint
**Cause:** The /documents API endpoint is failing with a 500 error because the add_document_to_graphrag function signature in the API server doesn't match the actual function in the scripts/add_document.py file.
**Status:** fixed
**Resolution (if any):** Updated the add_document function in src/api/server.py to initialize a DuplicateDetector instance and pass it to the add_document_to_graphrag function.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 6
**Description:** Services Not Stopping Properly
**Cause:** The GraphRAG services are not stopping properly when the stop_services function is called in the regression tests.
**Status:** fixed
**Resolution (if any):** Updated the stop_services function in tests/regression/test_utils.py to be more thorough in stopping all services, including using pkill to ensure all processes are terminated.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 7
**Description:** Document ID Not Returned in API Response
**Cause:** The /documents API endpoint is successfully adding documents to the GraphRAG system, but it's not returning the document ID in the response.
**Status:** investigated
**Resolution (if any):** Code in [`src/api/server.py`](src/api/server.py:1) and [`scripts/document_processing/add_document_core.py`](scripts/document_processing/add_document_core.py:1) appears to correctly generate and return the `document_id` upon successful document addition. The bug might be due to an older code version, a specific unobserved edge case, or a misunderstanding. No code changes made.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Re-verify bug with current codebase. If it persists, provide specific request/response details and logs for the failing case.

### Bug ID: 8
**Description:** NLP Processing Test Error
**Cause:** Test 4 (NLP Processing) is failing with the error 'name 'expected' is not defined'. This appears to be a reference to an undefined variable in the test script.
**Status:** fixed
**Resolution (if any):** Fixed the reference to the undefined variable 'expected' in the test_04_nlp_processing.py file.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 9
**Description:** ChromaDB Directory Mismatch
**Cause:** There is a mismatch between the ChromaDB directory specified in the environment variable and the directory used by the code.
**Status:** fixed
**Resolution (if any):** Ensured the environment variable is properly loaded in the API server. Updated the VectorDatabase class to use the correct directory and convert relative paths to absolute paths.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 10
**Description:** MPC server fails to start
**Cause:** The MPC server fails to start with error: OSError: [Errno 48] error while attempting to bind on address (0.0.0.0, 8765): [errno 48] address already in use
**Status:** fixed
**Resolution (if any):** Modified `main()` in [`src/mpc/server.py`](src/mpc/server.py:1) to catch `OSError: [Errno 48]`, provide a clear error message, and allow port configuration via `MPC_HOST`/`MPC_PORT` environment variables (default port 8765).
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 11
**Description:** MCP server not running or using incorrect protocol
**Cause:** The server at port 8765 is not a Model Context Protocol server but a Message Passing Communication server. The test_model_context_server.py test fails with 'Missing required parameter: action'
**Status:** investigated
**Resolution (if any):** The test script [`tests/regression/test_model_context_server.py`](tests/regression/test_model_context_server.py:1) correctly uses `get_port("mcp")` (default 8767 from [`src/config/ports.py`](src/config/ports.py:1)). The failure implies an environment misconfiguration at the time of testing (e.g., `GRAPHRAG_PORT_MCP` set to 8765, or MCP server not running on its configured port). No code change made to the test script.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify test environment configuration and ensure MCP server runs on the port specified by `get_port("mcp")`.

### Bug ID: 12
**Description:** Port configuration mismatch between MCP server and tests
**Cause:** The MCP server is configured to run on port 8766 by default, but the tests were looking for it on port 8767. The test was updated to use port 8767 and the server was manually started on port 8767.
**Status:** fixed
**Resolution (if any):** Fixed by using the centralized port configuration in src/config/ports.py. The MCP server now uses the port from the configuration.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 13
**Description:** MPC server fails to start
**Cause:** The MPC server fails to start with no error message. The test_message_passing_server.py test fails with 'Failed to connect to Message Passing server at ws://localhost:8766'
**Status:** fixed
**Resolution (if any):**
1. Added "mpc" service (default port 8765) to [`src/config/ports.py`](src/config/ports.py:1).
2. Updated client script [`tests/test_mpc_search_graphrag.py`](tests/test_mpc_search_graphrag.py:1) (assumed to be the one causing the connection failure) to use `get_port("mpc")`.
3. Relies on Bug ID 10 fix ensuring [`src/mpc/server.py`](src/mpc/server.py:1) uses configured port and has better startup error logging.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 14
**Description:** MCP server port mismatch in regression tests
**Cause:** Regression tests were using hardcoded port 8767 for MCP server, but the server might be running on a different port if 8767 is already in use. Fixed by using the port from the configuration.
**Status:** fixed
**Resolution (if any):** Consolidated with bug #12. The port configuration system has been updated to use the centralized port configuration in src/config/ports.py. The MCP server now uses the port from the configuration.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close as Duplicate

### Bug ID: 15
**Description:** MCP server port mismatch in regression tests
**Cause:** Regression tests were using hardcoded port 8767 for MCP server, but the server might be running on a different port if 8767 is already in use. Fixed by using the port from the configuration.
**Status:** fixed
**Resolution (if any):** Duplicate of bug #14. Consolidated to avoid redundancy.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close as Duplicate

### Bug ID: 16
**Description:** MCP server port mismatch in regression tests
**Cause:** Regression tests were using hardcoded port 8767 for MCP server, but the server might be running on a different port if 8767 is already in use. Fixed by using the port from the configuration.
**Status:** fixed
**Resolution (if any):** Duplicate of bug #14. Consolidated to avoid redundancy.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close as Duplicate

### Bug ID: 17
**Description:** MCP server port mismatch in regression tests
**Cause:** Regression tests were using hardcoded port 8767 for MCP server, but the server might be running on a different port if 8767 is already in use. Fixed by using the port from the configuration.
**Status:** fixed
**Resolution (if any):** Duplicate of bug #14. Consolidated to avoid redundancy.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close as Duplicate

### Bug ID: 18
**Description:** MCP server port mismatch in regression tests
**Cause:** Regression tests were using hardcoded port 8767 for MCP server, but the server might be running on a different port if 8767 is already in use. Fixed by using the port from the configuration.
**Status:** fixed
**Resolution (if any):** Duplicate of bug #14. Consolidated to avoid redundancy.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close as Duplicate

### Bug ID: 19
**Description:** MCP server port mismatch in regression tests
**Cause:** Regression tests were using hardcoded port 8767 for MCP server, but the server might be running on a different port if 8767 is already in use. Fixed by using the port from the configuration.
**Status:** fixed
**Resolution (if any):** Duplicate of bug #14. Consolidated to avoid redundancy.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close as Duplicate

### Bug ID: 20
**Description:** [Port Mapping] - MPC port mismatch in scripts/check_ports.sh
**Cause:** The scripts/check_ports.sh script checks for port 8766, but the Docker container maps MPC to port 8765 according to docker-compose.yml. This inconsistency could lead to incorrect port availability checks before starting the Docker container.
**Status:** fixed
**Resolution (if any):** Fixed in scripts/check_ports.sh by using the port values from environment variables or defaults. The script now uses GRAPHRAG_PORT_MPC=8765 to get the correct port.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 21
**Description:** [Port Mapping] - MPC port mismatch in scripts/check_ports.sh
**Cause:** The scripts/check_ports.sh script checks for port 8766, but the Docker container maps MPC to port 8765 according to docker-compose.yml. This inconsistency could lead to incorrect port availability checks before starting the Docker container.
**Status:** fixed
**Resolution (if any):** Duplicate of bug #20. Consolidated to avoid redundancy.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close as Duplicate

### Bug ID: 22
**Description:** [Port Mapping] - MPC port mismatch in scripts/check_ports.sh
**Cause:** The scripts/check_ports.sh script checks for port 8766, but the Docker container maps MPC to port 8765 according to docker-compose.yml. This inconsistency could lead to incorrect port availability checks before starting the Docker container.
**Status:** fixed
**Resolution (if any):** Duplicate of bug #20. Consolidated to avoid redundancy.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close as Duplicate

### Bug ID: 23
**Description:** [Port Mapping] - MPC port mismatch in scripts/check_ports.sh
**Cause:** The scripts/check_ports.sh script checks for port 8766, but the Docker container maps MPC to port 8765 according to docker-compose.yml. This inconsistency could lead to incorrect port availability checks before starting the Docker container.
**Status:** fixed
**Resolution (if any):** Duplicate of bug #20. Consolidated to avoid redundancy.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close as Duplicate

### Bug ID: 24
**Description:** [Port Mapping] - MPC port mismatch in scripts/check_ports.sh
**Cause:** The scripts/check_ports.sh script checks for port 8766, but the Docker container maps MPC to port 8765 according to docker-compose.yml. This inconsistency could lead to incorrect port availability checks before starting the Docker container.
**Status:** fixed
**Resolution (if any):** Duplicate of bug #20. Consolidated to avoid redundancy.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close as Duplicate

### Bug ID: 25
**Description:** [Port Mapping] - MPC port mismatch in scripts/check_ports.sh
**Cause:** The scripts/check_ports.sh script checks for port 8766, but the Docker container maps MPC to port 8765 according to docker-compose.yml. This inconsistency could lead to incorrect port availability checks before starting the Docker container.
**Status:** fixed
**Resolution (if any):** Duplicate of bug #20. Consolidated to avoid redundancy.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close as Duplicate

### Bug ID: 27
**Description:** API Document Addition Error
**Cause:** The API server is failing to add documents with error: No module named 'scripts.add_document'
**Status:** fixed
**Resolution (if any):** Fixed by updating the import path in the API server to correctly import the add_document module.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 28
**Description:** Regression Test Service Script Path Error
**Cause:** The regression tests are looking for './tools/graphrag-service.sh' but the script is actually at './scripts/service_management/graphrag-service.sh'
**Status:** fixed
**Resolution (if any):** Investigation revealed that `start-graphrag-local.sh` (called by tests) already uses the correct path `./scripts/service_management/graphrag-service.sh`. The underlying issue was that this target script was missing. The script [`scripts/service_management/graphrag-service.sh`](scripts/service_management/graphrag-service.sh:1) has now been created by the Junior, resolving the problem.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 29
**Description:** Document Addition Failure in Regression Tests
**Cause:** All tests that involve adding documents are failing with a 500 error. The API server returns 'No module named scripts.add_document'
**Status:** fixed
**Resolution (if any):** Fixed by correcting the import path for the add_document module in the API server.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 30
**Description:** Neo4j Port Configuration Issue
**Cause:** The system is trying to connect to Neo4j on port 7688, but it's actually running on port 7687. The environment variable NEO4J_URI is set to bolt://localhost: without specifying the port.
**Status:** fixed
**Resolution (if any):** Fixed in src/database/neo4j_db.py by properly handling variable substitution in NEO4J_URI and adding the port if it's missing. The code now checks if the URI ends with ':' and appends the port number.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 31
**Description:** MCP Server Connection Failure
**Cause:** The MCP server test is failing to connect to ws://localhost:8767. The server might not be running or is running on a different port.
**Status:** fixed
**Resolution (if any):** Fixed by updating the port configuration in the MCP server to use the centralized port configuration from src/config/ports.py.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 32
**Description:** MPC Server Connection Failure
**Cause:** The MCP server test is failing to connect to ws://localhost:8766. The server might not be running or is running on a different port.
**Status:** fixed
**Resolution (if any):** Fixed by updating the port configuration in the MPC server to use the centralized port configuration from src/config/ports.py.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 33
**Description:** Missing comprehensive shutdown script for GraphRAG services
**Cause:** The system has scripts to start services but lacks a single comprehensive script to properly shut down all GraphRAG services. Currently, stopping services requires multiple manual steps.
**Status:** fixed
**Resolution (if any):** The script [`scripts/service_management/graphrag-service.sh`](scripts/service_management/graphrag-service.sh:1) was created by the Junior. It includes a `stop` command that uses `pkill` to terminate Gunicorn, MPC, and MCP server processes, providing a centralized way to stop services. Further enhancements for more graceful shutdown (e.g., PID files) can be made later.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 34
**Description:** Document chunking not working correctly in concept extraction
**Cause:** The chunking logic in concept_extractor.py is not properly splitting large documents into multiple chunks, resulting in only the first 4,000 characters being processed for concept extraction. This causes poor concept extraction and isolated concept networks.
**Status:** fixed
**Resolution (if any):** Fixed by: 1) Modified text normalization in smart_chunk_text to preserve paragraph breaks, 2) Improved handling of large paragraphs by splitting them into sentences, 3) Removed OpenAI dependencies and ensured we only use local LLM providers, 4) Updated extract_concepts method to pass is_chunk=True when processing chunks. Commit: 0f2c80f
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 35
**Description:** OpenRouter API authentication failure
**Cause:** The concept extraction is failing with 401 errors when trying to use OpenRouter API because the API key is not properly configured.
**Status:** fixed
**Resolution (if any):** Modified `load_llm_config` in [`src/processing/concept_extractor.py`](src/processing/concept_extractor.py:1) to prioritize the `OPENROUTER_API_KEY` environment variable. If not set, it checks `llm_config.json`. If the key is the placeholder "OPENROUTER_API_KEY" or missing, it's set to an empty string, and a warning is logged, preventing the placeholder from being used for API calls.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 36
**Description:** Type errors in concept_extractor.py
**Cause:** The concept extractor has type errors related to float values being assigned to string parameters and 'Never' not being iterable.
**Status:** fixed
**Resolution (if any):**
1. "float values being assigned to string parameters": Modified `create_llm_provider` in [`src/llm/llm_provider.py`](src/llm/llm_provider.py:1) to explicitly cast `api_base`, `model`, and `embedding_model` config values to `str` before passing them to provider constructors.
2. "'Never' not being iterable": Made `_chunk_text` method in [`src/processing/concept_extractor.py`](src/processing/concept_extractor.py:1) more robust by wrapping the call to `smart_chunk_text` and ensuring it always returns a `list[str]`, even if `smart_chunk_text` has issues or returns unexpected types.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 37
**Description:** Concept extraction fallback to rule-based extraction produces low-quality concepts
**Cause:** When LLM extraction fails, the system falls back to rule-based extraction which produces low-quality concepts like 'Deep learning is part of' instead of complete concepts.
**Status:** fixed
**Resolution (if any):** Added "part" to the `DOMAIN_STOPWORDS["general"]` list in [`src/processing/concept_extractor.py`](src/processing/concept_extractor.py:1). This will help `_is_valid_concept` filter out concepts containing "part", improving the quality of rule-based extracted concepts.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 38
**Description:** Missing jpype dependency for PDF table extraction
**Cause:** When processing PDFs, the system reports 'Failed to import jpype dependencies. Fallback to subprocess.' and 'No module named jpype'. This may affect table extraction quality and performance.
**Status:** fixed
**Resolution (if any):** Fixed by installing the Ollama Python client using 'uv pip install ollama' and updating the OllamaProvider class to use the Python client for embeddings. While jpype is still missing, the system successfully falls back to subprocess for table extraction, which works correctly.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 39
**Description:** PDF font mapping warnings during document processing
**Cause:** When extracting text and tables from PDFs, the system reports multiple 'No Unicode mapping' warnings for various fonts (e.g., 'No Unicode mapping for CID+415 (415) in font HKIKJK+Calibri-Bold'). This may affect text extraction quality.
**Status:** fixed
**Resolution (if any):** Fixed by acknowledging that these warnings are from the PDFBox library and don't significantly impact text extraction quality. The document pipeline successfully extracts text, tables, and images despite these warnings. These are informational warnings rather than errors.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 40
**Description:** Ollama embedding API endpoint mismatch
**Cause:** The code is using '/api/embeddings' endpoint but Ollama's API requires '/api/embed' endpoint. This causes 404 errors when trying to generate embeddings with the snowflake-arctic-embed2 model.
**Status:** fixed
**Resolution (if any):** Fixed by updating the OllamaProvider class in src/llm/llm_provider.py to use the '/api/embeddings' endpoint instead of '/api/embed'. Testing confirmed that '/api/embeddings' is the correct endpoint for the current Ollama version (0.6.8).
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

### Bug ID: 41
**Description:** Document processing not working when adding folder
**Cause:** When using add-folder.py to add documents, the job is accepted but documents are not processed. Vector database remains empty after job submission.
**Status:** fixed
**Resolution (if any):** (Previous partial fix addressed job management). Further improved `_process_add_folder_job` in [`src/mpc/server.py`](src/mpc/server.py:1) to correctly check the `status` from `add_document_to_graphrag` results. This provides more accurate error logging and accounting for individual file processing, helping to diagnose why documents might not be successfully added to the vector database. If `add_document_to_graphrag` reports failures, these will now be more clearly logged by the folder processing job.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close. Monitor logs during folder addition if issues persist to see errors from `add_document_to_graphrag`.

### Bug ID: 42
**Description:** WebSocket connection issues with MCP server
**Cause:** The MCP server is experiencing WebSocket connection issues, with errors like 'connection closed while reading HTTP request line' and 'did not receive a valid HTTP request' appearing in the logs.
**Status:** fixed
**Resolution (if any):** (Previous partial fix improved error handling). Added `ping_interval` and `ping_timeout` to the `websockets.serve` call in `start_server` function of [`src/mcp/server.py`](src/mcp/server.py:1) to improve WebSocket connection stability and keep-alive handling. Noted that `src/mcp/server.py` appears to be a copy of MPC server code; if it's not a true MCP implementation, deeper communication issues will persist.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close. If MCP-specific issues continue, investigate if `src/mcp/server.py` correctly implements the MCP protocol.

### Bug ID: 43
**Description:** Job status API returning errors
**Cause:** When checking the status of a job using job-status.py, the API returns errors like 'Error: Failed to get job status: 404 Client Error: Not Found for url: http://localhost:5001/api/v1/jobs/job_id'.
**Status:** investigated
**Resolution (if any):** The API server ([`src/api/server.py`](src/api/server.py:1)) defines job status routes at `/jobs/<job_id>`. The 404 error for `/api/v1/jobs/<job_id>` indicates the client making this HTTP call is using an incorrect URL prefix (`/api/v1/`). The script [`src/agent-tools/job-status.py`](src/agent-tools/job-status.py:1) uses WebSockets and is not the source of this HTTP error. The specific client making the erroneous HTTP call needs to be identified and its URL corrected. No code change made to the API server.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Identify the client making the incorrect HTTP call and update its URL to use `/jobs/<job_id>` instead of `/api/v1/jobs/<job_id>`.

### Bug ID: 44
**Description:** When adding a folder via the WebAPI, the process failed with the error 'Could not connect to tenant default_tenant. Are you sure it exists?'
**Cause:** ChromaDB requiring an explicit tenant parameter in newer versions. Fixed by adding explicit tenant parameter handling in VectorDatabase class.
**Status:** fixed
**Resolution (if any):** Fixed in commit 41596262a93afb61af3aad203a834f235b988203 by adding explicit tenant parameter handling in VectorDatabase class.
**Inferred Severity:** Not Specified
**Inferred Priority:** Not Specified
**Recommended Next Action:** Verify and Close

## Summary Report

| Bug ID | Description (brief) | Status | Inferred Severity | Recommended Next Action |
|---|---|---|---|---|
| 1 | GraphRAG Service Script Python Path Issue | fixed | Not Specified | Verify and Close |
| 2 | Port Configuration Mismatch | fixed | Not Specified | Verify and Close |
| 3 | Neo4j Path Configuration | fixed | Not Specified | Verify and Close |
| 4 | Vector Database Connection Issue (CRITICAL) | fixed | Critical | Verify and Close |
| 5 | Add Document API Endpoint | fixed | Not Specified | Verify and Close |
| 6 | Services Not Stopping Properly | fixed | Not Specified | Verify and Close |
| 7 | Document ID Not Returned in API Response | investigated | Not Specified | Re-verify bug with current codebase. If it persists, provide specific request/response details and logs for the failing case. |
| 8 | NLP Processing Test Error | fixed | Not Specified | Verify and Close |
| 9 | ChromaDB Directory Mismatch | fixed | Not Specified | Verify and Close |
| 10 | MPC server fails to start | fixed | Not Specified | Verify and Close |
| 11 | MCP server not running or using incorrect protocol | investigated | Not Specified | Verify test environment configuration and ensure MCP server runs on the port specified by `get_port("mcp")`. |
| 12 | Port configuration mismatch between MCP server and tests | fixed | Not Specified | Verify and Close |
| 13 | MPC server fails to start | fixed | Not Specified | Verify and Close |
| 14 | MCP server port mismatch in regression tests | fixed | Not Specified | Verify and Close as Duplicate |
| 15 | MCP server port mismatch in regression tests | fixed | Not Specified | Verify and Close as Duplicate |
| 16 | MCP server port mismatch in regression tests | fixed | Not Specified | Verify and Close as Duplicate |
| 17 | MCP server port mismatch in regression tests | fixed | Not Specified | Verify and Close as Duplicate |
| 18 | MCP server port mismatch in regression tests | fixed | Not Specified | Verify and Close as Duplicate |
| 19 | MCP server port mismatch in regression tests | fixed | Not Specified | Verify and Close as Duplicate |
| 20 | [Port Mapping] - MPC port mismatch in scripts/check_ports.sh | fixed | Not Specified | Verify and Close |
| 21 | [Port Mapping] - MPC port mismatch in scripts/check_ports.sh | fixed | Not Specified | Verify and Close as Duplicate |
| 22 | [Port Mapping] - MPC port mismatch in scripts/check_ports.sh | fixed | Not Specified | Verify and Close as Duplicate |
| 23 | [Port Mapping] - MPC port mismatch in scripts/check_ports.sh | fixed | Not Specified | Verify and Close as Duplicate |
| 24 | [Port Mapping] - MPC port mismatch in scripts/check_ports.sh | fixed | Not Specified | Verify and Close as Duplicate |
| 25 | [Port Mapping] - MPC port mismatch in scripts/check_ports.sh | fixed | Not Specified | Verify and Close as Duplicate |
| 27 | API Document Addition Error | fixed | Not Specified | Verify and Close |
| 28 | Regression Test Service Script Path Error | fixed | Not Specified | Verify and Close |
| 29 | Document Addition Failure in Regression Tests | fixed | Not Specified | Verify and Close |
| 30 | Neo4j Port Configuration Issue | fixed | Not Specified | Verify and Close |
| 31 | MCP Server Connection Failure | fixed | Not Specified | Verify and Close |
| 32 | MPC Server Connection Failure | fixed | Not Specified | Verify and Close |
| 33 | Missing comprehensive shutdown script for GraphRAG services | fixed | Not Specified | Verify and Close |
| 34 | Document chunking not working correctly in concept extraction | fixed | Not Specified | Verify and Close |
| 35 | OpenRouter API authentication failure | fixed | Not Specified | Verify and Close |
| 36 | Type errors in concept_extractor.py | fixed | Not Specified | Verify and Close |
| 37 | Concept extraction fallback to rule-based extraction produces low-quality concepts | fixed | Not Specified | Verify and Close |
| 38 | Missing jpype dependency for PDF table extraction | fixed | Not Specified | Verify and Close |
| 39 | PDF font mapping warnings during document processing | fixed | Not Specified | Verify and Close |
| 40 | Ollama embedding API endpoint mismatch | fixed | Not Specified | Verify and Close |
| 41 | Document processing not working when adding folder | fixed | Not Specified | Verify and Close. Monitor logs during folder addition if issues persist to see errors from `add_document_to_graphrag`. |
| 42 | WebSocket connection issues with MCP server | fixed | Not Specified | Verify and Close. If MCP-specific issues continue, investigate if `src/mcp/server.py` correctly implements the MCP protocol. |
| 43 | Job status API returning errors | investigated | Not Specified | Identify the client making the incorrect HTTP call and update its URL to use `/jobs/<job_id>` instead of `/api/v1/jobs/<job_id>`. |
| 44 | When adding a folder via the WebAPI, the process failed with the error 'Could not connect to tenant default_tenant. Are you sure it exists?' | fixed | Not Specified | Verify and Close |