# Contributing to GraphRAG Tests

This guide provides information about contributing to the GraphRAG test suite.

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements-test.txt
   ```

2. Set up environment:
   ```bash
   cp tests/.env.example tests/.env
   # Edit .env with your configuration
   ```

3. Run setup verification:
   ```bash
   python tests/check_test_setup.py
   ```

## Test Organization

Tests are organized into two main suites:

1. Web API Tests (`web_api_suite/`)
   - Tests for the HTTP/REST API endpoints
   - Uses standard pytest
   - Synchronous HTTP requests

2. MCP Tests (`mcp_suite/`)
   - Tests for the Model Context Protocol
   - Uses pytest-asyncio
   - WebSocket communication

## Writing New Tests

### File Naming

- Web API tests: `[number]_web_test_[feature].py`
- MCP tests: `[number]_mcp_test_[feature].py`
- Use two digits for numbering (01, 02, etc.)

### Test Structure

1. Use common imports:
   ```python
   from tests.common_utils.test_utils import (
       print_test_result,
       sync_mcp_invoke_tool,  # for MCP tests
       add_test_document,     # for Web API tests
       run_pytest_async       # for async tests
   )
   ```

2. Follow the standard format:
   ```python
   def test_feature_name() -> None:
       """Test description."""
       print("\nTesting feature...")

       # Test implementation
       success, result = ...

       print_test_result(
           "Test Name",
           success,
           "Message about result"
       )
   ```

3. Use provided utilities:
   - Use test data generators
   - Use response type hints
   - Use synchronous wrappers for async calls

### Error Handling

1. Always check success/failure:
   ```python
   success, result = some_operation()
   if not success:
       print_test_result(
           "Operation Name",
           False,
           f"Failed: {result.get('error', 'Unknown error')}"
       )
       return
   ```

2. Clean up after tests:
   ```python
   try:
       # Test code
   finally:
       # Cleanup code
   ```

3. Use proper typing:
   ```python
   from typing import Dict, Any, Tuple

   WebResponse = Dict[str, Any]
   def my_test() -> Tuple[bool, WebResponse]:
   ```

## Test Documentation

1. Module docstring:
   ```python
   """Test [feature] functionality for the [Web API/MCP] server."""
   ```

2. Function docstring:
   ```python
   def test_something() -> None:
       """Test specific aspect or scenario.

       Describe:
       1. What is being tested
       2. Expected behavior
       3. Any special conditions
       """
   ```

3. Comments for complex logic:
   ```python
   # Explain non-obvious steps
   complex_operation()

   # Describe why certain checks are needed
   if condition:
       handle_special_case()
   ```

## Running Tests

1. Full suite:
   ```bash
   pytest
   ```

2. Specific suite:
   ```bash
   pytest tests/web_api_suite/
   pytest tests/mcp_suite/
   ```

3. Single test:
   ```bash
   pytest tests/web_api_suite/01_web_test_server_start_stop.py
   ```

4. With coverage:
   ```bash
   pytest --cov=src --cov-report=html
   ```

## Best Practices

1. Test Independence
   - Tests should not depend on each other
   - Each test should clean up after itself
   - Use fresh test data for each test

2. Clear Assertions
   - Use descriptive test names
   - Clear success/failure messages
   - Explain edge cases

3. Error Handling
   - Graceful failure handling
   - Informative error messages
   - Proper cleanup on failure

4. Performance
   - Minimize test duration
   - Clean up resources
   - Use parallel testing when possible

5. Maintenance
   - Keep tests up to date
   - Remove obsolete tests
   - Update documentation

## Review Process

1. Before submitting:
   - Run full test suite
   - Check code formatting
   - Update documentation
   - Verify cleanup works

2. Pull Request:
   - Clear description
   - List of changes
   - Test results
   - Any new dependencies

## Getting Help

- Check existing test files for examples
- Review test_utils.py for available helpers
- See README.md for common issues
- Open an issue for questions