# GraphRAG Tools Directory

This directory has been reorganized to reduce duplication and improve maintainability. The tools and scripts have been moved to more appropriate locations based on their functionality.

## New Directory Structure

- **bin/**: Executable scripts and command-line tools
  - Contains the main GraphRAG command-line tools

- **examples/**: Example usage scripts
  - Client examples (MPC, MCP)
  - Integration examples (LangChain, OpenAI)
  - Simple demos

- **scripts/**: Core functionality scripts
  - **document_processing/**: Document addition and processing
  - **database_management/**: Database operations
  - **service_management/**: Service control scripts
  - **query/**: Query and search scripts

- **tests/**: Testing scripts
  - **component/**: Component-level tests
  - **regression/**: Regression tests

- **utils/**: Utility scripts
  - Docker management
  - Environment setup
  - Miscellaneous utilities

## Migration Guide

If you were using scripts from the old `tools/` directory, here's where to find them now:

- `add_pdf_documents.py` → `scripts/document_processing/add_pdf_documents.py`
- `add_all_ebooks.py` → `scripts/document_processing/add_ebooks_batch.py`
- `add_prompting_ebooks.py` → `scripts/document_processing/add_prompting_ebooks.py`
- `test_mpc_connection.py` → `tests/component/test_mpc_connection.py`
- `test_async_processing.py` → `tests/component/test_async_processing.py`
- `test_mpc_search.py` → `tests/component/test_mpc_search.py`
- `graphrag-service.sh` → `scripts/service_management/graphrag-service.sh`
- `bugapi-service.sh` → `scripts/service_management/bugapi-service.sh`
- `bugmcp-service.sh` → `scripts/service_management/bugmcp-service.sh`
- `query_neo4j.py` → `scripts/query/query_neo4j.py`
- `list_documents.py` → `scripts/query/list_documents.py`
- `graphrag_mpc_client.py` → `examples/graphrag_mpc_client.py`
- `graphrag` → `bin/graphrag`
- `graphrag-mcp` → `bin/graphrag-mcp`
- `graphrag-monitor.py` → `bin/graphrag-monitor.py`

For any questions or issues with the new structure, please refer to the project documentation or open an issue on the repository.