#!/bin/bash
set -e

# Function to wait for Neo4j to be available
wait_for_neo4j() {
  echo "Waiting for Neo4j to be available..."

  # Wait for Neo4j to start accepting connections
  until curl -s http://0.0.0.0:7474 > /dev/null; do
    echo "Neo4j is not yet available, waiting..."
    sleep 2
  done

  echo "Neo4j is now available!"
}

# Start Neo4j in the background
echo "Starting Neo4j..."
/app/neo4j/bin/neo4j start

# Wait for Neo4j to be available
wait_for_neo4j

# Set Neo4j password if it's the first run
if [ ! -f /app/data/.neo4j_initialized ]; then
  echo "Setting Neo4j password..."
  # For Neo4j 5.x
  if [ -f /app/neo4j/bin/neo4j-admin ]; then
    /app/neo4j/bin/neo4j stop || true
    /app/neo4j/bin/neo4j-admin dbms set-initial-password $NEO4J_PASSWORD || /app/neo4j/bin/neo4j-admin set-initial-password $NEO4J_PASSWORD
    /app/neo4j/bin/neo4j start

    # Wait for Neo4j to restart
    wait_for_neo4j
  fi

  # Initialize the database
  echo "Initializing the database..."
  python /app/scripts/initialize_database.py

  # Mark as initialized
  touch /app/data/.neo4j_initialized
fi

# Start the API server in the background
echo "Starting API server..."
cd /app && gunicorn --bind 0.0.0.0:5000 src.api.wsgi:app --daemon

# Start the MPC server in the background
echo "Starting MPC server..."
cd /app && python -m src.mpc.server --host 0.0.0.0 --port 8765 &

# Keep the container running
echo "GraphRAG system is now running!"
echo "- Neo4j Browser: http://localhost:7475"
echo "- API Server: http://localhost:5001"
echo "- MPC Server: ws://localhost:8766"
echo ""
echo "Use the following commands to interact with the system:"
echo "- API: curl http://localhost:5001/health"
echo "- MPC: python scripts/mpc_client_example.py --port 8766"
echo ""
echo "Press Ctrl+C to stop the container"

# Keep the container running
tail -f /dev/null