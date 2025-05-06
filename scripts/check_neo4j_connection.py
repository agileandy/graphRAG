"""
Script to check Neo4j connection with explicit credentials.
"""
import sys
import os
from neo4j import GraphDatabase

def check_connection(uri, username, password):
    """
    Check Neo4j connection with given credentials.
    """
    print(f"Checking Neo4j connection to {uri} with username '{username}'...")
    
    try:
        # Try to connect with the provided credentials
        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session() as session:
            result = session.run("RETURN 1 AS result")
            value = result.single()["result"]
            print(f"✅ Connection successful! Query returned: {value}")
        
        driver.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    # Default values
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "graphrag"
    
    # Allow command-line overrides
    if len(sys.argv) > 1:
        uri = sys.argv[1]
    if len(sys.argv) > 2:
        username = sys.argv[2]
    if len(sys.argv) > 3:
        password = sys.argv[3]
    
    check_connection(uri, username, password)