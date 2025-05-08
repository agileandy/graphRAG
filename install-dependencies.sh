#!/bin/bash
# Install dependencies using uv

# Ensure the script is executable
# chmod +x install-dependencies.sh

# Install dependencies from requirements-update.txt
uv pip install -r requirements-update.txt

echo "Dependencies installed successfully!"