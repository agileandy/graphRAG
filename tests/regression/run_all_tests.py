#!/usr/bin/env python3
"""
GraphRAG Regression Test Suite

This script runs all regression tests in sequence.

Usage:
    python -m tests.regression.run_all_tests
"""
import os
import sys
import time
import importlib
from typing import List, Tuple

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Import test modules
from tests.regression import (
    test_01_start_stop,
    test_02_db_init,
    test_03_add_document,
    test_04_nlp_processing,
    test_05_search,
    test_06_deduplication
)

def run_test(test_module, test_name: str) -> Tuple[bool, str]:
    """
    Run a single test.
    
    Args:
        test_module: Test module to run
        test_name: Name of the test
        
    Returns:
        Tuple of (success, message)
    """
    print(f"\n{'='*80}")
    print(f"Running {test_name}...")
    print(f"{'='*80}\n")
    
    start_time = time.time()
    
    try:
        # Call the main function of the test module
        success = test_module.main() == 0
        
        end_time = time.time()
        duration = end_time - start_time
        
        if success:
            message = f"✅ {test_name} passed in {duration:.2f} seconds"
        else:
            message = f"❌ {test_name} failed in {duration:.2f} seconds"
        
        return success, message
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        message = f"❌ {test_name} failed with exception in {duration:.2f} seconds: {str(e)}"
        return False, message

def run_all_tests() -> List[Tuple[str, bool, str]]:
    """
    Run all regression tests in sequence.
    
    Returns:
        List of tuples (test_name, success, message)
    """
    tests = [
        (test_01_start_stop, "Test 1: Start and Stop Services"),
        (test_02_db_init, "Test 2: Database Initialization"),
        (test_03_add_document, "Test 3: Add Document"),
        (test_04_nlp_processing, "Test 4: NLP Processing"),
        (test_05_search, "Test 5: Search Functionality"),
        (test_06_deduplication, "Test 6: Deduplication")
    ]
    
    results = []
    
    for test_module, test_name in tests:
        success, message = run_test(test_module, test_name)
        results.append((test_name, success, message))
        
        # If a test fails, we might want to continue with the next test
        # but print a warning
        if not success:
            print(f"\n⚠️ {test_name} failed, but continuing with next test...")
    
    return results

def main():
    """Main function to run all tests."""
    print("\n" + "="*80)
    print("GraphRAG Regression Test Suite")
    print("="*80 + "\n")
    
    start_time = time.time()
    
    results = run_all_tests()
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # Print summary
    print("\n" + "="*80)
    print("Test Summary")
    print("="*80 + "\n")
    
    for test_name, success, message in results:
        print(message)
    
    # Calculate overall success
    total_tests = len(results)
    passed_tests = sum(1 for _, success, _ in results if success)
    
    print(f"\nTotal tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Total duration: {total_duration:.2f} seconds")
    
    if passed_tests == total_tests:
        print("\n✅ All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())