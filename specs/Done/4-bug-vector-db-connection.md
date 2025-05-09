# Bug Report: Vector Database Connection Issue (CRITICAL)

## Description
The vector database (ChromaDB) is not connecting properly, causing the API to report a degraded status and all document-related operations to fail with a 500 error. This is a critical issue that prevents all document-related functionality from working, including adding documents, searching, and retrieving concepts.

## Steps to Reproduce
1. Run the regression tests with `python -m tests.regression.run_all_tests`
2. Observe that all tests fail with a 500 error when trying to add a document
3. Check the API health endpoint and see that `vector_db_connected` is `false`
4. Examine the logs to see that the ChromaDB directory is not being found or accessed properly

## Expected Behavior
The vector database should connect properly, and the API should report a healthy status with `vector_db_connected` set to `true`. All document-related operations should work correctly.

## Actual Behavior
The vector database fails to connect, and the API reports a degraded status with `vector_db_connected` set to `false`. All document-related operations fail with a 500 error. The API server logs show that the ChromaDB directory is not being found or accessed properly.

## Root Cause Analysis
After extensive investigation, we identified two related issues:

1. **Path Resolution Issue**: The `check_database_directories` function in `src/utils/db_utils.py` is using a relative path (`./data/chromadb`) that depends on the current working directory. When the API server is started by the service script, the current working directory is different, so the directory is not found.

2. **Environment Variable Mismatch**: The environment variable `CHROMA_PERSIST_DIRECTORY` is set to `/Users/andyspamer/.graphrag/data/chromadb` in the config file, but this value is not being properly loaded or used by the API server. Instead, the code is falling back to the default value of `./data/chromadb`.

We verified this by:
- Checking the API health endpoint, which showed `vector_db_connected: false`
- Examining the config file at `/Users/andyspamer/.graphrag/config.env`, which has `CHROMA_PERSIST_DIRECTORY=/Users/andyspamer/.graphrag/data/chromadb`
- Checking that the directory `/Users/andyspamer/Dev-Space/pythonProjects/graphRAG/data/chromadb` exists but is not being used
- Creating the directory `/Users/andyspamer/.graphrag/data/chromadb` manually, but the API still couldn't connect

## Comprehensive Fix Required
To fully resolve this issue, we need to implement the following changes:

1. **Update Path Resolution**: Modify the `check_database_directories` function to always use absolute paths:

```python
def check_database_directories() -> bool:
    """
    Check if the required database directories exist and are writable.
    
    Returns:
        True if all directories are available, False otherwise
    """
    # Check ChromaDB directory
    chroma_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chromadb")
    
    # Convert to absolute path if it's a relative path
    if not os.path.isabs(chroma_dir):
        chroma_dir = os.path.abspath(chroma_dir)
    
    try:
        # Create directory if it doesn't exist
        if not os.path.exists(chroma_dir):
            logger.info(f"Creating ChromaDB directory: {chroma_dir}")
            os.makedirs(chroma_dir, exist_ok=True)
        
        # Check if directory is writable
        test_file = os.path.join(chroma_dir, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        
        logger.info(f"ChromaDB directory is available and writable: {chroma_dir}")
        return True
    except Exception as e:
        logger.error(f"Error checking database directories: {e}")
        return False
```

2. **Update VectorDatabase Class**: Ensure the VectorDatabase class also uses absolute paths and properly loads environment variables:

```python
def __init__(self, persist_directory: Optional[str] = None):
    """
    Initialize vector database connection.

    Args:
        persist_directory: Directory to persist vector database
            (default: from environment variable)
    """
    # Explicitly load environment variables to ensure they're available
    load_dotenv(os.path.expanduser("~/.graphrag/config.env"))
    
    self.persist_directory = persist_directory or os.getenv(
        "CHROMA_PERSIST_DIRECTORY", "./data/chromadb"
    )
    
    # Convert to absolute path if it's a relative path
    if not os.path.isabs(self.persist_directory):
        self.persist_directory = os.path.abspath(self.persist_directory)
        
    # Log the directory being used for debugging
    logger.info(f"Using ChromaDB directory: {self.persist_directory}")
        
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

3. **Update API Server**: Ensure the API server properly loads environment variables:

```python
# At the top of src/api/server.py
import os
from dotenv import load_dotenv

# Load environment variables from the config file
load_dotenv(os.path.expanduser("~/.graphrag/config.env"))
```

4. **Add Diagnostic Logging**: Add more detailed logging to help diagnose similar issues in the future:

```python
# In the VectorDatabase.verify_connection method
def verify_connection(self) -> bool:
    """
    Verify vector database connection.

    Returns:
        True if connection is successful, False otherwise.
    """
    try:
        logger.info(f"Verifying connection to ChromaDB at {self.persist_directory}")
        self.connect()
        # Check if we can get collection info
        assert self.collection is not None, "Collection is None after connect()"
        count = self.collection.count()
        logger.info(f"Successfully connected to ChromaDB. Collection contains {count} documents.")
        return True
    except Exception as e:
        logger.error(f"Vector database connection error: {e}")
        return False
```

## Resolution Path
1. Implement the fixes described above
2. Restart the GraphRAG services
3. Verify that the API health endpoint shows `vector_db_connected: true`
4. Run the regression tests again to confirm that document-related operations work correctly

## Additional Notes
- This is a critical bug that prevents all document-related functionality from working
- The fix is straightforward but requires careful attention to environment variable loading and path resolution
- After fixing this issue, we should add more robust error handling and diagnostics to prevent similar issues in the future