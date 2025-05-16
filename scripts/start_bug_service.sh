#!/bin/bash
# Simple script to start the bug tracking service and keep it running

# Determine project root directory
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$HOME/.graphrag/logs"
PID_DIR="$HOME/.graphrag/pids"

# Create necessary directories
mkdir -p "$LOG_DIR" "$PID_DIR"

# Default port
BUG_API_PORT=5005

# Function to check if a port is in use
port_in_use() {
    local port=$1
    nc -z localhost $port >/dev/null 2>&1
    return $?
}

# Check if the bug API is already running
if port_in_use $BUG_API_PORT; then
    echo "Bug API is already running on port $BUG_API_PORT"
    exit 0
fi

# Use absolute path to python
PYTHON_PATH="$PROJECT_ROOT/.venv-py312/bin/python"

if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Python not found at $PYTHON_PATH"
    echo "   Make sure the virtual environment is set up correctly."
    exit 1
fi

# Start the bug API server
echo "Starting Bug API server on port $BUG_API_PORT..."
cd "$PROJECT_ROOT"
nohup $PYTHON_PATH bugMCP/bugAPI.py --host 0.0.0.0 --port $BUG_API_PORT > "$LOG_DIR/bug_api.log" 2>&1 &
BUG_API_PID=$!
echo $BUG_API_PID > "$PID_DIR/bug_api.pid"

# Wait for the server to start
echo "Waiting for Bug API server to start..."
for i in $(seq 1 10); do
    if port_in_use $BUG_API_PORT; then
        echo "✅ Bug API server started successfully (PID: $BUG_API_PID)"
        echo "You can now use the bug tracking system with:"
        echo "  python bugMCP/bugAPI_client.py list"
        echo "  python bugMCP/bugAPI_client.py add --description \"Bug description\" --cause \"Bug cause\""
        exit 0
    fi
    
    # Check if process is still running
    if ! kill -0 $BUG_API_PID 2>/dev/null; then
        echo "❌ Bug API server process died"
        echo "Check Bug API server logs for errors:"
        echo "  $LOG_DIR/bug_api.log"
        rm -f "$PID_DIR/bug_api.pid"
        exit 1
    fi
    
    sleep 1
    echo -n "."
done

echo "❌ Failed to start Bug API server after 10 seconds"
echo "Check Bug API server logs for errors:"
echo "  $LOG_DIR/bug_api.log"
exit 1
