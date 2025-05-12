# MCP Docker Integration and Service Management

This document provides detailed implementation guidance for integrating the MCP server with Docker and creating service management scripts for the GraphRAG project.

## Overview

After implementing the MCP server, tools, and client configuration, we need to integrate the MCP server with Docker and create service management scripts to ensure it can be easily started, monitored, and stopped.

## Implementation Details

### 1. Docker Integration

#### 1.1 Update Dockerfile

**File**: `Dockerfile` (update existing file)

Add the following to the existing Dockerfile:

```dockerfile
# Install additional dependencies for MCP server
RUN uv pip install websockets

# Copy MCP server files
COPY src/mpc/mcp_server.py /app/src/mpc/
COPY tools/graphrag-mcp /app/tools/

# Make the MCP script executable
RUN chmod +x /app/tools/graphrag-mcp
```

#### 1.2 Update docker-compose.yml

**File**: `docker-compose.yml` (update existing file)

Add the following to the existing docker-compose.yml:

```yaml
services:
  graphrag:
    # ... existing configuration ...
    ports:
      # ... existing ports ...
      - "8766:8766"  # MCP server
    environment:
      # ... existing environment variables ...
      - MCP_HOST=0.0.0.0
      - MCP_PORT=8766
```

#### 1.3 Update docker-entrypoint.sh

**File**: `docker-entrypoint.sh` (update existing file)

Add the following to the existing docker-entrypoint.sh:

```bash
# Start the MCP server in the background
echo "Starting MCP server..."
cd /app && python -m src.mpc.mcp_server --host 0.0.0.0 --port 8766 &
MCP_PID=$!

# Give the MCP server a moment to start
sleep 3
echo "✅ MCP server started (PID: $MCP_PID)."

# Add MCP server to the list of processes to monitor
if [ -n "$MCP_PID" ]; then
    PIDS_TO_MONITOR="$PIDS_TO_MONITOR $MCP_PID"
fi
```

### 2. Service Management

#### 2.1 Create MCP Service Script

**File**: `tools/graphrag-service.sh`

```bash
#!/bin/bash
# GraphRAG Service Management Script

# Configuration
CONFIG_FILE="$HOME/.graphrag/config.env"
LOG_DIR="$HOME/.graphrag/logs"
PID_DIR="$HOME/.graphrag/pids"

# Default values
NEO4J_HOME="$HOME/.graphrag/neo4j"
NEO4J_URI="bolt://localhost:${GRAPHRAG_PORT_NEO4J_BOLT}"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="graphrag"
CHROMA_PERSIST_DIRECTORY="$HOME/.graphrag/data/chromadb"
API_PORT=5001
MPC_PORT=8765
MCP_PORT=8766
LOG_LEVEL="INFO"

# Load configuration
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    echo "Configuration file not found. Creating default configuration..."
    mkdir -p "$(dirname "$CONFIG_FILE")"
    cat > "$CONFIG_FILE" << EOF
# GraphRAG Configuration
NEO4J_HOME=$NEO4J_HOME
NEO4J_URI=$NEO4J_URI
NEO4J_USERNAME=$NEO4J_USERNAME
NEO4J_PASSWORD=$NEO4J_PASSWORD
CHROMA_PERSIST_DIRECTORY=$CHROMA_PERSIST_DIRECTORY
API_PORT=$API_PORT
MPC_PORT=$MPC_PORT
MCP_PORT=$MCP_PORT
LOG_LEVEL=$LOG_LEVEL
EOF
    echo "Default configuration created at $CONFIG_FILE"
fi

# Create directories if they don't exist
mkdir -p "$LOG_DIR"
mkdir -p "$PID_DIR"

# Set environment variables
export NEO4J_URI
export NEO4J_USERNAME
export NEO4J_PASSWORD
export CHROMA_PERSIST_DIRECTORY
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Function to start Neo4j
start_neo4j() {
    echo "Starting Neo4j..."
    if [ -x "$NEO4J_HOME/bin/neo4j" ]; then
        "$NEO4J_HOME/bin/neo4j" start
        echo "Neo4j started."
    else
        echo "Neo4j not found at $NEO4J_HOME. Please install Neo4j or update the configuration."
        return 1
    fi
}

# Function to stop Neo4j
stop_neo4j() {
    echo "Stopping Neo4j..."
    if [ -x "$NEO4J_HOME/bin/neo4j" ]; then
        "$NEO4J_HOME/bin/neo4j" stop
        echo "Neo4j stopped."
    else
        echo "Neo4j not found at $NEO4J_HOME. Please install Neo4j or update the configuration."
        return 1
    fi
}

# Function to start API server
start_api() {
    echo "Starting API server..."
    python -m src.api.server --port "$API_PORT" > "$LOG_DIR/api.log" 2>&1 &
    API_PID=$!
    echo $API_PID > "$PID_DIR/api.pid"
    echo "API server started with PID $API_PID."
}

# Function to stop API server
stop_api() {
    if [ -f "$PID_DIR/api.pid" ]; then
        API_PID=$(cat "$PID_DIR/api.pid")
        echo "Stopping API server (PID $API_PID)..."
        kill $API_PID 2>/dev/null || true
        rm "$PID_DIR/api.pid"
        echo "API server stopped."
    else
        echo "API server not running."
    fi
}

# Function to start MPC server
start_mpc() {
    echo "Starting MPC server..."
    python -m src.mpc.server --port "$MPC_PORT" > "$LOG_DIR/mpc.log" 2>&1 &
    MPC_PID=$!
    echo $MPC_PID > "$PID_DIR/mpc.pid"
    echo "MPC server started with PID $MPC_PID."
}

# Function to stop MPC server
stop_mpc() {
    if [ -f "$PID_DIR/mpc.pid" ]; then
        MPC_PID=$(cat "$PID_DIR/mpc.pid")
        echo "Stopping MPC server (PID $MPC_PID)..."
        kill $MPC_PID 2>/dev/null || true
        rm "$PID_DIR/mpc.pid"
        echo "MPC server stopped."
    else
        echo "MPC server not running."
    fi
}

# Function to start MCP server
start_mcp() {
    echo "Starting MCP server..."
    python -m src.mpc.mcp_server --host 0.0.0.0 --port "$MCP_PORT" --log-level "$LOG_LEVEL" > "$LOG_DIR/mcp.log" 2>&1 &
    MCP_PID=$!
    echo $MCP_PID > "$PID_DIR/mcp.pid"
    echo "MCP server started with PID $MCP_PID."
}

# Function to stop MCP server
stop_mcp() {
    if [ -f "$PID_DIR/mcp.pid" ]; then
        MCP_PID=$(cat "$PID_DIR/mcp.pid")
        echo "Stopping MCP server (PID $MCP_PID)..."
        kill $MCP_PID 2>/dev/null || true
        rm "$PID_DIR/mcp.pid"
        echo "MCP server stopped."
    else
        echo "MCP server not running."
    fi
}

# Function to start all services
start_all() {
    start_neo4j
    sleep 5  # Give Neo4j time to start
    start_api
    start_mpc
    start_mcp
    echo "All services started."
}

# Function to stop all services
stop_all() {
    stop_mcp
    stop_mpc
    stop_api
    stop_neo4j
    echo "All services stopped."
}

# Function to check service status
status() {
    echo "Checking service status..."
    
    # Check Neo4j
    if [ -x "$NEO4J_HOME/bin/neo4j" ]; then
        "$NEO4J_HOME/bin/neo4j" status
    else
        echo "Neo4j not found at $NEO4J_HOME."
    fi
    
    # Check API server
    if [ -f "$PID_DIR/api.pid" ]; then
        API_PID=$(cat "$PID_DIR/api.pid")
        if ps -p $API_PID > /dev/null; then
            echo "API server is running with PID $API_PID."
        else
            echo "API server is not running (stale PID file)."
            rm "$PID_DIR/api.pid"
        fi
    else
        echo "API server is not running."
    fi
    
    # Check MPC server
    if [ -f "$PID_DIR/mpc.pid" ]; then
        MPC_PID=$(cat "$PID_DIR/mpc.pid")
        if ps -p $MPC_PID > /dev/null; then
            echo "MPC server is running with PID $MPC_PID."
        else
            echo "MPC server is not running (stale PID file)."
            rm "$PID_DIR/mpc.pid"
        fi
    else
        echo "MPC server is not running."
    fi
    
    # Check MCP server
    if [ -f "$PID_DIR/mcp.pid" ]; then
        MCP_PID=$(cat "$PID_DIR/mcp.pid")
        if ps -p $MCP_PID > /dev/null; then
            echo "MCP server is running with PID $MCP_PID."
        else
            echo "MCP server is not running (stale PID file)."
            rm "$PID_DIR/mcp.pid"
        fi
    else
        echo "MCP server is not running."
    fi
}

# Function to view logs
logs() {
    case "$1" in
        api)
            tail -f "$LOG_DIR/api.log"
            ;;
        mpc)
            tail -f "$LOG_DIR/mpc.log"
            ;;
        mcp)
            tail -f "$LOG_DIR/mcp.log"
            ;;
        neo4j)
            tail -f "$NEO4J_HOME/logs/neo4j.log"
            ;;
        *)
            echo "Usage: $0 logs [api|mpc|mcp|neo4j]"
            ;;
    esac
}

# Main function
case "$1" in
    start)
        case "$2" in
            neo4j)
                start_neo4j
                ;;
            api)
                start_api
                ;;
            mpc)
                start_mpc
                ;;
            mcp)
                start_mcp
                ;;
            all)
                start_all
                ;;
            *)
                echo "Usage: $0 start [neo4j|api|mpc|mcp|all]"
                ;;
        esac
        ;;
    stop)
        case "$2" in
            neo4j)
                stop_neo4j
                ;;
            api)
                stop_api
                ;;
            mpc)
                stop_mpc
                ;;
            mcp)
                stop_mcp
                ;;
            all)
                stop_all
                ;;
            *)
                echo "Usage: $0 stop [neo4j|api|mpc|mcp|all]"
                ;;
        esac
        ;;
    restart)
        case "$2" in
            neo4j)
                stop_neo4j
                sleep 2
                start_neo4j
                ;;
            api)
                stop_api
                sleep 2
                start_api
                ;;
            mpc)
                stop_mpc
                sleep 2
                start_mpc
                ;;
            mcp)
                stop_mcp
                sleep 2
                start_mcp
                ;;
            all)
                stop_all
                sleep 5
                start_all
                ;;
            *)
                echo "Usage: $0 restart [neo4j|api|mpc|mcp|all]"
                ;;
        esac
        ;;
    status)
        status
        ;;
    logs)
        logs "$2"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs} [service]"
        echo "Services: neo4j, api, mpc, mcp, all"
        ;;
esac

exit 0
```

#### 2.2 Create systemd Service Files

**File**: `tools/systemd/graphrag-mcp.service`

```ini
[Unit]
Description=GraphRAG MCP Server
After=network.target neo4j.service

[Service]
Type=simple
User=graphrag
WorkingDirectory=/opt/graphrag
ExecStart=/usr/bin/python -m src.mpc.mcp_server --host 0.0.0.0 --port 8766
Restart=on-failure
Environment=PYTHONPATH=/opt/graphrag
Environment=NEO4J_URI=bolt://localhost:${GRAPHRAG_PORT_NEO4J_BOLT}
Environment=NEO4J_USERNAME=neo4j
Environment=NEO4J_PASSWORD=graphrag
Environment=CHROMA_PERSIST_DIRECTORY=/opt/graphrag/data/chromadb

[Install]
WantedBy=multi-user.target
```

**File**: `tools/systemd/install-services.sh`

```bash
#!/bin/bash
# Install GraphRAG systemd services

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root"
    exit 1
fi

# Configuration
GRAPHRAG_USER="graphrag"
GRAPHRAG_HOME="/opt/graphrag"
SYSTEMD_DIR="/etc/systemd/system"

# Create GraphRAG user if it doesn't exist
if ! id -u $GRAPHRAG_USER > /dev/null 2>&1; then
    echo "Creating user $GRAPHRAG_USER..."
    useradd -m -d $GRAPHRAG_HOME -s /bin/bash $GRAPHRAG_USER
    echo "User $GRAPHRAG_USER created."
fi

# Copy service files
echo "Installing systemd service files..."
cp tools/systemd/graphrag-api.service $SYSTEMD_DIR/
cp tools/systemd/graphrag-mpc.service $SYSTEMD_DIR/
cp tools/systemd/graphrag-mcp.service $SYSTEMD_DIR/

# Reload systemd
systemctl daemon-reload

# Enable services
systemctl enable graphrag-api.service
systemctl enable graphrag-mpc.service
systemctl enable graphrag-mcp.service

echo "GraphRAG services installed and enabled."
echo "You can start them with:"
echo "  systemctl start graphrag-api"
echo "  systemctl start graphrag-mpc"
echo "  systemctl start graphrag-mcp"
```

### 3. Health Checks

#### 3.1 Create Health Check Script

**File**: `tools/health-check.sh`

```bash
#!/bin/bash
# GraphRAG Health Check Script

# Configuration
CONFIG_FILE="$HOME/.graphrag/config.env"
PID_DIR="$HOME/.graphrag/pids"

# Default values
NEO4J_URI="bolt://localhost:${GRAPHRAG_PORT_NEO4J_BOLT}"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="graphrag"
API_PORT=5001
MPC_PORT=8765
MCP_PORT=8766

# Load configuration
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# Function to check if a port is open
check_port() {
    local host=$1
    local port=$2
    local service=$3
    
    nc -z -w 5 $host $port
    if [ $? -eq 0 ]; then
        echo "✅ $service is running on $host:$port"
        return 0
    else
        echo "❌ $service is NOT running on $host:$port"
        return 1
    fi
}

# Function to check if a process is running
check_process() {
    local pid_file=$1
    local service=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null; then
            echo "✅ $service is running with PID $pid"
            return 0
        else
            echo "❌ $service is NOT running (stale PID file)"
            return 1
        fi
    else
        echo "❌ $service is NOT running (no PID file)"
        return 1
    fi
}

# Function to check Neo4j
check_neo4j() {
    echo "Checking Neo4j..."
    
    # Check if Neo4j is running
    check_port "localhost" 7687 "Neo4j Bolt"
    local bolt_status=$?
    
    check_port "localhost" 7474 "Neo4j Browser"
    local browser_status=$?
    
    # Try to connect to Neo4j
    if [ $bolt_status -eq 0 ]; then
        echo "Testing Neo4j connection..."
        python -c "
from neo4j import GraphDatabase
try:
    driver = GraphDatabase.driver('$NEO4J_URI', auth=('$NEO4J_USERNAME', '$NEO4J_PASSWORD'))
    with driver.session() as session:
        result = session.run('RETURN 1 as n')
        record = result.single()
        if record and record['n'] == 1:
            print('✅ Neo4j connection successful')
        else:
            print('❌ Neo4j connection failed')
    driver.close()
except Exception as e:
    print(f'❌ Neo4j connection error: {e}')
"
    fi
}

# Function to check API server
check_api() {
    echo "Checking API server..."
    
    # Check if API server is running
    check_process "$PID_DIR/api.pid" "API server"
    local process_status=$?
    
    check_port "localhost" $API_PORT "API server"
    local port_status=$?
    
    # Try to connect to API server
    if [ $port_status -eq 0 ]; then
        echo "Testing API server..."
        curl -s "http://localhost:$API_PORT/health" | grep -q "ok"
        if [ $? -eq 0 ]; then
            echo "✅ API server health check successful"
        else
            echo "❌ API server health check failed"
        fi
    fi
}

# Function to check MPC server
check_mpc() {
    echo "Checking MPC server..."
    
    # Check if MPC server is running
    check_process "$PID_DIR/mpc.pid" "MPC server"
    local process_status=$?
    
    check_port "localhost" $MPC_PORT "MPC server"
    local port_status=$?
}

# Function to check MCP server
check_mcp() {
    echo "Checking MCP server..."
    
    # Check if MCP server is running
    check_process "$PID_DIR/mcp.pid" "MCP server"
    local process_status=$?
    
    check_port "localhost" $MCP_PORT "MCP server"
    local port_status=$?
    
    # Try to connect to MCP server
    if [ $port_status -eq 0 ]; then
        echo "Testing MCP server..."
        python -c "
import asyncio
import websockets
import json

async def test_mcp():
    try:
        async with websockets.connect('ws://localhost:$MCP_PORT') as websocket:
            await websocket.send(json.dumps({
                'jsonrpc': '2.0',
                'method': 'initialize',
                'params': {
                    'protocolVersion': '2024-11-05',
                    'capabilities': {},
                    'clientInfo': {
                        'name': 'health-check',
                        'version': '0.1.0'
                    }
                },
                'id': 0
            }))
            
            response = await websocket.recv()
            data = json.loads(response)
            
            if 'result' in data:
                print('✅ MCP server connection successful')
            else:
                print('❌ MCP server connection failed')
    except Exception as e:
        print(f'❌ MCP server connection error: {e}')

asyncio.run(test_mcp())
"
    fi
}

# Main function
echo "GraphRAG Health Check"
echo "===================="
echo

check_neo4j
echo

check_api
echo

check_mpc
echo

check_mcp
echo

echo "Health check complete."
```

### 4. Update Documentation

#### 4.1 Update Service Management Documentation

**File**: `docs/service_management.md` (update existing file)

Add the following section:

```markdown
## MCP Server Management

The MCP (Model Context Protocol) server allows AI agents to interact with the GraphRAG system. You can manage it using the service management script:

```bash
# Start the MCP server
./tools/graphrag-service.sh start mcp

# Stop the MCP server
./tools/graphrag-service.sh stop mcp

# Restart the MCP server
./tools/graphrag-service.sh restart mcp

# Check MCP server status
./tools/graphrag-service.sh status

# View MCP server logs
./tools/graphrag-service.sh logs mcp
```

### Using systemd (Linux)

If you've installed the systemd services, you can manage the MCP server using systemctl:

```bash
# Start the MCP server
sudo systemctl start graphrag-mcp

# Stop the MCP server
sudo systemctl stop graphrag-mcp

# Restart the MCP server
sudo systemctl restart graphrag-mcp

# Check MCP server status
sudo systemctl status graphrag-mcp

# View MCP server logs
sudo journalctl -u graphrag-mcp
```

### Health Checks

You can check the health of all GraphRAG services, including the MCP server, using the health check script:

```bash
./tools/health-check.sh
```

This script will check if all services are running and can be connected to.
```

## Next Steps

After implementing the Docker integration and service management, the next steps will be:

1. Test the Docker integration
2. Test the service management scripts
3. Test integration with AI agents
4. Update the main documentation with the new features