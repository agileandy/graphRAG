# Local Deployment Guide for GraphRAG

This guide explains how to run the GraphRAG system locally on macOS without Docker.

## Prerequisites

- macOS 10.15 or higher
- Python 3.8 or higher
- Neo4j 5.x (can be installed via the provided scripts)
- At least 4GB of RAM and 10GB of disk space

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/graphRAG.git
cd graphRAG
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Neo4j

You can download Neo4j from the [official website](https://neo4j.com/download-center/) or use the following command:

```bash
# Download Neo4j
mkdir -p ~/.graphrag/neo4j
curl -L -o /tmp/neo4j.tar.gz https://dist.neo4j.org/neo4j-community-5.18.1-unix.tar.gz
tar -xzf /tmp/neo4j.tar.gz -C ~/.graphrag/neo4j --strip-components=1
rm /tmp/neo4j.tar.gz

# Configure Neo4j
sed -i '' 's/#server.default_listen_address=0.0.0.0/server.default_listen_address=0.0.0.0/g' ~/.graphrag/neo4j/conf/neo4j.conf
sed -i '' 's/#dbms.memory.heap.initial_size=512m/dbms.memory.heap.initial_size=1024m/g' ~/.graphrag/neo4j/conf/neo4j.conf
sed -i '' 's/#dbms.memory.heap.max_size=512m/dbms.memory.heap.max_size=2048m/g' ~/.graphrag/neo4j/conf/neo4j.conf
sed -i '' 's/#dbms.memory.pagecache.size=10g/dbms.memory.pagecache.size=1024m/g' ~/.graphrag/neo4j/conf/neo4j.conf
echo "dbms.security.auth_enabled=true" >> ~/.graphrag/neo4j/conf/neo4j.conf
echo "dbms.connector.bolt.listen_address=0.0.0.0:7687" >> ~/.graphrag/neo4j/conf/neo4j.conf
echo "dbms.connector.http.listen_address=0.0.0.0:7474" >> ~/.graphrag/neo4j/conf/neo4j.conf
```

### 4. Configure GraphRAG

Create a configuration file:

```bash
mkdir -p ~/.graphrag
cat > ~/.graphrag/config.env << EOF
# GraphRAG Configuration
NEO4J_HOME=$HOME/.graphrag/neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=graphrag
CHROMA_PERSIST_DIRECTORY=$HOME/.graphrag/data/chromadb
GRAPHRAG_API_PORT=5001
GRAPHRAG_MPC_PORT=8765
GRAPHRAG_LOG_LEVEL=INFO
EOF
```

### 5. Initialize Neo4j

Start Neo4j and set the password:

```bash
# Start Neo4j
~/.graphrag/neo4j/bin/neo4j start

# Set password (for Neo4j 5.x)
~/.graphrag/neo4j/bin/neo4j-admin dbms set-initial-password graphrag

# Stop and restart Neo4j
~/.graphrag/neo4j/bin/neo4j stop
~/.graphrag/neo4j/bin/neo4j start
```

### 6. Initialize the Database

```bash
python scripts/initialize_database.py
```

## Running GraphRAG Services

### Using the Service Script

The `graphrag-service.sh` script provides an easy way to manage GraphRAG services:

```bash
# Make the script executable
chmod +x tools/graphrag-service.sh

# Start all services
tools/graphrag-service.sh start

# Check status
tools/graphrag-service.sh status

# Stop all services
tools/graphrag-service.sh stop

# Restart all services
tools/graphrag-service.sh restart
```

You can also manage individual services:

```bash
# Start/stop individual services
tools/graphrag-service.sh start-neo4j
tools/graphrag-service.sh start-api
tools/graphrag-service.sh start-mpc
tools/graphrag-service.sh stop-neo4j
tools/graphrag-service.sh stop-api
tools/graphrag-service.sh stop-mpc
```

### Service Monitoring

The `graphrag-monitor.py` script monitors the services and restarts them if they crash:

```bash
# Make the script executable
chmod +x tools/graphrag-monitor.py

# Run the monitor
tools/graphrag-monitor.py
```

To run the monitor as a background service:

```bash
# Run in the background
nohup tools/graphrag-monitor.py > ~/.graphrag/logs/monitor.out 2>&1 &

# To stop the monitor
pkill -f graphrag-monitor.py
```

## Verifying the Installation

### Verify Neo4j

```bash
# Check if Neo4j is running
curl -u neo4j:graphrag http://localhost:7474/browser/

# Should return the Neo4j Browser HTML
```

### Verify ChromaDB

```bash
# Run the ChromaDB verification script
python scripts/verify_chromadb.py
```

### Verify API Server

```bash
# Check the API health endpoint
curl http://localhost:5001/health

# Should return: {"neo4j_connected":true,"status":"ok","vector_db_connected":true,"version":"1.0.0"}
```

### Verify MPC Server

```bash
# Test the MPC server with the ping tool
python tools/mpc_client_example.py --port 8765 --tool ping
```

## Adding Documents

### Add a Single Document

```bash
python tools/add-document.py --file /path/to/document.pdf
```

### Add a Folder of Documents

```bash
python tools/add-folder.py --folder /path/to/documents --recursive
```

## Troubleshooting

### Service Won't Start

Check the log files in `~/.graphrag/logs/` for error messages.

### Neo4j Authentication Issues

If you encounter authentication issues with Neo4j:

```bash
# Stop Neo4j
~/.graphrag/neo4j/bin/neo4j stop

# Reset the password
~/.graphrag/neo4j/bin/neo4j-admin dbms set-initial-password graphrag

# Start Neo4j
~/.graphrag/neo4j/bin/neo4j start
```

### ChromaDB Issues

If ChromaDB encounters errors:

```bash
# Check ChromaDB version
python -c "import chromadb; print(chromadb.__version__)"

# Verify ChromaDB is working
python scripts/verify_chromadb.py

# If needed, clear ChromaDB data
rm -rf ~/.graphrag/data/chromadb/*
```

## Uninstalling

To completely remove GraphRAG from your system:

```bash
# Stop all services
tools/graphrag-service.sh stop

# Remove GraphRAG data
rm -rf ~/.graphrag
```

## Additional Resources

- [GraphRAG Documentation](./README.md)
- [API Documentation](./api_documentation.md)
- [MPC Server Documentation](./mpc_server_setup.md)
