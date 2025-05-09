# Bug Report: Port Configuration Mismatch

## Description
There was a mismatch between the port configured in the `.graphrag/config.env` file (5000) and the port expected by the test suite (5001). This caused all tests to fail because the API server couldn't be reached.

## Steps to Reproduce
1. Run the regression tests with `python -m tests.regression.run_all_tests`
2. Observe that all tests fail because the API cannot be reached at port 5001

## Expected Behavior
The API server should be configured to use port 5001 as expected by the test suite.

## Actual Behavior
The API server was configured to use port 5000 in the config file, but the test suite was looking for it on port 5001. Additionally, port 5000 was already in use by another process, causing the API server to fail to start.

## Fix Applied
1. Updated the config file to use port 5001: `GRAPHRAG_API_PORT=5001`
2. Killed the process that was using port 5000

## Additional Notes
- Consider adding a check in the test suite to verify that the port in the config file matches the port expected by the tests
- Alternatively, make the test suite read the port from the config file to ensure consistency