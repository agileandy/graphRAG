# GraphRAG Test Suite

This directory contains automated tests for the GraphRAG system, including both Web API and Model Context Protocol (MCP) tests.

## Test Organization

```
tests/
├── common_utils/          # Shared test utilities
│   ├── __init__.py
│   └── test_utils.py     # Common test functions
├── web_api_suite/        # Web API tests
│   ├── __init__.py
│   ├── conftest.py      # Web API test configuration
│   └── test files...    # Web API test modules
└── mcp_suite/           # MCP server tests
    ├── __init__.py
    ├── conftest.py      # MCP test configuration
    └── test files...    # MCP test modules
```

## Test Dependencies

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run specific test suites:
```bash
# Run Web API tests only
pytest tests/web_api_suite/

# Run MCP tests only
pytest tests/mcp_suite/
```

### Run with markers:
```bash
# Run integration tests
pytest -m integration

# Run smoke tests
pytest -m smoke
```

### Run with parallel execution:
```bash
pytest -n auto  # Uses pytest-xdist
```

### Run with coverage:
```bash
pytest --cov=src --cov-report=html
```

## Test Suite Organization

### Web API Tests

1. Server Start/Stop (`01_web_test_server_start_stop.py`)
2. Database Initialization (`02_web_test_database_init.py`)
3. Document Addition (`03_web_test_add_document.py`)
4. Folder Addition (`04_web_test_add_folder.py`)
5. Duplicate Rejection (`05_web_test_add_duplicate_rejection.py`)
6. Vector String Search (`06_web_test_search_vector_string.py`)
7. Graph Concept Search (`07_web_test_search_graph_concept.py`)
8. Related Documents (`08_web_test_find_related_documents.py`)
9. Job Queue (`09_web_test_add_job_queue.py`)
10. Job Status (`10_web_test_check_job_status.py`)
11. Job Deletion (`11_web_test_delete_unprocessed_job.py`)

### MCP Tests

1. Server Start/Stop (`01_mcp_test_server_start_stop.py`)
2. Database Initialization (`02_mcp_test_database_init.py`)
3. Document Addition (`03_mcp_test_add_document.py`)
4. Folder Addition (`04_mcp_test_add_folder.py`)
5. Duplicate Rejection (`05_mcp_test_add_duplicate_rejection.py`)
6. Vector String Search (`06_mcp_test_search_vector_string.py`)
7. Graph Concept Search (`07_mcp_test_search_graph_concept.py`)
8. Related Documents (`08_mcp_test_find_related_documents.py`)
9. Job Queue (`09_mcp_test_add_job_queue.py`)
10. Job Status (`10_mcp_test_check_job_status.py`)
11. Job Deletion (`11_mcp_test_delete_unprocessed_job.py`)

## Test Utilities

Common test utilities in `test_utils.py` include:

- Server connection helpers
- Test data generators
- Result formatting and reporting
- Web API request wrappers
- MCP websocket helpers
- Synchronous wrappers for async functions

## Test Configuration

Configuration is managed through:

- `pytest.ini` - Global pytest configuration
- `conftest.py` - Suite-specific fixtures and setup
- Environment variables (see `.env.example`)

## Test Markers

- `@pytest.mark.web` - Web API tests
- `@pytest.mark.mcp` - MCP server tests
- `@pytest.mark.async_test` - Asynchronous tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.smoke` - Smoke tests

## Contributing

When adding new tests:

1. Follow the existing file naming convention
2. Add appropriate test markers
3. Update this README if adding new test categories
4. Add any new dependencies to requirements-test.txt