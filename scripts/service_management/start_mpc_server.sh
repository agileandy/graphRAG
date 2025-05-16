#!/bin/bash

# Script to start the GraphRAG MCP server

# Change to the project root directory
cd "$(dirname "$0")/.."

# Start the MCP server
echo "Starting GraphRAG MCP server..."
python -m src.mcp.server "$@"