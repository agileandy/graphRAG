#!/bin/bash

# Script to build and debug the GraphRAG Docker container

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

# Make sure data directory exists
mkdir -p ./data/chromadb

# Check if ports are available
echo "Checking if ports are available..."
./scripts/check_ports.sh
if [ $? -ne 0 ]; then
    echo "❌ Port conflict detected. Please resolve the conflicts before proceeding."
    exit 1
fi

# Stop any existing containers
echo "Stopping any existing GraphRAG containers..."
docker-compose down

# Remove any existing images
echo "Removing any existing GraphRAG images..."
docker rmi graphrag_graphrag || true

# Build the container with verbose output
echo "Building the GraphRAG Docker container..."
docker-compose build --no-cache --progress=plain

# Check if the build was successful
if [ $? -eq 0 ]; then
    echo "✅ GraphRAG Docker container built successfully!"

    # Start the container
    echo "Starting the GraphRAG Docker container..."
    docker-compose up -d

    # Check if the container is running
    if [ $? -eq 0 ]; then
        echo "✅ GraphRAG Docker container is now running!"
        echo "- Neo4j Browser: http://localhost:7475 (username: neo4j, password: graphrag)"
        echo "- API Server: http://localhost:5001"
        echo "- MPC Server: ws://localhost:8766"
        echo ""
        echo "To view the logs, run: docker-compose logs -f"
        echo "To stop the container, run: docker-compose down"
    else
        echo "❌ Failed to start the GraphRAG Docker container."
        echo "Check the logs for more information: docker-compose logs"
    fi
else
    echo "❌ Failed to build the GraphRAG Docker container."
    echo "Please check the error messages above."
fi