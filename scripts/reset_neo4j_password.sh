#!/bin/bash

# Script to reset Neo4j password

# Stop Neo4j if it's running
echo "Stopping Neo4j..."
cd "$(dirname "$0")/.."
./neo4j/bin/neo4j stop

# Wait a moment for Neo4j to fully stop
sleep 5

# Set the new password
echo "Resetting password..."
./neo4j/bin/neo4j-admin dbms set-initial-password graphrag

echo "Password has been reset to 'graphrag'"
echo "You can now start Neo4j again with: ./scripts/start_neo4j.sh"