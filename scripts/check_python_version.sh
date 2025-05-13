#!/bin/bash
# Script to check Python version in the virtual environment

# Expected Python version
EXPECTED_VERSION="3.12.8"

# Path to virtual environment
VENV_PATH=".venv-py312"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "   Create it with: uv venv --python /Users/andyspamer/.local/share/uv/python/cpython-3.12.8-macos-aarch64-none/bin/python3.12 $VENV_PATH"
    exit 1
fi

# Get Python version from virtual environment
PYTHON_VERSION=$($VENV_PATH/bin/python --version 2>&1 | cut -d' ' -f2)

# Check if version matches expected version
if [ "$PYTHON_VERSION" != "$EXPECTED_VERSION" ]; then
    echo "❌ WARNING: Python version mismatch!"
    echo "   Expected: $EXPECTED_VERSION"
    echo "   Found:    $PYTHON_VERSION"
    echo ""
    echo "   This may cause compatibility issues with the project's dependencies."
    echo "   Consider recreating the virtual environment with the correct Python version:"
    echo ""
    echo "   1. Delete the current virtual environment:"
    echo "      rm -rf $VENV_PATH"
    echo ""
    echo "   2. Create a new virtual environment with the correct Python version:"
    echo "      uv venv --python /Users/andyspamer/.local/share/uv/python/cpython-3.12.8-macos-aarch64-none/bin/python3.12 $VENV_PATH"
    echo ""
    echo "   3. Install dependencies:"
    echo "      source $VENV_PATH/bin/activate && uv pip install -r requirements.txt"
    echo ""
    exit 1
else
    echo "✅ Python version check passed: $PYTHON_VERSION"
    exit 0
fi
