#!/usr/bin/env python3
"""
Script to update hardcoded port references in the codebase.

This script scans the codebase for hardcoded port numbers and suggests
replacements using the centralized port configuration.
"""

import os
import re
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.config.ports import DEFAULT_PORTS

# Define patterns for common port usages
PORT_PATTERNS = [
    # port = 8765
    r'port\s*=\s*(\d+)',
    # "port": 8765
    r'"port"\s*:\s*(\d+)',
    # 'port': 8765
    r"'port'\s*:\s*(\d+)",
    # localhost:8765
    r'localhost:(\d+)',
    # 127.0.0.1:8765
    r'127\.0\.0\.1:(\d+)',
    # --port 8765
    r'--port\s+(\d+)',
    # -p 8765
    r'-p\s+(\d+)',
]

# Define file extensions to scan
FILE_EXTENSIONS = ['.py', '.sh', '.md', '.json', '.yml', '.yaml']

# Define directories to exclude
EXCLUDE_DIRS = ['.git', '.venv-py312', 'data', '__pycache__', '.pytest_cache', '.ruff_cache']

# Create a reverse mapping from port to service
PORT_TO_SERVICE = {port: service for service, port in DEFAULT_PORTS.items()}

def scan_file(file_path):
    """Scan a file for hardcoded port numbers."""
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            content = f.read()
        except UnicodeDecodeError:
            print(f"Warning: Could not read {file_path} as text")
            return []
    
    findings = []
    for pattern in PORT_PATTERNS:
        for match in re.finditer(pattern, content):
            port = int(match.group(1))
            if port in PORT_TO_SERVICE:
                service = PORT_TO_SERVICE[port]
                findings.append({
                    'file': file_path,
                    'line': content.count('\n', 0, match.start()) + 1,
                    'match': match.group(0),
                    'port': port,
                    'service': service,
                    'replacement': f"get_port('{service}')"
                })
    
    return findings

def scan_directory(directory):
    """Recursively scan a directory for hardcoded port numbers."""
    findings = []
    for root, dirs, files in os.walk(directory):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            if any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                file_path = os.path.join(root, file)
                findings.extend(scan_file(file_path))
    
    return findings

def main():
    """Main function."""
    # Scan the project directory
    findings = scan_directory(project_root)
    
    # Print the findings
    if findings:
        print(f"Found {len(findings)} hardcoded port references:")
        for i, finding in enumerate(findings, 1):
            print(f"\n{i}. {finding['file']}:{finding['line']}")
            print(f"   Match: {finding['match']}")
            print(f"   Port: {finding['port']} (Service: {finding['service']})")
            print(f"   Suggested replacement: {finding['replacement']}")
    else:
        print("No hardcoded port references found.")
    
    # Print summary by service
    print("\nSummary by service:")
    service_counts = {}
    for finding in findings:
        service = finding['service']
        service_counts[service] = service_counts.get(service, 0) + 1
    
    for service, count in sorted(service_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {service}: {count} references")

if __name__ == "__main__":
    main()