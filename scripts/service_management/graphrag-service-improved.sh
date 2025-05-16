#!/bin/bash
# graphrag-service-improved.sh - Improved service management for GraphRAG
# This script prioritizes resilience, simplicity, and configuration consistency

# Set default values (will be overridden by .env if available)
DEFAULT_NEO4J_BOLT_PORT=7687
DEFAULT_NEO4J_HTTP_PORT=7474
DEFAULT_API_PORT=5001
DEFAULT_MCP_PORT=8767
DEFAULT_NEO4J_USERNAME="neo4j"
DEFAULT_NEO4J_PASSWORD="graphrag"
DEFAULT_CHROMA_DIR="$HOME/.graphrag/data/chromadb"
DEFAULT_LOG_DIR="$HOME/.graphrag/logs"

# Determine project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# Load configuration from .env file if it exists
if [ -f "$ENV_FILE" ]; then
    echo "Loading configuration from $ENV_FILE"
    set -a  # automatically export all variables
    source "$ENV_FILE"
    set +a
else
    echo "Warning: .env file not found at $ENV_FILE, using default values"
fi

# Set configuration values, preferring environment variables if set
NEO4J_BOLT_PORT=${GRAPHRAG_PORT_NEO4J_BOLT:-${NEO4J_BOLT_PORT:-$DEFAULT_NEO4J_BOLT_PORT}}
NEO4J_HTTP_PORT=${GRAPHRAG_PORT_NEO4J_HTTP:-${NEO4J_HTTP_PORT:-$DEFAULT_NEO4J_HTTP_PORT}}
API_PORT=${GRAPHRAG_PORT_API:-${API_PORT:-$DEFAULT_API_PORT}}
MCP_PORT=${GRAPHRAG_PORT_MCP:-${MCP_PORT:-$DEFAULT_MCP_PORT}}
NEO4J_USERNAME=${NEO4J_USERNAME:-$DEFAULT_NEO4J_USERNAME}
NEO4J_PASSWORD=${NEO4J_PASSWORD:-$DEFAULT_NEO4J_PASSWORD}
CHROMA_DIR=${CHROMA_PERSIST_DIRECTORY:-$DEFAULT_CHROMA_DIR}
LOG_DIR=${LOG_DIR:-$DEFAULT_LOG_DIR}

# Determine Neo4j installation
if [ -x "/opt/homebrew/bin/neo4j" ]; then
    NEO4J_BIN="/opt/homebrew/bin/neo4j"
elif [ -x "/usr/local/bin/neo4j" ]; then
    NEO4J_BIN="/usr/local/bin/neo4j"
elif [ -x "$HOME/.graphrag/neo4j/bin/neo4j" ]; then
    NEO4J_BIN="$HOME/.graphrag/neo4j/bin/neo4j"
else
    echo "Error: Neo4j installation not found"
    echo "Please install Neo4j or set NEO4J_BIN environment variable"
    exit 1
fi

# Create necessary directories
mkdir -p "$LOG_DIR" "$CHROMA_DIR"

# Print configuration for debugging
print_config() {
    echo "GraphRAG Service Configuration:"
    echo "  Project Root: $PROJECT_ROOT"
    echo "  Neo4j Binary: $NEO4J_BIN"
    echo "  Neo4j Bolt Port: $NEO4J_BOLT_PORT"
    echo "  Neo4j HTTP Port: $NEO4J_HTTP_PORT"
    echo "  API Port: $API_PORT"
    echo "  MCP Port: $MCP_PORT"
    echo "  ChromaDB Directory: $CHROMA_DIR"
    echo "  Log Directory: $LOG_DIR"
}

# Function to check if a port is in use
port_in_use() {
    local port=$1
    # Try nc first, then fall back to other methods
    if command -v nc >/dev/null 2>&1; then
        nc -z localhost $port >/dev/null 2>&1
        return $?
    elif command -v lsof >/dev/null 2>&1; then
        lsof -i ":$port" >/dev/null 2>&1
        return $?
    else
        # Last resort: try to connect with bash
        (echo > /dev/tcp/localhost/$port) >/dev/null 2>&1
        return $?
    fi
}

# Function to get PID of process using a port
get_pid_for_port() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        lsof -ti ":$port" 2>/dev/null
    else
        echo ""
    fi
}

# Function to gracefully stop a process
graceful_stop() {
    local pid=$1
    local name=$2
    local timeout=${3:-10}

    if [ -z "$pid" ]; then
        return 0
    fi

    echo "Gracefully stopping $name (PID: $pid)..."
    kill $pid

    # Wait for process to stop
    for i in $(seq 1 $timeout); do
        if ! kill -0 $pid 2>/dev/null; then
            return 0
        fi
        sleep 1
        echo -n "."
    done

    echo "Process did not stop gracefully after $timeout seconds"
    return 1
}

# Function to force kill a process
force_kill() {
    local pid=$1
    local name=$2

    if [ -z "$pid" ]; then
        return 0
    fi

    echo "Force killing $name (PID: $pid)..."
    kill -9 $pid

    # Verify process is killed
    if ! kill -0 $pid 2>/dev/null; then
        return 0
    else
        echo "Failed to kill process"
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
    $NEO4J_BIN start

    # Wait for Neo4j to start
    echo "Waiting for Neo4j to start..."
    for i in $(seq 1 30); do
        if port_in_use $NEO4J_HTTP_PORT; then
            echo "✅ Neo4j started successfully"
            return 0
        fi
        sleep 1
        echo -n "."
    done

    echo "❌ Failed to start Neo4j after 30 seconds"
    echo "Check Neo4j logs for errors:"
    echo "  $NEO4J_BIN console"
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

    # Check if Neo4j is running
    if ! port_in_use $NEO4J_BOLT_PORT; then
        echo "Warning: Neo4j does not appear to be running on port $NEO4J_BOLT_PORT"
        echo "API server may not function correctly"
    fi

    # Find gunicorn in virtual environment
    VENV_DIR="$PROJECT_ROOT/.venv-py312"
    if [ ! -d "$VENV_DIR" ]; then
        echo "❌ Virtual environment not found at $VENV_DIR"
        echo "Please create the virtual environment first"
        return 1
    fi

    GUNICORN_PATH="$VENV_DIR/bin/gunicorn"
    if [ ! -f "$GUNICORN_PATH" ]; then
        echo "❌ gunicorn not found at $GUNICORN_PATH"
        echo "Please install gunicorn in the virtual environment"
        return 1
    fi

    # Set environment variables for API server
    export NEO4J_URI="bolt://localhost:$NEO4J_BOLT_PORT"
    export NEO4J_USERNAME="$NEO4J_USERNAME"
    export NEO4J_PASSWORD="$NEO4J_PASSWORD"
    export CHROMA_PERSIST_DIRECTORY="$CHROMA_DIR"

    # Start API server
    cd "$PROJECT_ROOT"
    $GUNICORN_PATH \
        --bind 0.0.0.0:$API_PORT \
        --workers 2 \
        --threads 4 \
        --timeout 120 \
        --access-logfile "$LOG_DIR/api-access.log" \
        --error-logfile "$LOG_DIR/api-error.log" \
        --log-level info \
        --daemon \
        src.api.wsgi:app

    # Wait for API server to start
    echo "Waiting for API server to start..."
    for i in $(seq 1 15); do
        if port_in_use $API_PORT; then
            echo "✅ API server started successfully"
            return 0
        fi
        sleep 1
        echo -n "."
    done

    echo "❌ Failed to start API server after 15 seconds"
    echo "Check API server logs for errors:"
    echo "  $LOG_DIR/api-error.log"
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

    # Check if Neo4j is running
    if ! port_in_use $NEO4J_BOLT_PORT; then
        echo "Warning: Neo4j does not appear to be running on port $NEO4J_BOLT_PORT"
        echo "MCP server may not function correctly"
    fi

    # Find Python in virtual environment
    VENV_DIR="$PROJECT_ROOT/.venv-py312"
    if [ ! -d "$VENV_DIR" ]; then
        echo "❌ Virtual environment not found at $VENV_DIR"
        echo "Please create the virtual environment first"
        return 1
    fi

    PYTHON_PATH="$VENV_DIR/bin/python"
    if [ ! -f "$PYTHON_PATH" ]; then
        echo "❌ Python not found at $PYTHON_PATH"
        echo "Please check your virtual environment setup"
        return 1
    fi

    # Set environment variables for MCP server
    export NEO4J_URI="bolt://localhost:$NEO4J_BOLT_PORT"
    export NEO4J_USERNAME="$NEO4J_USERNAME"
    export NEO4J_PASSWORD="$NEO4J_PASSWORD"
    export CHROMA_PERSIST_DIRECTORY="$CHROMA_DIR"

    # Start MCP server
    cd "$PROJECT_ROOT"
    nohup $PYTHON_PATH -m src.mcp.server --host 0.0.0.0 --port $MCP_PORT > "$LOG_DIR/mcp.log" 2>&1 &
    MCP_PID=$!

    # Wait for MCP server to start
    echo "Waiting for MCP server to start..."
    for i in $(seq 1 10); do
        if port_in_use $MCP_PORT; then
            echo "✅ MCP server started successfully (PID: $MCP_PID)"
            return 0
        fi

        # Check if process is still running
        if ! kill -0 $MCP_PID 2>/dev/null; then
            echo "❌ MCP server process died"
            echo "Check MCP server logs for errors:"
            echo "  $LOG_DIR/mcp.log"
            return 1
        fi

        sleep 1
        echo -n "."
    done

    echo "❌ Failed to start MCP server after 10 seconds"
    echo "Check MCP server logs for errors:"
    echo "  $LOG_DIR/mcp.log"
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
    $NEO4J_BIN stop

    # Wait for Neo4j to stop
    echo "Waiting for Neo4j to stop..."
    for i in $(seq 1 15); do
        if ! port_in_use $NEO4J_HTTP_PORT; then
            echo "✅ Neo4j stopped successfully"
            return 0
        fi
        sleep 1
        echo -n "."
    done

    echo "❌ Failed to stop Neo4j gracefully after 15 seconds"
    echo "Attempting to force kill Neo4j processes..."

    # Get PIDs of processes using Neo4j ports
    HTTP_PID=$(get_pid_for_port $NEO4J_HTTP_PORT)
    BOLT_PID=$(get_pid_for_port $NEO4J_BOLT_PORT)

    # Force kill processes
    if [ ! -z "$HTTP_PID" ]; then
        force_kill "$HTTP_PID" "Neo4j HTTP"
    fi

    if [ ! -z "$BOLT_PID" ]; then
        force_kill "$BOLT_PID" "Neo4j Bolt"
    fi

    # Final check
    if ! port_in_use $NEO4J_HTTP_PORT && ! port_in_use $NEO4J_BOLT_PORT; then
        echo "✅ Neo4j stopped successfully"
        return 0
    else
        echo "❌ Failed to stop Neo4j"
        echo "Please try stopping Neo4j manually:"
        echo "  $NEO4J_BIN stop"
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

    # Get PID of process using API port
    API_PID=$(get_pid_for_port $API_PORT)

    if [ -z "$API_PID" ]; then
        echo "Warning: Could not find PID for API server"
        echo "Port $API_PORT is in use but process could not be identified"
        return 1
    fi

    # Try graceful stop first
    if graceful_stop "$API_PID" "API server" 10; then
        echo "✅ API server stopped successfully"
        return 0
    fi

    # Force kill if graceful stop failed
    if force_kill "$API_PID" "API server"; then
        echo "✅ API server force-killed successfully"
        return 0
    else
        echo "❌ Failed to stop API server"
        echo "Please try stopping the process manually:"
        echo "  kill -9 $API_PID"
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

    # Get PID of process using MCP port
    MCP_PID=$(get_pid_for_port $MCP_PORT)

    if [ -z "$MCP_PID" ]; then
        echo "Warning: Could not find PID for MCP server"
        echo "Port $MCP_PORT is in use but process could not be identified"
        return 1
    fi

    # Try graceful stop first
    if graceful_stop "$MCP_PID" "MCP server" 10; then
        echo "✅ MCP server stopped successfully"
        return 0
    fi

    # Force kill if graceful stop failed
    if force_kill "$MCP_PID" "MCP server"; then
        echo "✅ MCP server force-killed successfully"
        return 0
    else
        echo "❌ Failed to stop MCP server"
        echo "Please try stopping the process manually:"
        echo "  kill -9 $MCP_PID"
        return 1
    fi
}

# Function to check status
status() {
    echo "GraphRAG Service Status:"

    # Check Neo4j
    if port_in_use $NEO4J_HTTP_PORT; then
        NEO4J_PID=$(get_pid_for_port $NEO4J_HTTP_PORT)
        echo "Neo4j: ✅ Running (HTTP port: $NEO4J_HTTP_PORT, PID: $NEO4J_PID)"
    else
        echo "Neo4j: ❌ Stopped"
    fi

    # Check API server
    if port_in_use $API_PORT; then
        API_PID=$(get_pid_for_port $API_PORT)
        echo "API Server: ✅ Running (port: $API_PORT, PID: $API_PID)"
    else
        echo "API Server: ❌ Stopped"
    fi

    # Check MCP server
    if port_in_use $MCP_PORT; then
        MCP_PID=$(get_pid_for_port $MCP_PORT)
        echo "MCP Server: ✅ Running (port: $MCP_PORT, PID: $MCP_PID)"
    else
        echo "MCP Server: ❌ Stopped"
    fi
}

# Main command handling
case "$1" in
    start)
        start_neo4j && start_api && start_mcp
        ;;
    stop)
        stop_mcp && stop_api && stop_neo4j
        ;;
    restart)
        stop_mcp && stop_api && stop_neo4j && sleep 2 && start_neo4j && start_api && start_mcp
        ;;
    status)
        status
        ;;
    config)
        print_config
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
        echo "Usage: $0 {start|stop|restart|status|config|start-neo4j|start-api|start-mcp|stop-neo4j|stop-api|stop-mcp}"
        exit 1
        ;;
esac

exit 0
