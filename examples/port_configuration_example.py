"""Example of using the centralized port configuration.

This script demonstrates how to use the centralized port configuration
to get port numbers for various services.
"""

from src.config import get_port, is_port_in_use, print_port_configuration


def main() -> None:
    """Demonstrate port configuration usage."""
    # Print the current port configuration
    print_port_configuration()

    # Get port numbers for various services
    api_port = get_port("api")
    mpc_port = get_port("mpc")
    mcp_port = get_port("mcp")
    neo4j_port = get_port("neo4j_bolt")

    print("\nIndividual Port Examples:")
    print(f"API Port: {api_port}")
    print(f"MPC Port: {mpc_port}")
    print(f"MCP Port: {mcp_port}")
    print(f"Neo4j Bolt Port: {neo4j_port}")

    # Check if ports are in use
    print("\nPort Usage Status:")
    print(f"API Port ({api_port}) in use: {is_port_in_use(api_port)}")
    print(f"MPC Port ({mpc_port}) in use: {is_port_in_use(mpc_port)}")
    print(f"MCP Port ({mcp_port}) in use: {is_port_in_use(mcp_port)}")
    print(f"Neo4j Bolt Port ({neo4j_port}) in use: {is_port_in_use(neo4j_port)}")


if __name__ == "__main__":
    main()
