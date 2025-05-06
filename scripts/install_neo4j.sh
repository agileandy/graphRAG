#!/bin/bash

# Script to download and install Neo4j Community Edition

# Create Neo4j directory
mkdir -p neo4j

# Download Neo4j Community Edition
echo "Downloading Neo4j Community Edition..."
curl -L -o neo4j/neo4j.tar.gz https://dist.neo4j.org/neo4j-community-5.18.1-unix.tar.gz

# Extract Neo4j
echo "Extracting Neo4j..."
tar -xzf neo4j/neo4j.tar.gz -C neo4j --strip-components=1
rm neo4j/neo4j.tar.gz

# Configure Neo4j
echo "Configuring Neo4j..."
sed -i '' 's/#dbms.security.auth_enabled=false/dbms.security.auth_enabled=true/g' neo4j/conf/neo4j.conf
sed -i '' 's/#server.default_listen_address=0.0.0.0/server.default_listen_address=0.0.0.0/g' neo4j/conf/neo4j.conf

# Create script to start Neo4j
cat > scripts/start_neo4j.sh << 'EOF'
#!/bin/bash

# Start Neo4j server
cd "$(dirname "$0")/.."
./neo4j/bin/neo4j console
EOF

# Create script to stop Neo4j
cat > scripts/stop_neo4j.sh << 'EOF'
#!/bin/bash

# Stop Neo4j server
cd "$(dirname "$0")/.."
./neo4j/bin/neo4j stop
EOF

# Make scripts executable
chmod +x scripts/start_neo4j.sh
chmod +x scripts/stop_neo4j.sh

echo "Neo4j installation completed!"
echo "To start Neo4j, run: ./scripts/start_neo4j.sh"
echo "To stop Neo4j, run: ./scripts/stop_neo4j.sh"
echo "On first run, set the password for the 'neo4j' user to 'graphrag' (or update the .env file)"