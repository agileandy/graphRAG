#!/usr/bin/env python3
"""
Test client for the GraphRAG MCP server.
"""

import json
import asyncio
import websockets

async def test_mcp_server():
    """Test the MCP server."""
    uri = "ws://localhost:8767"
    
    async with websockets.connect(uri) as websocket:
        # Initialize
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
        print(f"Initialize response: {response}")
        
        # Get tools
        await websocket.send(json.dumps({
            "jsonrpc": "2.0",
            "method": "getTools",
            "params": {},
            "id": 1
        }))
        
        response = await websocket.recv()
        print(f"GetTools response: {response}")
        
        # Invoke tool
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
        print(f"InvokeTool response: {response}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
