#!/bin/bash

# Script to build and run the GraphRAG Docker container

# Change to the project root directory
cd "$(dirname "$0")/.."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit https://docs.docker.com/get-docker/ for installation instructions."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit https://docs.docker.com/compose/install/ for installation instructions."
    exit 1
fi

# Build and start the container
echo "Building and starting the GraphRAG Docker container..."
docker-compose build --no-cache
docker-compose up -d

# Check if the container is running
if [ $? -eq 0 ]; then
    echo "✅ GraphRAG Docker container is now running!"
    echo "- Neo4j Browser: http://localhost:7474 (username: neo4j, password: graphrag)"
    echo "- API Server: http://localhost:5000"
    echo "- MPC Server: ws://localhost:8765"
    echo ""
    echo "To stop the container, run: docker-compose down"
else
    echo "❌ Failed to start the GraphRAG Docker container."
    echo "Check the logs for more information: docker-compose logs"
fi