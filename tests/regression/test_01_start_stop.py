#!/usr/bin/env python3
"""Regression Test 1: Check start and stop of GraphRAG services.

This test:
1. Starts all GraphRAG services
2. Verifies the services are running by checking the API health
3. Stops all services
4. Verifies the services are stopped

Usage:
    python -m tests.regression.test_01_start_stop
"""

import os
import sys
import time

import requests

# Add the project root directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from tests.regression.test_utils import (
    HEALTH_ENDPOINT,
    check_api_health,
    start_services,
    stop_services,
)


def test_start_stop_services() -> bool:
    """Test starting and stopping GraphRAG services."""
    print("\n=== Test 1: Start and Stop Services ===\n")

    # Step 1: Start services
    print("Step 1: Starting services...")
    success, process = start_services()

    if not success:
        print("❌ Failed to start services")
        return False

    print("✅ Services started successfully")

    # Step 2: Verify services are running
    print("\nStep 2: Verifying services are running...")
    is_healthy, health_data = check_api_health()

    if is_healthy:
        print("✅ API health check passed")
        print(f"Health data: {health_data}")
    else:
        print("❌ API health check failed")
        print(f"Health data: {health_data}")
        stop_services(process)
        return False

    # Step 3: Stop services
    print("\nStep 3: Stopping services...")
    if stop_services(process):
        print("✅ Services stopped successfully")
    else:
        print("❌ Failed to stop services")
        return False

    # Step 4: Verify services are stopped
    print("\nStep 4: Verifying services are stopped...")
    time.sleep(2)  # Give services time to stop

    try:
        requests.get(HEALTH_ENDPOINT, timeout=2)
        print("❌ Services are still running")
        return False
    except requests.RequestException:
        print("✅ Services are stopped (API is not responding)")

    print("\n=== Test 1 Completed Successfully ===")
    return True


def main() -> int:
    """Main function to run the test."""
    success = test_start_stop_services()

    if success:
        print("\n✅ Test 1 passed: Start and stop services")
        return 0
    else:
        print("\n❌ Test 1 failed: Start and stop services")
        return 1


if __name__ == "__main__":
    sys.exit(main())
