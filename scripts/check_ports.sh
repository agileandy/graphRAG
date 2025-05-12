#!/bin/bash

# Script to check if required ports are available

# Change to the project root directory
cd "$(dirname "$0")/.."

# Load environment variables from .env file
if [ -f .env ]; then
    source .env
fi

# Get port values from environment variables or use defaults
NEO4J_HTTP_PORT=${GRAPHRAG_PORT_NEO4J_HTTP:-7474}
NEO4J_BOLT_PORT=${GRAPHRAG_PORT_NEO4J_BOLT:-7687}
DOCKER_NEO4J_BOLT_PORT=${GRAPHRAG_PORT_DOCKER_NEO4J_BOLT:-7688}
API_PORT=${GRAPHRAG_PORT_API:-5001}
MPC_PORT=${GRAPHRAG_PORT_MPC:-8765}
MCP_PORT=${GRAPHRAG_PORT_MCP:-8767}
BUG_MCP_PORT=${GRAPHRAG_PORT_BUG_MCP:-5005}

# Function to check if a port is in use
check_port() {
    local port=$1
    local service=$2
    
    # Check if the port is in use
    if lsof -i :$port -sTCP:LISTEN > /dev/null 2>&1; then
        echo "❌ Port $port ($service) is already in use."
        return 1
    else
        echo "✅ Port $port ($service) is available."
        return 0
    fi
}

# Check all required ports
echo "Checking if required ports are available..."
check_port $NEO4J_HTTP_PORT "Neo4j HTTP"
check_port $NEO4J_BOLT_PORT "Neo4j Bolt"
check_port $DOCKER_NEO4J_BOLT_PORT "Docker Neo4j Bolt"
check_port $API_PORT "API"
check_port $MPC_PORT "MPC"
check_port $MCP_PORT "MCP"
check_port $BUG_MCP_PORT "Bug MCP"

# Check if any port check failed
if [ $? -ne 0 ]; then
    echo "❌ Some ports are already in use. Please resolve the conflicts before proceeding."
    exit 1
else
    echo "✅ All required ports are available."
    exit 0
fi