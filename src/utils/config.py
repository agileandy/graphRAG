"""
Configuration utilities for GraphRAG project.

This module provides utilities for loading and managing configuration.
"""
import os
import json
import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

def load_config(config_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load configuration from environment variables with defaults.

    Args:
        config_path: Path to configuration file
        
    Returns:
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

def get_embedding_provider_config() -> Dict[str, Any]:
    """
    Get the embedding provider configuration.
    
    Returns:
        Embedding provider configuration dictionary
    """
    config = load_config()
    return config.get("embedding_provider", {})

def get_reranker_provider_config() -> Dict[str, Any]:
    """
    Get the reranker provider configuration.
    
    Returns:
        Reranker provider configuration dictionary
    """
    config = load_config()
    return config.get("reranker_provider", {})
