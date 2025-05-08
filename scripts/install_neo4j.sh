#!/bin/bash

# Script to download and install Neo4j Community Edition following best practices
# - Neo4j binaries installed in ~/.local/neo4j/
# - Neo4j data stored in ~/.graphrag/neo4j/

# Define installation directories
NEO4J_HOME="$HOME/.local/neo4j"
NEO4J_DATA_DIR="$HOME/.graphrag/neo4j"
NEO4J_VERSION="5.18.1"

# Create directories
echo "Creating installation directories..."
mkdir -p "$NEO4J_HOME"
mkdir -p "$NEO4J_DATA_DIR/data"
mkdir -p "$NEO4J_DATA_DIR/logs"
mkdir -p "$NEO4J_DATA_DIR/import"

# Download Neo4j Community Edition
echo "Downloading Neo4j Community Edition $NEO4J_VERSION..."
curl -L -o /tmp/neo4j.tar.gz "https://dist.neo4j.org/neo4j-community-$NEO4J_VERSION-unix.tar.gz"

# Extract Neo4j
echo "Extracting Neo4j to $NEO4J_HOME..."
tar -xzf /tmp/neo4j.tar.gz -C "$NEO4J_HOME" --strip-components=1
rm /tmp/neo4j.tar.gz

# Configure Neo4j
echo "Configuring Neo4j..."
NEO4J_CONF="$NEO4J_HOME/conf/neo4j.conf"

# Basic configuration
sed -i '' 's/#dbms.security.auth_enabled=false/dbms.security.auth_enabled=true/g' "$NEO4J_CONF"
sed -i '' 's/#server.default_listen_address=0.0.0.0/server.default_listen_address=0.0.0.0/g' "$NEO4J_CONF"

# Set data directory
echo "Setting Neo4j data directory to $NEO4J_DATA_DIR/data..."
sed -i '' "s|#server.directories.data=.*|server.directories.data=$NEO4J_DATA_DIR/data|g" "$NEO4J_CONF"

# Set logs directory
echo "Setting Neo4j logs directory to $NEO4J_DATA_DIR/logs..."
sed -i '' "s|#server.directories.logs=.*|server.directories.logs=$NEO4J_DATA_DIR/logs|g" "$NEO4J_CONF"

# Set import directory
echo "Setting Neo4j import directory to $NEO4J_DATA_DIR/import..."
sed -i '' "s|#server.directories.import=.*|server.directories.import=$NEO4J_DATA_DIR/import|g" "$NEO4J_CONF"

# Create script to start Neo4j
cat > scripts/start_neo4j.sh << EOF
#!/bin/bash

# Start Neo4j server
"$NEO4J_HOME/bin/neo4j" console
EOF

# Create script to stop Neo4j
cat > scripts/stop_neo4j.sh << EOF
#!/bin/bash

# Stop Neo4j server
"$NEO4J_HOME/bin/neo4j" stop
EOF

# Make scripts executable
chmod +x scripts/start_neo4j.sh
chmod +x scripts/stop_neo4j.sh

# Create a symbolic link to the project directory for backward compatibility
echo "Creating symbolic link for backward compatibility..."
if [ -d "neo4j" ]; then
    echo "Removing existing neo4j directory in project..."
    rm -rf neo4j
fi
ln -s "$NEO4J_HOME" neo4j

# Update .env file with Neo4j location
echo "Updating .env file with Neo4j location..."
if grep -q "NEO4J_HOME" .env; then
    sed -i '' "s|NEO4J_HOME=.*|NEO4J_HOME=$NEO4J_HOME|g" .env
else
    echo "NEO4J_HOME=$NEO4J_HOME" >> .env
fi

if grep -q "NEO4J_DATA_DIR" .env; then
    sed -i '' "s|NEO4J_DATA_DIR=.*|NEO4J_DATA_DIR=$NEO4J_DATA_DIR|g" .env
else
    echo "NEO4J_DATA_DIR=$NEO4J_DATA_DIR" >> .env
fi

echo "Neo4j installation completed!"
echo "Neo4j binaries installed in: $NEO4J_HOME"
echo "Neo4j data directory set to: $NEO4J_DATA_DIR"
echo "To start Neo4j, run: ./scripts/start_neo4j.sh"
echo "To stop Neo4j, run: ./scripts/stop_neo4j.sh"
echo "On first run, set the password for the 'neo4j' user to 'graphrag' (or update the .env file)"