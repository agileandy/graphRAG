#!/bin/bash

# Script to start the GraphRAG MPC server

# Change to the project root directory
cd "$(dirname "$0")/.."

# Start the MPC server
echo "Starting GraphRAG MPC server..."
python -m src.mpc.server "$@"