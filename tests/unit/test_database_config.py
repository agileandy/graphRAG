import os
import pytest
from unittest.mock import patch, MagicMock

# Assuming the relevant classes/functions are in these paths
# Adjust import paths if necessary
try:
    from src.database.neo4j_db import Neo4jDatabase
    from src.vector_database.vector_database import (
        VectorDatabase,
    )  # Assuming this is the correct path for VectorDatabase
except ImportError:
    pytest.fail(
        "Could not import database classes. Make sure the files exist and paths are correct (e.g., src.database.vector_db for VectorDatabase)."
    )


# Mocking environment variables for testing
@pytest.fixture(autouse=True)
def cleanup_env_vars():
    """Fixture to clean up environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


# --- Neo4j Database Tests (related to Bug 30) ---


def test_neo4j_uri_with_port():
    """Test Neo4j URI parsing when port is included."""
    os.environ["NEO4J_URI"] = "bolt://localhost:7687"
    os.environ["NEO4J_USER"] = "neo4j"
    os.environ["NEO4J_PASSWORD"] = "password"
    os.environ["NEO4J_DATABASE"] = "graphrag"

    # Mock the actual driver connection
    with patch("src.database.neo4j_db.GraphDatabase.driver") as mock_driver:
        db = Neo4jDatabase()
        mock_driver.assert_called_once_with(
            "bolt://localhost:7687", auth=("neo4j", "password")
        )
        assert db.database_name == "graphrag"


def test_neo4j_uri_without_port_adds_default():
    """Test Neo4j URI parsing when port is missing, should add default 7687."""
    os.environ["NEO4J_URI"] = "bolt://localhost:"  # Missing port after colon
    os.environ["NEO4J_USER"] = "neo4j"
    os.environ["NEO4J_PASSWORD"] = "password"
    os.environ["NEO4J_DATABASE"] = "graphrag"

    with patch("src.database.neo4j_db.GraphDatabase.driver") as mock_driver:
        db = Neo4jDatabase()
        # Should append the default port 7687
        mock_driver.assert_called_once_with(
            "bolt://localhost:7687", auth=("neo4j", "password")
        )
        assert db.database_name == "graphrag"


def test_neo4j_uri_without_port_and_colon_adds_default():
    """Test Neo4j URI parsing when port and colon are missing."""
    os.environ["NEO4J_URI"] = "bolt://localhost"  # Missing port and colon
    os.environ["NEO4J_USER"] = "neo4j"
    os.environ["NEO4J_PASSWORD"] = "password"
    os.environ["NEO4J_DATABASE"] = "graphrag"

    with patch("src.database.neo4j_db.GraphDatabase.driver") as mock_driver:
        db = Neo4jDatabase()
        # Should append the default port 7687
        mock_driver.assert_called_once_with(
            "bolt://localhost:7687", auth=("neo4j", "password")
        )
        assert db.database_name == "graphrag"


def test_neo4j_missing_env_vars():
    """Test Neo4j initialization with missing required environment variables."""
    # NEO4J_URI is missing
    os.environ["NEO4J_USER"] = "neo4j"
    os.environ["NEO4J_PASSWORD"] = "password"
    os.environ["NEO4J_DATABASE"] = "graphrag"

    with pytest.raises(KeyError):  # Or specific error raised by Neo4jDatabase
        Neo4jDatabase()


# --- Vector Database Tests (related to Bug 4, 9, 44) ---
# Assuming VectorDatabase is in src.vector_database.vector_database
# If it's in src.database.vector_db, adjust the patch path.
@patch(
    "src.vector_database.vector_database.chromadb.PersistentClient"
)  # Adjust if VectorDatabase path is different
@patch("os.path.abspath")
def test_vector_database_init_with_env_vars(mock_abspath, mock_client):
    """Test VectorDatabase initialization using environment variables."""
    mock_abspath.side_effect = lambda x: f"/abs/path/{x}"  # Simulate abspath

    os.environ["CHROMA_DB_IMPL"] = "duckdb+parquet"
    os.environ["CHROMA_DB_DIRECTORY"] = "test_chroma_dir"
    os.environ["CHROMA_TENANT"] = "my_tenant"
    os.environ["CHROMA_COLLECTION"] = "my_collection"

    db = VectorDatabase()

    mock_abspath.assert_called_once_with("test_chroma_dir")
    mock_client.assert_called_once_with(
        path="/abs/path/test_chroma_dir",
        tenant="my_tenant",  # Verify tenant is passed (Bug 44)
    )
    mock_client.return_value.get_or_create_collection.assert_called_once_with(
        name="my_collection"
    )
    assert db.collection_name == "my_collection"


@patch(
    "src.vector_database.vector_database.chromadb.PersistentClient"
)  # Adjust if VectorDatabase path is different
@patch("os.path.abspath")
def test_vector_database_init_default_tenant(mock_abspath, mock_client):
    """Test VectorDatabase initialization using default tenant."""
    mock_abspath.side_effect = lambda x: f"/abs/path/{x}"

    os.environ["CHROMA_DB_IMPL"] = "duckdb+parquet"
    os.environ["CHROMA_DB_DIRECTORY"] = "test_chroma_dir"
    # CHROMA_TENANT is NOT set
    os.environ["CHROMA_COLLECTION"] = "my_collection"

    db = VectorDatabase()

    mock_abspath.assert_called_once_with("test_chroma_dir")
    mock_client.assert_called_once_with(
        path="/abs/path/test_chroma_dir",
        tenant="default_tenant",  # Verify default tenant is passed (Bug 44)
    )
    mock_client.return_value.get_or_create_collection.assert_called_once_with(
        name="my_collection"
    )
    assert db.collection_name == "my_collection"


@patch(
    "src.vector_database.vector_database.chromadb.PersistentClient"
)  # Adjust if VectorDatabase path is different
@patch("os.path.abspath")
def test_vector_database_init_relative_path(mock_abspath, mock_client):
    """Test VectorDatabase initialization with a relative path."""
    mock_abspath.side_effect = lambda x: f"/abs/path/{x}"  # Simulate abspath conversion

    os.environ["CHROMA_DB_IMPL"] = "duckdb+parquet"
    os.environ["CHROMA_DB_DIRECTORY"] = "../relative/path"
    os.environ["CHROMA_TENANT"] = "my_tenant"
    os.environ["CHROMA_COLLECTION"] = "my_collection"

    VectorDatabase()

    # Verify abspath was called on the directory (Bug 4, 9)
    mock_abspath.assert_called_once_with("../relative/path")
    mock_client.assert_called_once_with(
        path="/abs/path/../relative/path",  # abspath result
        tenant="my_tenant",
    )


@patch(
    "src.vector_database.vector_database.chromadb.PersistentClient"
)  # Adjust if VectorDatabase path is different
def test_vector_database_missing_directory_env(mock_client):
    """Test VectorDatabase initialization with missing directory env var."""
    os.environ["CHROMA_DB_IMPL"] = "duckdb+parquet"
    # CHROMA_DB_DIRECTORY is missing
    os.environ["CHROMA_TENANT"] = "my_tenant"
    os.environ["CHROMA_COLLECTION"] = "my_collection"

    with pytest.raises(KeyError):  # Or specific error raised by VectorDatabase
        VectorDatabase()


@patch(
    "src.vector_database.vector_database.chromadb.PersistentClient"
)  # Adjust if VectorDatabase path is different
def test_vector_database_missing_collection_env(mock_client):
    """Test VectorDatabase initialization with missing collection env var."""
    os.environ["CHROMA_DB_IMPL"] = "duckdb+parquet"
    os.environ["CHROMA_DB_DIRECTORY"] = "test_chroma_dir"
    os.environ["CHROMA_TENANT"] = "my_tenant"
    # CHROMA_COLLECTION is missing

    with pytest.raises(KeyError):  # Or specific error raised by VectorDatabase
        VectorDatabase()
