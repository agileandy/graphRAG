"""
Port configuration for GraphRAG services.

This module provides a centralized location for all port configurations
used by GraphRAG services. It also includes utility functions for checking
port availability and resolving conflicts.

All port configurations should be defined here and accessed through the get_port() function.
Port values can be overridden through environment variables with the prefix GRAPHRAG_PORT_.

Example:
    To get the port for the API service:
    ```
    from src.config import get_port
    api_port = get_port('api')
    ```

    To override the API port through an environment variable:
    ```
    GRAPHRAG_PORT_API=5002
    ```
"""
import os
import socket
import logging
from typing import Dict, Optional, List, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Default port assignments
DEFAULT_PORTS = {
    # API Services
    "api": 5001,                # Main GraphRAG API

    # MCP Services
    "mcp": 8767,                # Model Context Protocol server
    "bug_mcp": 5005,            # Bug tracking MCP server

    # Database Services
    "neo4j_bolt": 7687,         # Neo4j Bolt protocol
    "neo4j_http": 7474,         # Neo4j HTTP API
    "neo4j_https": 7473,        # Neo4j HTTPS API

    # Monitoring Services
    "prometheus": 9090,         # Prometheus metrics
    "grafana": 3000,            # Grafana dashboard

    # Docker Port Mappings
    "docker_neo4j_bolt": 7688,  # Docker mapping for Neo4j Bolt
}

# Environment variable prefix for overriding ports
ENV_PREFIX = "GRAPHRAG_PORT_"

def get_port(service_name: str) -> int:
    """
    Get the port number for a service.

    Args:
        service_name: Name of the service

    Returns:
        Port number
    """
    # Check environment variable first
    env_var = f"{ENV_PREFIX}{service_name.upper()}"
    if env_var in os.environ:
        try:
            return int(os.environ[env_var])
        except ValueError:
            logger.warning(f"Invalid port in environment variable {env_var}: {os.environ[env_var]}")

    # Fall back to default port
    if service_name in DEFAULT_PORTS:
        return DEFAULT_PORTS[service_name]

    # If service not found, raise error
    raise ValueError(f"Unknown service: {service_name}")

def is_port_in_use(port: int, host: str = 'localhost') -> bool:
    """
    Check if a port is in use.

    Args:
        port: Port number to check
        host: Host to check

    Returns:
        True if port is in use, False otherwise
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def find_available_port(start_port: int, host: str = 'localhost') -> int:
    """
    Find an available port starting from start_port.

    Args:
        start_port: Port to start searching from
        host: Host to check

    Returns:
        Available port number
    """
    port = start_port
    while is_port_in_use(port, host):
        port += 1
    return port

def get_service_for_port(port: int) -> Optional[str]:
    """
    Get the service name for a port.

    Args:
        port: Port number

    Returns:
        Service name or None if not found
    """
    for service, service_port in DEFAULT_PORTS.items():
        if service_port == port:
            return service
    return None

def check_port_conflicts() -> List[Tuple[str, int]]:
    """
    Check for port conflicts among all services.

    Returns:
        List of (service_name, port) tuples with conflicts
    """
    conflicts = []
    for service, port in DEFAULT_PORTS.items():
        if is_port_in_use(port):
            conflicts.append((service, port))
    return conflicts

def print_port_configuration():
    """Print the current port configuration."""
    print("GraphRAG Port Configuration:")
    print("===========================")
    for service in sorted(DEFAULT_PORTS.keys()):
        port = get_port(service)
        in_use = is_port_in_use(port)
        status = "IN USE" if in_use else "available"
        print(f"{service.ljust(15)}: {port} ({status})")
    print()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Print current configuration
    print_port_configuration()

    # Check for conflicts
    conflicts = check_port_conflicts()
    if conflicts:
        print("Port conflicts detected:")
        for service, port in conflicts:
            print(f"  {service}: {port}")
    else:
        print("No port conflicts detected.")
