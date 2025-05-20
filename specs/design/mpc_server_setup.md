# GraphRAG MPC Server Setup Guide

This guide provides detailed instructions for setting up and troubleshooting the GraphRAG MPC (Model Context Protocol) server, which allows Claude and other AI assistants to interact with the GraphRAG system.

## What is the MPC Server?

The MPC server implements the Model Context Protocol, which is a standardized way for AI assistants like Claude to interact with external tools and services. The GraphRAG MPC server allows Claude to:

1. Search the GraphRAG knowledge base
2. Add documents to the system
3. Explore concepts and their relationships
4. Find passages about specific concepts

## Prerequisites

- Python 3.8 or higher
- Neo4j database (running locally or remotely)
- ChromaDB vector database
- GraphRAG system installed

## Installation

### 1. Install Required Dependencies

```bash
pip install neo4j>=5.14.0 websockets>=11.0.0 chromadb>=0.4.22 python-dotenv>=1.0.0
```

### 2. Configure Environment Variables

Create or update your `.env` file with the following settings:

```bash
NEO4J_URI=bolt://localhost:${GRAPHRAG_PORT_DOCKER_NEO4J_BOLT}  # Note: Using port 7688 for Docker mapping
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=graphrag
CHROMA_PERSIST_DIRECTORY=/path/to/graphRAG/data/chromadb
```

Note: If you're using Docker, the port mappings might be different. Check your `docker-compose.yml` file.

### 3. Configure MPC Settings

Create an `mcp_settings.json` file in Claude's configuration directory with the following content:

```json
{
  "mcpServers": {
    "GraphRAG": {
      "command": "/path/to/graphRAG/tools/graphrag-mcp",
      "args": ["--host", "0.0.0.0", "--port", "8767"],
      "env": {
        "PYTHONPATH": "/path/to/graphRAG",
        "NEO4J_URI": "bolt://localhost:${GRAPHRAG_PORT_DOCKER_NEO4J_BOLT}",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "graphrag",
        "CHROMA_PERSIST_DIRECTORY": "/path/to/graphRAG/data/chromadb"
      }
    }
  }
}
```

Replace `/path/to/graphRAG` with the actual path to your GraphRAG installation.

## Starting the MPC Server

### Option 1: Using the Wrapper Script

```bash
./tools/graphrag-mcp
```

This script will:

1. Set the correct PYTHONPATH
2. Install required dependencies if missing
3. Verify Neo4j driver installation
4. Start the MPC server on port 8767

### Option 2: Using Docker

If you're using Docker, the MPC server is automatically started when the container starts. You can check the logs to verify it's running:

```bash
docker-compose logs -f
```

### Option 3: Manual Start

```bash
export PYTHONPATH=/path/to/graphRAG
python -m src.mpc.mcp_server --host 0.0.0.0 --port ${GRAPHRAG_PORT_MCP}
```

## Testing the MPC Server

Use the provided test script to verify that the MPC server is working correctly:

```bash
python scripts/test_mcp_server.py
```

This script will:

1. Check if required dependencies are installed
2. Verify database connections
3. Test the MPC protocol by connecting to the server and making requests

## Troubleshooting

### Neo4j Driver Import Error

If you see an error like `cannot import name 'GraphDatabase' from 'neo4j'`, try:

1. Reinstalling the Neo4j driver:
   ```bash
   pip uninstall -y neo4j
   pip install neo4j>=5.14.0
   ```

2. Checking your Python path:
   ```bash
   python -c "import sys; print(sys.path)"
   ```

3. Verifying the Neo4j driver is installed:
   ```bash
   python -c "import neo4j; print(neo4j.__version__)"
   ```

### Database Connection Failures

If the MPC server is running in "limited mode" without database connections:

1. Verify Neo4j is running:
   ```bash
   curl http://localhost:${GRAPHRAG_PORT_NEO4J_HTTP}
   ```

2. Check your Neo4j credentials in the `.env` file

3. Verify the Neo4j port mapping if using Docker:
   ```bash
   docker-compose ps
   ```

4. Test the Neo4j connection directly:
   ```bash
   python -c "from neo4j import GraphDatabase; driver = GraphDatabase.driver('bolt://localhost:${GRAPHRAG_PORT_DOCKER_NEO4J_BOLT}', auth=('neo4j', 'graphrag')); session = driver.session(); result = session.run('RETURN 1'); print(result.single()[0]); driver.close()"
   ```

### Neo4j Password Reset Issues

If you're having trouble connecting to Neo4j, the password might not be set correctly. Here's how to reset it:

1. Stop the Neo4j server:
   ```bash
   ./neo4j/bin/neo4j stop
   ```

2. Reset the password using neo4j-admin:
   ```bash
   ./neo4j/bin/neo4j-admin dbms set-initial-password graphrag
   ```

   For Neo4j 4.x, use:
   ```bash
   ./neo4j/bin/neo4j-admin set-initial-password graphrag
   ```

3. Start Neo4j again:
   ```bash
   ./neo4j/bin/neo4j start
   ```

4. Verify the connection:
   ```bash
   curl -u neo4j:graphrag http://localhost:${GRAPHRAG_PORT_NEO4J_HTTP}/browser/
   ```

### Docker Port Mapping Issues

When using Docker, it's important to understand the port mappings:

| Service | Container Port | Host Port | Description |
|---------|---------------|-----------|-------------|
| Neo4j Browser | 7474 | 7475 | Neo4j web interface |
| Neo4j Bolt | 7687 | 7688 | Neo4j database connection |
| API Server | 5000 | 5001 | GraphRAG API |
| MPC Server | 8765 | 8766 | GraphRAG MPC server |

Common port mapping issues:

1. **Connection refused**: Make sure the ports are correctly mapped in `docker-compose.yml`

2. **Wrong connection URI**: When connecting from outside the container, use the host port (e.g., `bolt://localhost:${GRAPHRAG_PORT_DOCKER_NEO4J_BOLT}`). When connecting from inside the container, use the container port (e.g., `bolt://localhost:${GRAPHRAG_PORT_NEO4J_BOLT}`).

3. **Port conflicts**: If another service is using the same port, you'll need to change the host port mapping in `docker-compose.yml`.

4. **Checking port mappings**:
   ```bash
   docker-compose ps
   # or
   docker port graphrag
   ```

### WebSockets Import Error

If you see an error related to the `websockets` module:

```bash
pip install websockets>=11.0.0
```

### Claude Integration Issues

If Claude can't connect to the MPC server:

1. Verify the MPC server is running:
   ```bash
   curl -v telnet://localhost:${GRAPHRAG_PORT_MCP}
   ```

2. Check the `mcp_settings.json` file is in the correct location

3. Ensure the paths in `mcp_settings.json` are absolute paths

4. Check for network isolation issues if using Docker:
   ```bash
   docker network inspect graphrag_default
   ```

## Advanced Configuration

### Changing the Port

To change the port the MPC server listens on:

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

The MPC server logs to the console by default. To save logs to a file:

```bash
python -m src.mpc.mcp_server --host 0.0.0.0 --port ${GRAPHRAG_PORT_MCP} > mpc_server.log 2>&1
```

For more verbose logging, modify the logging level in `src/mpc/mcp_server.py`.

## Testing with Claude

To test the MPC server with Claude, follow these steps:

1. Make sure the MPC server is running and accessible from Claude's environment.

2. Verify Claude can see the GraphRAG tools by asking it to list available tools.

3. Test the search functionality:

   ```text
   Please search for "fine tuning" in the GraphRAG system.
   ```

4. Test the add-document functionality:

   ```text
   Please add this document to the GraphRAG system: "Fine-tuning is the process of taking a pre-trained language model and further training it on a specific dataset to adapt it for a particular task or domain."
   ```

5. If you encounter issues, ask Claude to diagnose the problem:

   ```text
   Can you check if there are any connection issues with the GraphRAG MPC server?
   ```

### Common Claude Integration Issues

1. **Tool not found**: Make sure the `mcp_settings.json` file is correctly configured and in the right location.

2. **Connection refused**: Verify the MPC server is running and the port is correctly specified in the `mcp_settings.json` file.

3. **Authentication errors**: Check that the Neo4j credentials in the `mcp_settings.json` file match those in the GraphRAG system.

4. **Timeout errors**: The MPC server might be taking too long to respond. Check the server logs for any performance issues.

5. **Missing dependencies**: Ensure all required Python packages are installed in Claude's environment.