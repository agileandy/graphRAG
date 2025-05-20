# graphRAG Docker Configuration

## Docker Configuration
<!-- TODO: Add content for Docker Configuration -->

## Docker Development
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

## Docker Build
# Docker Best Practices for GraphRAG Development

## Core Principles

### 1. Immutable Infrastructure

- **Never modify running containers**
  - All changes should be made to Dockerfiles, docker-compose files, or source code
  - Rebuild containers to apply changes
  - Avoid `docker exec` for making persistent changes

### 2. Infrastructure as Code

- **All container configurations should be version-controlled**
  - Dockerfile
  - docker-compose.yml
  - Environment files (with sensitive data excluded)
  - Initialization scripts

### 3. Reproducible Builds

- **Anyone should be able to build the same container**
  - Pin dependency versions
  - Use specific base image tags (not `latest`)
  - Document all build arguments and environment variables

## Development Workflow

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/username/graphRAG.git
cd graphRAG

# Create feature branch
git checkout -b feature/new-feature

# Build and start development environment
docker-compose -f docker-compose.dev.yml up -d --build

# Make code changes
# ...

# Test changes
docker-compose -f docker-compose.dev.yml exec graphrag python -m pytest

# Commit changes
git add .
git commit -m "Implement new feature"

# Push changes
git push origin feature/new-feature
```

### Making Changes to Container Configuration

```bash
# Update Dockerfile or docker-compose.yml
# ...

# Rebuild container
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d --build

# Verify changes
docker-compose -f docker-compose.dev.yml logs -f
```

### Adding Dependencies

```bash
# Add to requirements.txt
echo "new-package==1.2.3" >> requirements.txt

# Update Dockerfile if necessary
# ...

# Rebuild container
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d --build
```

## Docker Compose Configuration

### Development Environment

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  graphrag:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        - ENVIRONMENT=development
    volumes:
      - ./src:/app/src
      - ./scripts:/app/scripts
      - ./data:/app/data
      - /Users/username/ebooks:/app/ebooks
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=graphrag
    ports:
      - "7475:7474"  # Neo4j Browser
      - "7688:7687"  # Neo4j Bolt
      - "5001:5000"  # API Server
      - "8766:8765"  # MCP Server
    depends_on:
      - neo4j

  neo4j:
    image: neo4j:5.18.1
    environment:
      - NEO4J_AUTH=neo4j/graphrag
      - NEO4J_dbms_memory_heap_initial__size=512m
      - NEO4J_dbms_memory_heap_max__size=2G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    ports:
      - "7474:7474"  # Browser
      - "7687:7687"  # Bolt

volumes:
  neo4j_data:
  neo4j_logs:
```

### Production Environment

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  graphrag:
    image: ${REGISTRY}/graphrag:${TAG}
    restart: always
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=info
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
    ports:
      - "7475:7474"  # Neo4j Browser
      - "7688:7687"  # Neo4j Bolt
      - "5001:5000"  # API Server
      - "8766:8765"  # MCP Server
    depends_on:
      - neo4j
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  neo4j:
    image: neo4j:5.18.1
    restart: always
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
      - NEO4J_dbms_memory_heap_initial__size=1G
      - NEO4J_dbms_memory_heap_max__size=4G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    ports:
      - "7474:7474"  # Browser
      - "7687:7687"  # Bolt
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 6G

volumes:
  neo4j_data:
  neo4j_logs:
```

## Dockerfile Best Practices

### Multi-stage Builds

```dockerfile
# Build stage
FROM python:3.10-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Runtime stage
FROM python:3.10-slim

WORKDIR /app

# Copy wheels from builder stage
COPY --from=builder /wheels /wheels
COPY --from=builder /build/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Copy application code
COPY src/ /app/src/
COPY scripts/ /app/scripts/
COPY data/ /app/data/

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "/app/src/main.py"]
```

### Layer Optimization

- Order instructions from least to most frequently changed
- Group related commands to reduce layers
- Use `.dockerignore` to exclude unnecessary files
- Clean up in the same RUN instruction that creates temporary files

## Volume Management

### Data Persistence

- Use named volumes for persistent data
- Mount source code as volumes during development
- Use bind mounts for configuration files
- Consider using Docker volumes for backups

### Example Volume Commands

```bash
# Create a backup of Neo4j data
docker run --rm -v graphrag_neo4j_data:/data -v $(pwd)/backup:/backup \
  alpine tar -czf /backup/neo4j-data-$(date +%Y%m%d).tar.gz /data

# Restore from backup
docker run --rm -v graphrag_neo4j_data:/data -v $(pwd)/backup:/backup \
  alpine sh -c "rm -rf /data/* && tar -xzf /backup/neo4j-data-20230101.tar.gz -C /"
```

## Security Best Practices

### Least Privilege

- Run containers as non-root users
- Use read-only file systems where possible
- Limit capabilities and resources

### Secrets Management

- Never hardcode secrets in Dockerfiles or images
- Use environment variables or Docker secrets
- Consider using a secrets management tool (HashiCorp Vault, AWS Secrets Manager)

### Example Secure Dockerfile

```dockerfile
FROM python:3.10-slim

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ /app/src/
COPY scripts/ /app/scripts/

# Set permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

CMD ["python", "/app/src/main.py"]
```

## Networking

### Container Communication

- Use Docker networks for container communication
- Expose only necessary ports
- Use internal DNS names for service discovery

### Example Network Commands

```bash
# Create a custom network
docker network create graphrag-network

# Run containers on the network
docker run --network graphrag-network --name neo4j neo4j:5.18.1
docker run --network graphrag-network --name graphrag graphrag:latest
```

## Monitoring and Logging

### Container Health

- Implement health checks in docker-compose.yml
- Monitor container resource usage
- Set up alerts for container failures

### Centralized Logging

- Configure logging drivers
- Use structured logging (JSON)
- Consider using a logging stack (ELK, Grafana Loki)

### Example Health Check

```yaml
services:
  graphrag:
    # ...
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${GRAPHRAG_PORT_API}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## CI/CD Integration

### Automated Builds

- Set up CI/CD pipeline for automated builds
- Run tests in containers
- Scan images for vulnerabilities

### Example GitHub Actions Workflow

```yaml
# .github/workflows/docker-build.yml
name: Docker Build

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2

      - name: Build and test
        run: |
          docker-compose -f docker-compose.test.yml up --build --exit-code-from tests

      - name: Build and push
        if: github.event_name != 'pull_request'
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: username/graphrag:latest
```

## GraphRAG-Specific Recommendations

### Data Processing Workflow

```bash
# Correct way to process ebooks
# 1. Mount the ebooks directory in docker-compose.yml
# 2. Run the processing script through docker-compose exec

docker-compose exec graphrag python /app/scripts/process_ebooks.py --dir /app/ebooks/Industry5
```

### Handling Large Documents

- Configure ChromaDB with appropriate settings for large documents
- Implement chunking strategies in the application code
- Monitor memory usage during processing

### Neo4j Management

- Use Neo4j's backup and restore features
- Implement proper indexing for performance
- Monitor query performance

## Common Anti-patterns to Avoid

### 1. Modifying Running Containers

❌ **Bad Practice**:
```bash
docker exec -it graphrag pip install PyPDF2
docker exec -it graphrag python /app/scripts/process_ebooks.py --dir /app/ebooks/Industry5
```

✅ **Good Practice**:
```bash
# Add to requirements.txt
echo "PyPDF2==3.0.1" >> requirements.txt

# Rebuild container
docker-compose down
docker-compose build
docker-compose up -d

# Run script
docker-compose exec graphrag python /app/scripts/process_ebooks.py --dir /app/ebooks/Industry5
```

### 2. Using Latest Tag

❌ **Bad Practice**:
```dockerfile
FROM python:latest
```

✅ **Good Practice**:
```dockerfile
FROM python:3.10.12-slim
```

### 3. Hardcoding Secrets

❌ **Bad Practice**:
```dockerfile
ENV NEO4J_PASSWORD=my_secret_password
```

✅ **Good Practice**:
```yaml
# docker-compose.yml
services:
  graphrag:
    environment:
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
```

### 4. Not Cleaning Up

❌ **Bad Practice**:
```dockerfile
RUN apt-get update
RUN apt-get install -y some-package
```

✅ **Good Practice**:
```dockerfile
RUN apt-get update && \
    apt-get install -y some-package && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

## Conclusion

Following these Docker best practices will ensure that your GraphRAG development process is:

- **Reproducible**: Anyone can build and run the same environment
- **Maintainable**: Changes are tracked and documented
- **Secure**: Follows security best practices
- **Efficient**: Optimized for performance and resource usage

Remember: Always treat containers as immutable infrastructure and make changes through code, not by modifying running containers.
--------------

# Managing Docker Containers in the Development Lifecycle

## 1. Development Environment

### Local Development Setup

- **Docker Compose for Development**:
  - Use `docker-compose.yml` with development-specific configurations
  - Mount source code as volumes for live code editing
  - Enable debug ports and development tools

```yaml
# Example docker-compose.dev.yml
services:
  graphrag:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./src:/app/src  # Mount source code for live editing
      - ./scripts:/app/scripts
      - ./data:/app/data
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
    ports:
      - "7475:7474"  # Neo4j Browser
      - "7688:7687"  # Neo4j Bolt
      - "5001:5000"  # API Server
      - "8766:8765"  # MCP Server
```

- **Development Workflow**:
  ```bash
  # Start development environment
  docker-compose -f docker-compose.dev.yml up -d

  # View logs
  docker-compose -f docker-compose.dev.yml logs -f

  # Rebuild after Dockerfile changes
  docker-compose -f docker-compose.dev.yml up -d --build

  # Stop containers without removing them
  docker-compose -f docker-compose.dev.yml stop

  # Stop and remove containers
  docker-compose -f docker-compose.dev.yml down
  ```

### Development Best Practices

- **Use Multi-stage Builds**: Separate build dependencies from runtime dependencies
- **Layer Caching**: Order Dockerfile commands to maximize cache usage
- **Development Tools**: Include debugging tools in development images
- **Hot Reloading**: Configure applications for automatic reloading when code changes

## 2. Testing Environment

### Automated Testing

- **Test-specific Compose File**:
  ```yaml
  # docker-compose.test.yml
  services:
    graphrag:
      build:
        context: .
        dockerfile: Dockerfile.test
      environment:
        - TESTING=true
        - NEO4J_URI=bolt://neo4j-test:7687

    neo4j-test:
      image: neo4j:5.18.1
      environment:
        - NEO4J_AUTH=neo4j/test_password
  ```

- **CI/CD Integration**:
  ```bash
  # Run in CI pipeline
  docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
  ```

### Testing Best Practices

- **Ephemeral Containers**: Create and destroy containers for each test run
- **Isolated Networks**: Use Docker networks to isolate test environments
- **Volume Mounts**: Mount test fixtures and results as volumes
- **Health Checks**: Implement container health checks to ensure services are ready

## 3. Staging Environment

### Pre-production Validation

- **Staging Configuration**:
  ```yaml
  # docker-compose.staging.yml
  services:
    graphrag:
      image: ${REGISTRY}/graphrag:${TAG}
      environment:
        - ENVIRONMENT=staging
        - LOG_LEVEL=info
      restart: unless-stopped
  ```

- **Deployment to Staging**:
  ```bash
  # Deploy to staging
  TAG=$(git rev-parse --short HEAD)
  REGISTRY=your-registry.com

  # Build and push
  docker build -t ${REGISTRY}/graphrag:${TAG} .
  docker push ${REGISTRY}/graphrag:${TAG}

  # Deploy
  docker-compose -f docker-compose.staging.yml up -d
  ```

### Staging Best Practices

- **Mirror Production**: Make staging as similar to production as possible
- **Realistic Data**: Use anonymized production data or realistic synthetic data
- **Performance Testing**: Run load tests in staging environment
- **Monitoring**: Implement the same monitoring as production

## 4. Production Environment

### Production Deployment

- **Production Configuration**:
  ```yaml
  # docker-compose.prod.yml
  services:
    graphrag:
      image: ${REGISTRY}/graphrag:${TAG}
      environment:
        - ENVIRONMENT=production
        - LOG_LEVEL=warn
      restart: always
      deploy:
        replicas: 2
        update_config:
          parallelism: 1
          delay: 10s
        restart_policy:
          condition: on-failure
  ```

- **Deployment Strategies**:
  - Blue-Green Deployment: Run two identical environments, switch traffic
  - Rolling Updates: Update containers one at a time
  - Canary Releases: Route a percentage of traffic to new version

### Production Best Practices

- **Immutable Infrastructure**: Never modify running containers; replace them
- **Resource Limits**: Set memory and CPU limits for containers
- **Secrets Management**: Use Docker secrets or external vault for sensitive data
- **Logging and Monitoring**: Implement comprehensive logging and monitoring
- **Backup Strategy**: Regular backups of persistent data

## 5. Container Lifecycle Management

### Image Versioning

- **Tagging Strategy**:
  - Use semantic versioning (e.g., `v1.2.3`)
  - Include git commit hash (e.g., `v1.2.3-a1b2c3d`)
  - Tag latest stable version as `latest`
  - Tag development versions as `dev`

- **Image Registry**:
  - Use a private registry for proprietary code
  - Implement access controls and scanning
  - Set up retention policies for old images

### Container Orchestration

- **For Simple Setups**:
  - Docker Compose for single-host deployments
  - Docker Swarm for basic multi-host orchestration

- **For Complex Setups**:
  - Kubernetes for advanced orchestration
  - Helm charts for package management
  - Operators for complex applications

### Maintenance and Updates

- **Regular Updates**:
  - Update base images for security patches
  - Rebuild images periodically
  - Test updates in lower environments first

- **Monitoring and Alerting**:
  - Monitor container health and resource usage
  - Set up alerts for abnormal behavior
  - Implement auto-scaling based on metrics

## 6. Specific Recommendations for GraphRAG

Based on your GraphRAG project, here are specific recommendations:

### Development Workflow

1. **Source Control Integration**:
   ```bash
   # Create a feature branch
   git checkout -b feature/new-feature

   # Make changes to code

   # Build and test locally
   docker-compose -f docker-compose.dev.yml up -d --build

   # Run tests
   docker exec graphrag python -m pytest

   # Commit changes
   git add .
   git commit -m "Add new feature"

   # Push to remote
   git push origin feature/new-feature
   ```

2. **Managing Neo4j Data**:
   - Use named volumes for Neo4j data persistence
   - Implement backup scripts for Neo4j data
   - Create data initialization scripts for fresh environments

3. **ChromaDB Management**:
   - Implement proper error handling for ChromaDB operations
   - Set up regular backups of vector database
   - Monitor ChromaDB performance and resource usage

### Deployment Strategy

1. **Version Tagging**:
   ```bash
   # Tag a release
   git tag -a v2.1.0 -m "Release v2.1.0"
   git push origin v2.1.0

   # Build and tag Docker image
   docker build -t graphrag:v2.1.0 .

   # Push to registry (if using)
   docker push your-registry.com/graphrag:v2.1.0
   ```

2. **Environment-specific Configurations**:
   - Create `.env.dev`, `.env.test`, `.env.prod` files
   - Use Docker Compose environment file option:
     ```bash
     docker-compose --env-file .env.dev up -d
     ```

3. **Continuous Integration**:
   - Set up GitHub Actions or Jenkins pipeline
   - Automate testing and image building
   - Implement vulnerability scanning

## 7. Documentation and Standards

1. **Document Docker Setup**:
   - Create a `DOCKER.md` file explaining the setup
   - Document environment variables and configuration options
   - Include troubleshooting steps for common issues

2. **Standardize Commands**:
   - Create Makefiles or shell scripts for common operations:
     ```bash
     # Example Makefile
     .PHONY: dev test prod

     dev:
         docker-compose -f docker-compose.dev.yml up -d

     test:
         docker-compose -f docker-compose.test.yml up --build

     prod:
         docker-compose -f docker-compose.prod.yml up -d
     ```

3. **Create Onboarding Guide**:
   - Document steps for new developers to set up environment
   - Include common workflows and commands
   - Provide examples of typical development tasks

## Port Configuration
# Port Configuration Implementation

This document summarizes the implementation of the centralized port configuration system for the GraphRAG project.

## Overview

The centralized port configuration system provides a single source of truth for all port configurations used by GraphRAG services. It ensures consistent port usage across the codebase and makes it easy to override port values through environment variables.

## Implementation Details

### 1. Centralized Port Configuration

The centralized port configuration is defined in `src/config/ports.py`. This file:

- Defines default port values for all services
- Provides utility functions for working with ports
- Loads port values from environment variables

### 2. Environment Variables

Port values can be overridden through environment variables with the prefix `GRAPHRAG_PORT_`. For example:

```
GRAPHRAG_PORT_API=5002
GRAPHRAG_PORT_MPC=8766
```

These environment variables are loaded from the `.env` file in the project root.

### 3. Port Configuration Templates

The following templates have been created to help users configure port values:

- `config/env.sample`: Template for the `.env` file
- `config/env.docker`: Template for Docker environment variables
- `bugMCP/mcp_settings.template.json`: Template for the Bug MCP settings

### 4. Updated Files

The following files have been updated to use the centralized port configuration:

#### Python Files
- `src/config/ports.py`: Centralized port configuration
- `src/database/neo4j_db.py`: Neo4j database connection
- `src/agents/openai_functions.py`: OpenAI function calling integration
- `src/agents/langchain_tools.py`: LangChain tools integration
- `src/agent-tools/utils.py`: Agent tools utilities
- `bin/graphrag-monitor.py`: Service monitoring script
- `examples/mpc_client_example.py`: MPC client example
- `examples/mcp_client_example.py`: MCP client example
- `utils/generate-mcp-settings.py`: MCP settings generation
- `tests/test_neo4j.py`: Neo4j tests
- `tests/test_add_document_with_concepts.py`: Document tests
- `tests/test_mcp_server.py`: MCP server tests
- `tests/test_api_add_document.py`: API tests
- `tests/regression/test_utils.py`: Regression test utilities
- `scripts/document_processing/process_ebooks.py`: Ebook processing script
- `bugMCP/bugMCP.py`: Bug MCP server
- `bugMCP/bugAPI_client.py`: Bug API client
- `bugMCP/generate_settings.py`: Bug MCP settings generation

#### Shell Scripts
- `docker-entrypoint.sh`: Docker entrypoint script
- `utils/docker_build_run.sh`: Docker build and run script
- `utils/docker_build_debug.sh`: Docker build and debug script
- `scripts/service_management/graphrag-service.sh`: GraphRAG service script
- `scripts/service_management/bugmcp-service.sh`: Bug MCP service script
- `scripts/service_management/bugapi-service.sh`: Bug API service script
- `scripts/check_ports.sh`: Port availability checking script

#### Configuration Files
- `docker-compose.yml`: Docker Compose configuration
- `bugMCP/mcp_settings.template.json`: Bug MCP settings template

#### Documentation Files
- `docs/port_configuration.md`: Port configuration documentation
- `docs/updating_port_references.md`: Guide for updating port references
- `docs/port_configuration_summary.md`: Summary of port configuration changes
- Various other documentation files

### 5. Utility Scripts

The following utility scripts have been created to help with port configuration:

- `scripts/update_port_references.py`: Finds hardcoded port references in the codebase
- `scripts/update_docs_port_references.py`: Updates port references in documentation files
- `scripts/check_ports.sh`: Checks if required ports are available
- `bugMCP/generate_settings.py`: Generates Bug MCP settings from template

## Usage

### In Python Code

```python
from src.config import get_port

# Get the port for a specific service
api_port = get_port('api')
mpc_port = get_port('mpc')
neo4j_port = get_port('neo4j_bolt')

# Use the port in your code
app.run(port=api_port)
```

### In Shell Scripts

```bash
# Source the .env file
source .env

# Use the environment variables
echo "API Port: $GRAPHRAG_PORT_API"
echo "MPC Port: $GRAPHRAG_PORT_MPC"
```

### In Configuration Files

```json
{
  "server_details": {
    "host": "localhost",
    "port": "${GRAPHRAG_PORT_BUG_MCP}",
    "base_path": "/mcp"
  }
}
```

## Benefits

1. **Single source of truth**: All port configurations are defined in one place
2. **Easy to override**: Port values can be overridden through environment variables
3. **Consistent usage**: All code uses the same port values
4. **Better documentation**: Port configurations are well-documented
5. **Easier to maintain**: Changes to port values only need to be made in one place
6. **Reduced conflicts**: Port conflicts are easier to identify and resolve

## Next Steps

1. **Update remaining documentation**: Some documentation files still contain hardcoded port references
2. **Add port configuration tests**: Add tests to verify that port configuration works correctly
3. **Improve error handling**: Add better error handling for port conflicts
4. **Add port configuration UI**: Add a UI for configuring port values

# Port Configuration Summary

This document summarizes the changes made to implement a centralized port configuration system for the GraphRAG project.

## Changes Made

1. **Created a centralized port configuration system**:
   - Enhanced `src/config/ports.py` to provide a single source of truth for all port configurations
   - Added comprehensive documentation and utility functions
   - Ensured it reads from environment variables

2. **Updated environment configuration files**:
   - Updated `.env` with all port configurations
   - Updated `config/env.sample` to match `.env`
   - Updated `config/env.docker` for Docker-specific port configurations

3. **Updated Neo4j URI construction**:
   - Modified `src/database/neo4j_db.py` to use the centralized port configuration
   - Updated `scripts/database_management/clear_neo4j.py` to use the centralized port configuration
   - Updated `scripts/query/query_neo4j.py` to use the centralized port configuration

4. **Updated service management scripts**:
   - Modified `scripts/service_management/graphrag-service.sh` to use the centralized port configuration
   - Updated default configuration template in the script

5. **Created documentation and examples**:
   - Added `docs/port_configuration.md` with detailed documentation
   - Added `docs/updating_port_references.md` with guidance on updating hardcoded port references
   - Added `examples/port_configuration_example.py` demonstrating how to use the port configuration

6. **Created a utility script**:
   - Added `scripts/update_port_references.py` to find hardcoded port references in the codebase

## Remaining Work

The scan identified 102 hardcoded port references that still need to be updated:

- **docker_neo4j_bolt**: 21 references
- **mpc**: 20 references
- **api**: 19 references
- **mcp**: 14 references
- **neo4j_bolt**: 12 references
- **neo4j_http**: 8 references
- **bug_mcp**: 8 references

These references are spread across various files, including:

1. **Documentation files**: Many references are in markdown files and documentation
2. **Docker configuration**: References in Docker-related files
3. **Test files**: References in test scripts
4. **Agent tools**: References in agent tools and utilities
5. **Example scripts**: References in example scripts

## Next Steps

1. **Update Python files**:
   - Focus on updating Python files first, as they are the most critical
   - Prioritize files in the `src` directory

2. **Update shell scripts**:
   - Update shell scripts to use environment variables or Python utilities

3. **Update documentation**:
   - Update documentation files to reflect the new port configuration approach

4. **Update tests**:
   - Update test files to use the centralized port configuration

5. **Verify changes**:
   - Run tests to ensure everything still works correctly
   - Check for any missed references

## Benefits of the Centralized Port Configuration

1. **Single source of truth**: All port configurations are defined in one place
2. **Easy to override**: Port values can be overridden through environment variables
3. **Consistent usage**: All code uses the same port values
4. **Better documentation**: Port configurations are well-documented
5. **Easier to maintain**: Changes to port values only need to be made in one place

# Port Configuration in GraphRAG

This document explains the port configuration approach used in GraphRAG.

## Overview

GraphRAG uses a centralized port configuration system to manage all port assignments. This approach:

1. Provides a single source of truth for all port configurations
2. Allows for easy overriding of port values through environment variables
3. Includes utilities for checking port availability and resolving conflicts
4. Ensures consistent port usage across the codebase

## Port Configuration Files

The port configuration is managed through two main files:

1. **`.env`**: Contains environment variable overrides for port values
2. **`src/config/ports.py`**: Defines default port values and provides utility functions

## Using Port Configuration

### In Python Code

To use the port configuration in Python code:

```python
# Import the get_port function
from src.config import get_port

# Get the port for a specific service
api_port = get_port('api')
mpc_port = get_port('mpc')
neo4j_port = get_port('neo4j_bolt')

# Use the port in your code
app.run(port=api_port)
```

### In Shell Scripts

For shell scripts, you can either:

1. Source the `.env` file and use the environment variables directly:

```bash
# Source the .env file
source .env

# Use the environment variables
echo "API Port: $GRAPHRAG_PORT_API"
echo "MPC Port: $GRAPHRAG_PORT_MPC"
```

2. Or use the Python utility to get port values:

```bash
# Get port values using Python
API_PORT=$(python -c "from src.config import get_port; print(get_port('api'))")
MPC_PORT=$(python -c "from src.config import get_port; print(get_port('mpc'))")

echo "API Port: $API_PORT"
echo "MPC Port: $MPC_PORT"
```

## Available Ports

The following ports are defined in the configuration:

| Service | Default Port | Environment Variable | Description |
|---------|--------------|----------------------|-------------|
| API | 5001 | GRAPHRAG_PORT_API | Main GraphRAG API |
| MPC | 8765 | GRAPHRAG_PORT_MPC | Message Passing Communication server |
| MCP | 8767 | GRAPHRAG_PORT_MCP | Model Context Protocol server |
| Bug MCP | 5005 | GRAPHRAG_PORT_BUG_MCP | Bug tracking MCP server |
| Neo4j Bolt | 7687 | GRAPHRAG_PORT_NEO4J_BOLT | Neo4j Bolt protocol |
| Neo4j HTTP | 7474 | GRAPHRAG_PORT_NEO4J_HTTP | Neo4j HTTP API |
| Neo4j HTTPS | 7473 | GRAPHRAG_PORT_NEO4J_HTTPS | Neo4j HTTPS API |
| Prometheus | 9090 | GRAPHRAG_PORT_PROMETHEUS | Prometheus metrics |
| Grafana | 3000 | GRAPHRAG_PORT_GRAFANA | Grafana dashboard |
| Docker Neo4j Bolt | 7688 | GRAPHRAG_PORT_DOCKER_NEO4J_BOLT | Docker mapping for Neo4j Bolt |

## Overriding Port Values

To override a port value, set the corresponding environment variable in the `.env` file:

```
# Override the API port
GRAPHRAG_PORT_API=5002

# Override the MPC port
GRAPHRAG_PORT_MPC=8766
```

## Utility Functions

The `src/config` module provides several utility functions for working with ports:

- `get_port(service_name)`: Get the port number for a service
- `is_port_in_use(port, host='localhost')`: Check if a port is in use
- `find_available_port(start_port, host='localhost')`: Find an available port
- `get_service_for_port(port)`: Get the service name for a port
- `check_port_conflicts()`: Check for port conflicts among all services
- `print_port_configuration()`: Print the current port configuration

## Example Usage

See `examples/port_configuration_example.py` for a complete example of using the port configuration.

## Best Practices

1. **Always use `get_port()`**: Never hardcode port numbers in your code
2. **Check port availability**: Use `is_port_in_use()` to check if a port is available
3. **Handle conflicts**: Use `find_available_port()` to find an available port if needed
4. **Document new ports**: Add new ports to both `ports.py` and this documentation
5. **Use consistent naming**: Follow the existing naming convention for new ports

# Port Mapping Issues in GraphRAG

This document lists all identified port mapping inconsistencies in the GraphRAG system. These issues should be addressed to ensure consistent port usage across the system.

## Issue 1: MPC port mismatch in scripts/check_ports.sh

**Description:** The `scripts/check_ports.sh` script checks for port 8766, but the Docker container maps MPC to port 8765 according to docker-compose.yml.

**File:** scripts/check_ports.sh
```bash
# Define the ports to check
PORTS=(7475 7688 5001 8766)
```

**Expected:** PORTS=(7475 7688 5001 8765)

**Impact:** This inconsistency could lead to incorrect port availability checks before starting the Docker container.

## Issue 2: MPC port mismatch in agent tools

**Description:** The agent tools in `src/agent-tools/utils.py` use port 8766 for MPC, but the MPC server runs on port 8765.

**File:** src/agent-tools/utils.py
```python
DEFAULT_CONFIG = {
    "MPC_HOST": "localhost",
    "MPC_PORT": "8766",  # Default port for Docker mapping
    "NEO4J_URI": "bolt://localhost:${GRAPHRAG_PORT_DOCKER_NEO4J_BOLT}",  # Default port for Docker mapping
    "NEO4J_USERNAME": "neo4j",
    "NEO4J_PASSWORD": "graphrag"
}
```

**Expected:** "MPC_PORT": "8765"

**Impact:** Agent tools will attempt to connect to the wrong port by default, leading to connection failures.

## Issue 3: MPC port mismatch in docker-entrypoint.sh output

**Description:** The `docker-entrypoint.sh` script mentions "MPC Server: ws://localhost:8766" in its output, but starts the MPC server on port 8765.

**File:** docker-entrypoint.sh
```bash
echo "Service Endpoints:"
echo "- Neo4j Browser: http://localhost:7475"
echo "- API Server: http://localhost:${GRAPHRAG_PORT_API}"
echo "- MPC Server: ws://localhost:8766"
echo "- MCP Server: ws://localhost:${GRAPHRAG_PORT_MCP}"
```

**Expected:** echo "- MPC Server: ws://localhost:${GRAPHRAG_PORT_MPC}"

**Impact:** Misleading documentation that could cause confusion for users trying to connect to the MPC server.

## Issue 4: MPC port not used in Docker entrypoint

**Description:** The `.env.docker` file sets `GRAPHRAG_MPC_PORT=8765`, but this value is not used in the Docker entrypoint script.

**File:** docker-entrypoint.sh
```bash
# Start the MPC server in the background
echo "Starting MPC server..."
cd /app && python -m src.mpc.server --host 0.0.0.0 --port ${GRAPHRAG_PORT_MPC} &
MPC_PID=$!
```

**Expected:**
```bash
# Start the MPC server in the background
echo "Starting MPC server..."
cd /app && python -m src.mpc.server --host 0.0.0.0 --port ${GRAPHRAG_MPC_PORT:-8765} &
MPC_PID=$!
```

**Impact:** Environment variable overrides for the MPC port will not be respected in the Docker container.

## Issue 5: MCP port mismatch in mcp-docker-and-service.md

**Description:** The `specs/todo/mcp-docker-and-service.md` file mentions `MCP_PORT=8766`, but the MCP server runs on port 8767.

**File:** specs/todo/mcp-docker-and-service.md
```bash
# Default values
NEO4J_URI="bolt://localhost:${GRAPHRAG_PORT_NEO4J_BOLT}"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="graphrag"
API_PORT=5001
MPC_PORT=8765
MCP_PORT=8766
```

**Expected:** MCP_PORT=8767

**Impact:** Misleading documentation that could cause confusion for users trying to configure the MCP server.

## Issue 6: MPC port mismatch in config.env

**Description:** The `$HOME/.graphrag/config.env` file sets `GRAPHRAG_MPC_PORT=8767`, which conflicts with the default MPC port of 8765.

**File:** $HOME/.graphrag/config.env
```bash
# GraphRAG Configuration
NEO4J_HOME=/opt/homebrew
NEO4J_URI=bolt://localhost:${GRAPHRAG_PORT_NEO4J_BOLT}
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=graphrag
CHROMA_PERSIST_DIRECTORY=/Users/andyspamer/.graphrag/data/chromadb
GRAPHRAG_API_PORT=5001
GRAPHRAG_MPC_PORT=8767
GRAPHRAG_LOG_LEVEL=INFO
```

**Expected:** GRAPHRAG_MPC_PORT=8765

**Impact:** This could cause the MPC server to run on the wrong port when started using the service script, leading to connection failures.

## Issue 7: MCP server port hardcoded in mcp_server.py

**Description:** The MCP server port is hardcoded in `src/mpc/mcp_server.py` instead of using the centralized port configuration.

**File:** src/mpc/mcp_server.py
```python
def main():
    """Main function to start the MCP server.
    """
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Start the GraphRAG MCP server")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8767, help="Server port")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    args = parser.parse_args()
```

**Expected:**
```python
def main():
    """Main function to start the MCP server.
    """
    import argparse
    from src.config.ports import get_port

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Start the GraphRAG MCP server")
    parser.add_argument("--host", type=str, default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=get_port("mcp"), help="Server port")
    parser.add_argument("--log-level", type=str, default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Logging level")
    args = parser.parse_args()
```

**Impact:** Changes to the centralized port configuration will not be reflected in the MCP server.

## Issue 8: Bug MCP server port hardcoded

**Description:** The Bug MCP server port is hardcoded in `bugMCP/bugMCP.py` instead of using the centralized port configuration.

**File:** bugMCP/bugMCP.py
```python
# TCP Server setup
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 5005))
server.listen(1)
print("Server listening on port 5005...")
```

**Expected:** Use the centralized port configuration to get the port.

**Impact:** Changes to the centralized port configuration will not be reflected in the Bug MCP server.

# Updating Port References

This document provides guidance on updating hardcoded port references to use the centralized port configuration.

## Finding Hardcoded Port References

Use the `scripts/update_port_references.py` script to find hardcoded port references in the codebase:

```bash
python scripts/update_port_references.py
```

This script will scan the codebase for hardcoded port numbers and suggest replacements using the centralized port configuration.

## Manual Updates

For each hardcoded port reference, you'll need to update the code to use the `get_port()` function. Here are some common patterns and their replacements:

### Python Files

#### Before:
```python
port = 8765
```

#### After:
```python
from src.config import get_port
port = get_port('mpc')
```

### Shell Scripts

#### Before:
```bash
PORT=8765
```

#### After:
```bash
# Option 1: Source the .env file
source .env
PORT=$GRAPHRAG_PORT_MPC

# Option 2: Use Python to get the port
PORT=$(python -c "from src.config import get_port; print(get_port('mpc'))")
```

### Configuration Files

#### Before:
```json
{
  "port": 8765
}
```

#### After:
```json
{
  "port": "${GRAPHRAG_PORT_MPC}"
}
```

## Testing Changes

After updating port references, test the affected components to ensure they still work correctly:

1. Run the component with the updated port configuration
2. Verify that it uses the correct port
3. Test overriding the port through environment variables

## Common Issues

### Import Errors

If you encounter import errors when adding `from src.config import get_port`, you may need to adjust the import path based on the file's location in the project structure.

### Environment Variable Access

In some contexts (e.g., Docker containers), environment variables may not be accessible. In these cases, you may need to pass the port values explicitly or use a different configuration approach.

### Port Conflicts

If you encounter port conflicts after updating to the centralized configuration, you can:

1. Override the conflicting ports in the `.env` file
2. Use the `find_available_port()` function to dynamically find an available port
3. Update the default port values in `src/config/ports.py`