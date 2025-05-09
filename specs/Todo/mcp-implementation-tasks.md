# MCP Implementation Tasks

This document outlines the ordered atomic tasks required to implement the Model Context Protocol (MCP) server for the GraphRAG project. The MCP server will allow AI agents to interact with the GraphRAG system through standardized tools.

## Definition of Done
- AI agents can call the GraphRAG tools through an MCP client
- All 11 required tools are implemented and functional
- The MCP server follows the Model Context Protocol specification
- The MCP server can be started and stopped reliably
- Documentation is provided for integrating with AI agents

## Ordered Tasks

### 1. Create MCP Server Foundation
- **Task 1.1**: Create the basic MCP server implementation in `src/mpc/mcp_server.py`
- **Task 1.2**: Implement the JSON-RPC 2.0 protocol handlers (initialize, getTools, invokeTool)
- **Task 1.3**: Create a wrapper script at `tools/graphrag-mcp` to start the MCP server
- **Task 1.4**: Add configuration options for host, port, and environment variables

### 2. Implement MCP Tools
- **Task 2.1**: Create tool definitions for all 11 required tools:
  - ping
  - search
  - concept
  - documents
  - books-by-concept
  - related-concepts
  - passages-about-concept
  - add-document
  - add-folder
  - job-status
  - list-jobs
  - cancel-job
- **Task 2.2**: Implement tool handlers that bridge between MCP requests and the existing MPC server functionality
- **Task 2.3**: Add proper error handling and validation for all tool parameters
- **Task 2.4**: Implement asynchronous job handling for long-running operations

### 3. Create Client Configuration
- **Task 3.1**: Create a sample `mcp_settings.json` file for AI agent integration
- **Task 3.2**: Document the environment variables required for the MCP server
- **Task 3.3**: Create a configuration utility to generate the correct settings for different environments

### 4. Testing and Validation
- **Task 4.1**: Enhance the existing `tests/test_mcp_server.py` to test all tools
- **Task 4.2**: Create a simple client example in `scripts/mcp_client_example.py`
- **Task 4.3**: Test integration with an AI agent (Claude or similar)
- **Task 4.4**: Verify that all tools work correctly with the GraphRAG system

### 5. Docker Integration
- **Task 5.1**: Update the Docker configuration to start the MCP server
- **Task 5.2**: Configure port mappings for the MCP server
- **Task 5.3**: Update the Docker documentation with MCP server information

### 6. Documentation
- **Task 6.1**: Create comprehensive documentation for the MCP server in `docs/mcp_server_setup.md`
- **Task 6.2**: Update the main README.md with MCP server information
- **Task 6.3**: Create examples of using the MCP server with different AI agents
- **Task 6.4**: Document troubleshooting steps for common issues

### 7. Service Management
- **Task 7.1**: Update the service management scripts to include the MCP server
- **Task 7.2**: Implement proper logging for the MCP server
- **Task 7.3**: Add health checks for the MCP server

## Implementation Notes

### MCP vs MPC
The current codebase has an MPC (Message Passing Communication) server, but we need to implement an MCP (Model Context Protocol) server. The MCP server will use the JSON-RPC 2.0 protocol and follow the Model Context Protocol specification, while leveraging the existing MPC server functionality.

### Tool Implementation
Each tool should:
1. Accept parameters as defined in the MCP specification
2. Validate input parameters
3. Call the appropriate GraphRAG functionality
4. Return results in the expected format
5. Handle errors gracefully

### Configuration
The MCP server should be configurable through:
1. Command-line arguments
2. Environment variables
3. Configuration files

### Security Considerations
- The MCP server should validate all inputs
- Consider adding authentication for production environments
- Implement rate limiting to prevent abuse

### Performance
- Long-running operations should be handled asynchronously
- Consider implementing caching for frequently used operations
- Monitor memory usage, especially for large document operations