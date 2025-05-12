# MCP Client Configuration and Testing

This document provides detailed implementation guidance for creating the MCP client configuration and testing the MCP server for the GraphRAG project.

## Overview

After implementing the MCP server and tools, we need to create client configuration for AI agent integration and comprehensive tests to verify that everything works correctly.

## Implementation Details

### 1. Client Configuration

#### 1.1 Create MCP Settings Generator

**File**: `tools/generate-mcp-settings.py`

```python
#!/usr/bin/env python3
"""
Generate MCP settings for AI agent integration.

This script generates an MCP settings file that can be used to configure
AI agents to use the GraphRAG MCP server.
"""

import os
import sys
import json
import argparse
from pathlib import Path

def generate_mcp_settings(output_path: str, host: str = "localhost", port: int = 8766):
    """
    Generate MCP settings file.
    
    Args:
        output_path: Path to output file
        host: MCP server host
        port: MCP server port
    """
    # Get the absolute path to the GraphRAG installation
    graphrag_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Get the absolute path to the graphrag-mcp script
    mcp_script_path = os.path.join(graphrag_path, "tools", "graphrag-mcp")
    
    # Create the settings object
    settings = {
        "mcpServers": {
            "GraphRAG": {
                "command": mcp_script_path,
                "args": ["--host", "0.0.0.0", "--port", str(port)],
                "env": {
                    "PYTHONPATH": graphrag_path,
                    "NEO4J_URI": "bolt://localhost:${GRAPHRAG_PORT_DOCKER_NEO4J_BOLT}",
                    "NEO4J_USERNAME": "neo4j",
                    "NEO4J_PASSWORD": "graphrag",
                    "CHROMA_PERSIST_DIRECTORY": os.path.join(graphrag_path, "data", "chromadb")
                }
            }
        }
    }
    
    # Write the settings to the output file
    with open(output_path, "w") as f:
        json.dump(settings, f, indent=2)
    
    print(f"MCP settings written to {output_path}")
    print(f"GraphRAG path: {graphrag_path}")
    print(f"MCP script path: {mcp_script_path}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate MCP settings for AI agent integration")
    parser.add_argument("--output", type=str, default="mcp_settings.json", help="Output file path")
    parser.add_argument("--host", type=str, default="localhost", help="MCP server host")
    parser.add_argument("--port", type=int, default=8766, help="MCP server port")
    args = parser.parse_args()
    
    generate_mcp_settings(args.output, args.host, args.port)

if __name__ == "__main__":
    main()
```

#### 1.2 Create MCP Client Example

**File**: `scripts/mcp_client_example.py`

```python
#!/usr/bin/env python3
"""
Example client for the GraphRAG MCP server.

This script demonstrates how to interact with the GraphRAG MCP server
using the JSON-RPC 2.0 protocol.
"""

import json
import asyncio
import websockets
import argparse
from typing import Dict, Any, List, Optional

async def send_request(websocket, method: str, params: Dict[str, Any], request_id: int) -> Dict[str, Any]:
    """
    Send a JSON-RPC request to the MCP server.
    
    Args:
        websocket: WebSocket connection
        method: Method name
        params: Method parameters
        request_id: Request ID
        
    Returns:
        Server response
    """
    # Create the request
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }
    
    # Send the request
    await websocket.send(json.dumps(request))
    
    # Receive the response
    response = await websocket.recv()
    
    # Parse the response
    return json.loads(response)

async def initialize(websocket) -> Dict[str, Any]:
    """
    Initialize the MCP server connection.
    
    Args:
        websocket: WebSocket connection
        
    Returns:
        Initialize response
    """
    return await send_request(
        websocket,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "mcp-client-example",
                "version": "0.1.0"
            }
        },
        0
    )

async def get_tools(websocket) -> List[Dict[str, Any]]:
    """
    Get available tools from the MCP server.
    
    Args:
        websocket: WebSocket connection
        
    Returns:
        List of available tools
    """
    response = await send_request(
        websocket,
        "getTools",
        {},
        1
    )
    
    return response.get("result", {}).get("tools", [])

async def invoke_tool(websocket, tool_name: str, parameters: Dict[str, Any], request_id: int) -> Dict[str, Any]:
    """
    Invoke a tool on the MCP server.
    
    Args:
        websocket: WebSocket connection
        tool_name: Tool name
        parameters: Tool parameters
        request_id: Request ID
        
    Returns:
        Tool result
    """
    return await send_request(
        websocket,
        "invokeTool",
        {
            "name": tool_name,
            "parameters": parameters
        },
        request_id
    )

async def interactive_client(uri: str = "ws://localhost:8766"):
    """
    Run an interactive client for the MCP server.
    
    Args:
        uri: WebSocket URI
    """
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to MCP server.")
            
            # Initialize the connection
            init_response = await initialize(websocket)
            print("\nInitialize response:")
            print(json.dumps(init_response, indent=2))
            
            # Get available tools
            tools = await get_tools(websocket)
            print("\nAvailable tools:")
            for i, tool in enumerate(tools):
                print(f"{i+1}. {tool['name']} - {tool['description']}")
            
            # Interactive loop
            request_id = 2
            while True:
                print("\nEnter tool number to invoke (0 to exit):")
                choice = input("> ")
                
                if choice == "0":
                    break
                
                try:
                    tool_index = int(choice) - 1
                    if tool_index < 0 or tool_index >= len(tools):
                        print(f"Invalid tool number. Please enter a number between 1 and {len(tools)}.")
                        continue
                    
                    tool = tools[tool_index]
                    print(f"\nInvoking tool: {tool['name']}")
                    print(f"Description: {tool['description']}")
                    print("Parameters:")
                    
                    # Get parameters from user
                    parameters = {}
                    for prop_name, prop_info in tool.get("parameters", {}).get("properties", {}).items():
                        required = prop_name in tool.get("parameters", {}).get("required", [])
                        default = prop_info.get("default")
                        description = prop_info.get("description", "")
                        
                        prompt = f"{prop_name}"
                        if description:
                            prompt += f" ({description})"
                        if required:
                            prompt += " (required)"
                        elif default is not None:
                            prompt += f" (default: {default})"
                        prompt += ": "
                        
                        value = input(prompt)
                        
                        if value:
                            # Convert value to appropriate type
                            if prop_info.get("type") == "integer":
                                parameters[prop_name] = int(value)
                            elif prop_info.get("type") == "boolean":
                                parameters[prop_name] = value.lower() in ["true", "yes", "y", "1"]
                            else:
                                parameters[prop_name] = value
                    
                    # Invoke the tool
                    response = await invoke_tool(websocket, tool["name"], parameters, request_id)
                    request_id += 1
                    
                    print("\nResponse:")
                    print(json.dumps(response, indent=2))
                    
                except ValueError:
                    print("Invalid input. Please enter a number.")
                except Exception as e:
                    print(f"Error: {e}")
    
    except Exception as e:
        print(f"Error connecting to MCP server: {e}")

async def non_interactive_client(uri: str, tool_name: str, parameters: Dict[str, Any]):
    """
    Run a non-interactive client for the MCP server.
    
    Args:
        uri: WebSocket URI
        tool_name: Tool name
        parameters: Tool parameters
    """
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to MCP server. Invoking tool: {tool_name}")
            
            # Initialize the connection
            await initialize(websocket)
            
            # Invoke the tool
            response = await invoke_tool(websocket, tool_name, parameters, 1)
            
            print("\nResponse:")
            print(json.dumps(response, indent=2))
            
            return response
    
    except Exception as e:
        print(f"Error connecting to MCP server: {e}")
        return None

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Example client for the GraphRAG MCP server")
    parser.add_argument("--host", type=str, default="localhost", help="MCP server host")
    parser.add_argument("--port", type=int, default=8766, help="MCP server port")
    parser.add_argument("--tool", type=str, help="Tool to invoke (non-interactive mode)")
    parser.add_argument("--params", type=str, help="Tool parameters as JSON (non-interactive mode)")
    
    args = parser.parse_args()
    
    uri = f"ws://{args.host}:{args.port}"
    
    if args.tool:
        # Non-interactive mode
        parameters = {}
        if args.params:
            try:
                parameters = json.loads(args.params)
            except json.JSONDecodeError:
                print(f"Error parsing parameters: {args.params}")
                return
        
        asyncio.run(non_interactive_client(uri, args.tool, parameters))
    else:
        # Interactive mode
        asyncio.run(interactive_client(uri))

if __name__ == "__main__":
    main()
```

### 2. Testing

#### 2.1 Enhance MCP Server Test

**File**: `tests/test_mcp_server.py` (update existing file)

```python
#!/usr/bin/env python3
"""
Test script for the GraphRAG MCP server.

This script tests the MCP server by:
1. Checking if the Neo4j driver is installed
2. Verifying database connections
3. Testing the MCP server protocol
4. Testing all available tools
"""

import os
import sys
import json
import asyncio
import websockets
import importlib.util
from typing import Dict, Any, List, Optional

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def check_package_installed(package_name: str) -> bool:
    """Check if a package is installed."""
    return importlib.util.find_spec(package_name) is not None

def print_section(title: str) -> None:
    """Print a section title."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

async def send_request(websocket, method: str, params: Dict[str, Any], request_id: int) -> Dict[str, Any]:
    """
    Send a JSON-RPC request to the MCP server.
    
    Args:
        websocket: WebSocket connection
        method: Method name
        params: Method parameters
        request_id: Request ID
        
    Returns:
        Server response
    """
    # Create the request
    request = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }
    
    # Send the request
    await websocket.send(json.dumps(request))
    
    # Receive the response
    response = await websocket.recv()
    
    # Parse the response
    return json.loads(response)

async def test_mcp_protocol(uri: str = "ws://localhost:8766") -> None:
    """Test the MCP protocol."""
    print_section("Testing MCP Protocol")
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to MCP server")

            # Test initialize
            print("\nTesting initialize...")
            init_response = await send_request(
                websocket,
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "0.1.0"
                    }
                },
                0
            )
            print(f"Response: {json.dumps(init_response, indent=2)}")

            if "result" in init_response:
                print("✅ Initialize successful")
            else:
                print("❌ Initialize failed")

            # Test getTools
            print("\nTesting getTools...")
            tools_response = await send_request(
                websocket,
                "getTools",
                {},
                1
            )
            print(f"Response: {json.dumps(tools_response, indent=2)}")

            if "result" in tools_response and "tools" in tools_response["result"]:
                tools = tools_response["result"]["tools"]
                print(f"✅ GetTools successful, found {len(tools)} tools")
                
                # Test each tool
                for i, tool in enumerate(tools):
                    tool_name = tool["name"]
                    print(f"\nTesting tool {i+1}/{len(tools)}: {tool_name}")
                    
                    # Prepare test parameters for each tool
                    test_params = get_test_parameters(tool_name)
                    
                    # Invoke the tool
                    tool_response = await send_request(
                        websocket,
                        "invokeTool",
                        {
                            "name": tool_name,
                            "parameters": test_params
                        },
                        i + 2
                    )
                    
                    print(f"Response: {json.dumps(tool_response, indent=2)}")
                    
                    if "result" in tool_response:
                        print(f"✅ Tool {tool_name} invoked successfully")
                        if "error" in tool_response["result"].get("result", {}):
                            print(f"⚠️ Tool returned an error: {tool_response['result']['result'].get('error')}")
                    else:
                        print(f"❌ Tool {tool_name} invocation failed")
            else:
                print("❌ GetTools failed")

    except ConnectionRefusedError:
        print("❌ Connection refused. Make sure the MCP server is running.")
    except Exception as e:
        print(f"❌ Error testing MCP protocol: {e}")

def get_test_parameters(tool_name: str) -> Dict[str, Any]:
    """
    Get test parameters for a tool.
    
    Args:
        tool_name: Tool name
        
    Returns:
        Test parameters
    """
    # Define test parameters for each tool
    test_params = {
        "ping": {},
        "search": {
            "query": "neural networks"
        },
        "concept": {
            "concept_name": "neural networks"
        },
        "documents": {
            "concept_name": "neural networks",
            "limit": 3
        },
        "books-by-concept": {
            "concept_name": "neural networks",
            "limit": 3
        },
        "related-concepts": {
            "concept_name": "neural networks",
            "limit": 5
        },
        "passages-about-concept": {
            "concept_name": "neural networks",
            "limit": 3
        },
        "add-document": {
            "text": "This is a test document about neural networks and deep learning.",
            "metadata": {
                "title": "Test Document",
                "author": "MCP Test"
            },
            "async": False
        },
        "add-folder": {
            "folder_path": "./tests/test_data",
            "async": False
        },
        "job-status": {
            "job_id": "job-12345"
        },
        "list-jobs": {
            "limit": 5
        },
        "cancel-job": {
            "job_id": "job-12345"
        }
    }
    
    return test_params.get(tool_name, {})

def check_database_connections() -> None:
    """Check database connections."""
    print_section("Checking Database Connections")

    # Check Neo4j
    print("Checking Neo4j connection...")
    try:
        from src.database.neo4j_db import Neo4jDatabase
        # Try with port 7688 (Docker mapping) and explicit credentials
        neo4j_db = Neo4jDatabase(
            uri="bolt://localhost:${GRAPHRAG_PORT_DOCKER_NEO4J_BOLT}",
            username="neo4j",
            password="graphrag"
        )
        print(f"Connecting to Neo4j at {neo4j_db.uri} with username {neo4j_db.username}")
        if neo4j_db.verify_connection():
            print("✅ Neo4j connection successful")
        else:
            print("❌ Neo4j connection failed")
            # Try with the default port as fallback
            print("Trying with default port 7687...")
            neo4j_db = Neo4jDatabase(
                uri="bolt://localhost:${GRAPHRAG_PORT_NEO4J_BOLT}",
                username="neo4j",
                password="graphrag"
            )
            if neo4j_db.verify_connection():
                print("✅ Neo4j connection successful with default port")
            else:
                print("❌ Neo4j connection failed with default port")
    except ImportError as e:
        print(f"❌ Neo4j database module import failed: {e}")
    except Exception as e:
        print(f"❌ Neo4j connection error: {e}")

    # Check Vector DB
    print("\nChecking Vector DB connection...")
    try:
        from src.database.vector_db import VectorDatabase
        vector_db = VectorDatabase()
        if vector_db.verify_connection():
            print("✅ Vector DB connection successful")
        else:
            print("❌ Vector DB connection failed")
    except ImportError as e:
        print(f"❌ Vector DB module import failed: {e}")
    except Exception as e:
        print(f"❌ Vector DB connection error: {e}")

def check_dependencies() -> None:
    """Check if required dependencies are installed."""
    print_section("Checking Dependencies")

    dependencies = [
        ("neo4j", "Neo4j driver"),
        ("websockets", "WebSockets"),
        ("chromadb", "ChromaDB"),
        ("dotenv", "Python-dotenv")
    ]

    for package, description in dependencies:
        if check_package_installed(package):
            print(f"✅ {description} is installed")
        else:
            print(f"❌ {description} is NOT installed")

def main() -> None:
    """Main function."""
    print_section("GraphRAG MCP Server Test")
    print("This script tests the GraphRAG MCP server and its dependencies.")

    # Check dependencies
    check_dependencies()

    # Check database connections
    check_database_connections()

    # Test MCP protocol
    asyncio.run(test_mcp_protocol())

    print_section("Test Complete")

if __name__ == "__main__":
    main()
```

#### 2.2 Create Test Data

**Directory**: `tests/test_data/`

Create a few simple test documents in this directory:

**File**: `tests/test_data/test_document_1.txt`

```
# Neural Networks

Neural networks are a fundamental component of deep learning. They are inspired by the structure and function of the human brain, consisting of interconnected nodes or "neurons" that process and transmit information.

## Key Concepts

- Neurons: The basic computational units
- Weights: Parameters that determine the strength of connections
- Activation Functions: Functions that determine the output of a neuron
- Layers: Groups of neurons that process information together
```

**File**: `tests/test_data/test_document_2.txt`

```
# Deep Learning

Deep learning is a subset of machine learning that uses neural networks with multiple layers (deep neural networks) to analyze various factors of data. It is particularly effective for tasks like image recognition, natural language processing, and speech recognition.

## Applications

- Computer Vision
- Natural Language Processing
- Speech Recognition
- Recommendation Systems
```

### 3. Documentation

#### 3.1 Create MCP Server Setup Guide

**File**: `docs/mcp_server_setup.md`

```markdown
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
4. Python 3.12 or later installed
5. Required Python packages installed:
   - websockets
   - neo4j
   - chromadb

## Configuration

The MCP server uses the following environment variables:

- `NEO4J_URI`: URI for the Neo4j database (default: bolt://localhost:${GRAPHRAG_PORT_DOCKER_NEO4J_BOLT})
- `NEO4J_USERNAME`: Username for the Neo4j database (default: neo4j)
- `NEO4J_PASSWORD`: Password for the Neo4j database (default: graphrag)
- `CHROMA_PERSIST_DIRECTORY`: Directory for ChromaDB persistence (default: ./data/chromadb)

Create an `mcp_settings.json` file in Claude's configuration directory with the following content:

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
4. Start the MCP server on port 8766

### Option 2: Using Docker

If you're using Docker, the MCP server is automatically started when the container starts. You can check the logs to verify it's running:

```bash
docker-compose logs -f
```

### Option 3: Manual Start

```bash
export PYTHONPATH=/path/to/graphRAG
python -m src.mpc.mcp_server --host 0.0.0.0 --port 8766
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
python -m src.mpc.mcp_server --host 0.0.0.0 --port 8766 --log-level DEBUG > mcp_server.log 2>&1
```

For more verbose logging, use the `--log-level` option:

```bash
python -m src.mpc.mcp_server --host 0.0.0.0 --port 8766 --log-level DEBUG
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
```

#### 3.2 Update README.md

Add the following section to the existing README.md:

```markdown
## MCP Server

GraphRAG provides a Model Context Protocol (MCP) server that allows AI assistants like Claude to interact with the system:

```bash
# Start the MCP server
./tools/graphrag-mcp

# Test the MCP server
python tests/test_mcp_server.py

# Run the interactive client
python scripts/mcp_client_example.py
```

The MCP server implements the following tools:

- `ping`: Simple ping for connection testing
- `search`: Perform hybrid search across the GraphRAG system
- `concept`: Get information about a concept
- `documents`: Get documents for a concept
- `books-by-concept`: Find books mentioning a concept
- `related-concepts`: Find concepts related to a concept
- `passages-about-concept`: Find passages about a concept
- `add-document`: Add a single document to the system
- `add-folder`: Add a folder of documents to the system
- `job-status`: Get status of a job
- `list-jobs`: List all jobs
- `cancel-job`: Cancel a job

For detailed information about the MCP server, see the [MCP Server Setup Guide](docs/mcp_server_setup.md).
```

## Next Steps

After implementing the client configuration and testing, the next steps will be:

1. Update the Docker configuration to start the MCP server
2. Update the service management scripts to include the MCP server
3. Test integration with AI agents