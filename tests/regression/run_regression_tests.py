#!/usr/bin/env python3
"""
Run all regression tests for the GraphRAG system.

This script runs all the regression tests in sequence and reports the results.
"""

import os
import sys
import time
import argparse
from typing import Dict, Any, List, Optional, Tuple

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import test modules
from tests.regression.test_utils import print_section, print_test_header, print_test_result

# Import test modules
try:
    from tests.regression.test_message_passing_server import run_test as run_message_passing_test
except ImportError:
    def run_message_passing_test():
        print("Message Passing server test module not found")
        return False

try:
    from tests.regression.test_model_context_server import run_test as run_model_context_test
except ImportError:
    def run_model_context_test():
        print("Model Context Protocol server test module not found")
        return False

def run_all_tests(skip_tests=None):
    """
    Run all regression tests.

    Args:
        skip_tests: List of test names to skip

    Returns:
        True if all tests pass, False otherwise
    """
    if skip_tests is None:
        skip_tests = []

    print_test_header("GraphRAG Regression Tests")

    tests = [
        ("Message Passing Server", run_message_passing_test),
        ("Model Context Protocol Server", run_model_context_test)
    ]

    results = {}

    for test_name, test_func in tests:
        if test_name in skip_tests:
            print(f"Skipping {test_name} test")
            results[test_name] = "SKIPPED"
            continue

        print_section(f"Running {test_name} Test")

        try:
            success = test_func()
            results[test_name] = "PASS" if success else "FAIL"
        except Exception as e:
            print(f"Error running {test_name} test: {e}")
            results[test_name] = "ERROR"

    # Print summary
    print_section("Test Summary")

    for test_name, result in results.items():
        print(f"{test_name}: {result}")

    # Check if all tests passed
    all_passed = all(result == "PASS" for result in results.values())

    print_test_result("All Tests", all_passed, "All tests passed" if all_passed else "Some tests failed")

    return all_passed

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run GraphRAG regression tests")
    parser.add_argument("--skip", type=str, nargs="+", help="Tests to skip")
    args = parser.parse_args()

    skip_tests = args.skip or []

    success = run_all_tests(skip_tests)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
