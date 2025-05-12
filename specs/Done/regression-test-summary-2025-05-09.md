# GraphRAG Regression Test Summary - 2025-05-09

## Test Results

### Model Context Protocol (MCP) Server Test
- **Status**: PASSED
- **Issues Fixed**:
  - Port configuration mismatch between MCP server and tests
  - WebSocket connection timeout handling in test utilities

### Message Passing Communication (MPC) Server Test
- **Status**: FAILED
- **Issues**:
  - MPC server fails to start with no error message
  - Connection to MPC server at ws://localhost:8766 fails

## Bug Reports

1. **MCP server not running or using incorrect protocol**
   - Description: The server at port 8765 is not a Model Context Protocol server but a Message Passing Communication server
   - Cause: The test_model_context_server.py test fails with 'Missing required parameter: action'
   - Status: Fixed

2. **Port configuration mismatch between MCP server and tests**
   - Description: The MCP server is configured to run on port 8766 by default, but the tests were looking for it on port 8767
   - Cause: The test was updated to use port 8767 and the server was manually started on port 8767
   - Status: Fixed

3. **MPC server fails to start**
   - Description: The MPC server fails to start with no error message
   - Cause: The test_message_passing_server.py test fails with 'Failed to connect to Message Passing server at ws://localhost:8766'
   - Status: Open

## Recommendations

1. Update the configuration to use consistent port numbers across the codebase
2. Add better error handling and logging to the MPC server startup
3. Implement a health check endpoint for both MCP and MPC servers
4. Add a script to start all required services for testing

## Next Steps

1. Fix the MPC server startup issue
2. Run the full regression test suite again
3. Update the documentation with the correct port configurations
