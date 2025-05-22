#!/usr/bin/env python3
"""Example client for the GraphRAG MCP server.

This script demonstrates how to interact with the GraphRAG MCP server
using the JSON-RPC 2.0 protocol.
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Any

import websockets

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.config import get_port


async def send_request(
    websocket, method: str, params: dict[str, Any], request_id: int
) -> dict[str, Any]:
    """Send a JSON-RPC request to the MCP server.

    Args:
        websocket: WebSocket connection
        method: Method name
        params: Method parameters
        request_id: Request ID

    Returns:
        Server response

    """
    # Create the request
    request = {"jsonrpc": "2.0", "method": method, "params": params, "id": request_id}

    # Send the request
    await websocket.send(json.dumps(request))

    # Receive the response
    response = await websocket.recv()

    # Parse the response
    return json.loads(response)


async def initialize(websocket) -> dict[str, Any]:
    """Initialize the MCP server connection.

    Args:
        websocket: WebSocket connection

    Returns:
        Initialize response

    """
    return await send_request(
        websocket,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcp-client-example", "version": "0.1.0"},
        },
        0,
    )


async def get_tools(websocket) -> list[dict[str, Any]]:
    """Get available tools from the MCP server.

    Args:
        websocket: WebSocket connection

    Returns:
        List of available tools

    """
    response = await send_request(websocket, "getTools", {}, 1)

    return response.get("result", {}).get("tools", [])


async def invoke_tool(
    websocket, tool_name: str, parameters: dict[str, Any], request_id: int
) -> dict[str, Any]:
    """Invoke a tool on the MCP server.

    Args:
        websocket: WebSocket connection
        tool_name: Tool name
        parameters: Tool parameters
        request_id: Request ID

    Returns:
        Tool result

    """
    return await send_request(
        websocket,
        "invokeTool",
        {"name": tool_name, "parameters": parameters},
        request_id,
    )


# Get MCP port from centralized configuration
mcp_port = get_port("mcp")


async def interactive_client(uri: str = f"ws://localhost:{mcp_port}") -> None:
    """Run an interactive client for the MCP server.

    Args:
        uri: WebSocket URI

    """
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to MCP server.")

            # Initialize the connection
            init_response = await initialize(websocket)
            print("\nInitialize response:")
            print(json.dumps(init_response, indent=2))

            # Get available tools
            tools = await get_tools(websocket)
            print("\nAvailable tools:")
            for i, tool in enumerate(tools):
                print(f"{i + 1}. {tool['name']} - {tool['description']}")

            # Interactive loop
            request_id = 2
            while True:
                print("\nEnter tool number to invoke (0 to exit):")
                choice = input("> ")

                if choice == "0":
                    break

                try:
                    tool_index = int(choice) - 1
                    if tool_index < 0 or tool_index >= len(tools):
                        print(
                            f"Invalid tool number. Please enter a number between 1 and {len(tools)}."
                        )
                        continue

                    tool = tools[tool_index]
                    print(f"\nInvoking tool: {tool['name']}")
                    print(f"Description: {tool['description']}")
                    print("Parameters:")

                    # Get parameters from user
                    parameters = {}
                    for prop_name, prop_info in (
                        tool.get("parameters", {}).get("properties", {}).items()
                    ):
                        required = prop_name in tool.get("parameters", {}).get(
                            "required", []
                        )
                        default = prop_info.get("default")
                        description = prop_info.get("description", "")

                        prompt = f"{prop_name}"
                        if description:
                            prompt += f" ({description})"
                        if required:
                            prompt += " (required)"
                        elif default is not None:
                            prompt += f" (default: {default})"
                        prompt += ": "

                        value = input(prompt)

                        if value:
                            # Convert value to appropriate type
                            if prop_info.get("type") == "integer":
                                parameters[prop_name] = int(value)
                            elif prop_info.get("type") == "boolean":
                                parameters[prop_name] = value.lower() in [
                                    "true",
                                    "yes",
                                    "y",
                                    "1",
                                ]
                            else:
                                parameters[prop_name] = value

                    # Invoke the tool
                    response = await invoke_tool(
                        websocket, tool["name"], parameters, request_id
                    )
                    request_id += 1

                    print("\nResponse:")
                    print(json.dumps(response, indent=2))

                except ValueError:
                    print("Invalid input. Please enter a number.")
                except Exception as e:
                    print(f"Error: {e}")

    except Exception as e:
        print(f"Error connecting to MCP server: {e}")


async def non_interactive_client(uri: str, tool_name: str, parameters: dict[str, Any]):
    """Run a non-interactive client for the MCP server.

    Args:
        uri: WebSocket URI
        tool_name: Tool name
        parameters: Tool parameters

    """
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to MCP server. Invoking tool: {tool_name}")

            # Initialize the connection
            await initialize(websocket)

            # Invoke the tool
            response = await invoke_tool(websocket, tool_name, parameters, 1)

            print("\nResponse:")
            print(json.dumps(response, indent=2))

            return response

    except Exception as e:
        print(f"Error connecting to MCP server: {e}")
        return None


def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Example client for the GraphRAG MCP server"
    )
    parser.add_argument("--host", type=str, default="localhost", help="MCP server host")
    parser.add_argument(
        "--port",
        type=int,
        default=mcp_port,
        help=f"MCP server port (default: {mcp_port})",
    )
    parser.add_argument(
        "--tool", type=str, help="Tool to invoke (non-interactive mode)"
    )
    parser.add_argument(
        "--params", type=str, help="Tool parameters as JSON (non-interactive mode)"
    )

    args = parser.parse_args()

    uri = f"ws://{args.host}:{args.port}"

    if args.tool:
        # Non-interactive mode
        parameters = {}
        if args.params:
            try:
                parameters = json.loads(args.params)
            except json.JSONDecodeError:
                print(f"Error parsing parameters: {args.params}")
                return

        asyncio.run(non_interactive_client(uri, args.tool, parameters))
    else:
        # Interactive mode
        asyncio.run(interactive_client(uri))


if __name__ == "__main__":
    main()
