#!/usr/bin/env python3
import sys
import os
from neo4j import GraphDatabase

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_port

# Get Neo4j port from centralized configuration
docker_neo4j_port = get_port('docker_neo4j_bolt')

# Connect to Neo4j
driver = GraphDatabase.driver(
    f"bolt://localhost:{docker_neo4j_port}",
    auth=("neo4j", "graphrag")
)

# Test connection
with driver.session() as session:
    result = session.run("MATCH (n) RETURN count(n) as count")
    print(f"Node count: {result.single()['count']}")

# Close the driver
driver.close()