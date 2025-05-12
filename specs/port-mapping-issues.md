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
