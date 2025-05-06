FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    tmux \
    wget \
    procps \
    htop \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install Java for Neo4j
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jre \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user to run the application
RUN groupadd -r graphrag && useradd -r -g graphrag -m -d /home/graphrag graphrag

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install websockets for MPC server
RUN pip install --no-cache-dir websockets

# Copy the entire project
COPY . .

# Download and extract Neo4j
RUN mkdir -p /app/neo4j && \
    curl -L -o /tmp/neo4j.tar.gz https://dist.neo4j.org/neo4j-community-5.18.1-unix.tar.gz && \
    tar -xzf /tmp/neo4j.tar.gz -C /app/neo4j --strip-components=1 && \
    rm /tmp/neo4j.tar.gz

# Configure Neo4j with optimized settings
RUN sed -i 's/#server.default_listen_address=0.0.0.0/server.default_listen_address=0.0.0.0/g' /app/neo4j/conf/neo4j.conf && \
    sed -i 's/#dbms.memory.heap.initial_size=512m/dbms.memory.heap.initial_size=512m/g' /app/neo4j/conf/neo4j.conf && \
    sed -i 's/#dbms.memory.heap.max_size=512m/dbms.memory.heap.max_size=1024m/g' /app/neo4j/conf/neo4j.conf && \
    sed -i 's/#dbms.memory.pagecache.size=10g/dbms.memory.pagecache.size=512m/g' /app/neo4j/conf/neo4j.conf && \
    echo "dbms.security.auth_enabled=true" >> /app/neo4j/conf/neo4j.conf && \
    echo "dbms.connector.bolt.listen_address=0.0.0.0:7687" >> /app/neo4j/conf/neo4j.conf && \
    echo "dbms.connector.http.listen_address=0.0.0.0:7474" >> /app/neo4j/conf/neo4j.conf && \
    echo "dbms.jvm.additional=-XX:+UseG1GC" >> /app/neo4j/conf/neo4j.conf && \
    echo "dbms.jvm.additional=-XX:+UseStringDeduplication" >> /app/neo4j/conf/neo4j.conf && \
    echo "dbms.tx_state.memory_allocation=ON_HEAP" >> /app/neo4j/conf/neo4j.conf && \
    echo "dbms.memory.transaction.total_max=512m" >> /app/neo4j/conf/neo4j.conf && \
    echo "dbms.logs.query.enabled=true" >> /app/neo4j/conf/neo4j.conf && \
    echo "dbms.logs.query.rotation.keep_number=10" >> /app/neo4j/conf/neo4j.conf && \
    echo "dbms.logs.query.rotation.size=20m" >> /app/neo4j/conf/neo4j.conf

# Create data directories with proper permissions
RUN mkdir -p /app/data/chromadb /app/data/logs /app/data/neo4j

# Set environment variables with more configuration options
ENV NEO4J_URI=bolt://localhost:7687 \
    NEO4J_USERNAME=neo4j \
    NEO4J_PASSWORD=graphrag \
    CHROMA_PERSIST_DIRECTORY=/app/data/chromadb \
    GRAPHRAG_API_URL=http://localhost:5000 \
    PYTHONPATH=/app \
    GRAPHRAG_LOG_LEVEL=INFO \
    GRAPHRAG_LOG_DIR=/app/data/logs \
    JAVA_OPTS="-Xms512m -Xmx1024m" \
    GUNICORN_WORKERS=2 \
    GUNICORN_THREADS=4 \
    GUNICORN_TIMEOUT=120 \
    PYTHONUNBUFFERED=1

# Set proper permissions for the application
RUN chown -R graphrag:graphrag /app/data && \
    chmod -R 755 /app/data && \
    chown -R graphrag:graphrag /app/neo4j && \
    chmod -R 755 /app/neo4j

# Expose ports
# Neo4j
EXPOSE 7474 7687
# API Server
EXPOSE 5000
# MPC Server
EXPOSE 8765

# Create a startup script
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Add a health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Switch to non-root user for security
USER graphrag

# Set the entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]