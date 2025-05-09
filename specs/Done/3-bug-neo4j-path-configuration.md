# Bug Report: Neo4j Path Configuration

## Description
The GraphRAG service script is configured to use Neo4j from `~/.graphrag/neo4j`, but Neo4j is actually installed via Homebrew at `/opt/homebrew/bin/neo4j`.

## Steps to Reproduce
1. Run the regression tests with `python -m tests.regression.run_all_tests`
2. Observe that all tests fail because the services cannot be started
3. Check the logs and see that Neo4j cannot be found at the configured path

## Expected Behavior
The GraphRAG service script should use the correct path to the Neo4j installation.

## Actual Behavior
The script is looking for Neo4j at `~/.graphrag/neo4j/bin/neo4j`, but it's actually installed at `/opt/homebrew/bin/neo4j`.

## Fix Applied
Updated the config file to use the correct Neo4j home directory:
```
NEO4J_HOME=/opt/homebrew
```

## Additional Notes
- Consider adding a check in the service script to verify that Neo4j is installed and accessible
- The script should provide more helpful error messages when Neo4j cannot be found
- Consider using `which neo4j` to dynamically find the Neo4j installation path