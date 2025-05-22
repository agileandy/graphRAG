#!/bin/bash

# Define patterns for pgrep/pkill
GUNICORN_PATTERN="gunicorn.*src.api.server:app" # Verify this pattern
MPC_SERVER_PATTERN="python.*src.mpc.server"
MCP_SERVER_PATTERN="python.*src.mcp.server"

start_services() {
    echo "Starting GraphRAG services..."
    # Actual commands to start services will be added later.
    # For example:
    # echo "Starting API server (Gunicorn)..."
    # nohup gunicorn --bind 0.0.0.0:$(python -c "from src.config.ports import get_port; print(get_port('api'))") src.api.server:app &> api_server.log &
    # echo "Starting MPC server..."
    # nohup python -m src.mpc.server &> mpc_server.log &
    # echo "Starting MCP server..."
    # nohup python -m src.mcp.server &> mcp_server.log &
    echo "Note: Full start logic needs to be implemented."
}

stop_services() {
    echo "Stopping GraphRAG services..."

    echo "Attempting to stop Gunicorn API server..."
    pkill -f "$GUNICORN_PATTERN"
    sleep 1

    echo "Attempting to stop MPC server..."
    pkill -f "$MPC_SERVER_PATTERN"
    sleep 1

    echo "Attempting to stop MCP server..."
    pkill -f "$MCP_SERVER_PATTERN"
    sleep 1

    echo "Service stop commands issued. Please verify status."
}

status_services() {
    echo "Checking GraphRAG service status..."

    echo -n "Gunicorn API server: "
    pgrep -f "$GUNICORN_PATTERN" > /dev/null && echo "RUNNING" || echo "STOPPED"

    echo -n "MPC server: "
    pgrep -f "$MPC_SERVER_PATTERN" > /dev/null && echo "RUNNING" || echo "STOPPED"

    echo -n "MCP server: "
    pgrep -f "$MCP_SERVER_PATTERN" > /dev/null && echo "RUNNING" || echo "STOPPED"

    echo "Note: This is a basic status check."
}

# Main command handling
if [ -z "$1" ]; then
    echo "Usage: $0 {start|stop|status}"
    exit 1
fi

case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    status)
        status_services
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
esac

exit 0