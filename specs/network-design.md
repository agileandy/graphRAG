# GraphRAG Network Design

This document provides a comprehensive overview of the network architecture and port mappings used in the GraphRAG system.

## Port Configuration Overview

The GraphRAG system uses a centralized port configuration system defined in `src/config/ports.py`. This module provides:

1. Default port assignments for all services
2. Functions to get port numbers for services
3. Functions to check port availability and conflicts
4. Environment variable overrides with the prefix `GRAPHRAG_PORT_`

## Default Port Assignments

| Service | Default Port | Description | Docker Mapping |
|---------|-------------|-------------|----------------|
| api | 5001 | Main GraphRAG API | 5001:5000 |
| mpc | 8765 | Message Passing Communication server | 8765:8765 |
| mcp | 8767 | Model Context Protocol server | 8767:8767 |
| bug_mcp | 5005 | Bug tracking MCP server | N/A (not in Docker) |
| neo4j_bolt | 7687 | Neo4j Bolt protocol | 7688:7687 |
| neo4j_http | 7474 | Neo4j HTTP API | 7475:7474 |
| neo4j_https | 7473 | Neo4j HTTPS API | N/A |
| prometheus | 9090 | Prometheus metrics | N/A |
| grafana | 3000 | Grafana dashboard | N/A |

## Docker Port Mappings

When running in Docker, the following port mappings are used:

```yaml
ports:
  # Neo4j Browser (changed from 7474 to 7475)
  - "7475:7474"
  # Neo4j Bolt (changed from 7687 to 7688)
  - "7688:7687"
  # API Server (changed from 5000 to 5001)
  - "5001:5000"
  # MPC Server
  - "8765:8765"
  # MCP Server
  - "8767:8767"
```

## Service-Specific Port Configurations

### 1. Neo4j Database

- **Bolt Protocol**: Used for database connections
  - Default: 7687
  - Docker Mapping: 7688:7687
  - Configuration: `NEO4J_URI=bolt://localhost:${GRAPHRAG_PORT_NEO4J_BOLT}` (local) or `NEO4J_URI=bolt://0.0.0.0:7687` (Docker)

- **HTTP API**: Used for Neo4j Browser
  - Default: 7474
  - Docker Mapping: 7475:7474
  - Access: http://localhost:7475 (when using Docker)

### 2. API Server

- **HTTP API**: Main GraphRAG API
  - Default: 5001
  - Docker Mapping: 5001:5000
  - Configuration: `GRAPHRAG_API_PORT=5001`
  - Access: http://localhost:${GRAPHRAG_PORT_API}/health

### 3. Message Passing Communication (MPC) Server

- **WebSocket Server**: Used for agent communication
  - Default: 8765
  - Docker Mapping: 8765:8765
  - Configuration: `GRAPHRAG_MPC_PORT=8765`
  - Access: ws://localhost:${GRAPHRAG_PORT_MPC}

### 4. Model Context Protocol (MCP) Server

- **WebSocket Server**: Used for agent communication
  - Default: 8767
  - Docker Mapping: 8767:8767
  - Configuration: None (hardcoded in server.py)
  - Access: ws://localhost:${GRAPHRAG_PORT_MCP}

### 5. Bug Tracking MCP Server

- **TCP Server**: Used for bug tracking
  - Default: 5005
  - Docker Mapping: N/A (not in Docker)
  - Configuration: None (hardcoded in bugMCP.py)
  - Access: localhost:${GRAPHRAG_PORT_BUG_MCP}

## Port Configuration in Code

### Centralized Configuration

The `src/config/ports.py` module provides centralized port configuration:

```python
# Default port assignments
DEFAULT_PORTS = {
    # API Services
    "api": 5001,                # Main GraphRAG API
    
    # MPC Services
    "mpc": 8765,                # Message Passing Communication server
    
    # MCP Services
    "mcp": 8767,                # Model Context Protocol server
    "bug_mcp": 5005,            # Bug tracking MCP server
    
    # Database Services
    "neo4j_bolt": 7687,         # Neo4j Bolt protocol
    "neo4j_http": 7474,         # Neo4j HTTP API
    "neo4j_https": 7473,        # Neo4j HTTPS API
    
    # Monitoring Services
    "prometheus": 9090,         # Prometheus metrics
    "grafana": 3000,            # Grafana dashboard
}
```

### Environment Variables

Port configurations can be overridden using environment variables with the prefix `GRAPHRAG_PORT_`:

```bash
# Example: Override the MCP server port
export GRAPHRAG_PORT_MCP=8768
```

## Port Usage in Different Components

### 1. Docker Entrypoint

The `docker-entrypoint.sh` script starts services on the following ports:

- Neo4j: 7474 (HTTP) and 7687 (Bolt)
- API Server: Port from environment variable `${GRAPHRAG_API_PORT:-5001}`
- MPC Server: 8765 (hardcoded)
- MCP Server: 8767 (hardcoded)

### 2. Test Setup

The `tools/test_setup.py` script uses the centralized port configuration and can dynamically adjust ports if conflicts are detected.

### 3. Agent Tools

The agent tools in `src/agent-tools/utils.py` use the following default configuration:

```python
DEFAULT_CONFIG = {
    "MPC_HOST": "localhost",
    "MPC_PORT": "8766",  # Default port for Docker mapping
    "NEO4J_URI": "bolt://localhost:${GRAPHRAG_PORT_DOCKER_NEO4J_BOLT}",  # Default port for Docker mapping
    "NEO4J_USERNAME": "neo4j",
    "NEO4J_PASSWORD": "graphrag"
}
```

### 4. Bug MCP Server

The Bug MCP server in `bugMCP/bugMCP.py` uses a hardcoded port:

```python
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 5005))
server.listen(1)
```

## Port Checking

The `scripts/check_ports.sh` script checks the following ports before starting the Docker container:

```bash
# Define the ports to check
PORTS=(7475 7688 5001 8766)
```

## Known Port Inconsistencies

1. The `scripts/check_ports.sh` script checks for port 8766, but the Docker container maps MPC to port 8765.
2. The agent tools in `src/agent-tools/utils.py` use port 8766 for MPC, but the MPC server runs on port 8765.
3. The `docker-entrypoint.sh` script mentions "MPC Server: ws://localhost:8766" in its output, but starts the MPC server on port 8765.
4. The `.env.docker` file sets `GRAPHRAG_MPC_PORT=8765`, but this value is not used in the Docker entrypoint script.
5. The `scripts/service_management/graphrag-service.sh` script uses `GRAPHRAG_MPC_PORT=8765` from config, but the MPC server is hardcoded to use port 8765 in `src/mpc/server.py`.
6. The `specs/todo/mcp-docker-and-service.md` file mentions `MCP_PORT=8766`, but the MCP server runs on port 8767.
7. The `tools/generate-mcp-settings.py` script generates settings with port 8767 for MCP, which is correct according to the centralized configuration.
8. The `$HOME/.graphrag/config.env` file sets `GRAPHRAG_MPC_PORT=8767`, which conflicts with the default MPC port of 8765.
