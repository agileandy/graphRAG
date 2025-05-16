#!/bin/bash
# graphrag-simple.sh - Simple service management script for GraphRAG
# This script takes a clean-slate approach to service management

# Set default ports (these should match src/config/ports.py)
NEO4J_BOLT_PORT=7687
NEO4J_HTTP_PORT=7474
API_PORT=5001
MCP_PORT=8767

# Set default paths
NEO4J_HOME="/opt/homebrew"
NEO4J_DATA_DIR="$HOME/.graphrag/neo4j/data"
CHROMA_DIR="$HOME/.graphrag/data/chromadb"
LOG_DIR="$HOME/.graphrag/logs"

# Create necessary directories
mkdir -p "$LOG_DIR" "$CHROMA_DIR" "$NEO4J_DATA_DIR"

# Function to check if a port is in use
port_in_use() {
    nc -z localhost $1 >/dev/null 2>&1
    return $?
}

# Function to kill process using a port
kill_process_on_port() {
    local port=$1
    local pid=$(lsof -ti :$port)
    if [ ! -z "$pid" ]; then
        echo "Killing process $pid using port $port"
        kill -9 $pid
        return 0
    else
        echo "No process found using port $port"
        return 1
    fi
}

# Function to start Neo4j
start_neo4j() {
    echo "Starting Neo4j..."

    # Check if Neo4j is already running
    if port_in_use $NEO4J_HTTP_PORT; then
        echo "Neo4j is already running on port $NEO4J_HTTP_PORT"
        return 0
    fi

    # Start Neo4j
    "$NEO4J_HOME/bin/neo4j" start

    # Wait for Neo4j to start
    echo "Waiting for Neo4j to start..."
    for i in {1..30}; do
        if port_in_use $NEO4J_HTTP_PORT; then
            echo "✅ Neo4j started successfully"
            return 0
        fi
        sleep 1
        echo -n "."
    done

    echo "❌ Failed to start Neo4j after 30 seconds"
    return 1
}

# Function to start API server
start_api() {
    echo "Starting API server..."

    # Check if API server is already running
    if port_in_use $API_PORT; then
        echo "API server is already running on port $API_PORT"
        return 0
    fi

    # Start API server
    cd "$(dirname "$0")/../.."
    GUNICORN_PATH="$(pwd)/.venv-py312/bin/gunicorn"

    if [ ! -f "$GUNICORN_PATH" ]; then
        echo "❌ gunicorn not found at $GUNICORN_PATH"
        return 1
    fi

    # Set environment variables
    export NEO4J_URI="bolt://localhost:$NEO4J_BOLT_PORT"
    export NEO4J_USERNAME="neo4j"
    export NEO4J_PASSWORD="graphrag"
    export CHROMA_PERSIST_DIRECTORY="$CHROMA_DIR"

    $GUNICORN_PATH \
        --bind 0.0.0.0:$API_PORT \
        --workers 2 \
        --threads 4 \
        --timeout 120 \
        --access-logfile "$LOG_DIR/gunicorn-access.log" \
        --error-logfile "$LOG_DIR/gunicorn-error.log" \
        --log-level info \
        --daemon \
        src.api.wsgi:app

    # Wait for API server to start
    echo "Waiting for API server to start..."
    for i in {1..15}; do
        if port_in_use $API_PORT; then
            echo "✅ API server started successfully"
            return 0
        fi
        sleep 1
        echo -n "."
    done

    echo "❌ Failed to start API server after 15 seconds"
    return 1
}

# Function to start MCP server
start_mcp() {
    echo "Starting MCP server..."

    # Check if MCP server is already running
    if port_in_use $MCP_PORT; then
        echo "MCP server is already running on port $MCP_PORT"
        return 0
    fi

    # Start MCP server
    cd "$(dirname "$0")/../.."
    PYTHON_PATH="$(pwd)/.venv-py312/bin/python"

    if [ ! -f "$PYTHON_PATH" ]; then
        echo "❌ Python not found at $PYTHON_PATH"
        return 1
    fi

    # Set environment variables
    export NEO4J_URI="bolt://localhost:$NEO4J_BOLT_PORT"
    export NEO4J_USERNAME="neo4j"
    export NEO4J_PASSWORD="graphrag"
    export CHROMA_PERSIST_DIRECTORY="$CHROMA_DIR"

    nohup $PYTHON_PATH -m src.mcp.server --host 0.0.0.0 --port $MCP_PORT > "$LOG_DIR/mcp.log" 2>&1 &

    # Wait for MCP server to start
    echo "Waiting for MCP server to start..."
    for i in {1..10}; do
        if port_in_use $MCP_PORT; then
            echo "✅ MCP server started successfully"
            return 0
        fi
        sleep 1
        echo -n "."
    done

    echo "❌ Failed to start MCP server after 10 seconds"
    return 1
}

# Function to stop Neo4j
stop_neo4j() {
    echo "Stopping Neo4j..."

    # Check if Neo4j is running
    if ! port_in_use $NEO4J_HTTP_PORT; then
        echo "Neo4j is not running"
        return 0
    fi

    # Stop Neo4j gracefully
    "$NEO4J_HOME/bin/neo4j" stop

    # Wait for Neo4j to stop
    echo "Waiting for Neo4j to stop..."
    for i in {1..15}; do
        if ! port_in_use $NEO4J_HTTP_PORT; then
            echo "✅ Neo4j stopped successfully"
            return 0
        fi
        sleep 1
        echo -n "."
    done

    # Force kill if necessary
    echo "❌ Failed to stop Neo4j gracefully, attempting to force kill..."
    kill_process_on_port $NEO4J_HTTP_PORT
    kill_process_on_port $NEO4J_BOLT_PORT

    if ! port_in_use $NEO4J_HTTP_PORT; then
        echo "✅ Neo4j stopped successfully"
        return 0
    else
        echo "❌ Failed to stop Neo4j"
        return 1
    fi
}

# Function to stop API server
stop_api() {
    echo "Stopping API server..."

    # Check if API server is running
    if ! port_in_use $API_PORT; then
        echo "API server is not running"
        return 0
    fi

    # Kill process using API port
    kill_process_on_port $API_PORT

    if ! port_in_use $API_PORT; then
        echo "✅ API server stopped successfully"
        return 0
    else
        echo "❌ Failed to stop API server"
        return 1
    fi
}

# Function to stop MCP server
stop_mcp() {
    echo "Stopping MCP server..."

    # Check if MCP server is running
    if ! port_in_use $MCP_PORT; then
        echo "MCP server is not running"
        return 0
    fi

    # Kill process using MCP port
    kill_process_on_port $MCP_PORT

    if ! port_in_use $MCP_PORT; then
        echo "✅ MCP server stopped successfully"
        return 0
    else
        echo "❌ Failed to stop MCP server"
        return 1
    fi
}

# Function to check status
status() {
    echo "GraphRAG Service Status:"

    # Check Neo4j
    if port_in_use $NEO4J_HTTP_PORT; then
        echo "Neo4j: ✅ Running (port $NEO4J_HTTP_PORT)"
    else
        echo "Neo4j: ❌ Stopped"
    fi

    # Check API server
    if port_in_use $API_PORT; then
        echo "API Server: ✅ Running (port $API_PORT)"
    else
        echo "API Server: ❌ Stopped"
    fi

    # Check MCP server
    if port_in_use $MCP_PORT; then
        echo "MCP Server: ✅ Running (port $MCP_PORT)"
    else
        echo "MCP Server: ❌ Stopped"
    fi
}

# Function to force kill all services
force_kill_all() {
    echo "Force killing all GraphRAG services..."

    kill_process_on_port $NEO4J_HTTP_PORT
    kill_process_on_port $NEO4J_BOLT_PORT
    kill_process_on_port $API_PORT
    kill_process_on_port $MCP_PORT

    echo "All services killed"
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
    force-kill)
        force_kill_all
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
        echo "Usage: $0 {start|stop|restart|status|force-kill|start-neo4j|start-api|start-mcp|stop-neo4j|stop-api|stop-mcp}"
        exit 1
        ;;
esac

exit 0
