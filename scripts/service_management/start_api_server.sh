#!/bin/bash

# Script to start the GraphRAG API server

# Change to the project root directory
cd "$(dirname "$0")/.."

# Activate the virtual environment
source /Users/andyspamer/Dev-Space/PythonProjects/graphRAG/.venv-py312/bin/activate

# Install the project in editable mode
uv pip install -e .

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "❌ gunicorn is not installed. Please install it with: pip install gunicorn"
    exit 1
fi

# Get the API port from environment variable or use default
API_PORT=${GRAPHRAG_API_PORT:-5001}

# Start the API server
echo "Starting GraphRAG API server on port $API_PORT..."
gunicorn --bind 0.0.0.0:$API_PORT src.api.wsgi:app
