#!/bin/bash
# Script to start the GraphRAG service locally

# Change to the project root directory
cd "$(dirname "$0")"

# Check if Neo4j is installed via Homebrew
if ! command -v neo4j &> /dev/null; then
    echo "❌ Neo4j is not installed. Please install it with: brew install neo4j"
    exit 1
fi

# Check if the virtual environment exists
if [ ! -d ".venv-py312" ]; then
    echo "❌ Virtual environment not found. Please create it with: uv venv --python 3.12.8 .venv-py312"
    exit 1
fi

# Check if required Python packages are installed
if ! .venv-py312/bin/python -c "import neo4j, chromadb, flask, websockets" &> /dev/null; then
    echo "❌ Required Python packages are not installed. Please install them with: uv pip install -r requirements.txt --python .venv-py312/bin/python"
    exit 1
fi

# Use the graphrag-service.sh script to start the services
if [ -f "tools/graphrag-service.sh" ]; then
    echo "Starting GraphRAG services using tools/graphrag-service.sh..."
    ./tools/graphrag-service.sh start
else
    echo "❌ tools/graphrag-service.sh not found. Please check your installation."
    exit 1
fi

# Print usage instructions
echo ""
echo "GraphRAG service is starting..."
echo ""
echo "To check the status of the services:"
echo "  ./tools/graphrag-service.sh status"
echo ""
echo "To stop the services:"
echo "  ./tools/graphrag-service.sh stop"
echo ""
echo "To restart the services:"
echo "  ./tools/graphrag-service.sh restart"
echo ""
echo "To add a document:"
echo "  uv run --python .venv-py312/bin/python scripts/add_document.py /path/to/document.pdf"
echo ""
echo "To query the system:"
echo "  uv run --python .venv-py312/bin/python scripts/query_graphrag.py \"your query here\""
echo ""
echo "To clear the databases:"
echo "  uv run --python .venv-py312/bin/python scripts/clean_database.py --yes"
echo ""
echo "For more information, see the project-dictionary.md file."