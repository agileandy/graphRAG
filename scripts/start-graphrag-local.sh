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
    echo "❌ Virtual environment not found. Please create it with: uv venv --python /Users/andyspamer/.local/share/uv/python/cpython-3.12.8-macos-aarch64-none/bin/python3.12 .venv-py312"
    exit 1
fi

# Check Python version in the virtual environment
if [ -f "scripts/check_python_version.sh" ]; then
    ./scripts/check_python_version.sh
    if [ $? -ne 0 ]; then
        exit 1
    fi
else
    echo "⚠️ Python version check script not found. Skipping version check."
fi

# Check if required Python packages are installed
if ! .venv-py312/bin/python -c "import neo4j, chromadb, flask, websockets" &> /dev/null; then
    echo "❌ Required Python packages are not installed. Please install them with: uv pip install -r requirements.txt --python .venv-py312/bin/python"
    exit 1
fi

# Use the graphrag-service.sh script to start the services
if [ -f "scripts/service_management/graphrag-service.sh" ]; then
    echo "Starting GraphRAG services using scripts/service_management/graphrag-service.sh..."
    ./scripts/service_management/graphrag-service.sh start
else
    echo "❌ scripts/service_management/graphrag-service.sh not found. Please check your installation."
    exit 1
fi

# Print usage instructions
echo ""
echo "GraphRAG service is starting..."
echo ""
echo "To check the status of the services:"
echo "  ./scripts/service_management/graphrag-service.sh status"
echo ""
echo "To stop the services:"
echo "  ./scripts/service_management/graphrag-service.sh stop"
echo ""
echo "To restart the services:"
echo "  ./scripts/service_management/graphrag-service.sh restart"
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