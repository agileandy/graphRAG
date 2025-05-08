#!/bin/bash

# Stop Neo4j server
# Check for environment variables first
if [ -n "$NEO4J_HOME" ]; then
    echo "Using Neo4j installation from NEO4J_HOME: $NEO4J_HOME"
    "$NEO4J_HOME/bin/neo4j" stop
elif [ -d "$HOME/.local/neo4j" ]; then
    echo "Using Neo4j installation from ~/.local/neo4j"
    "$HOME/.local/neo4j/bin/neo4j" stop
elif [ -d "$(dirname "$0")/../neo4j" ]; then
    echo "Using Neo4j installation from project directory"
    cd "$(dirname "$0")/.."
    ./neo4j/bin/neo4j stop
else
    echo "❌ Neo4j installation not found!"
    echo "Please install Neo4j using: ./scripts/install_neo4j.sh"
    exit 1
fi
