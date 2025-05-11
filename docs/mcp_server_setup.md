# GraphRAG MCP Server Setup Guide

This guide provides detailed instructions for setting up and troubleshooting the GraphRAG MCP (Model Context Protocol) server, which allows Claude and other AI assistants to interact with the GraphRAG system.

## What is the MCP Server?

The MCP server implements the Model Context Protocol, which is a standardized way for AI assistants like Claude to interact with external tools and services. The GraphRAG MCP server allows Claude to:

1. Search the GraphRAG knowledge base
2. Add documents to the system
3. Explore concepts and their relationships
4. Find passages about specific concepts

## Prerequisites

Before setting up the MCP server, ensure you have:

1. GraphRAG installed and configured
2. Neo4j database running and accessible
3. ChromaDB initialized with a collection
4. Python 3.11 or later installed
5. Required Python packages installed:
   - websockets
   - neo4j
   - chromadb

## Configuration

The MCP server uses the following environment variables:

- `NEO4J_URI`: URI for the Neo4j database (default: bolt://localhost:7688)
- `NEO4J_USERNAME`: Username for the Neo4j database (default: neo4j)
- `NEO4J_PASSWORD`: Password for the Neo4j database (default: graphrag)
- `CHROMA_PERSIST_DIRECTORY`: Directory for ChromaDB persistence (default: ./data/chromadb)

Create an `mcp_settings.json` file in Claude's configuration directory with the following content:

```json
{
  "mcpServers": {
    "GraphRAG": {
      "command": "/path/to/graphRAG/tools/graphrag-mcp",
      "args": ["--host", "0.0.0.0", "--port", "8767"],
      "env": {
        "PYTHONPATH": "/path/to/graphRAG",
        "NEO4J_URI": "bolt://localhost:7688",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "graphrag",
        "CHROMA_PERSIST_DIRECTORY": "/path/to/graphRAG/data/chromadb"
      }
    }
  }
}
```

Replace `/path/to/graphRAG` with the actual path to your GraphRAG installation.

You can generate this file automatically using the provided script:

```bash
python tools/generate-mcp-settings.py --output mcp_settings.json
```

## Starting the MCP Server

### Option 1: Using the Wrapper Script

```bash
./tools/graphrag-mcp
```

This script will:

1. Set the correct PYTHONPATH
2. Install required dependencies if missing
3. Verify Neo4j driver installation
4. Start the MCP server on port 8767

### Option 2: Using Docker

If you're using Docker, the MCP server is automatically started when the container starts. You can check the logs to verify it's running:

```bash
docker-compose logs -f
```

### Option 3: Manual Start

```bash
export PYTHONPATH=/path/to/graphRAG
python -m src.mpc.mcp_server --host 0.0.0.0 --port 8767
```

## Testing the MCP Server

You can test the MCP server using the provided test script:

```bash
python tests/test_mcp_server.py
```

This script will:

1. Check if required dependencies are installed
2. Verify database connections
3. Test the MCP protocol
4. Test all available tools

You can also use the interactive client to test the MCP server:

```bash
python scripts/mcp_client_example.py
```

## Available Tools

The MCP server provides the following tools:

1. `ping`: Simple ping for connection testing
2. `search`: Perform hybrid search across the GraphRAG system
3. `concept`: Get information about a concept
4. `documents`: Get documents for a concept
5. `books-by-concept`: Find books mentioning a concept
6. `related-concepts`: Find concepts related to a concept
7. `passages-about-concept`: Find passages about a concept
8. `add-document`: Add a single document to the system
9. `add-folder`: Add a folder of documents to the system
10. `job-status`: Get status of a job
11. `list-jobs`: List all jobs
12. `cancel-job`: Cancel a job

## Advanced Configuration

### Changing the Port

To change the port the MCP server listens on:

1. Update the port in the `tools/graphrag-mcp` script
2. Update the port in your `mcp_settings.json` file
3. Update the port mapping in `docker-compose.yml` if using Docker

### Running in Production

For production environments:

1. Use a process manager like Supervisor or systemd
2. Set up proper logging
3. Configure authentication if needed
4. Consider using a reverse proxy for SSL termination

## Logs and Debugging

The MCP server logs to the console by default. To save logs to a file:

```bash
python -m src.mpc.mcp_server --host 0.0.0.0 --port 8767 > mcp_server.log 2>&1
```

For more verbose logging, use the `--log-level` option:

```bash
python -m src.mpc.mcp_server --host 0.0.0.0 --port 8767 --log-level DEBUG
```

## Troubleshooting

### Common Issues

1. **Connection refused**: Verify the MCP server is running and the port is correctly specified in the `mcp_settings.json` file.

2. **Neo4j connection error**: Check that Neo4j is running and the credentials in the environment variables are correct.

3. **ChromaDB connection error**: Verify that the ChromaDB persist directory exists and is writable.

4. **Tool not found**: Make sure the tool name is correct and the MCP server is properly initialized.

5. **Tool invocation error**: Check the tool parameters and make sure they match the expected format.

### Common Claude Integration Issues

1. **Tool not found**: Make sure the `mcp_settings.json` file is correctly configured and in the right location.

2. **Connection refused**: Verify the MCP server is running and the port is correctly specified in the `mcp_settings.json` file.

3. **Authentication errors**: Check that the Neo4j credentials in the `mcp_settings.json` file match those in the GraphRAG system.

4. **Timeout errors**: The MCP server might be taking too long to respond. Check the server logs for any performance issues.

5. **Missing dependencies**: Ensure all required Python packages are installed in Claude's environment.
