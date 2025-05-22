#!/bin/bash
# graphrag-service-robust.sh - Consolidated and enhanced service management script for GraphRAG

# --- Configuration ---
# Determine project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Configuration file paths
PROJECT_ENV_FILE="$PROJECT_ROOT/.env"
USER_CONFIG_FILE="$HOME/.graphrag/config.env"

# Default values (can be overridden by config files or environment variables)
DEFAULT_GRAPHRAG_PORT_NEO4J_BOLT=7687
DEFAULT_GRAPHRAG_PORT_NEO4J_HTTP=7474
DEFAULT_GRAPHRAG_PORT_NEO4J_HTTPS=7473 # Though not actively used in start/stop, kept for completeness
DEFAULT_GRAPHRAG_PORT_API=5001
DEFAULT_GRAPHRAG_PORT_MCP=8767
# DEFAULT_GRAPHRAG_PORT_BUG_MCP=5005 # Bug MCP omitted as per instruction

DEFAULT_NEO4J_USERNAME="neo4j"
DEFAULT_NEO4J_PASSWORD="graphrag"

DEFAULT_LOG_DIR="$HOME/.graphrag/logs"
DEFAULT_PID_DIR="$HOME/.graphrag/pids"
DEFAULT_CHROMA_PERSIST_DIRECTORY="$HOME/.graphrag/data/chromadb"
DEFAULT_GRAPHRAG_LOG_LEVEL="INFO"
DEFAULT_VENV_PYTHON_PATH="$PROJECT_ROOT/.venv-py312/bin/python"
DEFAULT_VENV_GUNICORN_PATH="$PROJECT_ROOT/.venv-py312/bin/gunicorn"

# --- Load Configuration ---
CONFIG_SOURCED=false
# Attempt to load from project .env file first
if [ -f "$PROJECT_ENV_FILE" ]; then
    echo "Loading configuration from $PROJECT_ENV_FILE"
    set -a # Automatically export all variables
    source "$PROJECT_ENV_FILE"
    set +a
    CONFIG_SOURCED=true
# If project .env not found, attempt to load from user's ~/.graphrag/config.env
elif [ -f "$USER_CONFIG_FILE" ]; then
    echo "Loading configuration from $USER_CONFIG_FILE"
    set -a
    source "$USER_CONFIG_FILE"
    set +a
    CONFIG_SOURCED=true
else
    echo "No existing configuration file found. Creating default user configuration at $USER_CONFIG_FILE..."
    mkdir -p "$(dirname "$USER_CONFIG_FILE")"
    cat > "$USER_CONFIG_FILE" << EOF
# GraphRAG User Configuration (created by graphrag-service-robust.sh)
# These are default values. For project-specific settings, prefer a .env file in the project root.

# Port Configuration
GRAPHRAG_PORT_NEO4J_BOLT=${DEFAULT_GRAPHRAG_PORT_NEO4J_BOLT}
GRAPHRAG_PORT_NEO4J_HTTP=${DEFAULT_GRAPHRAG_PORT_NEO4J_HTTP}
GRAPHRAG_PORT_NEO4J_HTTPS=${DEFAULT_GRAPHRAG_PORT_NEO4J_HTTPS}
GRAPHRAG_PORT_API=${DEFAULT_GRAPHRAG_PORT_API}
GRAPHRAG_PORT_MCP=${DEFAULT_GRAPHRAG_PORT_MCP}

# Neo4j Credentials
NEO4J_USERNAME=${DEFAULT_NEO4J_USERNAME}
NEO4J_PASSWORD=${DEFAULT_NEO4J_PASSWORD}

# Data and Log Paths
CHROMA_PERSIST_DIRECTORY=${DEFAULT_CHROMA_PERSIST_DIRECTORY}
# LOG_DIR=${DEFAULT_LOG_DIR} # Usually managed by the script itself
# PID_DIR=${DEFAULT_PID_DIR} # Usually managed by the script itself

# Other Configuration
GRAPHRAG_LOG_LEVEL=${DEFAULT_GRAPHRAG_LOG_LEVEL}
EOF
    echo "Default configuration created. Loading it now."
    set -a
    source "$USER_CONFIG_FILE"
    set +a
    CONFIG_SOURCED=true
fi

if ! $CONFIG_SOURCED ; then
    echo "Warning: No configuration file was loaded. Using script defaults."
fi

# Set final configuration values, preferring environment variables, then sourced config, then script defaults
GRAPHRAG_PORT_NEO4J_BOLT=${GRAPHRAG_PORT_NEO4J_BOLT:-$DEFAULT_GRAPHRAG_PORT_NEO4J_BOLT}
GRAPHRAG_PORT_NEO4J_HTTP=${GRAPHRAG_PORT_NEO4J_HTTP:-$DEFAULT_GRAPHRAG_PORT_NEO4J_HTTP}
GRAPHRAG_PORT_NEO4J_HTTPS=${GRAPHRAG_PORT_NEO4J_HTTPS:-$DEFAULT_GRAPHRAG_PORT_NEO4J_HTTPS}
GRAPHRAG_PORT_API=${GRAPHRAG_PORT_API:-$DEFAULT_GRAPHRAG_PORT_API}
GRAPHRAG_PORT_MCP=${GRAPHRAG_PORT_MCP:-$DEFAULT_GRAPHRAG_PORT_MCP}

NEO4J_USERNAME=${NEO4J_USERNAME:-$DEFAULT_NEO4J_USERNAME}
NEO4J_PASSWORD=${NEO4J_PASSWORD:-$DEFAULT_NEO4J_PASSWORD}

LOG_DIR=${LOG_DIR:-$DEFAULT_LOG_DIR}
PID_DIR=${PID_DIR:-$DEFAULT_PID_DIR}
CHROMA_PERSIST_DIRECTORY=${CHROMA_PERSIST_DIRECTORY:-$DEFAULT_CHROMA_PERSIST_DIRECTORY}
GRAPHRAG_LOG_LEVEL=${GRAPHRAG_LOG_LEVEL:-$DEFAULT_GRAPHRAG_LOG_LEVEL}

VENV_PYTHON_PATH=${VENV_PYTHON_PATH:-$DEFAULT_VENV_PYTHON_PATH}
VENV_GUNICORN_PATH=${VENV_GUNICORN_PATH:-$DEFAULT_VENV_GUNICORN_PATH}

# Neo4j URI (constructed based on port)
NEO4J_URI="bolt://localhost:${GRAPHRAG_PORT_NEO4J_BOLT}"

# Determine Neo4j binary path
if [ -n "$NEO4J_BIN_OVERRIDE" ] && [ -x "$NEO4J_BIN_OVERRIDE" ]; then
    NEO4J_BIN="$NEO4J_BIN_OVERRIDE"
elif [ -x "/opt/homebrew/bin/neo4j" ]; then # Common for macOS Homebrew
    NEO4J_BIN="/opt/homebrew/bin/neo4j"
elif [ -x "/usr/local/bin/neo4j" ]; then # Common for Linux or older Homebrew
    NEO4J_BIN="/usr/local/bin/neo4j"
elif [ -n "$NEO4J_HOME" ] && [ -x "$NEO4J_HOME/bin/neo4j" ]; then # If NEO4J_HOME is set
    NEO4J_BIN="$NEO4J_HOME/bin/neo4j"
elif [ -x "$HOME/.graphrag/neo4j/bin/neo4j" ]; then # Local install
     NEO4J_BIN="$HOME/.graphrag/neo4j/bin/neo4j"
else
    echo "Error: Neo4j installation not found."
    echo "Please install Neo4j, set NEO4J_HOME, or set NEO4J_BIN_OVERRIDE environment variable."
    # Do not exit here, allow commands like 'config' or 'help' to run
fi


# --- Create necessary directories ---
mkdir -p "$LOG_DIR" "$PID_DIR" "$CHROMA_PERSIST_DIRECTORY"


# --- Helper Functions ---

# Function to print current configuration
print_config() {
    echo "GraphRAG Service Configuration:"
    echo "  Project Root: $PROJECT_ROOT"
    echo "  Project .env File: $PROJECT_ENV_FILE"
    echo "  User Config File: $USER_CONFIG_FILE"
    echo "  Neo4j Binary: ${NEO4J_BIN:-Not Found}"
    echo "  Neo4j Bolt Port: $GRAPHRAG_PORT_NEO4J_BOLT"
    echo "  Neo4j HTTP Port: $GRAPHRAG_PORT_NEO4J_HTTP"
    echo "  Neo4j URI: $NEO4J_URI"
    echo "  Neo4j Username: $NEO4J_USERNAME"
    echo "  API Port: $GRAPHRAG_PORT_API"
    echo "  MCP Port: $GRAPHRAG_PORT_MCP"
    echo "  ChromaDB Directory: $CHROMA_PERSIST_DIRECTORY"
    echo "  Log Directory: $LOG_DIR"
    echo "  PID Directory: $PID_DIR"
    echo "  Log Level: $GRAPHRAG_LOG_LEVEL"
    echo "  Venv Python: $VENV_PYTHON_PATH"
    echo "  Venv Gunicorn: $VENV_GUNICORN_PATH"
}

# Function to check if a port is in use (more robust)
is_port_in_use() {
    local port=$1
    if command -v nc &>/dev/null; then
        nc -z localhost "$port" &>/dev/null
        return $?
    elif command -v lsof &>/dev/null; then
        lsof -i ":$port" &>/dev/null
        return $?
    elif (echo > "/dev/tcp/localhost/$port") &>/dev/null; then # Bash specific
        return 0 # Successfully connected
    else
        return 1 # All methods failed or port not in use
    fi
}

# Function to get PID of process using a port
get_pid_for_port() {
    local port=$1
    if command -v lsof &>/dev/null; then
        lsof -ti ":$port" 2>/dev/null
    else
        # Fallback or error if lsof is not available
        # For simplicity, we'll rely on PID files more if lsof isn't there.
        echo ""
    fi
}

# Function to check if a process is running
is_process_running() {
    local pid=$1
    if [ -z "$pid" ]; then
        return 1 # False, PID is empty
    fi
    # Check if process exists
    if ps -p "$pid" > /dev/null; then
        return 0 # True, process is running
    else
        return 1 # False, process not running
    fi
}

# Function to clean up stale PID files
cleanup_stale_pid() {
    local service_name=$1
    local pid_file="$PID_DIR/$service_name.pid"

    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file")
        if ! is_process_running "$pid"; then
            echo "Removing stale PID file for $service_name (PID: $pid)"
            rm -f "$pid_file"
        fi
    fi
}

# Function to gracefully stop a process by PID
graceful_stop() {
    local pid=$1
    local service_name=$2
    local timeout=${3:-10} # Default timeout 10 seconds

    if ! is_process_running "$pid"; then
        echo "$service_name (PID: $pid) is not running or PID is invalid."
        return 0 # Consider it stopped
    fi

    echo "Attempting to gracefully stop $service_name (PID: $pid)..."
    kill "$pid"
    for i in $(seq 1 "$timeout"); do
        if ! is_process_running "$pid"; then
            echo "✅ $service_name stopped gracefully."
            return 0
        fi
        sleep 1
        echo -n "."
    done
    echo "" # Newline after dots
    echo "⚠️ $service_name (PID: $pid) did not stop gracefully after $timeout seconds."
    return 1
}

# Function to force kill a process by PID
force_kill() {
    local pid=$1
    local service_name=$2

    if ! is_process_running "$pid"; then
        echo "$service_name (PID: $pid) is not running or PID is invalid. No need to force kill."
        return 0
    fi

    echo "Attempting to force kill $service_name (PID: $pid)..."
    kill -9 "$pid"
    sleep 1 # Give a moment for the OS to process the kill
    if ! is_process_running "$pid"; then
        echo "✅ $service_name force-killed successfully."
        return 0
    else
        echo "❌ Failed to force kill $service_name (PID: $pid)."
        return 1
    fi
}

# --- Service Management Functions ---

# Function to start Neo4j
start_neo4j() {
    if [ -z "$NEO4J_BIN" ] || [ ! -x "$NEO4J_BIN" ]; then
        echo "❌ Neo4j binary not found or not executable at '${NEO4J_BIN}'. Cannot start Neo4j."
        print_config # Show config to help user debug
        return 1
    fi
    echo "Starting Neo4j..."
    if is_port_in_use "$GRAPHRAG_PORT_NEO4J_HTTP"; then
        echo "Neo4j appears to be already running (port $GRAPHRAG_PORT_NEO4J_HTTP is in use)."
        return 0
    fi

    cleanup_stale_pid "neo4j" # Though Neo4j manages its own PID mostly

    # Start Neo4j, setting NEO4J_CONF to project root might help it find neo4j.conf if customized there
    NEO4J_CONF="$PROJECT_ROOT" "$NEO4J_BIN" start
    if [ $? -ne 0 ]; then
        echo "❌ Neo4j start command failed."
        return 1
    fi

    echo "Waiting for Neo4j to start (checking port $GRAPHRAG_PORT_NEO4J_HTTP)..."
    for i in {1..60}; do # Increased timeout for Neo4j
        if curl -s "http://localhost:$GRAPHRAG_PORT_NEO4J_HTTP" > /dev/null; then
            echo "✅ Neo4j started successfully."
            # Neo4j manages its own PID, but we can try to find it if needed for consistency
            # local neo4j_pid=$(get_pid_for_port "$GRAPHRAG_PORT_NEO4J_HTTP")
            # if [ -n "$neo4j_pid" ]; then echo "$neo4j_pid" > "$PID_DIR/neo4j.pid"; fi
            return 0
        fi
        sleep 1
        echo -n "."
    done
    echo ""
    echo "❌ Failed to start Neo4j after 60 seconds (port $GRAPHRAG_PORT_NEO4J_HTTP did not become active)."
    echo "   Check Neo4j logs: \`$NEO4J_BIN console\` or logs in Neo4j's data directory."
    return 1
}

# Function to start API server
start_api() {
    echo "Starting API server..."
    if [ ! -f "$VENV_GUNICORN_PATH" ]; then
        echo "❌ Gunicorn not found at $VENV_GUNICORN_PATH"
        echo "   Make sure Gunicorn is installed in the virtual environment: $PROJECT_ROOT/.venv-py312"
        return 1
    fi
    if is_port_in_use "$GRAPHRAG_PORT_API"; then
        echo "API server appears to be already running (port $GRAPHRAG_PORT_API is in use)."
        return 0
    fi
    if ! is_port_in_use "$GRAPHRAG_PORT_NEO4J_BOLT"; then
        echo "⚠️ Warning: Neo4j does not appear to be running on port $GRAPHRAG_PORT_NEO4J_BOLT. API server might fail."
    fi

    cleanup_stale_pid "api"
    cd "$PROJECT_ROOT" || return 1 # Ensure we are in project root

    # Export necessary environment variables for Gunicorn/Flask app
    export NEO4J_URI="$NEO4J_URI"
    export NEO4J_USERNAME="$NEO4J_USERNAME"
    export NEO4J_PASSWORD="$NEO4J_PASSWORD"
    export CHROMA_PERSIST_DIRECTORY="$CHROMA_PERSIST_DIRECTORY"
    export GRAPHRAG_LOG_LEVEL="$GRAPHRAG_LOG_LEVEL"

    "$VENV_GUNICORN_PATH" \
        --bind "0.0.0.0:$GRAPHRAG_PORT_API" \
        --workers 2 \
        --threads 4 \
        --timeout 300 \
        --graceful-timeout 300 \
        --keep-alive 300 \
        --access-logfile "$LOG_DIR/api-access.log" \
        --error-logfile "$LOG_DIR/api-error.log" \
        --log-level "$GRAPHRAG_LOG_LEVEL" \
        --daemon \
        --pid "$PID_DIR/api.pid" \
        src.api.wsgi:app

    if [ $? -ne 0 ]; then
        echo "❌ Gunicorn command failed to launch."
        return 1
    fi

    echo "Waiting for API server to start (checking port $GRAPHRAG_PORT_API)..."
    for i in {1..30}; do # 30 seconds timeout
        # Check port first, then health endpoint if available
        if is_port_in_use "$GRAPHRAG_PORT_API"; then
             # Attempt to curl health endpoint, but don't fail if it's not immediately ready
            if curl -s "http://localhost:$GRAPHRAG_PORT_API/health" > /dev/null; then
                echo "✅ API server started successfully (health check OK)."
                return 0
            else
                # If health check fails but port is up, give it a few more seconds
                if [ "$i" -gt 25 ]; then # If close to timeout and health still fails
                    echo "✅ API server started (port $GRAPHRAG_PORT_API is up, health check pending/failed)."
                    return 0 # Consider it started if port is up near timeout
                fi
                echo -n "h" # Health check pending
            fi
        fi
        sleep 1
        echo -n "."
    done
    echo ""
    echo "❌ Failed to start API server after 30 seconds (port $GRAPHRAG_PORT_API did not become active or health check failed)."
    echo "   Check API logs: $LOG_DIR/api-error.log"
    return 1
}

# Function to start MCP server
start_mcp() {
    echo "Starting MCP server..."
     if [ ! -f "$VENV_PYTHON_PATH" ]; then
        echo "❌ Python not found at $VENV_PYTHON_PATH"
        echo "   Make sure the virtual environment is set up correctly: $PROJECT_ROOT/.venv-py312"
        return 1
    fi
    if is_port_in_use "$GRAPHRAG_PORT_MCP"; then
        echo "MCP server appears to be already running (port $GRAPHRAG_PORT_MCP is in use)."
        return 0
    fi
    if ! is_port_in_use "$GRAPHRAG_PORT_NEO4J_BOLT"; then
        echo "⚠️ Warning: Neo4j does not appear to be running on port $GRAPHRAG_PORT_NEO4J_BOLT. MCP server might fail."
    fi

    cleanup_stale_pid "mcp"
    cd "$PROJECT_ROOT" || return 1

    export NEO4J_URI="$NEO4J_URI"
    export NEO4J_USERNAME="$NEO4J_USERNAME"
    export NEO4J_PASSWORD="$NEO4J_PASSWORD"
    export CHROMA_PERSIST_DIRECTORY="$CHROMA_PERSIST_DIRECTORY"
    export GRAPHRAG_LOG_LEVEL="$GRAPHRAG_LOG_LEVEL"

    nohup "$VENV_PYTHON_PATH" -m src.mcp.server --host 0.0.0.0 --port "$GRAPHRAG_PORT_MCP" > "$LOG_DIR/mcp.log" 2>&1 &
    MCP_PID=$!
    echo "$MCP_PID" > "$PID_DIR/mcp.pid"

    if ! is_process_running "$MCP_PID"; then
        echo "❌ MCP server failed to launch (process $MCP_PID not found immediately)."
        rm -f "$PID_DIR/mcp.pid"
        return 1
    fi

    echo "Waiting for MCP server to start (checking port $GRAPHRAG_PORT_MCP)..."
    for i in {1..20}; do # 20 seconds timeout
        if is_port_in_use "$GRAPHRAG_PORT_MCP"; then
            echo "✅ MCP server started successfully (PID: $MCP_PID)."
            return 0
        fi
        # Check if process died
        if ! is_process_running "$MCP_PID"; then
            echo "❌ MCP server process (PID: $MCP_PID) died during startup."
            rm -f "$PID_DIR/mcp.pid"
            echo "   Check MCP logs: $LOG_DIR/mcp.log"
            return 1
        fi
        sleep 1
        echo -n "."
    done
    echo ""
    echo "❌ Failed to start MCP server after 20 seconds (port $GRAPHRAG_PORT_MCP did not become active)."
    echo "   Process $MCP_PID might still be starting or stuck. Check MCP logs: $LOG_DIR/mcp.log"
    return 1
}

# Function to stop Neo4j
stop_neo4j() {
    if [ -z "$NEO4J_BIN" ] || [ ! -x "$NEO4J_BIN" ]; then
        echo "❌ Neo4j binary not found or not executable. Cannot stop Neo4j."
        return 1
    fi
    echo "Stopping Neo4j..."
    if ! is_port_in_use "$GRAPHRAG_PORT_NEO4J_HTTP" && ! is_port_in_use "$GRAPHRAG_PORT_NEO4J_BOLT"; then
        echo "Neo4j does not appear to be running (ports $GRAPHRAG_PORT_NEO4J_HTTP, $GRAPHRAG_PORT_NEO4J_BOLT not in use)."
        cleanup_stale_pid "neo4j" # Clean if any, though Neo4j manages its own
        return 0
    fi

    NEO4J_CONF="$PROJECT_ROOT" "$NEO4J_BIN" stop
    # Neo4j stop command can take a while. We'll check ports.
    echo "Waiting for Neo4j to stop..."
    for i in {1..30}; do
        if ! is_port_in_use "$GRAPHRAG_PORT_NEO4J_HTTP" && ! is_port_in_use "$GRAPHRAG_PORT_NEO4J_BOLT"; then
            echo "✅ Neo4j stopped successfully."
            cleanup_stale_pid "neo4j"
            return 0
        fi
        sleep 1
        echo -n "."
    done
    echo ""
    echo "⚠️ Neo4j did not stop gracefully after 30 seconds (ports still in use)."
    echo "   Attempting to find and force kill Neo4j processes..."
    local http_pid
    http_pid=$(get_pid_for_port "$GRAPHRAG_PORT_NEO4J_HTTP")
    local bolt_pid
    bolt_pid=$(get_pid_for_port "$GRAPHRAG_PORT_NEO4J_BOLT")

    if [ -n "$http_pid" ]; then force_kill "$http_pid" "Neo4j (HTTP Port)"; fi
    if [ -n "$bolt_pid" ] && [ "$bolt_pid" != "$http_pid" ]; then force_kill "$bolt_pid" "Neo4j (Bolt Port)"; fi

    sleep 2 # Give a moment for kill to take effect
    if ! is_port_in_use "$GRAPHRAG_PORT_NEO4J_HTTP" && ! is_port_in_use "$GRAPHRAG_PORT_NEO4J_BOLT"; then
        echo "✅ Neo4j force-killed successfully."
        cleanup_stale_pid "neo4j"
        return 0
    else
        echo "❌ Failed to stop Neo4j even with force kill. Manual intervention may be required."
        return 1
    fi
}

# Function to stop API server
stop_api() {
    echo "Stopping API server..."
    local pid_file="$PID_DIR/api.pid"
    local api_pid

    if [ -f "$pid_file" ]; then
        api_pid=$(cat "$pid_file")
        if ! is_process_running "$api_pid"; then
            echo "API server PID file found (PID: $api_pid), but process is not running."
            if is_port_in_use "$GRAPHRAG_PORT_API"; then
                 echo "Port $GRAPHRAG_PORT_API is still in use by another process. Trying to find and kill it."
                 api_pid=$(get_pid_for_port "$GRAPHRAG_PORT_API") # Try to get current PID from port
            else
                echo "API server is not running (port $GRAPHRAG_PORT_API is free)."
                rm -f "$pid_file"
                return 0
            fi
        fi
    elif is_port_in_use "$GRAPHRAG_PORT_API"; then
        echo "API server PID file not found, but port $GRAPHRAG_PORT_API is in use."
        api_pid=$(get_pid_for_port "$GRAPHRAG_PORT_API")
        if [ -z "$api_pid" ]; then
            echo "❌ Could not identify process using port $GRAPHRAG_PORT_API. Manual intervention required."
            return 1
        fi
        echo "Found process $api_pid using port $GRAPHRAG_PORT_API."
    else
        echo "API server is not running (PID file not found and port $GRAPHRAG_PORT_API is free)."
        return 0
    fi

    if [ -n "$api_pid" ]; then
        if graceful_stop "$api_pid" "API server"; then
            rm -f "$pid_file" # Clean up PID file on successful graceful stop
        else
            if force_kill "$api_pid" "API server"; then
                 rm -f "$pid_file" # Clean up PID file on successful force kill
            else
                echo "❌ Failed to stop API server (PID: $api_pid)."
                return 1
            fi
        fi
    fi

    # Final check on port
    if is_port_in_use "$GRAPHRAG_PORT_API"; then
        echo "❌ API Server port $GRAPHRAG_PORT_API is still in use after stop attempts."
        return 1
    else
        echo "✅ API server stopped successfully."
        rm -f "$pid_file" # Ensure PID file is removed
        return 0
    fi
}

# Function to stop MCP server
stop_mcp() {
    echo "Stopping MCP server..."
    local pid_file="$PID_DIR/mcp.pid"
    local mcp_pid

    if [ -f "$pid_file" ]; then
        mcp_pid=$(cat "$pid_file")
        if ! is_process_running "$mcp_pid"; then
            echo "MCP server PID file found (PID: $mcp_pid), but process is not running."
             if is_port_in_use "$GRAPHRAG_PORT_MCP"; then
                 echo "Port $GRAPHRAG_PORT_MCP is still in use by another process. Trying to find and kill it."
                 mcp_pid=$(get_pid_for_port "$GRAPHRAG_PORT_MCP")
            else
                echo "MCP server is not running (port $GRAPHRAG_PORT_MCP is free)."
                rm -f "$pid_file"
                return 0
            fi
        fi
    elif is_port_in_use "$GRAPHRAG_PORT_MCP"; then
        echo "MCP server PID file not found, but port $GRAPHRAG_PORT_MCP is in use."
        mcp_pid=$(get_pid_for_port "$GRAPHRAG_PORT_MCP")
        if [ -z "$mcp_pid" ]; then
            echo "❌ Could not identify process using port $GRAPHRAG_PORT_MCP. Manual intervention required."
            return 1
        fi
        echo "Found process $mcp_pid using port $GRAPHRAG_PORT_MCP."
    else
        echo "MCP server is not running (PID file not found and port $GRAPHRAG_PORT_MCP is free)."
        return 0
    fi

    if [ -n "$mcp_pid" ]; then
        if graceful_stop "$mcp_pid" "MCP server"; then
            rm -f "$pid_file"
        else
            if force_kill "$mcp_pid" "MCP server"; then
                rm -f "$pid_file"
            else
                echo "❌ Failed to stop MCP server (PID: $mcp_pid)."
                return 1
            fi
        fi
    fi

    if is_port_in_use "$GRAPHRAG_PORT_MCP"; then
        echo "❌ MCP Server port $GRAPHRAG_PORT_MCP is still in use after stop attempts."
        return 1
    else
        echo "✅ MCP server stopped successfully."
        rm -f "$pid_file"
        return 0
    fi
}

# Function to check status of all services
status() {
    echo "GraphRAG Service Status:"
    local overall_status=0 # 0 for all good, 1 for some issues

    # Check Neo4j
    echo -n "Neo4j: "
    if is_port_in_use "$GRAPHRAG_PORT_NEO4J_HTTP"; then
        echo "✅ Running (port $GRAPHRAG_PORT_NEO4J_HTTP)"
    else
        echo "❌ Stopped"
        overall_status=1
    fi
    cleanup_stale_pid "neo4j" # Not strictly necessary as Neo4j manages its own PID

    # Check API Server
    echo -n "API Server: "
    local api_pid_file="$PID_DIR/api.pid"
    if is_port_in_use "$GRAPHRAG_PORT_API"; then
        if [ -f "$api_pid_file" ]; then
            local pid
            pid=$(cat "$api_pid_file")
            if is_process_running "$pid"; then
                echo "✅ Running (port $GRAPHRAG_PORT_API, PID: $pid)"
            else
                echo "⚠️ Running (port $GRAPHRAG_PORT_API), but PID $pid from $api_pid_file is stale."
                overall_status=1
            fi
        else
            echo "✅ Running (port $GRAPHRAG_PORT_API), PID file not found."
        fi
    else
        echo "❌ Stopped"
        overall_status=1
    fi
    cleanup_stale_pid "api"

    # Check MCP Server
    echo -n "MCP Server: "
    local mcp_pid_file="$PID_DIR/mcp.pid"
    if is_port_in_use "$GRAPHRAG_PORT_MCP"; then
        if [ -f "$mcp_pid_file" ]; then
            local pid
            pid=$(cat "$mcp_pid_file")
            if is_process_running "$pid"; then
                echo "✅ Running (port $GRAPHRAG_PORT_MCP, PID: $pid)"
            else
                echo "⚠️ Running (port $GRAPHRAG_PORT_MCP), but PID $pid from $mcp_pid_file is stale."
                overall_status=1
            fi
        else
            echo "✅ Running (port $GRAPHRAG_PORT_MCP), PID file not found."
        fi
    else
        echo "❌ Stopped"
        overall_status=1
    fi
    cleanup_stale_pid "mcp"

    return $overall_status
}

# Function to force kill all core services
force_kill_all() {
    echo "Force killing all GraphRAG core services..."
    local neo4j_http_pid mcp_pid api_pid neo4j_bolt_pid

    neo4j_http_pid=$(get_pid_for_port "$GRAPHRAG_PORT_NEO4J_HTTP")
    neo4j_bolt_pid=$(get_pid_for_port "$GRAPHRAG_PORT_NEO4J_BOLT")
    api_pid=$(get_pid_for_port "$GRAPHRAG_PORT_API")
    mcp_pid=$(get_pid_for_port "$GRAPHRAG_PORT_MCP")

    if [ -n "$mcp_pid" ]; then force_kill "$mcp_pid" "MCP Server"; rm -f "$PID_DIR/mcp.pid"; fi
    if [ -n "$api_pid" ]; then force_kill "$api_pid" "API Server"; rm -f "$PID_DIR/api.pid"; fi
    if [ -n "$neo4j_http_pid" ]; then force_kill "$neo4j_http_pid" "Neo4j (HTTP)"; fi
    if [ -n "$neo4j_bolt_pid" ] && [ "$neo4j_bolt_pid" != "$neo4j_http_pid" ]; then force_kill "$neo4j_bolt_pid" "Neo4j (Bolt)"; fi

    # Also run Neo4j's own stop command just in case it does more cleanup
    if [ -n "$NEO4J_BIN" ] && [ -x "$NEO4J_BIN" ]; then
      "$NEO4J_BIN" stop &>/dev/null # Suppress output as we are force killing
    fi

    echo "Force kill attempts completed. Verifying..."
    status
}

# --- Main Command Handling ---
usage() {
    echo "Usage: $0 {start|stop|restart|status|config|force-kill-all|start-neo4j|stop-neo4j|start-api|stop-api|start-mcp|stop-mcp}"
    exit 1
}

if [ "$#" -eq 0 ]; then
    usage
fi

case "$1" in
    start)
        start_neo4j && start_api && start_mcp
        status
        ;;
    stop)
        stop_mcp
        stop_api
        stop_neo4j
        status
        ;;
    restart)
        echo "Restarting all services..."
        stop_mcp
        stop_api
        stop_neo4j
        echo "Waiting a few seconds before starting..."
        sleep 3
        start_neo4j && start_api && start_mcp
        status
        ;;
    status)
        status
        ;;
    config)
        print_config
        ;;
    force-kill-all)
        force_kill_all
        ;;
    start-neo4j)
        start_neo4j
        ;;
    stop-neo4j)
        stop_neo4j
        ;;
    start-api)
        start_api
        ;;
    stop-api)
        stop_api
        ;;
    start-mcp)
        start_mcp
        ;;
    stop-mcp)
        stop_mcp
        ;;
    *)
        usage
        ;;
esac

exit $?
