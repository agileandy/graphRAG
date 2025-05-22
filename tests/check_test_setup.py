#!/usr/bin/env python3
"""Verify test environment setup and dependencies."""

import os
import sys
import subprocess
import importlib
from typing import List, Tuple

def check_python_version() -> Tuple[bool, str]:
    """Check Python version meets minimum requirements."""
    min_version = (3, 8)
    current = sys.version_info[:2]

    if current >= min_version:
        return True, f"Python version {'.'.join(map(str, current))} OK"
    return False, f"Python {'.'.join(map(str, min_version))}+ required, found {'.'.join(map(str, current))}"

def check_required_packages() -> List[Tuple[str, bool, str]]:
    """Check all required packages are installed."""
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "requests",
        "websockets",
        "python-dotenv",
        "pydantic",
    ]

    results = []
    for package in required_packages:
        try:
            importlib.import_module(package.replace("-", "_"))
            results.append((package, True, "OK"))
        except ImportError as e:
            results.append((package, False, str(e)))

    return results

def check_test_directories() -> List[Tuple[str, bool, str]]:
    """Check required test directories exist."""
    required_dirs = [
        "tests/common_utils",
        "tests/web_api_suite",
        "tests/mcp_suite",
    ]

    results = []
    for dir_path in required_dirs:
        exists = os.path.isdir(dir_path)
        results.append((dir_path, exists, "OK" if exists else "Missing"))

    return results

def check_config_files() -> List[Tuple[str, bool, str]]:
    """Check required configuration files exist."""
    required_files = [
        "pytest.ini",
        "requirements-test.txt",
        "tests/README.md",
        "tests/.env.example",
    ]

    results = []
    for file_path in required_files:
        exists = os.path.isfile(file_path)
        results.append((file_path, exists, "OK" if exists else "Missing"))

    return results

def check_pytest_runs() -> Tuple[bool, str]:
    """Check if pytest can run without errors."""
    try:
        result = subprocess.run(
            ["pytest", "--collect-only"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True, "pytest runs successfully"
        return False, f"pytest error: {result.stderr}"
    except Exception as e:
        return False, f"Failed to run pytest: {str(e)}"

def main() -> None:
    """Run all setup checks."""
    print("\n=== GraphRAG Test Setup Verification ===\n")

    # Check Python version
    success, message = check_python_version()
    print(f"Python Version: {'✓' if success else '✗'} {message}")

    # Check required packages
    print("\nRequired Packages:")
    for package, success, message in check_required_packages():
        print(f"  {package}: {'✓' if success else '✗'} {message}")

    # Check directories
    print("\nRequired Directories:")
    for dir_path, exists, message in check_test_directories():
        print(f"  {dir_path}: {'✓' if exists else '✗'} {message}")

    # Check config files
    print("\nConfiguration Files:")
    for file_path, exists, message in check_config_files():
        print(f"  {file_path}: {'✓' if exists else '✗'} {message}")

    # Check pytest
    print("\nPytest Check:")
    success, message = check_pytest_runs()
    print(f"  {'✓' if success else '✗'} {message}")

    print("\nVerification complete!")

if __name__ == "__main__":
    main()