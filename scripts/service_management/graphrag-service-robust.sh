#!/bin/bash
# graphrag-service-robust.sh - Enhanced service management script for GraphRAG

# Configuration
CONFIG_FILE="$HOME/.graphrag/config.env"
LOG_DIR="$HOME/.graphrag/logs"
PID_DIR="$HOME/.graphrag/pids"

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Load configuration
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    echo "Configuration file not found. Creating default configuration..."
    mkdir -p "$(dirname "$CONFIG_FILE")"
    cat > "$CONFIG_FILE" << EOF
# GraphRAG Configuration
NEO4J_HOME=$HOME/.graphrag/neo4j

# Port Configuration
GRAPHRAG_PORT_NEO4J_BOLT=7687
GRAPHRAG_PORT_NEO4J_HTTP=7474
GRAPHRAG_PORT_NEO4J_HTTPS=7473
GRAPHRAG_PORT_API=5001
GRAPHRAG_PORT_MCP=8767
GRAPHRAG_PORT_BUG_MCP=5005
GRAPHRAG_PORT_DOCKER_NEO4J_BOLT=7688

# Neo4j Configuration
NEO4J_URI=bolt://localhost:\${GRAPHRAG_PORT_NEO4J_BOLT}
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=graphrag

# ChromaDB Configuration
CHROMA_PERSIST_DIRECTORY=$HOME/.graphrag/data/chromadb

# Other Configuration
GRAPHRAG_LOG_LEVEL=INFO
EOF
    source "$CONFIG_FILE"
fi

# Function to check if a port is in use
is_port_in_use() {
    local port=$1
    # Use nc (netcat) to check if port is in use
    nc -z localhost $port >/dev/null 2>&1
    return $?
}

# Function to check if a process is running
is_process_running() {
    local pid=$1
    if [ -z "$pid" ]; then
        return 1
    fi

    if ps -p $pid > /dev/null; then
        return 0
    else
        return 1
    fi
}

# Function to clean up stale PID files
cleanup_stale_pid() {
    local service=$1
    local pid_file="$PID_DIR/$service.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ! is_process_running $pid; then
            echo "Removing stale PID file for $service (PID: $pid)"
            rm -f "$pid_file"
        fi
    fi
}

# Function to start Neo4j with robust checks
start_neo4j() {
    echo "Starting Neo4j..."

    # Check if Neo4j is already running by port
    if is_port_in_use $GRAPHRAG_PORT_NEO4J_HTTP; then
        echo "Neo4j is already running (port $GRAPHRAG_PORT_NEO4J_HTTP is in use)."
        return 0
    fi

    # Clean up stale PID file if it exists
    cleanup_stale_pid "neo4j"

    # Start Neo4j
    "$NEO4J_HOME/bin/neo4j" start

    # Wait for Neo4j to start
    echo "Waiting for Neo4j to start..."
    for i in {1..30}; do
        if curl -s http://localhost:$GRAPHRAG_PORT_NEO4J_HTTP > /dev/null; then
            echo "✅ Neo4j started successfully."
            return 0
        fi
        sleep 1
        echo -n "."
    done

    echo "❌ Failed to start Neo4j after 30 seconds."
    return 1
}

# Function to start API server with robust checks
start_api() {
    echo "Starting API server..."

    # Check if API server is already running by port
    if is_port_in_use $GRAPHRAG_PORT_API; then
        echo "API server is already running (port $GRAPHRAG_PORT_API is in use)."
        return 0
    fi

    # Clean up stale PID file if it exists
    cleanup_stale_pid "api"

    # Change to project root directory
    cd "$(dirname "$0")/../.."

    # Use absolute path to gunicorn
    GUNICORN_PATH="$(pwd)/.venv-py312/bin/gunicorn"

    if [ ! -f "$GUNICORN_PATH" ]; then
        echo "❌ gunicorn not found at $GUNICORN_PATH"
        echo "   Make sure gunicorn is installed in the virtual environment."
        return 1
    fi

    $GUNICORN_PATH \
        --bind 0.0.0.0:$GRAPHRAG_PORT_API \
        --workers 2 \
        --threads 4 \
        --timeout 120 \
        --access-logfile "$LOG_DIR/gunicorn-access.log" \
        --error-logfile "$LOG_DIR/gunicorn-error.log" \
        --log-level $GRAPHRAG_LOG_LEVEL \
        --daemon \
        --pid "$PID_DIR/api.pid" \
        src.api.wsgi:app

    # Wait for API server to start
    echo "Waiting for API server to start..."
    for i in {1..15}; do
        if curl -s http://localhost:$GRAPHRAG_PORT_API/health > /dev/null; then
            echo "✅ API server started successfully."
            return 0
        fi
        sleep 1
        echo -n "."
    done

    echo "❌ Failed to start API server after 15 seconds."
    return 1
}

# Function to start MCP server with robust checks
start_mcp() {
    echo "Starting MCP server..."

    # Check if MCP server is already running by port
    if is_port_in_use $GRAPHRAG_PORT_MCP; then
        echo "MCP server is already running (port $GRAPHRAG_PORT_MCP is in use)."
        return 0
    fi

    # Clean up stale PID file if it exists
    cleanup_stale_pid "mcp"

    # Change to project root directory
    cd "$(dirname "$0")/../.."

    # Use absolute path to python
    PYTHON_PATH="$(pwd)/.venv-py312/bin/python"

    if [ ! -f "$PYTHON_PATH" ]; then
        echo "❌ Python not found at $PYTHON_PATH"
        echo "   Make sure the virtual environment is set up correctly."
        return 1
    fi

    $PYTHON_PATH -m src.mcp.server --host 0.0.0.0 --port $GRAPHRAG_PORT_MCP > "$LOG_DIR/mcp.log" 2>&1 &
    echo $! > "$PID_DIR/mcp.pid"

    # Wait for MCP server to start
    echo "Waiting for MCP server to start..."
    for i in {1..10}; do
        if is_port_in_use $GRAPHRAG_PORT_MCP; then
            echo "✅ MCP server started successfully."
            return 0
        fi
        sleep 1
        echo -n "."
    done

    # Check if process is still running
    if [ -f "$PID_DIR/mcp.pid" ]; then
        PID=$(cat "$PID_DIR/mcp.pid")
        if is_process_running $PID; then
            echo "✅ MCP server process is running, but port check failed. Proceeding anyway."
            return 0
        else
            echo "❌ MCP server process died."
            rm -f "$PID_DIR/mcp.pid"
        fi
    fi

    echo "❌ Failed to start MCP server after 10 seconds."
    return 1
}

# Function to stop Neo4j with robust checks
stop_neo4j() {
    echo "Stopping Neo4j..."

    # Check if Neo4j is running by port
    if ! is_port_in_use $GRAPHRAG_PORT_NEO4J_HTTP; then
        echo "Neo4j is not running."
        return 0
    fi

    # Stop Neo4j
    "$NEO4J_HOME/bin/neo4j" stop

    # Wait for Neo4j to stop
    echo "Waiting for Neo4j to stop..."
    for i in {1..15}; do
        if ! is_port_in_use $GRAPHRAG_PORT_NEO4J_HTTP; then
            echo "✅ Neo4j stopped successfully."
            return 0
        fi
        sleep 1
        echo -n "."
    done

    echo "❌ Failed to stop Neo4j after 15 seconds. You may need to kill it manually."
    return 1
}

# Function to stop API server with robust checks
stop_api() {
    echo "Stopping API server..."

    # Check if API server is running by port
    if ! is_port_in_use $GRAPHRAG_PORT_API; then
        echo "API server is not running."
        cleanup_stale_pid "api"
        return 0
    fi

    # Stop API server
    if [ -f "$PID_DIR/api.pid" ]; then
        PID=$(cat "$PID_DIR/api.pid")
        if is_process_running $PID; then
            kill $PID

            # Wait for API server to stop
            echo "Waiting for API server to stop..."
            for i in {1..10}; do
                if ! is_port_in_use $GRAPHRAG_PORT_API; then
                    echo "✅ API server stopped successfully."
                    rm -f "$PID_DIR/api.pid"
                    return 0
                fi
                sleep 1
                echo -n "."
            done

            echo "❌ Failed to stop API server gracefully. Attempting to force kill..."
            kill -9 $PID
            rm -f "$PID_DIR/api.pid"
        else
            echo "API server PID file exists but process is not running."
            rm -f "$PID_DIR/api.pid"
        fi
    else
        echo "API server PID file not found, but port is in use."
        echo "Please manually identify and kill the process using the port."
        echo "You can use: lsof -i :$GRAPHRAG_PORT_API"
    fi

    # Final check
    if is_port_in_use $GRAPHRAG_PORT_API; then
        echo "❌ Failed to stop API server. Port $GRAPHRAG_PORT_API is still in use."
        return 1
    else
        echo "✅ API server stopped successfully."
        return 0
    fi
}

# Function to stop MPC server with robust checks
stop_mcp() {
    echo "Stopping MCP server..."

    # Check if MCP server is running by port
    if ! is_port_in_use $GRAPHRAG_PORT_MCP; then
        echo "MCP server is not running."
        cleanup_stale_pid "mcp"
        return 0
    fi

    # Stop MCP server
    if [ -f "$PID_DIR/mcp.pid" ]; then
        PID=$(cat "$PID_DIR/mcp.pid")
        if is_process_running $PID; then
            kill $PID

            # Wait for MCP server to stop
            echo "Waiting for MCP server to stop..."
            for i in {1..10}; do
                if ! is_port_in_use $GRAPHRAG_PORT_MCP; then
                    echo "✅ MCP server stopped successfully."
                    rm -f "$PID_DIR/mcp.pid"
                    return 0
                fi
                sleep 1
                echo -n "."
            done

            echo "❌ Failed to stop MCP server gracefully. Attempting to force kill..."
            kill -9 $PID
            rm -f "$PID_DIR/mcp.pid"
        else
            echo "MCP server PID file exists but process is not running."
            rm -f "$PID_DIR/mcp.pid"
        fi
    else
        echo "MCP server PID file not found, but port is in use."
        echo "Please manually identify and kill the process using the port."
        echo "You can use: lsof -i :$GRAPHRAG_PORT_MCP"
    fi

    # Final check
    if is_port_in_use $GRAPHRAG_PORT_MCP; then
        echo "❌ Failed to stop MCP server. Port $GRAPHRAG_PORT_MCP is still in use."
        return 1
    else
        echo "✅ MCP server stopped successfully."
        return 0
    fi
}

# Function to check status with robust checks
status() {
    echo "GraphRAG Service Status:"

    # Check Neo4j
    if is_port_in_use $GRAPHRAG_PORT_NEO4J_HTTP; then
        echo "Neo4j: ✅ Running (port $GRAPHRAG_PORT_NEO4J_HTTP)"
    else
        echo "Neo4j: ❌ Stopped"
    fi

    # Check API server
    if is_port_in_use $GRAPHRAG_PORT_API; then
        # Get PID from file if it exists
        if [ -f "$PID_DIR/api.pid" ]; then
            PID=$(cat "$PID_DIR/api.pid")
            if is_process_running $PID; then
                echo "API Server: ✅ Running (port $GRAPHRAG_PORT_API, PID: $PID)"
            else
                echo "API Server: ✅ Running (port $GRAPHRAG_PORT_API), but PID file is stale"
                echo "  ⚠️  Warning: PID file exists but process is not running with that PID"
            fi
        else
            echo "API Server: ✅ Running (port $GRAPHRAG_PORT_API), but no PID file found"
        fi
    else
        echo "API Server: ❌ Stopped"
        cleanup_stale_pid "api"
    fi

    # Check MCP server
    if is_port_in_use $GRAPHRAG_PORT_MCP; then
        # Get PID from file if it exists
        if [ -f "$PID_DIR/mcp.pid" ]; then
            PID=$(cat "$PID_DIR/mcp.pid")
            if is_process_running $PID; then
                echo "MCP Server: ✅ Running (port $GRAPHRAG_PORT_MCP, PID: $PID)"
            else
                echo "MCP Server: ✅ Running (port $GRAPHRAG_PORT_MCP), but PID file is stale"
                echo "  ⚠️  Warning: PID file exists but process is not running with that PID"
            fi
        else
            echo "MCP Server: ✅ Running (port $GRAPHRAG_PORT_MCP), but no PID file found"
        fi

    else
        echo "MCP Server: ❌ Stopped"
        cleanup_stale_pid "mcp"
    fi
}

# Main command handling
case "$1" in
    start)
        start_neo4j
        start_api
        start_mcp
        ;;
    stop)
        stop_mcp
        stop_api
        stop_neo4j
        ;;
    restart)
        stop_mcp
        stop_api
        stop_neo4j
        sleep 2
        start_neo4j
        start_api
        start_mcp
        ;;
    status)
        status
        ;;
    start-neo4j)
        start_neo4j
        ;;
    start-api)
        start_api
        ;;
    start-mcp)
        start_mcp
        ;;
    stop-neo4j)
        stop_neo4j
        ;;
    stop-api)
        stop_api
        ;;
    stop-mcp)
        stop_mcp
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|start-neo4j|start-api|start-mcp|stop-neo4j|stop-api|stop-mcp}"
        exit 1
        ;;
esac

exit 0
