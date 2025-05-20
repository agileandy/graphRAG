# GraphRAG

## Project Overview

GraphRAG is a comprehensive system designed to manage and analyze graph-based data. It leverages Neo4j for graph database management and provides a robust API for interacting with the graph data. The system includes utilities for checking port availability, resolving conflicts, and ensuring consistent port usage across the codebase.

### Key Features

- Centralized port configuration system
- Environment variable overrides for port values
- Utility functions for port management
- Consistent port usage across the codebase

### Technology Stack

- **Backend**: Python
- **Database**: Neo4j
- **API**: Flask
- **Port Management**: Custom Python module

### System Requirements

- Python 3.8+
- Neo4j 4.0+
- Flask 2.0+

## Installation

To run GraphRAG locally on macOS without Docker, follow these steps:

1. **Prerequisites**:
   - Ensure you have Python 3.8+ installed.
   - Ensure you have Neo4j 4.0+ installed and running.

2. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/graphrag.git
   cd graphrag
   ```

3. **Create a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Environment Variables**:
   Create a `.env` file in the project root and add the following variables:
   ```
   GRAPHRAG_PORT_API=5001
   GRAPHRAG_PORT_MPC=8765
   GRAPHRAG_PORT_NEO4J_BOLT=7687
   ```

6. **Start the Services**:
   ```bash
   ./scripts/start-graphrag-local.sh
   ```

## Usage

After starting the services, you can interact with the GraphRAG API using tools like `curl` or Postman. The API will be available at `http://localhost:5001`.

## Configuration

GraphRAG uses a centralized port configuration system to manage all port assignments. This approach provides a single source of truth for all port configurations and allows for easy overriding of port values through environment variables. The port configuration is managed through two main files:

1. **`.env`**: Contains environment variable overrides for port values.
2. **`src/config/ports.py`**: Defines default port values and provides utility functions.

### Available Ports

The following ports are defined in the configuration:

| Service | Default Port | Environment Variable | Description |
|---------|--------------|----------------------|-------------|
| API | 5001 | GRAPHRAG_PORT_API | Main GraphRAG API |
| MPC | 8765 | GRAPHRAG_PORT_MPC | Message Passing Communication server |
| Neo4j Bolt | 7687 | GRAPHRAG_PORT_NEO4J_BOLT | Neo4j Bolt protocol |

### Overriding Port Values

To override a port value, set the corresponding environment variable in the `.env` file:
```
# Override the API port
GRAPHRAG_PORT_API=5002

# Override the MPC port
GRAPHRAG_PORT_MPC=8766
```

### Utility Functions

The `src/config` module provides several utility functions for working with ports:

- `get_port(service_name)`: Get the port number for a service.
- `is_port_in_use(port, host='localhost')`: Check if a port is in use.
- `find_available_port(start_port, host='localhost')`: Find an available port.
- `get_service_for_port(port)`: Get the service name for a port.
- `check_port_conflicts()`: Check for port conflicts among all services.
- `print_port_configuration()`: Print the current port configuration.

## Contributing

[Placeholder for contributing guidelines]

## License

[Placeholder for license information]