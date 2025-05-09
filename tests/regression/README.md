# GraphRAG Regression Tests

This directory contains regression tests for the GraphRAG system. These tests verify that the core functionality of the system works as expected.

## Test Structure

Each test is designed to be standalone and can be run independently. The tests are also designed to be run in sequence, with each test building on the previous one.

The tests are:

1. **Test 1: Start and Stop Services** - Verifies that the GraphRAG services can be started and stopped correctly.
2. **Test 2: Database Initialization** - Verifies that the databases (Neo4j and ChromaDB) can be initialized correctly.
3. **Test 3: Add Document** - Verifies that documents can be added to the system and indexed properly.
4. **Test 4: NLP Processing** - Verifies that NLP processing works correctly, extracting concepts and relationships from documents.
5. **Test 5: Search Functionality** - Verifies that search functionality works correctly, using both vector and graph approaches.
6. **Test 6: Deduplication** - Verifies that deduplication works correctly, preventing duplicate documents and concepts.
7. **Test 7: Message Passing Server** - Verifies that the Message Passing Communication (MPC) server works correctly, handling requests and returning appropriate responses.
8. **Test 8: Model Context Protocol Server** - Verifies that the Model Context Protocol (MCP) server works correctly, implementing the protocol for AI agent integration.

## Running the Tests

### Running All Tests

To run all tests in sequence:

```bash
python -m tests.regression.run_all_tests
```

### Running Individual Tests

Each test can be run individually:

```bash
python -m tests.regression.test_01_start_stop
python -m tests.regression.test_02_db_init
python -m tests.regression.test_03_add_document
python -m tests.regression.test_04_nlp_processing
python -m tests.regression.test_05_search
python -m tests.regression.test_06_deduplication
```

## Test Data

The `data` directory contains test documents and other data used by the tests.

## Utilities

The `test_utils.py` file contains utility functions used by the tests, such as functions to start and stop services, add documents, and search for documents.

## Notes

- These tests are designed to be run against a clean installation of the GraphRAG system.
- The tests will modify the databases, so they should not be run against a production system.
- Some tests may take a few minutes to run, especially those that involve NLP processing.
- If a test fails, it will provide detailed information about what went wrong.