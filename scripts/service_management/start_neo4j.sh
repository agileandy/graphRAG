#!/bin/bash

# Start Neo4j server
# This script expects the NEO4J_HOME environment variable to be set,
# pointing to the root directory of your Neo4j installation.
# For example: export NEO4J_HOME="/opt/neo4j-community-5.18.1"

if [ -z "$NEO4J_HOME" ]; then
  echo "Error: NEO4J_HOME environment variable is not set."
  echo "Please set NEO4J_HOME to point to your Neo4j installation directory."
  exit 1
fi

NEO4J_BIN="$NEO4J_HOME/bin/neo4j"

if [ ! -x "$NEO4J_BIN" ]; then
  echo "Error: Neo4j executable not found or not executable at $NEO4J_BIN"
  echo "Please check your NEO4J_HOME variable and Neo4j installation."
  exit 1
fi

echo "Starting Neo4j server from $NEO4J_HOME..."
"$NEO4J_BIN" console
