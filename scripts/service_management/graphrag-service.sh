#!/bin/bash
# graphrag-service.sh - Service management script for GraphRAG

# Set default values (will be overridden by .env if available)
DEFAULT_NEO4J_BOLT_PORT=7687
DEFAULT_NEO4J_HTTP_PORT=7474
DEFAULT_NEO4J_HTTPS_PORT=7473
DEFAULT_API_PORT=5001
DEFAULT_MCP_PORT=8767
DEFAULT_BUG_MCP_PORT=5005
DEFAULT_NEO4J_USERNAME="neo4j"
DEFAULT_NEO4J_PASSWORD="graphrag"
DEFAULT_CHROMA_DIR="$HOME/.graphrag/data/chromadb"
DEFAULT_LOG_DIR="$HOME/.graphrag/logs"
DEFAULT_PID_DIR="$HOME/.graphrag/pids"

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
NEO4J_BOLT_PORT=${GRAPHRAG_PORT_NEO4J_BOLT:-$DEFAULT_NEO4J_BOLT_PORT}
NEO4J_HTTP_PORT=${GRAPHRAG_PORT_NEO4J_HTTP:-$DEFAULT_NEO4J_HTTP_PORT}
NEO4J_HTTPS_PORT=${GRAPHRAG_PORT_NEO4J_HTTPS:-$DEFAULT_NEO4J_HTTPS_PORT}
API_PORT=${GRAPHRAG_PORT_API:-$DEFAULT_API_PORT}
MCP_PORT=${GRAPHRAG_PORT_MCP:-$DEFAULT_MCP_PORT}
BUG_MCP_PORT=${GRAPHRAG_PORT_BUG_MCP:-$DEFAULT_BUG_MCP_PORT}
NEO4J_USERNAME=${NEO4J_USERNAME:-$DEFAULT_NEO4J_USERNAME}
NEO4J_PASSWORD=${NEO4J_PASSWORD:-$DEFAULT_NEO4J_PASSWORD}
CHROMA_DIR=${CHROMA_PERSIST_DIRECTORY:-$DEFAULT_CHROMA_DIR}
LOG_DIR=${LOG_DIR:-$DEFAULT_LOG_DIR}
PID_DIR=${PID_DIR:-$DEFAULT_PID_DIR}

# Determine Neo4j installation
if [ -x "/opt/homebrew/bin/neo4j" ]; then
    NEO4J_BIN="/opt/homebrew/bin/neo4j"
elif [ -x "/usr/local/bin/neo4j" ]; then
    NEO4J_BIN="/usr/local/bin/neo4j"
elif [ -x "$HOME/.graphrag/neo4j/bin/neo4j" ]; then
    NEO4J_BIN="$HOME/.graphrag/neo4j/bin/neo4j"
elif [ -n "$NEO4J_HOME" ] && [ -x "$NEO4J_HOME/bin/neo4j" ]; then
    NEO4J_BIN="$NEO4J_HOME/bin/neo4j"
else
    echo "Error: Neo4j installation not found"
    echo "Please install Neo4j or set NEO4J_HOME environment variable"
    exit 1
fi

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

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

# Function to start Neo4j
start_neo4j() {
    echo "Starting Neo4j..."

    # Check if Neo4j is already running
    if port_in_use $NEO4J_HTTP_PORT; then
        echo "Neo4j is already running on port $NEO4J_HTTP_PORT"
        return 0
    fi

    # Clean up stale PID file if it exists
    cleanup_stale_pid "neo4j"

    # Start Neo4j with custom configuration
    NEO4J_CONF="$PROJECT_ROOT" $NEO4J_BIN start

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

    # Clean up stale PID file if it exists
    cleanup_stale_pid "api"

    # Change to project root directory
    cd "$PROJECT_ROOT"

    # Use absolute path to gunicorn
    GUNICORN_PATH="$PROJECT_ROOT/.venv-py312/bin/gunicorn"

    if [ ! -f "$GUNICORN_PATH" ]; then
        echo "❌ gunicorn not found at $GUNICORN_PATH"
        echo "   Make sure gunicorn is installed in the virtual environment."
        return 1
    fi

    # Set environment variables for API server
    export NEO4J_URI="bolt://localhost:$NEO4J_BOLT_PORT"
    export NEO4J_USERNAME="$NEO4J_USERNAME"
    export NEO4J_PASSWORD="$NEO4J_PASSWORD"
    export CHROMA_PERSIST_DIRECTORY="$CHROMA_DIR"

    # Use a 10-minute idle timeout to keep Gunicorn running between requests
    $GUNICORN_PATH \
        --bind 0.0.0.0:$API_PORT \
        --workers 2 \
        --threads 4 \
        --timeout 600 \
        --graceful-timeout 600 \
        --keep-alive 600 \
        --access-logfile "$LOG_DIR/api-access.log" \
        --error-logfile "$LOG_DIR/api-error.log" \
        --log-level info \
        --daemon \
        --pid "$PID_DIR/api.pid" \
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

    # Clean up stale PID file if it exists
    cleanup_stale_pid "mcp"

    # Change to project root directory
    cd "$PROJECT_ROOT"

    # Use absolute path to python
    PYTHON_PATH="$PROJECT_ROOT/.venv-py312/bin/python"

    if [ ! -f "$PYTHON_PATH" ]; then
        echo "❌ Python not found at $PYTHON_PATH"
        echo "   Make sure the virtual environment is set up correctly."
        return 1
    fi

    # Set environment variables for MCP server
    export NEO4J_URI="bolt://localhost:$NEO4J_BOLT_PORT"
    export NEO4J_USERNAME="$NEO4J_USERNAME"
    export NEO4J_PASSWORD="$NEO4J_PASSWORD"
    export CHROMA_PERSIST_DIRECTORY="$CHROMA_DIR"

    # Start MCP server (using src.mcp.server module)
    nohup $PYTHON_PATH -m src.mcp.server --host 0.0.0.0 --port $MCP_PORT > "$LOG_DIR/mcp.log" 2>&1 &
    MCP_PID=$!
    echo $MCP_PID > "$PID_DIR/mcp.pid"

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
            rm -f "$PID_DIR/mcp.pid"
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

# Function to start Bug API server
start_bug_api() {
    echo "Starting Bug API server..."

    # Check if Bug API server is already running
    if port_in_use $BUG_MCP_PORT; then
        echo "Bug API server is already running on port $BUG_MCP_PORT"
        return 0
    fi

    # Clean up stale PID file if it exists
    cleanup_stale_pid "bug_api"

    # Change to project root directory
    cd "$PROJECT_ROOT"

    # Use absolute path to python
    PYTHON_PATH="$PROJECT_ROOT/.venv-py312/bin/python"

    if [ ! -f "$PYTHON_PATH" ]; then
        echo "❌ Python not found at $PYTHON_PATH"
        echo "   Make sure the virtual environment is set up correctly."
        return 1
    fi

    # Start Bug API server
    nohup $PYTHON_PATH bugMCP/bugAPI.py --host 0.0.0.0 --port $BUG_MCP_PORT > "$LOG_DIR/bug_api.log" 2>&1 &
    BUG_API_PID=$!
    echo $BUG_API_PID > "$PID_DIR/bug_api.pid"

    # Wait for Bug API server to start
    echo "Waiting for Bug API server to start..."
    for i in $(seq 1 10); do
        if port_in_use $BUG_MCP_PORT; then
            echo "✅ Bug API server started successfully (PID: $BUG_API_PID)"
            return 0
        fi

        # Check if process is still running
        if ! kill -0 $BUG_API_PID 2>/dev/null; then
            echo "❌ Bug API server process died"
            echo "Check Bug API server logs for errors:"
            echo "  $LOG_DIR/bug_api.log"
            rm -f "$PID_DIR/bug_api.pid"
            return 1
        fi

        sleep 1
        echo -n "."
    done

    echo "❌ Failed to start Bug API server after 10 seconds"
    echo "Check Bug API server logs for errors:"
    echo "  $LOG_DIR/bug_api.log"
    return 1
}

# Function to stop Neo4j
stop_neo4j() {
    echo "Stopping Neo4j..."
    NEO4J_CONF="$PROJECT_ROOT" $NEO4J_BIN stop
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

# Function to stop MCP server
stop_mcp() {
    echo "Stopping MCP server..."
    if [ -f "$PID_DIR/mcp.pid" ]; then
        PID=$(cat "$PID_DIR/mcp.pid")
        kill $PID
        rm -f "$PID_DIR/mcp.pid"
        echo "MCP server stopped."
    else
        # Check if old MPC PID file exists (for backward compatibility)
        if [ -f "$PID_DIR/mpc.pid" ]; then
            PID=$(cat "$PID_DIR/mpc.pid")
            kill $PID
            rm -f "$PID_DIR/mpc.pid"
            echo "MCP server stopped."
        else
            echo "MCP server is not running."
        fi
    fi
}

# Function to stop Bug API server
stop_bug_api() {
    echo "Stopping Bug API server..."
    if [ -f "$PID_DIR/bug_api.pid" ]; then
        PID=$(cat "$PID_DIR/bug_api.pid")
        kill $PID
        rm -f "$PID_DIR/bug_api.pid"
        echo "Bug API server stopped."
    else
        echo "Bug API server is not running."
    fi
}

# Function to check status
status() {
    echo "GraphRAG Service Status:"

    # Check Neo4j
    if port_in_use $NEO4J_HTTP_PORT; then
        echo "Neo4j: Running (port $NEO4J_HTTP_PORT)"
    else
        echo "Neo4j: Stopped"
    fi

    # Check API server
    if port_in_use $API_PORT; then
        PID=$(lsof -ti :$API_PORT 2>/dev/null | head -1)
        if [ ! -z "$PID" ]; then
            echo "API Server: Running (PID: $PID)"
        else
            echo "API Server: Running (port $API_PORT in use, but PID not found)"
        fi

        # Check PID file consistency
        if [ -f "$PID_DIR/api.pid" ]; then
            FILE_PID=$(cat "$PID_DIR/api.pid")
            if [ ! -z "$PID" ] && [ "$FILE_PID" != "$PID" ]; then
                echo "  ⚠️  Warning: PID file ($FILE_PID) doesn't match actual process ($PID)"
            fi
        else
            echo "  ⚠️  Warning: No PID file found for running API server"
        fi
    else
        # Clean up stale PID file
        cleanup_stale_pid "api"
        echo "API Server: Stopped"
    fi

    # Check MCP server
    if port_in_use $MCP_PORT; then
        PID=$(lsof -ti :$MCP_PORT 2>/dev/null | head -1)
        if [ ! -z "$PID" ]; then
            echo "MCP Server: Running (PID: $PID)"
        else
            echo "MCP Server: Running (port $MCP_PORT in use, but PID not found)"
        fi

        # Check PID file consistency
        if [ -f "$PID_DIR/mcp.pid" ]; then
            FILE_PID=$(cat "$PID_DIR/mcp.pid")
            if [ ! -z "$PID" ] && [ "$FILE_PID" != "$PID" ]; then
                echo "  ⚠️  Warning: PID file ($FILE_PID) doesn't match actual process ($PID)"
            fi
        else
            echo "  ⚠️  Warning: No PID file found for running MCP server"
        fi
    else
        # Clean up stale PID file
        cleanup_stale_pid "mcp"
        echo "MCP Server: Stopped"
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
