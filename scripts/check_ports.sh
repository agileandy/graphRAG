#!/bin/bash

# Script to check if ports are available before starting the Docker container

# Define the ports to check
PORTS=(7475 7688 5001 8766)

# Check if each port is available
for PORT in "${PORTS[@]}"; do
    if lsof -i ":$PORT" > /dev/null; then
        echo "❌ Port $PORT is already in use."
        echo "Please stop the process using this port or change the port in docker-compose.yml."
        exit 1
    else
        echo "✅ Port $PORT is available."
    fi
done

echo "All ports are available. You can proceed with starting the Docker container."
exit 0