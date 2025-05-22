#!/bin/bash

# Script to start all GraphRAG services

# Change to the project root directory
cd "$(dirname "$0")/.."

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux is not installed. Please install it to run all services."
    echo "On macOS: brew install tmux"
    echo "On Ubuntu: apt-get install tmux"
    exit 1
fi

# Create a new tmux session
tmux new-session -d -s graphrag

# Start Neo4j in the first window
tmux rename-window -t graphrag:0 'neo4j'
tmux send-keys -t graphrag:0 './scripts/start_neo4j.sh' C-m

# Create a window for the API server
tmux new-window -t graphrag:1 -n 'api'
tmux send-keys -t graphrag:1 'sleep 5 && ./scripts/start_api_server.sh' C-m

# Create a window for the MCP server
tmux new-window -t graphrag:2 -n 'mcp'
tmux send-keys -t graphrag:2 'sleep 5 && ./scripts/service_management/start_mcp_server.sh' C-m

# Attach to the tmux session
tmux attach-session -t graphrag

# Note: To detach from the tmux session, press Ctrl+B then D
# To kill the session, run: tmux kill-session -t graphrag