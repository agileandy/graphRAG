"""Configuration utilities for GraphRAG project.

This module provides utilities for loading and managing configuration.
"""

import json
import logging

from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

def load_config(config_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load configuration from environment variables with defaults.
=======
import os
from typing import Any

logger = logging.getLogger(__name__)


def load_config(config_path: str | None = None) -> dict[str, Any]:
    """Load configuration from file.

    Args:
        config_path: Path to configuration file
      
        Returns:
        Dictionary with configuration values
    """
    # Get ports from centralized configuration
    from src.config.ports import get_port
    mpc_port = get_port('mpc')
    docker_neo4j_port = get_port('docker_neo4j_bolt')

    # Default configuration that can be overridden by environment variables
    DEFAULT_CONFIG = {
        "MPC_HOST": "localhost",
        "MPC_PORT": str(mpc_port),
        "NEO4J_URI": f"bolt://localhost:{docker_neo4j_port}",  # Default port for Docker mapping
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "graphrag"
    }

    config = DEFAULT_CONFIG.copy()

    # Override defaults with environment variables if they exist
    for key in config:
        if key in os.environ:
            config[key] = os.environ[key]

    return config
=======
        Configuration dictionary

    """
    # Default config path for LLM configuration
    if config_path is None:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "config",
            "llm_config.json",
        )

    try:
        with open(config_path) as f:
            config = json.load(f)
        return config
    except Exception as e:
        logger.error(f"Error loading config from {config_path}: {e}")
        # Return default config
        return {
            "primary_provider": {
                "type": "openai-compatible",
                "api_base": "http://192.168.1.21:1234/v1",
                "api_key": "dummy-key",
                "model": "lmstudio-community/Phi-4-mini-reasoning-MLX-4bit",
                "temperature": 0.1,
                "max_tokens": 1000,
                "timeout": 60,
            }
        }


def get_embedding_provider_config() -> dict[str, Any]:
    """Get the embedding provider configuration.

    Returns:
        Embedding provider configuration dictionary

    """
    config = load_config()
    return config.get("embedding_provider", {})


def get_reranker_provider_config() -> dict[str, Any]:
    """Get the reranker provider configuration.

    Returns:
        Reranker provider configuration dictionary

    """
    config = load_config()
    return config.get("reranker_provider", {})
