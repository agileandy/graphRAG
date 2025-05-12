#!/usr/bin/env python3
"""
Generate MCP settings file from template.

This script generates the mcp_settings.json file from the template,
replacing placeholders with values from the centralized port configuration.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.config import get_port

def generate_settings():
    """Generate MCP settings file from template."""
    # Get the template file path
    template_path = Path(__file__).parent / "mcp_settings.template.json"
    output_path = Path(__file__).parent / "mcp_settings.json"
    
    # Read the template
    with open(template_path, "r") as f:
        template = f.read()
    
    # Get port values
    bug_mcp_port = get_port("bug_mcp")
    
    # Replace placeholders
    settings = template.replace("${GRAPHRAG_PORT_BUG_MCP}", str(bug_mcp_port))
    
    # Write the settings file
    with open(output_path, "w") as f:
        f.write(settings)
    
    print(f"Generated {output_path} with bug_mcp_port={bug_mcp_port}")

if __name__ == "__main__":
    generate_settings()