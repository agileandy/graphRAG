#!/bin/bash
# graphrag-service.sh - Service management script for GraphRAG

# Configuration
CONFIG_FILE="$HOME/.graphrag/config.env"
LOG_DIR="$HOME/.graphrag/logs"
PID_DIR="$HOME/.graphrag/pids"

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
GRAPHRAG_PORT_MPC=8765
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

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Function to start Neo4j
start_neo4j() {
    echo "Starting Neo4j..."
    if [ -f "$PID_DIR/neo4j.pid" ]; then
        echo "Neo4j is already running."
        return 1
    fi

    "$NEO4J_HOME/bin/neo4j" start

    # Wait for Neo4j to start
    echo "Waiting for Neo4j to start..."
    for i in {1..30}; do
        if curl -s http://localhost:7474 > /dev/null; then
            echo "Neo4j started successfully."
            return 0
        fi
        sleep 1
    done

    echo "Failed to start Neo4j."
    return 1
}

# Function to start API server
start_api() {
    echo "Starting API server..."
    if [ -f "$PID_DIR/api.pid" ]; then
        echo "API server is already running."
        return 1
    fi

    cd "$(dirname "$0")/.." && \
    .venv-py312/bin/gunicorn \
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
            echo "API server started successfully."
            return 0
        fi
        sleep 1
    done

    echo "Failed to start API server."
    return 1
}

# Function to start MPC server
start_mpc() {
    echo "Starting MPC server..."
    if [ -f "$PID_DIR/mpc.pid" ]; then
        echo "MPC server is already running."
        return 1
    fi

    cd "$(dirname "$0")/.." && \
    .venv-py312/bin/python -m src.mpc.server --host 0.0.0.0 --port $GRAPHRAG_PORT_MPC > "$LOG_DIR/mpc.log" 2>&1 &
    echo $! > "$PID_DIR/mpc.pid"

    # Wait for MPC server to start
    echo "Waiting for MPC server to start..."
    sleep 3

    if [ -f "$PID_DIR/mpc.pid" ]; then
        PID=$(cat "$PID_DIR/mpc.pid")
        if ps -p $PID > /dev/null; then
            echo "MPC server started successfully."
            return 0
        fi
    fi

    echo "Failed to start MPC server."
    return 1
}

# Function to stop Neo4j
stop_neo4j() {
    echo "Stopping Neo4j..."
    "$NEO4J_HOME/bin/neo4j" stop
    rm -f "$PID_DIR/neo4j.pid"
    echo "Neo4j stopped."
}

# Function to stop API server
stop_api() {
    echo "Stopping API server..."
    if [ -f "$PID_DIR/api.pid" ]; then
        PID=$(cat "$PID_DIR/api.pid")
        kill $PID
        rm -f "$PID_DIR/api.pid"
        echo "API server stopped."
    else
        echo "API server is not running."
    fi
}

# Function to stop MPC server
stop_mpc() {
    echo "Stopping MPC server..."
    if [ -f "$PID_DIR/mpc.pid" ]; then
        PID=$(cat "$PID_DIR/mpc.pid")
        kill $PID
        rm -f "$PID_DIR/mpc.pid"
        echo "MPC server stopped."
    else
        echo "MPC server is not running."
    fi
}

# Function to check status
status() {
    echo "GraphRAG Service Status:"

    # Check Neo4j
    if curl -s http://localhost:$GRAPHRAG_PORT_NEO4J_HTTP > /dev/null; then
        echo "Neo4j: Running"
    else
        echo "Neo4j: Stopped"
    fi

    # Check API server
    if [ -f "$PID_DIR/api.pid" ]; then
        PID=$(cat "$PID_DIR/api.pid")
        if ps -p $PID > /dev/null; then
            echo "API Server: Running (PID: $PID)"
        else
            echo "API Server: Crashed (PID file exists but process is not running)"
            rm -f "$PID_DIR/api.pid"
        fi
    else
        echo "API Server: Stopped"
    fi

    # Check MPC server
    if [ -f "$PID_DIR/mpc.pid" ]; then
        PID=$(cat "$PID_DIR/mpc.pid")
        if ps -p $PID > /dev/null; then
            echo "MPC Server: Running (PID: $PID)"
        else
            echo "MPC Server: Crashed (PID file exists but process is not running)"
            rm -f "$PID_DIR/mpc.pid"
        fi
    else
        echo "MPC Server: Stopped"
    fi
}

# Main command handling
case "$1" in
    start)
        start_neo4j
        start_api
        start_mpc
        ;;
    stop)
        stop_mpc
        stop_api
        stop_neo4j
        ;;
    restart)
        stop_mpc
        stop_api
        stop_neo4j
        sleep 2
        start_neo4j
        start_api
        start_mpc
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
    start-mpc)
        start_mpc
        ;;
    stop-neo4j)
        stop_neo4j
        ;;
    stop-api)
        stop_api
        ;;
    stop-mpc)
        stop_mpc
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|start-neo4j|start-api|start-mpc|stop-neo4j|stop-api|stop-mpc}"
        exit 1
        ;;
esac

exit 0
