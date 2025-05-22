import os
import pytest
from unittest.mock import patch, MagicMock

# Assuming the relevant classes/functions are in these paths
# Adjust import paths if necessary
try:
    from src.processing.concept_extractor import (
        ConceptExtractor,
        smart_chunk_text,
        _is_valid_concept,
        DOMAIN_STOPWORDS,
        load_llm_config as load_concept_extractor_llm_config,
    )
    from src.llm.llm_provider import (
        create_llm_provider,
        OllamaProvider,
        load_llm_config as load_provider_llm_config,
    )
except ImportError:
    pytest.fail(
        "Could not import processing/LLM classes. Make sure the files exist and paths are correct."
    )


# Mocking environment variables for testing
@pytest.fixture(autouse=True)
def cleanup_env_vars():
    """Fixture to clean up environment variables after each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


# --- Concept Extraction Tests (related to Bug 34, 37) ---


def test_smart_chunk_text_basic():
    """Test basic chunking."""
    text = "This is the first sentence. This is the second sentence."
    # Assuming smart_chunk_text is from concept_extractor, not document_processor for this test's context
    chunks = smart_chunk_text(
        text, chunk_size=50, overlap=10
    )  # smart_chunk_text in concept_extractor might have different signature
    assert len(chunks) > 0
    # The smart_chunk_text in concept_extractor.py uses document_processor's smart_chunk_text.
    # Let's assume the test is for the one in document_processor via concept_extractor's _chunk_text
    # The direct test of smart_chunk_text should be on document_processor's version.
    # For now, let's assume this test is valid for the behavior expected from the bug report.
    assert all(
        len(chunk) <= 50 + 10 for chunk in chunks
    )  # Max size can be slightly larger due to word boundaries
    assert "".join(chunks).replace(" ", "").replace("\n", "") == text.replace(
        " ", ""
    ).replace("\n", "")


def test_smart_chunk_text_with_paragraphs():
    """Test chunking preserves paragraph breaks (Bug 34)."""
    text = "Paragraph 1 sentence 1.\n\nParagraph 2 sentence 1."
    # Assuming smart_chunk_text from document_processor is used by concept_extractor._chunk_text
    chunks = smart_chunk_text(
        text, chunk_size=100, overlap=20, semantic_boundaries=True
    )
    assert len(chunks) >= 2
    assert "Paragraph 1 sentence 1." in "".join(chunks)
    assert "Paragraph 2 sentence 1." in "".join(chunks)


def test_smart_chunk_text_large_paragraph():
    """Test chunking handles large paragraphs by splitting sentences (Bug 34)."""
    long_sentence = "This is a very long sentence that should be split." * 10
    text = f"Short sentence. {long_sentence} Another short sentence."
    chunks = smart_chunk_text(text, chunk_size=50, overlap=10, semantic_boundaries=True)
    assert len(chunks) > 2
    assert all(len(chunk) <= 50 + 10 for chunk in chunks)


def test__is_valid_concept_with_stopwords():
    """Test _is_valid_concept filters concepts with stopwords (Bug 37)."""
    # Ensure "part" is in stopwords for the test
    original_stopwords = DOMAIN_STOPWORDS["general"].copy()
    DOMAIN_STOPWORDS["general"].add("part")

    # Assuming ConceptExtractor instance is needed to call _is_valid_concept
    # Or if _is_valid_concept is a static/standalone function, call it directly.
    # From the bug report, it seems _is_valid_concept is part of ConceptExtractor.
    # For simplicity, let's assume we can test _is_valid_concept directly or via an instance.
    # If it's an instance method, we'd need to instantiate ConceptExtractor.
    # Let's assume it's a static method or we are testing the standalone version.
    assert _is_valid_concept("Valid concept") is True
    assert _is_valid_concept("Concept part of something") is False
    assert _is_valid_concept("Part of a concept") is False
    assert _is_valid_concept("Something is part") is False
    assert _is_valid_concept("Just a part") is False
    assert _is_valid_concept("Another valid concept.") is True

    DOMAIN_STOPWORDS["general"] = original_stopwords  # Restore original


# --- LLM Provider Tests (related to Bug 35, 36, 40) ---


@patch("src.llm.llm_provider.OllamaProvider")
@patch("src.llm.llm_provider.OpenAIProvider")  # Assuming OpenAIProvider exists
@patch("src.llm.llm_provider.OpenRouterProvider")  # Assuming OpenRouterProvider exists
def test_create_llm_provider_ollama(mock_openrouter, mock_openai, mock_ollama):
    """Test creating Ollama provider with correct parameters (Bug 36, 40)."""
    config = {
        "type": "ollama",  # Changed from "provider" to "type" as per create_llm_provider
        "api_base": "http://localhost:11434",
        "model": "llama2",
        "embedding_model": "nomic-embed-text",
    }
    create_llm_provider(config)
    mock_ollama.assert_called_once_with(
        api_base="http://localhost:11434",
        model="llama2",
        embedding_model="nomic-embed-text",
        temperature=0.0,  # Default from OllamaProvider
        max_tokens=1000,  # Default from OllamaProvider
        timeout=60,  # Default from OllamaProvider
    )
    mock_openai.assert_not_called()
    mock_openrouter.assert_not_called()


@patch(
    "src.processing.concept_extractor.os.getenv"
)  # Patch getenv used by load_llm_config in concept_extractor
@patch("src.processing.concept_extractor.json.load")
@patch("builtins.open", new_callable=MagicMock)  # Mock open globally for this test
def test_load_concept_extractor_llm_config_openrouter_env_priority(
    mock_open_file, mock_json_load, mock_getenv
):
    """Test loading OpenRouter key from env var priority for concept_extractor (Bug 35)."""
    mock_getenv.side_effect = (
        lambda key, default=None: "env_openrouter_key"
        if key == "OPENROUTER_API_KEY"
        else default
    )
    mock_json_load.return_value = {
        "primary_provider": {
            "type": "openrouter",
            "api_key": "file_openrouter_key",  # This should be ignored
        }
    }
    mock_open_file.return_value.__enter__.return_value = (
        MagicMock()
    )  # Mock file context

    config = load_concept_extractor_llm_config("dummy_path")

    assert config["primary_provider"]["api_key"] == "env_openrouter_key"
    mock_getenv.assert_any_call("OPENROUTER_API_KEY")
    mock_open_file.assert_called_once_with("dummy_path", "r")


@patch("src.processing.concept_extractor.os.getenv")
@patch("src.processing.concept_extractor.json.load")
@patch("builtins.open", new_callable=MagicMock)
@patch("src.processing.concept_extractor.logger")  # Mock logger in concept_extractor
def test_load_concept_extractor_llm_config_openrouter_placeholder(
    mock_logger, mock_open_file, mock_json_load, mock_getenv
):
    """Test loading OpenRouter key handles placeholder for concept_extractor (Bug 35)."""
    mock_getenv.side_effect = lambda key, default=None: default
    mock_json_load.return_value = {
        "primary_provider": {
            "type": "openrouter",
            "api_key": "OPENROUTER_API_KEY",  # Placeholder
        }
    }
    mock_open_file.return_value.__enter__.return_value = MagicMock()

    config = load_concept_extractor_llm_config("dummy_path")

    assert config["primary_provider"]["api_key"] == ""  # Should be set to empty string
    mock_logger.warning.assert_called_once()
    assert "OPENROUTER_API_KEY" in mock_logger.warning.call_args[0][0]


@patch("src.llm.llm_provider.requests.post")
def test_ollama_provider_embedding_endpoint(mock_post):
    """Test OllamaProvider uses the correct embedding endpoint (Bug 40)."""
    # Assuming OllamaProvider uses /api/embeddings as per Bug 40 resolution
    provider = OllamaProvider(
        api_base="http://localhost:11434",
        model="llama2",
        embedding_model="nomic-embed-text",
    )
    provider.use_python_client = False  # Force HTTP for this test

    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
    mock_post.return_value = mock_response

    provider.get_embeddings(["test text"])

    mock_post.assert_called_once()
    called_url = mock_post.call_args[0][0]
    assert called_url == "http://localhost:11434/api/embeddings"


@patch(
    "src.processing.concept_extractor.smart_chunk_text"
)  # Mock the one concept_extractor._chunk_text calls
def test__concept_extractor_chunk_text_robustness(mock_smart_chunk_text_dep):
    """Test ConceptExtractor._chunk_text wrapper ensures list[str] return type (Bug 36)."""
    # Mock dependencies for ConceptExtractor instantiation
    mock_llm_manager = MagicMock()
    # ConceptExtractor in the provided code doesn't take db in __init__
    # extractor = ConceptExtractor(llm_manager=mock_llm_manager) # Assuming llm_manager is passed or set
    extractor = ConceptExtractor()  # Default init
    extractor.llm_manager = mock_llm_manager  # Manually set if needed by other methods

    # Case 1: smart_chunk_text (dependency) returns None
    mock_smart_chunk_text_dep.return_value = None
    chunks = extractor._chunk_text("some text", 100)
    assert isinstance(chunks, list), (
        "Should return a list even if dependency returns None"
    )
    assert all(isinstance(c, str) for c in chunks), (
        "All items in list should be strings"
    )
    # Based on the fix "ensuring it always returns a list[str]", [] or ["None"] are plausible.
    # The provided concept_extractor._chunk_text returns [] on error or unexpected type.
    assert chunks == [], "Should return empty list if smart_chunk_text returns None"

    # Case 2: smart_chunk_text (dependency) returns a non-list, non-None value
    mock_smart_chunk_text_dep.return_value = "single chunk string"
    chunks = extractor._chunk_text("some text", 100)
    assert isinstance(chunks, list), (
        "Should return a list even if dependency returns a string"
    )
    assert all(isinstance(c, str) for c in chunks), (
        "All items in list should be strings"
    )
    # The provided concept_extractor._chunk_text returns ["single chunk string"] in this case.
    assert chunks == ["single chunk string"], "Should wrap string in a list"

    # Case 3: smart_chunk_text (dependency) raises an exception
    mock_smart_chunk_text_dep.side_effect = ValueError("Chunking failed")
    chunks = extractor._chunk_text("some text", 100)
    assert isinstance(chunks, list), (
        "Should return a list even if dependency raises error"
    )
    assert all(isinstance(c, str) for c in chunks), (
        "All items in list should be strings"
    )
    assert chunks == [], "Should return empty list if smart_chunk_text raises error"


@patch("src.llm.llm_provider.OllamaProvider")
@patch("src.llm.llm_provider.OpenAIProvider")
@patch("src.llm.llm_provider.OpenRouterProvider")
def test_create_llm_provider_type_casting(mock_openrouter, mock_openai, mock_ollama):
    """Test create_llm_provider casts config values to str (Bug 36)."""
    config_numeric = {
        "type": "ollama",
        "api_base": 12345,  # Should be cast to str
        "model": None,  # Should be cast to str ("None")
        "embedding_model": 678.9,  # Should be cast to str
    }
    create_llm_provider(config_numeric)
    mock_ollama.assert_called_once_with(
        api_base="12345",
        model="None",
        embedding_model="678.9",
        temperature=0.0,
        max_tokens=1000,
        timeout=60,  # Defaults
    )
    mock_ollama.reset_mock()

    config_str = {
        "type": "ollama",
        "api_base": "http://localhost:11434",
        "model": "llama2",
        "embedding_model": "nomic-embed-text",
    }
    create_llm_provider(config_str)
    mock_ollama.assert_called_once_with(
        api_base="http://localhost:11434",
        model="llama2",
        embedding_model="nomic-embed-text",
        temperature=0.0,
        max_tokens=1000,
        timeout=60,  # Defaults
    )
