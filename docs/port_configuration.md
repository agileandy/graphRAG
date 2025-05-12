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