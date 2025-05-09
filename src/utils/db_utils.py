"""
Database utility functions for GraphRAG project.
"""
import logging
import os
from typing import Optional
from packaging.version import parse as parse_version

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_chromadb_version(min_required: str = "1.0.7") -> bool:
    """
    Check if the installed ChromaDB version meets the minimum requirement.

    Args:
        min_required: Minimum required ChromaDB version

    Returns:
        True if version requirement is met, False otherwise
    """
    try:
        import chromadb
        current_version = chromadb.__version__

        logger.info(f"Installed ChromaDB version: {current_version}")

        if parse_version(current_version) < parse_version(min_required):
            logger.warning(
                f"ChromaDB version {current_version} is older than required {min_required}. "
                f"Please update ChromaDB to avoid potential issues."
            )
            return False

        logger.info(f"ChromaDB version {current_version} meets the minimum requirement of {min_required}")
        return True
    except ImportError:
        logger.error("ChromaDB is not installed. Please install it with 'pip install chromadb'")
        return False
    except Exception as e:
        logger.error(f"Error checking ChromaDB version: {e}")
        return False

def check_database_directories() -> bool:
    """
    Check if the required database directories exist and are writable.

    Returns:
        True if all directories are available, False otherwise
    """
    # Explicitly load environment variables from the config file
    from dotenv import load_dotenv
    config_env_path = os.path.expanduser("~/.graphrag/config.env")
    if os.path.exists(config_env_path):
        logger.info(f"Loading environment variables from {config_env_path} in check_database_directories")
        load_dotenv(config_env_path)

    # Check ChromaDB directory
    chroma_dir = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chromadb")
    logger.info(f"ChromaDB directory from environment: {chroma_dir}")

    # Convert to absolute path if it's a relative path
    if not os.path.isabs(chroma_dir):
        chroma_dir = os.path.abspath(chroma_dir)
        logger.info(f"Converted to absolute path: {chroma_dir}")

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
        logger.error(f"Failed to access or create directory: {chroma_dir}")
        return False

def get_chromadb_info() -> Optional[dict]:
    """
    Get information about the ChromaDB installation.

    Returns:
        Dictionary with ChromaDB information or None if not available
    """
    try:
        import chromadb
        import platform
        import sys

        return {
            "version": chromadb.__version__,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": platform.platform(),
            "is_64bit": sys.maxsize > 2**32
        }
    except ImportError:
        logger.error("ChromaDB is not installed")
        return None
    except Exception as e:
        logger.error(f"Error getting ChromaDB info: {e}")
        return None

if __name__ == "__main__":
    # Example usage
    check_chromadb_version()
    check_database_directories()
    print(get_chromadb_info())
