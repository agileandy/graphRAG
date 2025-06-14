# GraphRAG Configuration Guide

This document explains the configuration approach used in GraphRAG.

## Configuration Files

GraphRAG uses multiple configuration files to support different deployment scenarios:

1. **Project-specific Configuration**: `.env` (in project root)
   - Contains settings specific to the current project
   - Primary configuration file for development
   - Should be used for most configuration needs

2. **System-wide Configuration**: `~/.graphrag/config.env`
   - Optional system-wide settings that apply to all GraphRAG instances on the machine
   - Used primarily by service scripts and daemons
   - Takes precedence over project-specific configuration
   - **Note**: Only use this for system-specific settings that shouldn't be in version control

3. **Docker Configuration**: `.env.docker` / `config/env.docker`
   - Contains settings specific to Docker deployment
   - Used when running in a container
   - Mounted into the container at runtime

4. **Sample Configuration**: `.env.sample` / `config/env.sample`
   - Template for users to create their own configuration files
   - Contains all available configuration options with default values and comments

## Configuration Hierarchy

The configuration is loaded in the following order:

1. `~/.graphrag/config.env` (if exists)
2. `.env` (in project root)
3. Default values hardcoded in the application

This allows for a flexible configuration approach where system-wide settings can be overridden by project-specific settings.

## Important Note on Configuration Files

The codebase is designed to check for both `.env` and `~/.graphrag/config.env`, but you should generally prefer using just the `.env` file in the project root for most configuration needs. The system-wide configuration should only be used for settings that are specific to your machine and shouldn't be committed to version control.

If you find that both files exist and contain conflicting settings, the system-wide configuration (`~/.graphrag/config.env`) will take precedence. To avoid confusion, it's recommended to:

1. Use `.env` for most configuration needs
2. Only use `~/.graphrag/config.env` for machine-specific settings that shouldn't be in version control
3. Avoid duplicating settings between the two files

## Configuration Options

### Neo4j Configuration

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=graphrag
NEO4J_HOME=/opt/homebrew/bin/neo4j
NEO4J_DATA_DIR=~/.graphrag/neo4j
```

- `NEO4J_URI`: URI for connecting to Neo4j
- `NEO4J_USERNAME`: Neo4j username
- `NEO4J_PASSWORD`: Neo4j password
- `NEO4J_HOME`: Path to Neo4j installation
- `NEO4J_DATA_DIR`: Path to Neo4j data directory

### ChromaDB Configuration

```
CHROMA_PERSIST_DIRECTORY=./data/chromadb
```

- `CHROMA_PERSIST_DIRECTORY`: Path to ChromaDB persistence directory

### API Configuration

```
GRAPHRAG_API_PORT=5001
GRAPHRAG_MPC_PORT=8765
GRAPHRAG_LOG_LEVEL=INFO
```

- `GRAPHRAG_API_PORT`: Port for the GraphRAG API server
- `GRAPHRAG_MPC_PORT`: Port for the GraphRAG MPC server
- `GRAPHRAG_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### LLM Configuration

```
LLM_ENDPOINT=http://192.168.1.21:1234
OLLAMA_ENDPOINT=http://localhost:11434
EMBEDDING_MODEL=snowflake-arctic-embed2:latest
RERANKER_MODEL=qllama/bge-reranker-large:latest
CONCEPT_MODEL=lmstudio-community/Phi-4-mini-reasoning-MLX-4bit
USE_LOCAL_LLM=true
```

- `LLM_ENDPOINT`: Endpoint for the LLM service (e.g., LM Studio)
- `OLLAMA_ENDPOINT`: Endpoint for the Ollama service
- `EMBEDDING_MODEL`: Model to use for embeddings
- `RERANKER_MODEL`: Model to use for reranking
- `CONCEPT_MODEL`: Model to use for concept extraction
- `USE_LOCAL_LLM`: Whether to use a local LLM (true) or a remote one (false)

## Creating Your Configuration

1. Copy the sample configuration:
   ```bash
   cp config/env.sample .env
   ```

2. Edit the `.env` file to match your environment:
   ```bash
   nano .env
   ```

3. For system-wide configuration:
   ```bash
   mkdir -p ~/.graphrag
   cp config/env.sample ~/.graphrag/config.env
   nano ~/.graphrag/config.env
   ```

## Docker Configuration

When running in Docker, the configuration is loaded from `.env.docker`. You can customize this file before building the Docker image.

To use a custom configuration with Docker:

```bash
cp config/env.docker .env.docker.custom
nano .env.docker.custom
docker-compose --env-file .env.docker.custom up
```

## Security and Sensitive Information

### Managing Configuration Files

All configuration files in this directory that may contain sensitive information (API keys, credentials, etc.) are provided as templates with the `.sample` extension. To use them:

1. Copy the sample file without the `.sample` extension:

   ```bash
   cp config/openrouter_config.json.sample config/openrouter_config.json
   ```

2. Edit the new file with your actual credentials
3. The original file will be ignored by git (configured in .gitignore)
4. Never commit files containing real credentials to the repository

### Managing API Keys and Secrets

- Store all API keys and secrets in your local `.env` file
- Never commit the `.env` file to the repository
- Use `env.sample` as a template for required environment variables
- Consider using a secrets management service for production deployments

### Managing Database Credentials

- Default Neo4j credentials in sample files are for development only
- Always change credentials in production
- Use environment variables for database credentials
- Consider using connection strings with placeholders:

  ```env
  NEO4J_URI=bolt://localhost:${GRAPHRAG_PORT_NEO4J_BOLT}
  ```

### Security Best Practices

1. Rotate API keys and credentials regularly
2. Use different credentials for development and production
3. Limit API key permissions to only what's needed
4. Monitor for exposed secrets using git hooks or security scanning tools
5. Use environment variables instead of hardcoding secrets in files