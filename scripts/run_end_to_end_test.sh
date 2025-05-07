#!/bin/bash

# Script to run the end-to-end test using uv

# Change to the project root directory
cd "$(dirname "$0")/.."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first."
    echo "Visit https://github.com/astral-sh/uv for installation instructions."
    exit 1
fi

# Run the end-to-end test
echo "Running end-to-end test..."
uv run scripts/test_end_to_end.py "$@"

# Check the exit code
if [ $? -eq 0 ]; then
    echo "✅ End-to-end test completed successfully!"
else
    echo "❌ End-to-end test failed."
    echo "Please check the error messages above."
fi
