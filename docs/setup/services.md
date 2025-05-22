# Service Setup

This document provides step-by-step instructions for setting up GraphRAG services.

## Prerequisites

- Python 3.10 or higher
- Neo4j installed and running
- Required Python packages (install via `pip install -r requirements.txt`)
- Environment variables configured (see [`config/env.sample`](config/env.sample))

## Service Overview

GraphRAG consists of the following services:

1. **API Server**: Main GraphRAG API (default port: 5001)
2. **MPC Server**: Message Passing Communication (default port: 8765)
3. **MCP Server**: Model Context Protocol (default port: 8767)
4. **Neo4j**: Graph database (default Bolt port: 7687)

## Starting Services

### Manual Start

1. **API Server**:
   ```bash
   gunicorn --bind 0.0.0.0:$(python -c "from src.config.ports import get_port; print(get_port('api'))") src.api.server:app
   ```

2. **MPC Server**:
   ```bash
   python -m src.mpc.server
   ```

3. **MCP Server**:
   ```bash
   python -m src.mcp.server
   ```

### Using Service Management Script

The [`scripts/service_management/graphrag-service.sh`](scripts/service_management/graphrag-service.sh) script provides basic service management:

```bash
# Start all services
./scripts/service_management/graphrag-service.sh start

# Stop all services
./scripts/service_management/graphrag-service.sh stop

# Check service status
./scripts/service_management/graphrag-service.sh status
```

## Docker Setup

To run services in Docker:

```bash
docker-compose up -d
```

This will start all services with the default port mappings defined in [`docker-compose.yml`](docker-compose.yml).

## Environment Variables

Key environment variables for service setup:

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USERNAME` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | `graphrag` |
| `CHROMA_PERSIST_DIRECTORY` | ChromaDB storage path | `./data/chromadb` |