# Bug Report: Services Not Stopping Properly

## Description
The GraphRAG services are not stopping properly when the `stop_services` function is called in the regression tests. This causes Test 1 (Start and Stop Services) to fail.

## Steps to Reproduce
1. Run the regression tests with `python -m tests.regression.run_all_tests`
2. Observe that Test 1 fails at the "Verifying services are stopped" step

## Expected Behavior
When the `stop_services` function is called, all GraphRAG services (API server, MPC server, Neo4j) should be stopped, and the API should no longer be accessible.

## Actual Behavior
After calling `stop_services`, the API server is still running and accessible, causing the test to fail.

## Possible Causes
1. The `stop_services` function in `tests/regression/test_utils.py` may not be properly terminating all processes
2. The PID files in `~/.graphrag/pids/` may not be accurate, causing the wrong processes to be terminated
3. The `pkill` command may not be finding all relevant processes

## Suggested Fix
Update the `stop_services` function in `tests/regression/test_utils.py` to be more thorough in stopping all services:

```python
def stop_services(process: Optional[subprocess.Popen] = None) -> bool:
    """
    Stop the GraphRAG services.
    
    Args:
        process: Process object returned by start_services
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if process:
            # Try to terminate the process gracefully
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't terminate
                process.kill()
        
        # Use the stop script to ensure all services are stopped
        result = subprocess.run(
            ["./tools/graphrag-service.sh", "stop"],
            capture_output=True,
            text=True
        )
        
        # Additional cleanup to make sure all processes are stopped
        subprocess.run(["pkill", "-f", "gunicorn"], check=False)
        subprocess.run(["pkill", "-f", "src.mpc.server"], check=False)
        
        # Wait a moment for processes to terminate
        time.sleep(2)
        
        return True
    except Exception as e:
        print(f"Error stopping services: {e}")
        return False
```

## Additional Notes
- This issue affects the reliability of the regression tests
- The fix should ensure that all services are properly stopped between tests to prevent interference