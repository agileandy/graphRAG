# Bug Report: ChromaDB Directory Mismatch

## Description
There is a mismatch between the ChromaDB directory specified in the environment variable and the directory used by the code. This causes the vector database to fail to connect, resulting in a degraded API status and all document-related operations failing with a 500 error.

## Steps to Reproduce
1. Run the regression tests with `python -m tests.regression.run_all_tests`
2. Observe that all tests fail with a 500 error when trying to add a document
3. Check the API health endpoint and see that `vector_db_connected` is `false`

## Expected Behavior
The vector database should connect to the directory specified in the environment variable.

## Actual Behavior
The vector database is trying to connect to a different directory than the one specified in the environment variable.

## Root Cause
The environment variable `CHROMA_PERSIST_DIRECTORY` is set to `/Users/andyspamer/.graphrag/data/chromadb` in the config file, but the code is using a default value of `./data/chromadb` when the environment variable is not found.

## Fix Required
1. Ensure the environment variable is properly loaded in the API server
2. Update the VectorDatabase class to use the correct directory:

```python
def __init__(self, persist_directory: Optional[str] = None):
    """
    Initialize vector database connection.

    Args:
        persist_directory: Directory to persist vector database
            (default: from environment variable)
    """
    # Load environment variables
    load_dotenv()
    
    self.persist_directory = persist_directory or os.getenv(
        "CHROMA_PERSIST_DIRECTORY", "./data/chromadb"
    )
    
    # Convert to absolute path if it's a relative path
    if not os.path.isabs(self.persist_directory):
        self.persist_directory = os.path.abspath(self.persist_directory)
        
    self.client = None
    self.collection = None
    self.duplicate_detector = None

    # Check ChromaDB version
    self.version_check_passed = check_chromadb_version()
    if not self.version_check_passed:
        logger.warning("ChromaDB version check failed. Some features may not work correctly.")

    # Check database directories
    check_database_directories()
```

3. Make sure the config.env file is properly loaded by the API server

## Additional Notes
- This is a critical bug that prevents all document-related functionality from working
- The fix is straightforward and should be implemented immediately