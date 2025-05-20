import os
import sys

# Add the project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, project_root)
"""
WSGI entry point for the GraphRAG API server.
"""
from src.api.server import app

if __name__ == "__main__":
    app.run()
