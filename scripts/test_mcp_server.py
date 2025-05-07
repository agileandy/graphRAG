#!/usr/bin/env python3
"""
Test script for the GraphRAG MCP server.

This script tests the MCP server by:
1. Checking if the Neo4j driver is installed
2. Verifying database connections
3. Testing the MCP server protocol
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

async def test_mcp_protocol(uri: str = "ws://localhost:8766") -> None:
    """Test the MCP protocol."""
    print_section("Testing MCP Protocol")
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to MCP server")

            # Test initialize
            print("\nTesting initialize...")
            await websocket.send(json.dumps({
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "0.1.0"
                    }
                },
                "id": 0
            }))

            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Response: {json.dumps(response_data, indent=2)}")

            if "result" in response_data:
                print("✅ Initialize successful")
            else:
                print("❌ Initialize failed")

            # Test getTools
            print("\nTesting getTools...")
            await websocket.send(json.dumps({
                "jsonrpc": "2.0",
                "method": "getTools",
                "params": {},
                "id": 1
            }))

            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Response: {json.dumps(response_data, indent=2)}")

            if "result" in response_data and "tools" in response_data["result"]:
                print(f"✅ GetTools successful, found {len(response_data['result']['tools'])} tools")
            else:
                print("❌ GetTools failed")

            # Test invokeTool
            print("\nTesting invokeTool (search)...")
            await websocket.send(json.dumps({
                "jsonrpc": "2.0",
                "method": "invokeTool",
                "params": {
                    "name": "search",
                    "parameters": {
                        "query": "GraphRAG"
                    }
                },
                "id": 2
            }))

            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"Response: {json.dumps(response_data, indent=2)}")

            if "result" in response_data:
                print("✅ InvokeTool successful")
                if "error" in response_data["result"].get("result", {}):
                    print("⚠️ Tool returned an error (this is expected if database connections are not available)")
                    print(f"Error message: {response_data['result']['result'].get('message', 'Unknown error')}")
            else:
                print("❌ InvokeTool failed")

    except ConnectionRefusedError:
        print("❌ Connection refused. Make sure the MCP server is running.")
    except Exception as e:
        print(f"❌ Error testing MCP protocol: {e}")

def check_database_connections() -> None:
    """Check database connections."""
    print_section("Checking Database Connections")

    # Check Neo4j
    print("Checking Neo4j connection...")
    try:
        from src.database.neo4j_db import Neo4jDatabase
        # Try with port 7688 (Docker mapping) and explicit credentials
        neo4j_db = Neo4jDatabase(
            uri="bolt://localhost:7688",
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
                uri="bolt://localhost:7687",
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