# MCP Server Foundation Implementation

This document provides detailed implementation guidance for creating the MCP server foundation for the GraphRAG project.

## Overview

The Model Context Protocol (MCP) server will allow AI agents to interact with the GraphRAG system through standardized tools. The server will implement the JSON-RPC 2.0 protocol and follow the Model Context Protocol specification.

## Implementation Details

### 1. Create Basic MCP Server Implementation

**File**: `src/mpc/mcp_server.py`

```python
"""
MCP (Model Context Protocol) server for GraphRAG project.

This module implements the Model Context Protocol server that allows AI agents
to interact with the GraphRAG system through standardized tools.

The server follows the JSON-RPC 2.0 protocol and implements the MCP specification.
"""
import os
import sys
import json
import asyncio
import logging
import websockets
from typing import Dict, Any, List, Optional, Callable

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database.neo4j_db import Neo4jDatabase
from src.database.vector_db import VectorDatabase
from src.database.db_linkage import DatabaseLinkage
from src.processing.job_manager import JobManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mcp_server')

# Initialize database connections
neo4j_db = Neo4jDatabase()
vector_db = VectorDatabase()
db_linkage = DatabaseLinkage(neo4j_db, vector_db)

# Initialize job manager
job_manager = JobManager()

# MCP protocol version
MCP_PROTOCOL_VERSION = "2024-11-05"

# Server information
SERVER_NAME = "GraphRAG MCP Server"
SERVER_VERSION = "1.0.0"

# Tool definitions
TOOLS = [
    {
        "name": "ping",
        "description": "Simple ping for connection testing",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    # Additional tools will be added here
]

# Tool handlers
async def handle_ping(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle ping request.
    
    Args:
        parameters: Request parameters (empty for ping)
        
    Returns:
        Ping response
    """
    return {
        "message": "Pong!",
        "timestamp": asyncio.get_event_loop().time(),
        "status": "success"
    }

# Map of tool handlers
TOOL_HANDLERS = {
    "ping": handle_ping,
    # Additional tool handlers will be added here
}

async def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle initialize request.
    
    Args:
        params: Initialize parameters
        
    Returns:
        Initialize response
    """
    client_protocol_version = params.get("protocolVersion")
    client_info = params.get("clientInfo", {})
    
    logger.info(f"Client connected: {client_info.get('name')} {client_info.get('version')}")
    logger.info(f"Client protocol version: {client_protocol_version}")
    
    return {
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION
        },
        "protocolVersion": MCP_PROTOCOL_VERSION,
        "capabilities": {}
    }

async def handle_get_tools(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle getTools request.
    
    Args:
        params: GetTools parameters
        
    Returns:
        GetTools response with tool definitions
    """
    return {
        "tools": TOOLS
    }

async def handle_invoke_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle invokeTool request.
    
    Args:
        params: InvokeTool parameters
        
    Returns:
        InvokeTool response with tool result
    """
    tool_name = params.get("name")
    tool_parameters = params.get("parameters", {})
    
    if tool_name not in TOOL_HANDLERS:
        return {
            "error": {
                "code": -32601,
                "message": f"Tool not found: {tool_name}",
                "data": {
                    "availableTools": list(TOOL_HANDLERS.keys())
                }
            }
        }
    
    try:
        handler = TOOL_HANDLERS[tool_name]
        result = await handler(tool_parameters)
        return {
            "result": result
        }
    except Exception as e:
        logger.exception(f"Error invoking tool {tool_name}")
        return {
            "error": {
                "code": -32603,
                "message": f"Error invoking tool: {str(e)}"
            }
        }

async def handle_connection(websocket):
    """
    Handle WebSocket connection.
    
    Args:
        websocket: WebSocket connection
    """
    client_id = id(websocket)
    logger.info(f"Client connected: {client_id}")
    
    try:
        async for message in websocket:
            try:
                # Parse message
                data = json.loads(message)
                
                # Extract JSON-RPC fields
                jsonrpc = data.get("jsonrpc")
                method = data.get("method")
                params = data.get("params", {})
                request_id = data.get("id")
                
                # Validate JSON-RPC version
                if jsonrpc != "2.0":
                    response = {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32600,
                            "message": "Invalid JSON-RPC version"
                        },
                        "id": request_id
                    }
                    await websocket.send(json.dumps(response))
                    continue
                
                # Handle method
                result = None
                error = None
                
                if method == "initialize":
                    result = await handle_initialize(params)
                elif method == "getTools":
                    result = await handle_get_tools(params)
                elif method == "invokeTool":
                    result = await handle_invoke_tool(params)
                else:
                    error = {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                
                # Prepare response
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id
                }
                
                if error:
                    response["error"] = error
                else:
                    response["result"] = result
                
                # Send response
                await websocket.send(json.dumps(response))
                
            except json.JSONDecodeError:
                # Invalid JSON
                response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    },
                    "id": None
                }
                await websocket.send(json.dumps(response))
            except Exception as e:
                # Internal error
                logger.exception("Error handling message")
                response = {
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    },
                    "id": None
                }
                await websocket.send(json.dumps(response))
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {client_id}")
    except Exception as e:
        logger.exception(f"Error handling connection for client {client_id}")

async def start_server(host: str = 'localhost', port: int = 8766):
    """
    Start the MCP server.
    
    Args:
        host: Server host
        port: Server port
    """
    server = await websockets.serve(handle_connection, host, port)
    logger.info(f"MCP server started on ws://{host}:{port}")
    logger.info(f"Available tools: {', '.join(TOOL_HANDLERS.keys())}")
    
    # Keep the server running
    await server.wait_closed()

def main():
    """
    Main function to start the MCP server.
    """
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Start the GraphRAG MCP server")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8766, help="Server port")
    parser.add_argument("--log-level", type=str, default="INFO", 
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    args = parser.parse_args()
    
    # Set logging level
    logger.setLevel(getattr(logging, args.log_level))
    
    # Start the server
    try:
        asyncio.run(start_server(args.host, args.port))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception("Error starting server")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 2. Create Wrapper Script

**File**: `tools/graphrag-mcp`

```bash
#!/bin/bash
# GraphRAG MCP Server Wrapper Script

# Change to the project root directory
cd "$(dirname "$0")/.."

# Default values
HOST="0.0.0.0"
PORT="8766"
LOG_LEVEL="INFO"

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set PYTHONPATH
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Check if required packages are installed
REQUIRED_PACKAGES=("websockets" "neo4j" "chromadb")
MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python -c "import $package" &>/dev/null; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "Missing required packages: ${MISSING_PACKAGES[*]}"
    echo "Installing missing packages..."
    uv pip install "${MISSING_PACKAGES[@]}"
fi

# Start the MCP server
echo "Starting GraphRAG MCP server on $HOST:$PORT..."
python -m src.mpc.mcp_server --host "$HOST" --port "$PORT" --log-level "$LOG_LEVEL"
```

### 3. Update Docker Configuration

**File**: `docker-compose.yml` (add to existing configuration)

```yaml
  # Add MCP server port mapping
  ports:
    - "8766:8766"  # MCP server
```

**File**: `docker-entrypoint.sh` (add to existing script)

```bash
# Start the MCP server in the background
echo "Starting MCP server..."
cd /app && python -m src.mpc.mcp_server --host 0.0.0.0 --port 8766 &

# Give the MCP server a moment to start
sleep 3
echo "✅ MCP server started."
```

### 4. Create Sample MCP Settings

**File**: `docs/mcp_settings_example.json`

```json
{
  "mcpServers": {
    "GraphRAG": {
      "command": "/path/to/graphRAG/tools/graphrag-mcp",
      "args": ["--host", "0.0.0.0", "--port", "8766"],
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

## Next Steps

After implementing the MCP server foundation, the next steps will be:

1. Implement all 11 required tools
2. Create comprehensive tests for the MCP server
3. Update documentation with MCP server information
4. Test integration with AI agents