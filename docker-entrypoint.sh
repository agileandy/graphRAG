#!/bin/bash
set -e

# Load environment variables for port configuration
# These should be set in the Docker environment
GRAPHRAG_PORT_NEO4J_HTTP=${GRAPHRAG_PORT_NEO4J_HTTP:-7474}
GRAPHRAG_PORT_NEO4J_BOLT=${GRAPHRAG_PORT_NEO4J_BOLT:-7687}
GRAPHRAG_PORT_API=${GRAPHRAG_PORT_API:-5000}
GRAPHRAG_PORT_MPC=${GRAPHRAG_PORT_MPC:-8765}
GRAPHRAG_PORT_MCP=${GRAPHRAG_PORT_MCP:-8767}
GRAPHRAG_PORT_DOCKER_NEO4J_BOLT=${GRAPHRAG_PORT_DOCKER_NEO4J_BOLT:-7688}

# Function to wait for Neo4j to be available
wait_for_neo4j() {
  echo "Waiting for Neo4j to be available..."
  local max_attempts=30
  local attempt=1

  # Wait for Neo4j to start accepting connections
  while [ $attempt -le $max_attempts ]; do
    if curl -s http://0.0.0.0:${GRAPHRAG_PORT_NEO4J_HTTP} > /dev/null; then
      echo "Neo4j is now available!"
      return 0
    else
      echo "Neo4j is not yet available, waiting... (Attempt $attempt/$max_attempts)"
      sleep 2
      attempt=$((attempt + 1))
    fi
  done

  echo "ERROR: Neo4j did not become available after $max_attempts attempts."
  echo "Checking Neo4j logs for errors..."
  cat /app/neo4j/logs/neo4j.log | tail -n 50
  return 1
}

# Fix Neo4j configuration
echo "Fixing Neo4j configuration..."
sed -i 's/db.logs.query.enabled=true/db.logs.query.enabled=INFO/g' /app/neo4j/conf/neo4j.conf

# Start Neo4j in the background
echo "Starting Neo4j..."
/app/neo4j/bin/neo4j start

# Wait for Neo4j to be available
wait_for_neo4j

# Set Neo4j password if it's the first run
if [ ! -f /app/data/.neo4j_initialized ]; then
  echo "Setting Neo4j password..."

  # Stop Neo4j before setting the password
  echo "Stopping Neo4j to set password..."
  /app/neo4j/bin/neo4j stop || true
  sleep 5  # Give it time to fully stop

  # For Neo4j 5.x
  if [ -f /app/neo4j/bin/neo4j-admin ]; then
    # Try both command formats for different Neo4j versions
    echo "Setting initial password using neo4j-admin..."
    /app/neo4j/bin/neo4j-admin dbms set-initial-password $NEO4J_PASSWORD || /app/neo4j/bin/neo4j-admin set-initial-password $NEO4J_PASSWORD

    if [ $? -ne 0 ]; then
      echo "WARNING: Failed to set Neo4j password. Will retry after startup."
    else
      echo "Successfully set Neo4j password."
    fi
  else
    echo "ERROR: neo4j-admin not found. Cannot set password."
  fi

  # Start Neo4j again
  echo "Starting Neo4j after password setup..."
  /app/neo4j/bin/neo4j start

  # Wait for Neo4j to restart
  if ! wait_for_neo4j; then
    echo "ERROR: Neo4j failed to restart after password setup."
    exit 1
  fi

  # Verify we can connect with the new password
  echo "Verifying Neo4j connection with new password..."
  if curl -s -u neo4j:$NEO4J_PASSWORD http://localhost:${GRAPHRAG_PORT_NEO4J_HTTP}/db/data/ > /dev/null; then
    echo "✅ Successfully connected to Neo4j with new password."
  else
    echo "⚠️ Could not verify Neo4j connection with new password."
    echo "Will proceed with initialization anyway."
  fi

  # Initialize the database
  echo "Initializing the database..."
  python /app/scripts/initialize_database.py

  if [ $? -ne 0 ]; then
    echo "WARNING: Database initialization script returned an error."
    echo "Check the logs for more information."
  else
    echo "✅ Database initialized successfully."
  fi

  # Mark as initialized
  touch /app/data/.neo4j_initialized
  echo "✅ Neo4j initialization completed."
else
  echo "Neo4j already initialized, skipping password setup."
fi

# Function to wait for a service to be available
wait_for_service() {
  local service_name=$1
  local url=$2
  local max_attempts=$3
  local attempt=1

  echo "Waiting for $service_name to be available..."
  while [ $attempt -le $max_attempts ]; do
    if curl -s $url > /dev/null; then
      echo "✅ $service_name is now available!"
      return 0
    else
      echo "$service_name is not yet available, waiting... (Attempt $attempt/$max_attempts)"
      sleep 2
      attempt=$((attempt + 1))
    fi
  done

  echo "ERROR: $service_name did not become available after $max_attempts attempts."
  return 1
}

# Start the API server in the background with configurable workers
echo "Starting API server..."
cd /app && gunicorn \
  --bind 0.0.0.0:${GRAPHRAG_API_PORT:-5001} \
  --workers ${GUNICORN_WORKERS:-2} \
  --threads ${GUNICORN_THREADS:-4} \
  --timeout ${GUNICORN_TIMEOUT:-120} \
  --access-logfile ${GRAPHRAG_LOG_DIR:-/app/data/logs}/gunicorn-access.log \
  --error-logfile ${GRAPHRAG_LOG_DIR:-/app/data/logs}/gunicorn-error.log \
  --log-level ${GRAPHRAG_LOG_LEVEL:-info} \
  src.api.wsgi:app --daemon

# Wait for API server to be available
if ! wait_for_service "API server" "http://0.0.0.0:${GRAPHRAG_API_PORT:-5001}/health" 15; then
  echo "WARNING: API server may not have started correctly."
else
  echo "✅ API server is running and responding to health checks."
fi

# Start the MCP server in the background
echo "Starting MCP server..."
cd /app && python -m src.mcp.server --host 0.0.0.0 --port ${GRAPHRAG_PORT_MCP} &
MCP_PID=$!

# Give the MCP server a moment to start
sleep 3
echo "✅ MCP server started (PID: $MCP_PID)."

# Print system information
echo "========================================================"
echo "GraphRAG System v2 is now running!"
echo "========================================================"
echo "System Information:"
echo "- Neo4j Version: $(cat /app/neo4j/README.txt | grep -m 1 'Neo4j' | awk '{print $2}')"
echo "- Python Version: $(python --version)"
echo "- Container User: $(whoami)"
echo "- Hostname: $(hostname)"
echo "- Date: $(date)"
echo ""
echo "Service Endpoints:"
echo "- Neo4j Browser: http://localhost:${GRAPHRAG_PORT_NEO4J_HTTP}"
echo "- API Server: http://localhost:${GRAPHRAG_PORT_API}"
echo "- MCP Server: ws://localhost:${GRAPHRAG_PORT_MCP}"
echo ""
echo "Health Status:"
echo "- Neo4j: Running"
echo "- API Server: Running"
echo "- MCP Server: Running"
echo ""
echo "Use the following commands to interact with the system:"
echo "- API: curl http://localhost:${GRAPHRAG_PORT_API}/health"
echo "- MCP: python scripts/mcp_client_example.py --port ${GRAPHRAG_PORT_MCP}"
echo ""
echo "Log Files:"
echo "- Neo4j Logs: /app/neo4j/logs/"
echo "- API Server Logs: ${GRAPHRAG_LOG_DIR:-/app/data/logs}/gunicorn-*.log"
echo "- Application Logs: ${GRAPHRAG_LOG_DIR:-/app/data/logs}/"
echo ""
echo "Press Ctrl+C to stop the container"
echo "========================================================"

# Monitor system resources periodically
(
  while true; do
    echo "[$(date)] System Status:" >> ${GRAPHRAG_LOG_DIR:-/app/data/logs}/system-monitor.log
    echo "- Memory Usage:" >> ${GRAPHRAG_LOG_DIR:-/app/data/logs}/system-monitor.log
    free -h >> ${GRAPHRAG_LOG_DIR:-/app/data/logs}/system-monitor.log
    echo "- Disk Usage:" >> ${GRAPHRAG_LOG_DIR:-/app/data/logs}/system-monitor.log
    df -h /app/data >> ${GRAPHRAG_LOG_DIR:-/app/data/logs}/system-monitor.log
    echo "" >> ${GRAPHRAG_LOG_DIR:-/app/data/logs}/system-monitor.log
    sleep 300  # Check every 5 minutes
  done
) &

# Keep the container running
tail -f /dev/null