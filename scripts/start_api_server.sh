#!/bin/bash

# Script to start the GraphRAG API server

# Change to the project root directory
cd "$(dirname "$0")/.."

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "❌ gunicorn is not installed. Please install it with: pip install gunicorn"
    exit 1
fi

# Start the API server
echo "Starting GraphRAG API server..."
gunicorn --bind 0.0.0.0:5000 src.api.wsgi:app