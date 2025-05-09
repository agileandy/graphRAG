# Bug Report: GraphRAG Service Script Python Path Issue

## Description
The `graphrag-service.sh` script was using the system's default `python` and `gunicorn` commands instead of the ones from the virtual environment. This caused the services to fail to start during regression testing.

## Steps to Reproduce
1. Run the regression tests with `python -m tests.regression.run_all_tests`
2. Observe that Test 1 passes but all other tests fail because the API cannot be started

## Expected Behavior
All services should start correctly using the Python interpreter and packages from the virtual environment.

## Actual Behavior
The MPC server fails to start with the error: `./tools/graphrag-service.sh: line 100: python: command not found`
The API server also fails to start because gunicorn is not found in the system path.

## Fix Applied
Modified `tools/graphrag-service.sh` to use the Python interpreter and gunicorn from the virtual environment:
1. Changed `python -m src.mpc.server` to `.venv-py312/bin/python -m src.mpc.server`
2. Changed `gunicorn` to `.venv-py312/bin/gunicorn`

## Additional Notes
- This issue highlights the importance of using absolute paths to the virtual environment's binaries in service scripts
- Consider adding a check at the beginning of the script to verify that the virtual environment exists and is properly set up