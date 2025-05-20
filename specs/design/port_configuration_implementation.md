# Port Configuration Implementation

This document summarizes the implementation of the centralized port configuration system for the GraphRAG project.

## Overview

The centralized port configuration system provides a single source of truth for all port configurations used by GraphRAG services. It ensures consistent port usage across the codebase and makes it easy to override port values through environment variables.

## Implementation Details

### 1. Centralized Port Configuration

The centralized port configuration is defined in `src/config/ports.py`. This file:

- Defines default port values for all services
- Provides utility functions for working with ports
- Loads port values from environment variables

### 2. Environment Variables

Port values can be overridden through environment variables with the prefix `GRAPHRAG_PORT_`. For example:

```
GRAPHRAG_PORT_API=5002
GRAPHRAG_PORT_MPC=8766
```

These environment variables are loaded from the `.env` file in the project root.

### 3. Port Configuration Templates

The following templates have been created to help users configure port values:

- `config/env.sample`: Template for the `.env` file
- `config/env.docker`: Template for Docker environment variables
- `bugMCP/mcp_settings.template.json`: Template for the Bug MCP settings

### 4. Updated Files

The following files have been updated to use the centralized port configuration:

#### Python Files
- `src/config/ports.py`: Centralized port configuration
- `src/database/neo4j_db.py`: Neo4j database connection
- `src/agents/openai_functions.py`: OpenAI function calling integration
- `src/agents/langchain_tools.py`: LangChain tools integration
- `src/agent-tools/utils.py`: Agent tools utilities
- `bin/graphrag-monitor.py`: Service monitoring script
- `examples/mpc_client_example.py`: MPC client example
- `examples/mcp_client_example.py`: MCP client example
- `utils/generate-mcp-settings.py`: MCP settings generation
- `tests/test_neo4j.py`: Neo4j tests
- `tests/test_add_document_with_concepts.py`: Document tests
- `tests/test_mcp_server.py`: MCP server tests
- `tests/test_api_add_document.py`: API tests
- `tests/regression/test_utils.py`: Regression test utilities
- `scripts/document_processing/process_ebooks.py`: Ebook processing script
- `bugMCP/bugMCP.py`: Bug MCP server
- `bugMCP/bugAPI_client.py`: Bug API client
- `bugMCP/generate_settings.py`: Bug MCP settings generation

#### Shell Scripts
- `docker-entrypoint.sh`: Docker entrypoint script
- `utils/docker_build_run.sh`: Docker build and run script
- `utils/docker_build_debug.sh`: Docker build and debug script
- `scripts/service_management/graphrag-service.sh`: GraphRAG service script
- `scripts/service_management/bugmcp-service.sh`: Bug MCP service script
- `scripts/service_management/bugapi-service.sh`: Bug API service script
- `scripts/check_ports.sh`: Port availability checking script

#### Configuration Files
- `docker-compose.yml`: Docker Compose configuration
- `bugMCP/mcp_settings.template.json`: Bug MCP settings template

#### Documentation Files
- `docs/port_configuration.md`: Port configuration documentation
- `docs/updating_port_references.md`: Guide for updating port references
- `docs/port_configuration_summary.md`: Summary of port configuration changes
- Various other documentation files

### 5. Utility Scripts

The following utility scripts have been created to help with port configuration:

- `scripts/update_port_references.py`: Finds hardcoded port references in the codebase
- `scripts/update_docs_port_references.py`: Updates port references in documentation files
- `scripts/check_ports.sh`: Checks if required ports are available
- `bugMCP/generate_settings.py`: Generates Bug MCP settings from template

## Usage

### In Python Code

```python
from src.config import get_port

# Get the port for a specific service
api_port = get_port('api')
mpc_port = get_port('mpc')
neo4j_port = get_port('neo4j_bolt')

# Use the port in your code
app.run(port=api_port)
```

### In Shell Scripts

```bash
# Source the .env file
source .env

# Use the environment variables
echo "API Port: $GRAPHRAG_PORT_API"
echo "MPC Port: $GRAPHRAG_PORT_MPC"
```

### In Configuration Files

```json
{
  "server_details": {
    "host": "localhost", 
    "port": "${GRAPHRAG_PORT_BUG_MCP}",
    "base_path": "/mcp"
  }
}
```

## Benefits

1. **Single source of truth**: All port configurations are defined in one place
2. **Easy to override**: Port values can be overridden through environment variables
3. **Consistent usage**: All code uses the same port values
4. **Better documentation**: Port configurations are well-documented
5. **Easier to maintain**: Changes to port values only need to be made in one place
6. **Reduced conflicts**: Port conflicts are easier to identify and resolve

## Next Steps

1. **Update remaining documentation**: Some documentation files still contain hardcoded port references
2. **Add port configuration tests**: Add tests to verify that port configuration works correctly
3. **Improve error handling**: Add better error handling for port conflicts
4. **Add port configuration UI**: Add a UI for configuring port values