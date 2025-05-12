"""
LLM Provider module for GraphRAG project.

This module provides a flexible architecture for integrating with various LLM endpoints,
including local LLM servers (e.g., LM Studio, Ollama) and cloud APIs.
"""
from typing import List, Dict, Any, Optional
import requests
import logging
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text based on prompt."""
        pass

    @abstractmethod
    def generate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate text for multiple prompts."""
        pass

    @abstractmethod
    def get_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """Get embeddings for texts."""
        pass

class OpenAICompatibleProvider(LLMProvider):
    """Provider for OpenAI-compatible API endpoints (including LM Studio)."""

    def __init__(self,
                 api_base: str = "http://localhost:1234/v1",
                 api_key: str = "dummy-key",
                 model: str = "local-model",
                 embedding_model: str = None,
                 temperature: float = 0.0,
                 max_tokens: int = 1000,
                 timeout: int = 60):
        """
        Initialize OpenAI-compatible provider.

        Args:
            api_base: Base URL for API
            api_key: API key (can be dummy for local servers)
            model: Model name to use
            embedding_model: Model for embeddings (if different)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
        """
        self.api_base = api_base
        self.api_key = api_key
        self.model = model
        self.embedding_model = embedding_model or model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        # Test connection
        self._test_connection()

    def _test_connection(self):
        """Test connection to the API endpoint."""
        try:
            # Simple test request
            response = requests.get(
                f"{self.api_base}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout
            )

            if response.status_code == 200:
                logger.info(f"Successfully connected to LLM API at {self.api_base}")
            else:
                logger.warning(f"Connected to {self.api_base} but received status code {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to connect to LLM API at {self.api_base}: {e}")

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on prompt using chat completions API.

        Args:
            prompt: Text prompt
            **kwargs: Additional parameters to override defaults

        Returns:
            Generated text
        """
        system_prompt = kwargs.get("system_prompt", "You are a helpful assistant.")
        model_name = kwargs.get("model", self.model)

        # Check if we're using Phi-4 model and format accordingly
        if "phi-4" in model_name.lower():
            # Format for Phi-4 models
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        else:
            # Standard format for other models
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

        # Prepare request payload
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens)
        }

        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in ["system_prompt", "model", "temperature", "max_tokens"]:
                payload[key] = value

        try:
            # Make API request
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            # Extract generated text
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0]["message"]

                # Handle different response formats (some models use content, others use reasoning_content)
                content = message.get("content", "")
                reasoning_content = message.get("reasoning_content", "")

                # Return whichever content field has data
                return content if content else reasoning_content
            else:
                logger.warning("No choices in LLM response")
                return ""

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling LLM API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status code: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
            return f"Error: {str(e)}"

    def generate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """
        Generate text for multiple prompts.

        Args:
            prompts: List of text prompts
            **kwargs: Additional parameters

        Returns:
            List of generated texts
        """
        return [self.generate(prompt, **kwargs) for prompt in prompts]

    def get_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Get embeddings for texts.

        Args:
            texts: List of texts to embed
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors
        """
        model = kwargs.get("model", self.embedding_model)

        try:
            # Make API request
            response = requests.post(
                f"{self.api_base}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": model, "input": texts},
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            # Extract embeddings
            if "data" in result:
                return [item["embedding"] for item in result["data"]]
            else:
                logger.warning("No embeddings in response")
                return [[0.0] for _ in texts]  # Return dummy embeddings

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting embeddings: {e}")
            # Return dummy embeddings in case of error
            return [[0.0] for _ in texts]

class OllamaProvider(LLMProvider):
    """Provider for Ollama API endpoints."""

    def __init__(self,
                 api_base: str = "http://localhost:11434",
                 model: str = "llama2",
                 embedding_model: str = None,
                 temperature: float = 0.0,
                 max_tokens: int = 1000,
                 timeout: int = 60):
        """
        Initialize Ollama provider.

        Args:
            api_base: Base URL for Ollama API
            model: Model name to use
            embedding_model: Model for embeddings (if different)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
        """
        self.api_base = api_base
        self.model = model
        self.embedding_model = embedding_model or model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        # Test connection
        self._test_connection()

    def _test_connection(self):
        """Test connection to the Ollama API endpoint."""
        try:
            # Simple test request
            response = requests.get(
                f"{self.api_base}/api/tags",
                timeout=self.timeout
            )

            if response.status_code == 200:
                logger.info(f"Successfully connected to Ollama API at {self.api_base}")
                models = response.json().get("models", [])
                if models:
                    logger.info(f"Available models: {', '.join([m.get('name', '') for m in models])}")
            else:
                logger.warning(f"Connected to {self.api_base} but received status code {response.status_code}")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to connect to Ollama API at {self.api_base}: {e}")

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on prompt using Ollama API.

        Args:
            prompt: Text prompt
            **kwargs: Additional parameters to override defaults

        Returns:
            Generated text
        """
        # Prepare system prompt if provided
        system = kwargs.get("system_prompt", "")

        # Prepare request payload
        payload = {
            "model": kwargs.get("model", self.model),
            "prompt": prompt,
            "system": system,
            "temperature": kwargs.get("temperature", self.temperature),
            "num_predict": kwargs.get("max_tokens", self.max_tokens),
            "stream": False
        }

        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in ["system_prompt", "model", "temperature", "max_tokens"]:
                payload[key] = value

        try:
            # Make API request
            response = requests.post(
                f"{self.api_base}/api/generate",
                json=payload,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            # Extract generated text
            return result.get("response", "")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status code: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text}")
            return f"Error: {str(e)}"

    def generate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """
        Generate text for multiple prompts.

        Args:
            prompts: List of text prompts
            **kwargs: Additional parameters

        Returns:
            List of generated texts
        """
        return [self.generate(prompt, **kwargs) for prompt in prompts]

    def get_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Get embeddings for texts using Ollama API.

        Args:
            texts: List of texts to embed
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors
        """
        model = kwargs.get("model", self.embedding_model)

        embeddings = []

        for text in texts:
            try:
                # Make API request
                response = requests.post(
                    f"{self.api_base}/api/embeddings",
                    json={"model": model, "prompt": text},
                    timeout=self.timeout
                )

                response.raise_for_status()
                result = response.json()

                # Extract embedding
                embedding = result.get("embedding", [0.0])
                embeddings.append(embedding)

            except requests.exceptions.RequestException as e:
                logger.error(f"Error getting embedding: {e}")
                # Return dummy embedding in case of error
                embeddings.append([0.0])

        return embeddings

class LLMManager:
    """Manager for LLM providers with fallback capabilities."""

    def __init__(self, primary_provider: LLMProvider, fallback_provider: Optional[LLMProvider] = None):
        """
        Initialize LLM manager.

        Args:
            primary_provider: Primary LLM provider
            fallback_provider: Fallback provider (optional)
        """
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text with fallback capability.

        Args:
            prompt: Text prompt
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        try:
            return self.primary_provider.generate(prompt, **kwargs)
        except Exception as e:
            logger.warning(f"Primary provider failed: {e}")
            if self.fallback_provider:
                logger.info("Trying fallback provider")
                return self.fallback_provider.generate(prompt, **kwargs)
            else:
                raise

    def generate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate text for multiple prompts with fallback."""
        try:
            return self.primary_provider.generate_batch(prompts, **kwargs)
        except Exception as e:
            logger.warning(f"Primary provider failed for batch: {e}")
            if self.fallback_provider:
                logger.info("Trying fallback provider for batch")
                return self.fallback_provider.generate_batch(prompts, **kwargs)
            else:
                raise

    def get_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """Get embeddings with fallback."""
        try:
            return self.primary_provider.get_embeddings(texts, **kwargs)
        except Exception as e:
            logger.warning(f"Primary provider failed for embeddings: {e}")
            if self.fallback_provider:
                logger.info("Trying fallback provider for embeddings")
                return self.fallback_provider.get_embeddings(texts, **kwargs)
            else:
                raise

# Factory function to create LLM provider based on configuration
def create_llm_provider(config: Dict[str, Any]) -> LLMProvider:
    """
    Create LLM provider based on configuration.

    Args:
        config: Configuration dictionary

    Returns:
        LLM provider instance
    """
    provider_type = config.get("type", "openai-compatible")

    if provider_type == "openai-compatible":
        return OpenAICompatibleProvider(
            api_base=config.get("api_base", "http://localhost:1234/v1"),
            api_key=config.get("api_key", "dummy-key"),
            model=config.get("model", "local-model"),
            embedding_model=config.get("embedding_model"),
            temperature=config.get("temperature", 0.0),
            max_tokens=config.get("max_tokens", 1000),
            timeout=config.get("timeout", 60)
        )
    elif provider_type == "ollama":
        return OllamaProvider(
            api_base=config.get("api_base", "http://localhost:11434"),
            model=config.get("model", "llama2"),
            embedding_model=config.get("embedding_model"),
            temperature=config.get("temperature", 0.0),
            max_tokens=config.get("max_tokens", 1000),
            timeout=config.get("timeout", 60)
        )
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")
