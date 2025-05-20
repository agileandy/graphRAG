"""
LLM Provider module for GraphRAG project.

This module provides a flexible architecture for integrating with various LLM endpoints,
including local LLM servers (e.g., LM Studio, Ollama) and cloud APIs.
"""
from typing import List, Dict, Any, Optional
import requests
import logging
import json
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
                 api_base: str = None,
                 api_key: str = None,
                 model: str = None,
                 embedding_model: Optional[str] = None,
                 temperature: float = 0.0,
                 max_tokens: int = 1000,
                 timeout: int = 60):
        # Load from environment if not provided
        self.api_base = api_base or os.getenv("LLM_API_BASE", "http://localhost:1234/v1")
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.model = model or os.getenv("LLM_MODEL", "local-model")
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

class OpenRouterProvider(LLMProvider):
    """Provider for OpenRouter API endpoints."""

    def __init__(self,
                 api_key: str,
                 model: str = "google/gemini-2.0-flash-exp:free",
                 embedding_model: Optional[str] = None,
                 temperature: float = 0.0,
                 max_tokens: int = 1000,
                 timeout: int = 60):
        """
        Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key
            model: Model name to use (default: google/gemini-2.0-flash-exp:free)
            embedding_model: Model for embeddings (if different)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            timeout: Request timeout in seconds
        """
        self.api_base = "https://openrouter.ai/api/v1"
        self.api_key = api_key
        self.model = model
        self.embedding_model = embedding_model or "openai/text-embedding-ada-002"  # Default embedding model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

        # Test connection
        self._test_connection()

    def _test_connection(self):
        """Test connection to the OpenRouter API endpoint."""
        try:
            # Simple test request to check API key validity
            response = requests.get(
                f"{self.api_base}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout
            )

            if response.status_code == 200:
                logger.info(f"Successfully connected to OpenRouter API")
                models = response.json().get("data", [])
                if models:
                    logger.info(f"Available models include: {', '.join([m.get('id', '') for m in models[:5]])}")
            else:
                logger.warning(f"Connected to OpenRouter but received status code {response.status_code}")
                logger.warning(f"Response: {response.text}")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Failed to connect to OpenRouter API: {e}")

    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text based on prompt using OpenRouter API.

        Args:
            prompt: Text prompt
            **kwargs: Additional parameters to override defaults

        Returns:
            Generated text
        """
        system_prompt = kwargs.get("system_prompt", "You are a helpful assistant.")
        model_name = kwargs.get("model", self.model)

        # Prepare request payload
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens)
        }

        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in ["system_prompt", "model", "temperature", "max_tokens"]:
                payload[key] = value

        try:
            # Make API request
            logger.info(f"Sending request to OpenRouter API with model {model_name}")

            try:
                response = requests.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "https://graphrag.local",  # Required by OpenRouter
                        "X-Title": "GraphRAG",  # Optional but recommended
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=self.timeout
                )

                # Log the response status code
                logger.info(f"OpenRouter API response status code: {response.status_code}")

                # Check for error status codes
                if response.status_code != 200:
                    logger.error(f"OpenRouter API error: {response.text}")
                    return f"Error: OpenRouter API returned status code {response.status_code}"

                # Parse the response
                try:
                    result = response.json()
                except Exception as e:
                    logger.error(f"Error parsing OpenRouter API response: {e}")
                    logger.error(f"Response text: {response.text[:500]}")
                    return f"Error: Could not parse OpenRouter API response"

                # Extract generated text
                if "choices" in result and len(result["choices"]) > 0:
                    message = result["choices"][0]["message"]
                    content = message.get("content", "")
                    logger.info(f"Successfully generated text with OpenRouter API (length: {len(content)})")
                    return content
                else:
                    logger.warning(f"No choices in OpenRouter response: {result}")
                    # Fall back to using the entire response as a string
                    return f"API Response: {json.dumps(result)}"
            except requests.exceptions.Timeout:
                logger.error(f"OpenRouter API request timed out after {self.timeout} seconds")
                return "Error: OpenRouter API request timed out"

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling OpenRouter API: {e}")
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
        Get embeddings for texts using OpenRouter API.

        Args:
            texts: List of texts to embed
            **kwargs: Additional parameters

        Returns:
            List of embedding vectors
        """
        model = kwargs.get("model", self.embedding_model)

        try:
            logger.info(f"Sending embeddings request to OpenRouter API with model {model}")

            try:
                # Make API request
                response = requests.post(
                    f"{self.api_base}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "HTTP-Referer": "https://graphrag.local",
                        "X-Title": "GraphRAG",
                        "Content-Type": "application/json"
                    },
                    json={"model": model, "input": texts},
                    timeout=self.timeout
                )

                # Log the response status code
                logger.info(f"OpenRouter API embeddings response status code: {response.status_code}")

                # Check for error status codes
                if response.status_code != 200:
                    logger.error(f"OpenRouter API embeddings error: {response.text}")
                    return [[0.0] for _ in texts]  # Return dummy embeddings

                # Parse the response
                try:
                    result = response.json()
                except Exception as e:
                    logger.error(f"Error parsing OpenRouter API embeddings response: {e}")
                    logger.error(f"Response text: {response.text[:500]}")
                    return [[0.0] for _ in texts]  # Return dummy embeddings

                # Extract embeddings
                if "data" in result:
                    embeddings = [item["embedding"] for item in result["data"]]
                    logger.info(f"Successfully generated {len(embeddings)} embeddings with OpenRouter API")
                    return embeddings
                else:
                    logger.warning(f"No embeddings in OpenRouter response: {result}")
                    return [[0.0] for _ in texts]  # Return dummy embeddings
            except requests.exceptions.Timeout:
                logger.error(f"OpenRouter API embeddings request timed out after {self.timeout} seconds")
                return [[0.0] for _ in texts]  # Return dummy embeddings

        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting embeddings: {e}")
            # Return dummy embeddings in case of error
            return [[0.0] for _ in texts]

class OllamaProvider(LLMProvider):
    """Provider for Ollama API endpoints."""

    def __init__(self,
                 api_base: str = "http://localhost:11434",
                 model: str = "qwen3",
                 embedding_model: Optional[str] = "snowflake-arctic-embed2",
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

        # Try to import the Ollama Python client
        try:
            import ollama
            self.ollama = ollama
            self.use_python_client = True
            logger.info("Using Ollama Python client for API calls")
        except ImportError:
            logger.warning("Ollama Python client not found. Using HTTP requests instead.")
            self.use_python_client = False

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
        model_name = kwargs.get("model", self.model)

        # Prepare request payload
        payload = {
            "model": model_name,
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
            if self.use_python_client:
                # Use the Python client
                try:
                    # Convert payload to match ollama.generate parameters
                    generate_params = {
                        "model": model_name,
                        "prompt": prompt,
                        "system": system,
                        "temperature": kwargs.get("temperature", self.temperature),
                        "num_predict": kwargs.get("max_tokens", self.max_tokens),
                    }

                    # Add any additional parameters
                    for key, value in kwargs.items():
                        if key not in ["system_prompt", "model", "temperature", "max_tokens"]:
                            generate_params[key] = value

                    response = self.ollama.generate(**generate_params)
                    return response.response
                except Exception as e:
                    logger.error(f"Error using Ollama Python client: {e}")
                    # Fall back to HTTP request
                    logger.info("Falling back to HTTP request for generation")
                    self.use_python_client = False
                    # Continue to HTTP request path

            # If Python client is not available or failed, use HTTP request
            if not self.use_python_client:
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

            # This should never be reached, but add a fallback return
            return ""

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
                if self.use_python_client:
                    # Use the Python client
                    try:
                        response = self.ollama.embeddings(
                            model=model,
                            prompt=text
                        )
                        embedding = response.embedding
                        embeddings.append(embedding)
                    except Exception as e:
                        logger.error(f"Error using Ollama Python client for embeddings: {e}")
                        # Fall back to HTTP request
                        logger.info("Falling back to HTTP request for embeddings")
                        self.use_python_client = False
                        # Continue to HTTP request path

                # If Python client is not available or failed, use HTTP request
                if not self.use_python_client:
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

            except Exception as e:
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
            response = self.primary_provider.generate(prompt, **kwargs)

            # Check if the response indicates an error or rate limiting
            if (response.startswith("Error:") or
                response.startswith("API Response:") or
                "rate-limited" in response or
                "error" in response.lower()):

                logger.warning(f"Primary provider returned error response: {response[:100]}...")

                if self.fallback_provider:
                    logger.info("Trying fallback provider due to error in primary response")
                    return self.fallback_provider.generate(prompt, **kwargs)
                else:
                    return response

            return response
        except Exception as e:
            logger.warning(f"Primary provider failed with exception: {e}")
            if self.fallback_provider:
                logger.info("Trying fallback provider due to exception")
                return self.fallback_provider.generate(prompt, **kwargs)
            else:
                raise

    def generate_batch(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate text for multiple prompts with fallback."""
        results = []
        primary_failed = False

        # Try to use primary provider for each prompt
        for prompt in prompts:
            if primary_failed and self.fallback_provider:
                # If primary provider has already failed, use fallback for all remaining prompts
                logger.info("Using fallback provider for remaining prompts in batch")
                remaining_prompts = prompts[len(results):]
                remaining_results = self.fallback_provider.generate_batch(remaining_prompts, **kwargs)
                results.extend(remaining_results)
                break

            try:
                response = self.primary_provider.generate(prompt, **kwargs)

                # Check if the response indicates an error or rate limiting
                if (response.startswith("Error:") or
                    response.startswith("API Response:") or
                    "rate-limited" in response or
                    "error" in response.lower()):

                    logger.warning(f"Primary provider returned error response in batch: {response[:100]}...")
                    primary_failed = True

                    if self.fallback_provider:
                        logger.info("Trying fallback provider for this prompt")
                        fallback_response = self.fallback_provider.generate(prompt, **kwargs)
                        results.append(fallback_response)
                    else:
                        results.append(response)
                else:
                    results.append(response)
            except Exception as e:
                logger.warning(f"Primary provider failed for prompt in batch: {e}")
                primary_failed = True

                if self.fallback_provider:
                    logger.info("Trying fallback provider for this prompt")
                    try:
                        fallback_response = self.fallback_provider.generate(prompt, **kwargs)
                        results.append(fallback_response)
                    except Exception as e2:
                        logger.error(f"Fallback provider also failed: {e2}")
                        results.append(f"Error: Both providers failed - {str(e2)}")
                else:
                    raise

        return results

    def get_embeddings(self, texts: List[str], **kwargs) -> List[List[float]]:
        """Get embeddings with fallback."""
        try:
            embeddings = self.primary_provider.get_embeddings(texts, **kwargs)

            # Check if embeddings are valid (not all zeros)
            all_zeros = True
            if embeddings and len(embeddings) > 0 and len(embeddings[0]) > 0:
                for emb in embeddings:
                    if any(val != 0.0 for val in emb):
                        all_zeros = False
                        break

            if all_zeros:
                logger.warning("Primary provider returned zero embeddings")
                if self.fallback_provider:
                    logger.info("Trying fallback provider for embeddings")
                    return self.fallback_provider.get_embeddings(texts, **kwargs)
                else:
                    return embeddings

            return embeddings
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
            embedding_model=config.get("embedding_model", "local-model"),
            temperature=config.get("temperature", 0.0),
            max_tokens=config.get("max_tokens", 1000),
            timeout=config.get("timeout", 60)
        )
    elif provider_type == "ollama":
        return OllamaProvider(
            api_base=config.get("api_base", "http://localhost:11434"),
            model=config.get("model", "qwen3"),
            embedding_model=config.get("embedding_model", "snowflake-arctic-embed2"),
            temperature=config.get("temperature", 0.0),
            max_tokens=config.get("max_tokens", 1000),
            timeout=config.get("timeout", 60)
        )
    elif provider_type == "openrouter":
        return OpenRouterProvider(
            api_key=config.get("api_key", ""),
            model=config.get("model", "google/gemini-2.0-flash-exp:free"),
            embedding_model=config.get("embedding_model", "openai/text-embedding-ada-002"),
            temperature=config.get("temperature", 0.0),
            max_tokens=config.get("max_tokens", 1000),
            timeout=config.get("timeout", 60)
        )
    else:
        raise ValueError(f"Unsupported provider type: {provider_type}")
