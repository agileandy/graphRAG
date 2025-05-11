#!/usr/bin/env python3
"""
Generate MCP settings for AI agent integration.

This script generates an MCP settings file that can be used to configure
AI agents to use the GraphRAG MCP server.
"""

import os
import sys
import json
import argparse
from pathlib import Path

def generate_mcp_settings(output_path: str, host: str = "localhost", port: int = 8767):
    """
    Generate MCP settings file.
    
    Args:
        output_path: Path to output file
        host: MCP server host
        port: MCP server port
    """
    # Get the absolute path to the GraphRAG installation
    graphrag_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Get the absolute path to the graphrag-mcp script
    mcp_script_path = os.path.join(graphrag_path, "tools", "graphrag-mcp")
    
    # Create the settings object
    settings = {
        "mcpServers": {
            "GraphRAG": {
                "command": mcp_script_path,
                "args": ["--host", "0.0.0.0", "--port", "8767"],
                "env": {
                    "PYTHONPATH": graphrag_path,
                    "NEO4J_URI": "bolt://localhost:7688",
                    "NEO4J_USERNAME": "neo4j",
                    "NEO4J_PASSWORD": "graphrag",
                    "CHROMA_PERSIST_DIRECTORY": os.path.join(graphrag_path, "data", "chromadb")
                }
            }
        }
    }
    
    # Write the settings to the output file
    with open(output_path, "w") as f:
        json.dump(settings, f, indent=2)
    
    print(f"MCP settings written to {output_path}")
    print(f"GraphRAG path: {graphrag_path}")
    print(f"MCP script path: {mcp_script_path}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate MCP settings for AI agent integration")
    parser.add_argument("--output", type=str, default="mcp_settings.json", help="Output file path")
    parser.add_argument("--host", type=str, default="localhost", help="MCP server host")
    parser.add_argument("--port", type=int, default=8767, help="MCP server port")
    args = parser.parse_args()
    
    generate_mcp_settings(args.output, args.host, args.port)

if __name__ == "__main__":
    main()
