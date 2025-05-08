#!/bin/bash
# Install dependencies using uv

# Ensure the script is executable
# chmod +x install-dependencies.sh

# Install dependencies from requirements.txt
uv pip install -r requirements.txt

echo "Dependencies installed successfully!"