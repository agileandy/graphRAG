"""Simple test script to check MPC server connection."""

import asyncio
import json
import sys

import websockets


async def test_connection(uri) -> bool | None:
    """Test connection to MPC server."""
    try:
        print(f"Connecting to {uri}...")
        async with websockets.connect(uri) as websocket:
            print("Connected successfully!")

            # Send a simple message to get available actions
            message = {
                "action": "invalid-action"  # This will trigger the server to return available actions
            }

            print("Sending message...")
            await websocket.send(json.dumps(message))

            print("Waiting for response...")
            response = await websocket.recv()

            print("\nResponse received:")
            response_data = json.loads(response)
            print(json.dumps(response_data, indent=2))

            return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


async def main() -> None:
    uri = "ws://localhost:8766"
    success = await test_connection(uri)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
