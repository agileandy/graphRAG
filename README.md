# GraphRAG

GraphRAG is a hybrid approach that combines vector embeddings with knowledge graphs for enhanced information retrieval. This system integrates Neo4j for knowledge graph storage and ChromaDB/LanceDB for vector embeddings, providing powerful semantic search capabilities.

## Directory Structure

The project has been reorganized to reduce duplication and improve maintainability:

### Core Components

- **src/**: Main source code
  - **api/**: API server implementation
  - **database/**: Database interfaces (Neo4j, ChromaDB)
  - **llm/**: Large Language Model integrations
  - **loaders/**: Document loaders for various formats
  - **mcp/**: Model Context Protocol server
  - **processing/**: Document processing utilities
  - **search/**: Search implementations
  - **utils/**: Utility functions

### Scripts and Tools

- **bin/**: Executable scripts and command-line tools
  - `graphrag`: Main CLI tool for interacting with GraphRAG
  - `graphrag-mcp`: MCP server CLI tool
  - `graphrag-monitor.py`: Monitoring utility

- **scripts/**: Core functionality scripts
  - **document_processing/**: Document addition and processing
  - **database_management/**: Database operations
  - **service_management/**: Service control scripts
  - **query/**: Query and search scripts

- **examples/**: Example usage scripts
  - Client examples (MCP)
  - Integration examples (LangChain, OpenAI)
  - Simple demos

- **tests/**: Testing scripts
  - **component/**: Component-level tests
  - **regression/**: Regression tests

- **utils/**: Utility scripts
  - Docker management
  - Environment setup
  - Miscellaneous utilities

### Configuration and Documentation

- **config/**: Configuration files
  - `lmstudio_config.json`: LM Studio configuration
  - Other configuration files

- **specs/**: Specifications and design documents
  - **design/**: System design documentation

- **docs/**: Documentation files

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Neo4j 5.x
- Docker (optional, for containerized deployment)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/graphRAG.git
   cd graphRAG
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv-py312
   source .venv-py312/bin/activate  # On Windows: .venv-py312\Scripts\activate
   ```

3. Install dependencies using UV:
   ```bash
   ./utils/uvrun.sh install
   ```

4. Install Neo4j (if not already installed):
   ```bash
   ./utils/install_neo4j.sh
   ```

5. Initialize the database:
   ```bash
   python -m scripts.database_management.initialize_database
   ```

### Running the Services

You can start all services using the service management script:

```bash
./scripts/service_management/graphrag-service.sh start
```

Or start individual services:

```bash
# Start Neo4j
./scripts/service_management/graphrag-service.sh start-neo4j

# Start API server
./scripts/service_management/graphrag-service.sh start-api

# Start MCP server
./scripts/service_management/graphrag-service.sh start-mcp
```

### Adding Documents

To add documents to the system:

```bash
# Add a single document
python -m scripts.document_processing.add_document_core

# Add PDF documents
python -m scripts.document_processing.add_pdf_documents --file /path/to/document.pdf

# Add a batch of ebooks
python -m scripts.document_processing.add_ebooks_batch --folder /path/to/ebooks
```

### Querying the System

```bash
# Simple query
python -m scripts.query.query_graphrag --query "Your search query"

# Query with the CLI tool
./bin/graphrag search --query "Your search query"
```

## Development

### Branching Strategy

When starting new work:

1. Create a branch with the appropriate naming convention:
   ```bash
   git checkout -b feature-description  # For new features
   git checkout -b task-description     # For tasks
   git checkout -b bug-description      # For bug fixes
   ```

2. Make your changes and commit them:
   ```bash
   git add .
   git commit -m "feat: add new feature"  # Use conventional commit format
   ```

3. When ready, merge to main and tag with version:
   ```bash
   git checkout main
   git merge feature-description
   git tag -a v0.1.0 -m "Version 0.1.0"
   ```

### Running Tests

```bash
# Run all regression tests
python -m tests.regression.run_all_tests

# Run a specific component test
python -m tests.component.test_neo4j
```

## Docker Deployment

Build and run with Docker:

```bash
# Build the Docker image
./utils/docker_build_run.sh

# Or build and run in debug mode
./utils/docker_build_debug.sh
```

## Configuration

GraphRAG uses a flexible configuration approach with multiple configuration files:

### Configuration Files

1. **Project-specific Configuration**: `.env` (in project root)
   - Contains settings specific to the current project
   - Primary configuration file for development
   - **Recommended for most configuration needs**

2. **System-wide Configuration**: `~/.graphrag/config.env`
   - Optional system-wide settings for all GraphRAG instances
   - Used primarily by service scripts and daemons
   - Takes precedence over project-specific configuration
   - **Only use for machine-specific settings that shouldn't be in version control**

3. **Docker Configuration**: `.env.docker` / `config/env.docker`
   - Contains settings specific to Docker deployment
   - Used when running in a container

4. **Sample Configuration**: `.env.sample` / `config/env.sample`
   - Template for users to create their own configuration files

### Setting Up Configuration

1. Create a project-specific configuration (recommended approach):
   ```bash
   cp config/env.sample .env
   nano .env  # Edit as needed
   ```

2. For system-wide configuration (optional, only if needed):
   ```bash
   mkdir -p ~/.graphrag
   cp config/env.sample ~/.graphrag/config.env
   nano ~/.graphrag/config.env  # Edit as needed
   ```

### Important Note

To avoid confusion with multiple configuration files:
- Use `.env` for most configuration needs
- Only use `~/.graphrag/config.env` for machine-specific settings
- Avoid duplicating settings between the two files

For a complete list of configuration options and detailed explanation, see [Configuration Guide](config/README.md).

## License

[Specify your license here]

## Acknowledgments

- Neo4j for the graph database
- ChromaDB for the vector database
- LM Studio for local LLM integration