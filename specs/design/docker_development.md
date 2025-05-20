# Docker Development Guide

This guide provides instructions for developing with the GraphRAG Docker container and ensuring changes are properly synchronized between the container and your local source code.

## Table of Contents

1. [Introduction](#introduction)
2. [Development Workflow](#development-workflow)
3. [Synchronizing Changes](#synchronizing-changes)
4. [Testing End-to-End](#testing-end-to-end)
5. [Troubleshooting](#troubleshooting)

## Introduction

The GraphRAG system can be run in a Docker container, which provides a consistent environment with all dependencies pre-installed. However, when making changes to the code, it's important to ensure that these changes are properly synchronized between the container and your local source code.

## Development Workflow

### Option 1: Development with Volume Mounts (Recommended)

The recommended approach is to use volume mounts to share your local source code with the container. This way, any changes you make to the local code are immediately reflected in the container.

1. **Use the volume mounts in docker-compose.yml**:
   ```yaml
   volumes:
     # Persist data
     - ./data:/app/data
     # Mount ebooks folder
     - /Users/andyspamer/ebooks:/app/ebooks
     # Mount source code (add this line)
     - ./src:/app/src
     - ./scripts:/app/scripts
     - ./tools:/app/tools
   ```

2. **Rebuild and restart the container**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Option 2: Development Inside the Container

If you prefer to develop inside the container, you'll need to periodically copy your changes back to your local source code.

1. **Connect to the container**:
   ```bash
   docker exec -it graphrag /bin/bash
   ```

2. **Make changes inside the container**

3. **Copy changes back to local source code** (from your local machine):
   ```bash
   docker cp graphrag:/app/src ./
   docker cp graphrag:/app/scripts ./
   docker cp graphrag:/app/tools ./
   ```

## Synchronizing Changes

When you make changes directly in the Docker container (e.g., installing new packages), you need to ensure these changes are reflected in your local source code.

### Python Packages

If you install new Python packages in the container:

1. **Update requirements.txt**:
   ```bash
   # Inside the container
   pip freeze > /tmp/requirements.txt
   
   # From your local machine
   docker cp graphrag:/tmp/requirements.txt ./
   ```

2. **Or manually add the package to requirements.txt**:
   ```
   # Example
   websockets>=11.0.0
   ```

3. **Update the Dockerfile** if you installed packages outside of requirements.txt:
   ```dockerfile
   # Install additional packages
   RUN pip install --no-cache-dir package-name
   ```

### Configuration Changes

If you modify configuration files in the container:

1. **Copy the modified files back to your local source code**:
   ```bash
   docker cp graphrag:/app/path/to/config.file ./path/to/config.file
   ```

2. **Update any relevant documentation** to reflect the changes.

## Testing End-to-End

To ensure your changes work correctly, you should test the system end-to-end:

1. **Using the provided test script**:
   ```bash
   uv run scripts/test_end_to_end.py
   ```

   This script:
   - Resets the databases (Neo4j and ChromaDB)
   - Verifies database connections
   - Adds a test document
   - Performs a search query
   - Displays the results

2. **Manual testing**:
   ```bash
   # Reset databases
   uv run scripts/clean_database.py -y
   
   # Add a document
   uv run scripts/add_document.py
   
   # Query the system
   uv run scripts/query_graphrag.py --query "Your search query"
   ```

## Troubleshooting

### Common Issues

1. **Package not found errors**:
   - Ensure the package is in requirements.txt
   - Install the package locally: `uv pip install package-name`
   - Rebuild the Docker container: `docker-compose build --no-cache`

2. **Database connection errors**:
   - Check if Neo4j is running: `docker exec graphrag /app/neo4j/bin/neo4j status`
   - Verify Neo4j password: Check NEO4J_PASSWORD in docker-compose.yml
   - Reset Neo4j password: `docker exec graphrag /app/neo4j/bin/neo4j-admin set-initial-password graphrag`

3. **Invalid collection errors in ChromaDB**:
   - Reset the ChromaDB directory: `rm -rf data/chromadb/* && mkdir -p data/chromadb`
   - Restart the container: `docker-compose restart`

4. **Port conflicts**:
   - Check for port usage: `lsof -i :7475` or `lsof -i :7688`
   - Modify port mappings in docker-compose.yml if needed

### Debugging

For more detailed debugging:

1. **Check container logs**:
   ```bash
   docker-compose logs -f
   ```

2. **Check Neo4j logs**:
   ```bash
   docker exec graphrag cat /app/neo4j/logs/neo4j.log
   ```

3. **Check API server logs**:
   ```bash
   docker exec graphrag cat /app/data/logs/gunicorn-error.log
   ```

4. **Interactive debugging inside the container**:
   ```bash
   docker exec -it graphrag /bin/bash
   cd /app
   python -m pdb scripts/your_script.py
   ```

Remember to always synchronize any changes you make in the container back to your local source code to ensure they're not lost when the container is rebuilt.
