#!/usr/bin/env python3
from neo4j import GraphDatabase

# Connect to Neo4j
driver = GraphDatabase.driver(
    "bolt://localhost:7688",
    auth=("neo4j", "graphrag")
)

# Test connection
with driver.session() as session:
    result = session.run("MATCH (n) RETURN count(n) as count")
    print(f"Node count: {result.single()['count']}")

# Close the driver
driver.close()