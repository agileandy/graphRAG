#!/usr/bin/env python3
"""
Script to update port references in documentation files.

This script scans documentation files for hardcoded port numbers and
replaces them with references to the centralized port configuration.
"""

import os
import re
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.config.ports import DEFAULT_PORTS

# Define patterns for common port usages in documentation
PORT_PATTERNS = [
    # localhost:8765
    (r'localhost:(\d+)', r'localhost:${GRAPHRAG_PORT_{}'),
    # 127.0.0.1:8765
    (r'127\.0\.0\.1:(\d+)', r'127.0.0.1:${GRAPHRAG_PORT_{}'),
    # --port 8765
    (r'--port\s+(\d+)', r'--port ${GRAPHRAG_PORT_{}'),
    # -p 8765
    (r'-p\s+(\d+)', r'-p ${GRAPHRAG_PORT_{}'),
]

# Define file extensions to scan
FILE_EXTENSIONS = ['.md', '.txt', '.json']

# Define directories to scan
DOCS_DIRS = ['docs', 'specs', 'bugMCP']

# Create a reverse mapping from port to service
PORT_TO_SERVICE = {port: service.upper() for service, port in DEFAULT_PORTS.items()}

def update_file(file_path):
    """Update port references in a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            content = f.read()
        except UnicodeDecodeError:
            print(f"Warning: Could not read {file_path} as text")
            return False
    
    original_content = content
    
    for pattern, replacement_template in PORT_PATTERNS:
        for match in re.finditer(pattern, content):
            port = int(match.group(1))
            if port in PORT_TO_SERVICE:
                service = PORT_TO_SERVICE[port]
                replacement = replacement_template.format(service) + '}'
                content = content.replace(match.group(0), replacement)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def scan_directory(directory):
    """Recursively scan a directory for files to update."""
    updated_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                file_path = os.path.join(root, file)
                if update_file(file_path):
                    updated_files.append(file_path)
    
    return updated_files

def main():
    """Main function."""
    updated_files = []
    
    # Scan documentation directories
    for docs_dir in DOCS_DIRS:
        dir_path = os.path.join(project_root, docs_dir)
        if os.path.exists(dir_path):
            updated_files.extend(scan_directory(dir_path))
    
    # Print the results
    if updated_files:
        print(f"Updated {len(updated_files)} files:")
        for file in updated_files:
            print(f"  - {file}")
    else:
        print("No files were updated.")

if __name__ == "__main__":
    main()