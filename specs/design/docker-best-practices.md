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
      - "8766:8765"  # MPC Server
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
      - "8766:8765"  # MPC Server
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
      test: ["CMD", "curl", "-f", "http://localhost:5001/health"]
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
