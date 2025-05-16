import pytest

from tests.regression.test_utils import start_services, stop_services, check_api_health, wait_for_api_ready

def test_start_stop_servers():
    """Verify clean server start/stop"""
    print("\nTesting server start/stop...")
    process = None
    try:
        # Start services
        success, process = start_services()
        assert success, "Failed to start services"
        print("Services started successfully.")

        # Check if API is healthy
        is_healthy, health_data = check_api_health()
        assert is_healthy, f"API is not healthy after start: {health_data}"
        print("API is healthy after start.")

    finally:
        # Stop services
        if process:
            stop_success = stop_services(process)
            assert stop_success, "Failed to stop services"
            print("Services stopped successfully.")

        # Verify services are stopped
        is_healthy, health_data = check_api_health()
        assert not is_healthy, f"API is still healthy after stop: {health_data}"
        print("API is not healthy after stop (correct).")


def test_server_restart():
    """Test server restart with persistence"""
    print("\nTesting server restart...")
    process1 = None
    process2 = None
    try:
        # Start services
        success1, process1 = start_services()
        assert success1, "Failed to start services for restart test (first start)"
        print("Services started successfully for restart test (first start).")

        # Check if API is healthy
        is_healthy1, health_data1 = check_api_health()
        assert is_healthy1, f"API is not healthy after first start: {health_data1}"
        print("API is healthy after first start.")

        # Stop services
        stop_success1 = stop_services(process1)
        assert stop_success1, "Failed to stop services for restart test (first stop)"
        print("Services stopped successfully for restart test (first stop).")

        # Verify services are stopped
        is_healthy_after_stop, health_data_after_stop = check_api_health()
        assert not is_healthy_after_stop, f"API is still healthy after first stop: {health_data_after_stop}"
        print("API is not healthy after first stop (correct).")

        # Start services again (restart)
        success2, process2 = start_services()
        assert success2, "Failed to start services for restart test (second start)"
        print("Services started successfully for restart test (second start).")

        # Check if API is healthy after restart
        is_healthy2, health_data2 = check_api_health()
        assert is_healthy2, f"API is not healthy after restart: {health_data2}"
        print("API is healthy after restart.")

        # Note: Persistence testing (e.g., data still exists) would require
        # adding data before the first stop and verifying it exists after the second start.
        # This is covered in database operation tests.

    finally:
        # Stop services after restart test
        if process2:
            stop_success2 = stop_services(process2)
            assert stop_success2, "Failed to stop services for restart test (second stop)"
            print("Services stopped successfully for restart test (second stop).")

        # Verify services are stopped
        is_healthy_after_restart_stop, health_data_after_restart_stop = check_api_health()
        assert not is_healthy_after_restart_stop, f"API is still healthy after second stop: {health_data_after_restart_stop}"
        print("API is not healthy after second stop (correct).")