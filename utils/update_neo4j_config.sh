#!/bin/bash

# Script to update Neo4j configuration

# Stop Neo4j if it's running
echo "Stopping Neo4j..."
cd "$(dirname "$0")/.."
./neo4j/bin/neo4j stop

# Wait a moment for Neo4j to fully stop
sleep 5

# Update configuration
echo "Updating Neo4j configuration..."
CONFIG_FILE="./neo4j/conf/neo4j.conf"

# Enable authentication
sed -i '' 's/#dbms.security.auth_enabled=false/dbms.security.auth_enabled=true/g' "$CONFIG_FILE"

# Set listen address
sed -i '' 's/#server.default_listen_address=0.0.0.0/server.default_listen_address=0.0.0.0/g' "$CONFIG_FILE"

# Enable Bolt connector
sed -i '' 's/#server.bolt.enabled=true/server.bolt.enabled=true/g' "$CONFIG_FILE"
sed -i '' 's/#server.bolt.listen_address=:7687/server.bolt.listen_address=0.0.0.0:7687/g' "$CONFIG_FILE"

# Enable HTTP connector
sed -i '' 's/#server.http.enabled=true/server.http.enabled=true/g' "$CONFIG_FILE"
sed -i '' 's/#server.http.listen_address=:7474/server.http.listen_address=0.0.0.0:7474/g' "$CONFIG_FILE"

echo "Neo4j configuration updated!"
echo "You can now start Neo4j again with: ./scripts/start_neo4j.sh"