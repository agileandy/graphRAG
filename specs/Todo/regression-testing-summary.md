# GraphRAG Regression Testing Summary

## Overview
This document summarizes the results of running the GraphRAG regression test suite. The tests were run on the `task-regression-testing` branch.

## Test Results
All tests are currently failing due to various issues. The main issues are:

1. The vector database (ChromaDB) is not connecting properly, causing the API to report a degraded status and all document-related operations to fail with a 500 error.
2. The services are not stopping properly when the `stop_services` function is called in the regression tests.
3. The `/documents` API endpoint is not returning the document ID in the response.
4. The NLP Processing test is failing with the error "name 'expected' is not defined".

## Issues Fixed
The following issues were fixed during the regression testing:

1. **GraphRAG Service Script Python Path Issue**
   - The `graphrag-service.sh` script was using the system's default `python` and `gunicorn` commands instead of the ones from the virtual environment.
   - Fixed by updating the script to use the Python interpreter and gunicorn from the virtual environment.

2. **Port Configuration Mismatch**
   - There was a mismatch between the port configured in the `.graphrag/config.env` file (5000) and the port expected by the test suite (5001).
   - Fixed by updating the config file to use port 5001.

3. **Neo4j Path Configuration**
   - The GraphRAG service script was configured to use Neo4j from `~/.graphrag/neo4j`, but Neo4j is actually installed via Homebrew at `/opt/homebrew/bin/neo4j`.
   - Fixed by updating the config file to use the correct Neo4j home directory.

4. **Vector Database Absolute Paths**
   - The vector database was using relative paths that depended on the current working directory, causing the directory to not be found.
   - Fixed by updating the code to use absolute paths.

5. **Document ID Not Returned in API Response**
   - The `/documents` API endpoint was returning `doc_id` instead of `document_id` in the response.
   - Fixed by updating the `add_document_to_graphrag` function to return `document_id` instead of `doc_id`.

## Issues Reported
The following issues were reported but not fixed:

1. **Add Document API Endpoint**
   - The `/documents` API endpoint is failing with a 500 error because the `add_document_to_graphrag` function signature in the API server doesn't match the actual function in the `scripts/add_document.py` file.
   - The function in the script requires a `duplicate_detector` parameter, but the API server isn't providing it.

2. **Services Not Stopping Properly**
   - The GraphRAG services are not stopping properly when the `stop_services` function is called in the regression tests.
   - This causes Test 1 to fail at the "Verifying services are stopped" step.

3. **NLP Processing Test Error**
   - Test 4 (NLP Processing) is failing with the error "name 'expected' is not defined".
   - This appears to be a reference to an undefined variable in the test script.

4. **ChromaDB Directory Mismatch**
   - There is a mismatch between the ChromaDB directory specified in the environment variable and the directory used by the code.
   - The environment variable `CHROMA_PERSIST_DIRECTORY` is set to `/Users/andyspamer/.graphrag/data/chromadb` in the config file, but the code is using a default value of `./data/chromadb` when the environment variable is not found.

## Next Steps
To make the regression tests pass, the following steps need to be taken:

1. Fix the ChromaDB directory mismatch issue to ensure the vector database connects properly.
2. Fix the services not stopping properly issue to ensure Test 1 passes.
3. Fix the NLP Processing test error to ensure Test 4 passes.
4. Run the regression tests again to verify that all tests pass.

## Conclusion
The GraphRAG system has several issues that need to be fixed before the regression tests can pass. The most critical issue is the vector database connection, which is preventing all document-related operations from working. Once this issue is fixed, the other issues can be addressed one by one.