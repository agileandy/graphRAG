# Port Configuration

GraphRAG uses a centralized port management system defined in [`src/config/ports.py`](src/config/ports.py). This document explains how ports are configured and managed.

## Default Port Assignments

| Service | Default Port | Description |
|---------|--------------|-------------|
| API | 5001 | Main GraphRAG API |
| MCP | 8767 | Model Context Protocol server |
| MPC | 8765 | Message Passing Communication server |
| Bug MCP | 5005 | Bug tracking MCP server |
| Neo4j Bolt | 7687 | Neo4j Bolt protocol |
| Neo4j HTTP | 7474 | Neo4j HTTP API |
| Neo4j HTTPS | 7473 | Neo4j HTTPS API |
| Prometheus | 9090 | Prometheus metrics |
| Grafana | 3000 | Grafana dashboard |
| Docker Neo4j Bolt | 7688 | Docker mapping for Neo4j Bolt |

## Overriding Ports

Ports can be overridden using environment variables with the prefix `GRAPHRAG_PORT_`. For example:

```bash
GRAPHRAG_PORT_API=5002  # Changes API port to 5002
```

## Docker Port Mappings

When running in Docker, ports are mapped as follows:

| Container Port | Host Port (Default) | Service |
|----------------|---------------------|---------|
| 5000 | 5001 | API Server |
| 7687 | 7688 | Neo4j Bolt |
| 7474 | 7474 | Neo4j Browser |
| 8767 | 8767 | MCP Server |

## Troubleshooting Port Conflicts

Use the following commands to check for port conflicts:

```bash
# Check if a specific port is in use
python -c "from src.config.ports import is_port_in_use; print(is_port_in_use(5001))"

# Find an available port starting from 5001
python -c "from src.config.ports import find_available_port; print(find_available_port(5001))"

# Print current port configuration
python -c "from src.config.ports import print_port_configuration; print_port_configuration()"