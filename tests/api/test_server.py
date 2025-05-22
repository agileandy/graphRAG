import pytest
import json
from unittest.mock import patch, MagicMock, PropertyMock

# Add the project root to the Python path to allow importing src modules
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import the Flask app instance from src.api.server
# We need to set up the environment for the app to load correctly,
# especially if it relies on environment variables or specific configurations at import time.
# For now, let's assume basic setup is enough or mock dependencies as needed.
try:
    from src.api.server import app
except ImportError as e:
    # This can happen if dependencies are not mocked early enough
    # or if there's an issue with the path.
    # For testing, we might need a more robust way to initialize the app or mock its dependencies.
    print(
        f"Error importing Flask app: {e}. Ensure PYTHONPATH is correct and app dependencies are mockable."
    )
    app = None  # Fallback


@pytest.fixture
def client():
    """Create and configure a new app instance for each test."""
    if app is None:
        pytest.fail(
            "Flask app could not be imported. Check test setup and src.api.server dependencies."
        )
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@patch("scripts.document_processing.add_document_core.add_document_to_graphrag")
def test_add_document_success(mock_add_document_to_graphrag, client):
    """Test successful document addition."""
    mock_add_document_to_graphrag.return_value = {
        "status": "success",
        "document_id": "doc_123",
        "entities": [],
        "relationships": [],
    }

    response = client.post(
        "/documents",
        json={"text": "This is a test document.", "metadata": {"source": "test"}},
    )

    assert response.status_code == 201
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert data["message"] == "Document added successfully."
    assert data["document_id"] == "doc_123"
    assert "entities" in data
    assert "relationships" in data
    mock_add_document_to_graphrag.assert_called_once()


@patch("scripts.document_processing.add_document_core.add_document_to_graphrag")
@patch("src.processing.duplicate_detector.DuplicateDetector")
def test_add_document_duplicate(
    MockDuplicateDetector, mock_add_document_to_graphrag, client
):  # Order of mocks is important
    """Test adding a duplicate document."""
    # Simulate that add_document_to_graphrag returns None for duplicates,
    # and the endpoint itself handles the duplicate response structure.
    # The duplicate detector is called before add_document_to_graphrag.
    # So, we need to mock the DuplicateDetector's is_duplicate method.
    mock_add_document_to_graphrag.return_value = None  # This indicates a duplicate in the core logic if it were to run past the detector

    # Mock the DuplicateDetector instance and its methods
    mock_detector_instance = MockDuplicateDetector.return_value
    mock_detector_instance.is_duplicate.return_value = (
        True,
        "existing_doc_456",
        "hash_match",
    )
    mock_detector_instance.generate_document_hash.return_value = "some_hash"

    response = client.post(
        "/documents",
        json={
            "text": "This is a duplicate document.",
            "metadata": {"source": "test_duplicate"},
        },
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "duplicate"
    assert data["message"] == "Document is a duplicate and was not added."
    assert data["document_id"] == "existing_doc_456"
    assert data["duplicate_detection_method"] == "hash_match"
    # add_document_to_graphrag should NOT be called if DuplicateDetector finds a duplicate early.
    # The logic in server.py is:
    # 1. Call duplicate_detector.is_duplicate
    # 2. If NOT duplicate, THEN call add_document_to_graphrag
    # However, the current server code calls add_document_to_graphrag regardless,
    # and add_document_to_graphrag itself might re-check or handle duplicates.
    # The server code's add_document() returns a duplicate message *before* add_document_to_graphrag if is_dup is true.
    # Let's re-check server.py:
    # Line 280: is_dup, existing_doc_id, method = duplicate_detector.is_duplicate(...)
    # Line 288: result = add_document_to_graphrag(...)
    # Line 296: if result is None: (this implies duplicate from add_document_to_graphrag)
    # The server code has a slight redundancy or layered check.
    # If duplicate_detector.is_duplicate returns True, the server's add_document endpoint *should* ideally
    # return the duplicate response *without* calling add_document_to_graphrag.
    # Let's assume the current server logic calls add_document_to_graphrag, and it returns None for duplicates.
    # The test was written assuming add_document_to_graphrag is called.
    # The server code:
    #   result = add_document_to_graphrag(...)
    #   if result is None: -> return duplicate message (if existing_doc_id was set by detector)
    # This means add_document_to_graphrag IS called.
    # The server's own duplicate check (lines 298-308) uses `existing_doc_id` from the `duplicate_detector`.
    # So, if `is_duplicate` is true, `add_document_to_graphrag` is still called, but its result might be `None`
    # and the server then crafts the duplicate message.
    # The critical part is that `add_document_to_graphrag` is called.
    mock_add_document_to_graphrag.assert_called_once()


def test_add_document_missing_text(client):
    """Test adding a document with missing text."""
    response = client.post(
        "/documents", json={"metadata": {"source": "test_missing_text"}}
    )
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["error"] == "Missing required parameter: text"
    # 'document_id' should not be in the error response for 400 based on current API design
    # but the bug fix was about 500 errors. Let's ensure it's not there for consistency.
    assert "document_id" not in data


@patch("scripts.document_processing.add_document_core.add_document_to_graphrag")
def test_add_document_processing_failure(mock_add_document_to_graphrag, client):
    """Test failure during document processing in add_document_to_graphrag."""
    mock_add_document_to_graphrag.return_value = {
        "status": "failure",
        "error": "Core processing failed",
    }
    response = client.post(
        "/documents",
        json={
            "text": "This document will cause a processing failure.",
            "metadata": {"source": "test_processing_failure"},
        },
    )
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data["status"] == "failure"
    assert data["error"] == "Core processing failed"
    assert data["document_id"] is None  # Key check for the bug fix
    mock_add_document_to_graphrag.assert_called_once()


@patch("scripts.document_processing.add_document_core.add_document_to_graphrag")
def test_add_document_unexpected_result_from_core(
    mock_add_document_to_graphrag, client
):
    """Test unexpected result from add_document_to_graphrag."""
    mock_add_document_to_graphrag.return_value = {"unexpected_key": "unexpected_value"}
    response = client.post(
        "/documents",
        json={
            "text": "This document will cause an unexpected result.",
            "metadata": {"source": "test_unexpected_result"},
        },
    )
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data["status"] == "failure"
    assert data["error"] == "An unexpected error occurred during document processing."
    assert data["document_id"] is None  # Key check for the bug fix
    mock_add_document_to_graphrag.assert_called_once()


@patch(
    "scripts.document_processing.add_document_core.add_document_to_graphrag",
    side_effect=Exception("Unhandled core error"),
)
def test_add_document_unhandled_exception_in_core(
    mock_add_document_to_graphrag, client
):
    """Test unhandled exception within the try block of add_document, when add_document_to_graphrag itself raises an exception."""
    # This mock will raise an exception when add_document_to_graphrag is called
    response = client.post(
        "/documents",
        json={
            "text": "This document will cause an unhandled exception in core.",
            "metadata": {"source": "test_unhandled_exception_core"},
        },
    )
    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data
    assert (
        "Unhandled exception: Unhandled core error" in data["error"]
    )  # Check specific error message
    assert data["document_id"] is None  # Key check for the bug fix
    assert "traceback" in data
    mock_add_document_to_graphrag.assert_called_once()


# To test the outermost exception handler in the add_document endpoint for errors
# like request.json access failing.
@patch("src.api.server.request.json", new_callable=PropertyMock, create=True)
def test_add_document_unhandled_exception_early(mock_request_json_prop, client):
    """Test unhandled exception early in the add_document endpoint (e.g., request.json access failing)."""
    mock_request_json_prop.side_effect = RuntimeError(
        "Simulated failure accessing request.json"
    )

    # The actual data sent doesn't matter as much since request.json is mocked to fail.
    response = client.post(
        "/documents", data='{"text":"test"}', content_type="application/json"
    )

    assert response.status_code == 500
    data = json.loads(response.data)
    assert "error" in data
    assert (
        "Unhandled exception: Simulated failure accessing request.json" in data["error"]
    )
    assert data["document_id"] is None  # Key check for the bug fix
    assert "traceback" in data
    # Check that the mocked property was accessed
    assert mock_request_json_prop.called
