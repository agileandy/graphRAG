#!/bin/bash
# This script ensures git commands run with the correct PATH

# Change to the project directory
cd /Users/andyspamer/Dev-Space/PythonProjects/graphRAG

# Run git command with the correct PATH
PATH="/opt/homebrew/bin:$PATH" git "$@"