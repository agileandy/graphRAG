#!/bin/bash
# UV wrapper script for GraphRAG
# This script ensures that Python commands are run using UV

# Set the Python environment
PYTHON_ENV=".venv-py312"

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "❌ UV is not installed. Please install it with: pip install uv"
    exit 1
fi

# Check if the virtual environment exists
if [ ! -d "$PYTHON_ENV" ]; then
    echo "❌ Virtual environment not found. Creating it with UV..."
    uv venv --python 3.12 "$PYTHON_ENV"
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment."
        exit 1
    fi
    
    echo "✅ Virtual environment created successfully."
fi

# Parse command line arguments
if [ "$1" == "install" ]; then
    # Install dependencies
    shift
    echo "📦 Installing dependencies with UV..."
    uv pip install "$@" --python "$PYTHON_ENV/bin/python"
elif [ "$1" == "run" ]; then
    # Run a Python script
    shift
    echo "🚀 Running with UV..."
    uv run --python "$PYTHON_ENV/bin/python" "$@"
elif [ "$1" == "test" ]; then
    # Run tests
    shift
    echo "🧪 Running tests with UV..."
    uv run --python "$PYTHON_ENV/bin/python" -m pytest "$@"
elif [ "$1" == "lint" ]; then
    # Run linting
    shift
    echo "🧹 Running linting with UV..."
    uv run --python "$PYTHON_ENV/bin/python" -m ruff "$@"
elif [ "$1" == "format" ]; then
    # Run formatting
    shift
    echo "✨ Running formatting with UV..."
    uv run --python "$PYTHON_ENV/bin/python" -m ruff format "$@"
elif [ "$1" == "shell" ]; then
    # Activate the virtual environment
    echo "🐚 Activating virtual environment..."
    source "$PYTHON_ENV/bin/activate"
    exec "$SHELL"
else
    # Default to running the command with UV
    echo "🚀 Running with UV..."
    uv run --python "$PYTHON_ENV/bin/python" "$@"
fi
