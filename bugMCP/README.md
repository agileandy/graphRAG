# Bug Tracking API Server

This directory contains a FastAPI-based bug tracking system for the GraphRAG project.

## Overview

The Bug Tracking API Server provides a RESTful interface for managing bugs in the GraphRAG project. It's designed to be simple, reliable, and easy to use.

## Files

- `bugAPI.py`: The main API server implementation
- `bugAPI_client.py`: A client script for interacting with the API server
- `test_bugAPI.py`: A test script for verifying the API server functionality
- `bugs.json`: The data file where bugs are stored

## Usage

### Starting the Server

You can start the server using the service script:

```bash
./tools/bugapi-service.sh start
```

Or directly:

```bash
python bugMCP/bugAPI.py
```

By default, the server runs on `localhost:${GRAPHRAG_PORT_BUG_MCP}`. You can customize the host and port:

```bash
python bugMCP/bugAPI.py --host 0.0.0.0 --port ${GRAPHRAG_PORT_BUG_MCP}
```

### Using the Client

The client script provides both interactive and command-line modes:

#### Interactive Mode

```bash
python bugMCP/bugAPI_client.py
```

#### Command-Line Mode

```bash
# List all bugs
python bugMCP/bugAPI_client.py list

# Add a new bug
python bugMCP/bugAPI_client.py add --description "Bug description" --cause "Bug cause"

# Update a bug
python bugMCP/bugAPI_client.py update --id 1 --status fixed --resolution "Fixed in PR #123"

# Delete a bug
python bugMCP/bugAPI_client.py delete --id 1

# Get a specific bug
python bugMCP/bugAPI_client.py get --id 1
```

### Running Tests

To run the tests:

```bash
python bugMCP/test_bugAPI.py
```

## API Endpoints

The server provides the following RESTful endpoints:

1. `GET /bugs`: List all bugs
2. `POST /bugs`: Add a new bug
3. `GET /bugs/{bug_id}`: Get a specific bug
4. `PUT /bugs/{bug_id}`: Update a bug
5. `DELETE /bugs/{bug_id}`: Delete a bug

## Integration with AI Agents

AI agents can connect to the Bug Tracking API Server using standard HTTP requests. Here's an example of how an AI agent might use the API:

```python
import requests

# Add a bug
response = requests.post(
    "http://localhost:${GRAPHRAG_PORT_BUG_MCP}/bugs",
    json={
        "description": "Bug found by AI agent",
        "cause": "Identified during analysis"
    }
)
result = response.json()
bug_id = result.get("bug_id")

# Update the bug
response = requests.put(
    f"http://localhost:${GRAPHRAG_PORT_BUG_MCP}/bugs/{bug_id}",
    json={
        "status": "fixed",
        "resolution": "Fixed by AI agent"
    }
)
```

## Service Management

The `tools/bugapi-service.sh` script provides commands for managing the server:

```bash
# Start the server
./tools/bugapi-service.sh start

# Stop the server
./tools/bugapi-service.sh stop

# Restart the server
./tools/bugapi-service.sh restart

# Check server status
./tools/bugapi-service.sh status
```

## Troubleshooting

If you encounter issues:

1. Check if the server is running: `./tools/bugapi-service.sh status`
2. Check the log file: `cat bugMCP/bugapi.log`
3. Ensure the port is not in use by another application
4. Verify that the required packages are installed: `pip list | grep fastapi`

## API Documentation

When the server is running, you can access the auto-generated API documentation at:

- Swagger UI: `http://localhost:${GRAPHRAG_PORT_BUG_MCP}/docs`
- ReDoc: `http://localhost:${GRAPHRAG_PORT_BUG_MCP}/redoc`

These interactive documentation pages allow you to explore and test the API endpoints directly from your browser.