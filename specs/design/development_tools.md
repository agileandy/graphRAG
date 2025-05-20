# GraphRAG Development Tools

This document describes the development tools available in the GraphRAG project.

## UV Wrapper Script

The UV wrapper script (`tools/uvrun.sh`) ensures that Python commands are run using UV, which is the preferred package manager and runtime for the GraphRAG project.

### Usage

```bash
# Install dependencies
./tools/uvrun.sh install [packages]

# Run a Python script
./tools/uvrun.sh run [script.py] [args]

# Run tests
./tools/uvrun.sh test [test_file.py]

# Run linting
./tools/uvrun.sh lint [directory]

# Run formatting
./tools/uvrun.sh format [directory]

# Activate the virtual environment
./tools/uvrun.sh shell
```

## Bug Tracking Client

The bug tracking client (`tools/bug_client.py`) provides a robust interface to the bug tracking system. It includes error handling, retries, and fallback mechanisms.

### Usage

```bash
# Add a bug
./tools/bug_client.py add "Bug description" "Bug cause"

# Add a critical bug
./tools/bug_client.py add "Critical bug description" "Bug cause" --critical

# List all bugs
./tools/bug_client.py list

# Sync pending bugs
./tools/bug_client.py sync
```

## Test Environment Setup

The test environment setup script (`tools/test_setup.py`) sets up the test environment for GraphRAG by starting required services, checking port availability, and providing a clean shutdown mechanism.

### Usage

```bash
# Start the test environment
./tools/test_setup.py --start

# Stop the test environment
./tools/test_setup.py --stop

# Show the status of the test environment
./tools/test_setup.py --status
```

## Regression Test Runner

The regression test runner (`tools/run_regression_tests.sh`) runs the regression tests with proper environment setup.

### Usage

```bash
# Run all regression tests
./tools/run_regression_tests.sh
```

## Port Configuration

The port configuration module (`src/config/ports.py`) provides a centralized location for all port configurations used by GraphRAG services. It also includes utility functions for checking port availability and resolving conflicts.

### Default Port Assignments

| Service | Port | Description |
|---------|------|-------------|
| api | 5001 | Main GraphRAG API |
| mpc | 8765 | Message Passing Communication server |
| mcp | 8767 | Model Context Protocol server |
| bug_mcp | 5005 | Bug tracking MCP server |
| neo4j_bolt | 7687 | Neo4j Bolt protocol |
| neo4j_http | 7474 | Neo4j HTTP API |
| neo4j_https | 7473 | Neo4j HTTPS API |
| prometheus | 9090 | Prometheus metrics |
| grafana | 3000 | Grafana dashboard |

### Environment Variables

You can override the default port assignments by setting environment variables with the prefix `GRAPHRAG_PORT_`. For example:

```bash
# Override the MCP server port
export GRAPHRAG_PORT_MCP=8768
```

## Best Practices

1. **Always use UV for Python commands**
   - Use the UV wrapper script (`tools/uvrun.sh`) for all Python commands
   - This ensures consistent dependency management and runtime environment

2. **Use the centralized port configuration**
   - Import port settings from `src.config.ports` instead of hardcoding them
   - This prevents port conflicts and ensures consistent configuration

3. **Report bugs using the bug tracking client**
   - Use `tools/bug_client.py` instead of directly editing bug files
   - This ensures proper error handling and fallback mechanisms

4. **Set up the test environment before running tests**
   - Use `tools/test_setup.py` to set up the test environment
   - This ensures all required services are running with the correct configuration

5. **Use the regression test runner for comprehensive testing**
   - Use `tools/run_regression_tests.sh` to run all regression tests
   - This ensures proper environment setup and bug reporting
