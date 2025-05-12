#!/bin/bash
# Service script for the Bug Tracking MCP server

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Activate the virtual environment
source "$PROJECT_ROOT/.venv-py312/bin/activate"

# Default values
HOST="localhost"
PORT=5005
LOG_LEVEL="INFO"
ACTION="start"

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        start|stop|status|restart)
            ACTION="$1"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to start the server
start_server() {
    echo "Starting Bug Tracking MCP server on $HOST:$PORT..."
    
    # Check if the server is already running
    if pgrep -f "python.*bugMCP_mcp.py" > /dev/null; then
        echo "Server is already running."
        return
    fi
    
    # Start the server in the background
    nohup python "$PROJECT_ROOT/bugMCP/bugMCP_mcp.py" \
        --host "$HOST" \
        --port "$PORT" \
        --log-level "$LOG_LEVEL" \
        > "$PROJECT_ROOT/bugMCP/bugmcp.log" 2>&1 &
    
    # Wait a moment for the server to start
    sleep 2
    
    # Check if the server started successfully
    if pgrep -f "python.*bugMCP_mcp.py" > /dev/null; then
        echo "Server started successfully."
    else
        echo "Failed to start server. Check the log file for details."
        exit 1
    fi
}

# Function to stop the server
stop_server() {
    echo "Stopping Bug Tracking MCP server..."
    
    # Find and kill the server process
    pkill -f "python.*bugMCP_mcp.py"
    
    # Wait a moment for the server to stop
    sleep 2
    
    # Check if the server stopped successfully
    if pgrep -f "python.*bugMCP_mcp.py" > /dev/null; then
        echo "Failed to stop server. Trying force kill..."
        pkill -9 -f "python.*bugMCP_mcp.py"
        sleep 1
        
        if pgrep -f "python.*bugMCP_mcp.py" > /dev/null; then
            echo "Failed to force kill server."
            exit 1
        else
            echo "Server force killed."
        fi
    else
        echo "Server stopped successfully."
    fi
}

# Function to check the server status
check_status() {
    if pgrep -f "python.*bugMCP_mcp.py" > /dev/null; then
        echo "Bug Tracking MCP server is running."
        
        # Get the process ID
        PID=$(pgrep -f "python.*bugMCP_mcp.py")
        echo "Process ID: $PID"
        
        # Check if the server is listening on the expected port
        if netstat -tuln | grep -q ":$PORT "; then
            echo "Server is listening on port $PORT."
        else
            echo "Warning: Server is running but not listening on port $PORT."
        fi
    else
        echo "Bug Tracking MCP server is not running."
    fi
}

# Perform the requested action
case "$ACTION" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        start_server
        ;;
    status)
        check_status
        ;;
    *)
        echo "Usage: $0 [start|stop|restart|status] [--host HOST] [--port PORT] [--log-level LEVEL]"
        exit 1
        ;;
esac

exit 0