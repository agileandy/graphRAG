#!/bin/bash

# Start Neo4j server
cd "$(dirname "$0")/.."
./neo4j/bin/neo4j console
