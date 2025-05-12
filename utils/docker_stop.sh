#!/bin/bash

# Script to stop the GraphRAG Docker container

# Change to the project root directory
cd "$(dirname "$0")/.."

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit https://docs.docker.com/compose/install/ for installation instructions."
    exit 1
fi

# Stop the container
echo "Stopping the GraphRAG Docker container..."
docker-compose down

# Check if the container was stopped
if [ $? -eq 0 ]; then
    echo "✅ GraphRAG Docker container has been stopped."
else
    echo "❌ Failed to stop the GraphRAG Docker container."
    echo "Check the logs for more information: docker-compose logs"
fi